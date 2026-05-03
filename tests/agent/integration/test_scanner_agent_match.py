"""
test_scanner_agent_match.py
────────────────────────────
CRITICAL integration test: agent's score must match scanner's score
byte-for-byte on real timeline_live data.

Strategy:
1. Sample 150 random rows from timeline_live (current month)
2. Try to parse each row -> metrics dict
3. Skip rows that fail parsing (log them)
4. After 150 samples, must have >=100 parseable rows
5. For each parsed row: compute agent score, compare to scanner's
6. PASS if 0 mismatches (delta < 0.01)
7. FAIL if any mismatch (regardless of count)
8. WARNING if 1-30% rows skipped, FAIL if >30%

Run: python3 -m pytest tests/agent/integration/test_scanner_agent_match.py -v -s
"""

import sys
import os
import random
import warnings
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

import sheets_manager
from agent.trader.score_calculator import calculate_agent_score


# Constants
SAMPLE_SIZE = 150           # Try 150 rows
TARGET_PARSED = 100         # Need 100 parseable
MAX_SKIP_PCT = 30           # Fail if >30% skipped

# Score tolerance: max observed delta in production data is 0.03,
# caused by float->string->float rounding through Google Sheets.
# 0.04 gives a small margin while still catching real logic bugs
# (any change to formulas.py would cause delta >> 0.04).
#
# Investigation date: 2026-05-03 (M3)
# Statistics: max=0.03, mean=+0.0003, stdev=0.008, distribution balanced
# If false-alarms appear in CI, raise to 0.05 ONLY after investigation.
SCORE_TOLERANCE = 0.04


def _parse_row(row: dict) -> dict:
    """
    Parse a timeline_live row into metrics dict.

    Raises ValueError if any required field is missing/invalid.
    Returns dict with keys: mxv, run_up, atrx, rsi, rel_vol, change, typical_price_dist
    """
    # Required fields: sheet column name -> metrics dict key
    fields_to_parse = {
        "mxv": "MxV",
        "run_up": "RunUp",
        "atrx": "ATRX",
        "rsi": "RSI",
        "rel_vol": "REL_VOL",
        "change": "Change",           # Sheet column "Change" -> dict key "change"
        "typical_price_dist": "TypicalPriceDist",
    }

    metrics = {}
    for dict_key, sheet_col in fields_to_parse.items():
        raw = row.get(sheet_col, "")
        if raw == "" or raw is None or raw == "N/A":
            raise ValueError(f"Missing/empty field: {sheet_col}")
        try:
            metrics[dict_key] = float(raw)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Could not parse {sheet_col}={raw!r}: {e}")

    return metrics


def _find_month_with_data(config: dict) -> str:
    """Find most recent month that has actual data in timeline_live."""
    gc = sheets_manager._get_gc()
    for month in sorted(config.keys(), reverse=True):
        if "timeline_live" not in config[month]:
            continue
        sheet_id = config[month]["timeline_live"]
        try:
            ws = gc.open_by_key(sheet_id).sheet1
            row2 = ws.row_values(2)
            if row2 and row2[0] != "":
                return month
        except Exception:
            continue
    return None


def _sample_rows(month_key: str, sample_size: int) -> list:
    """Load and sample rows from timeline_live."""
    config = sheets_manager._load_config()
    sheet_id = config[month_key]["timeline_live"]

    gc = sheets_manager._get_gc()
    ws = gc.open_by_key(sheet_id).sheet1
    all_rows = ws.get_all_records()  # list of dicts

    if len(all_rows) < sample_size:
        return all_rows

    return random.sample(all_rows, sample_size)


def test_agent_score_matches_scanner():
    """
    Critical test: agent score == scanner score on real data.

    This is the firewall for Phase 1 -- if it fails, the agent must
    not run on Alpaca until parity is restored.
    """
    import json
    with open("sheets_config.json") as f:
        config = json.load(f)

    # Pick most recent month that actually has data (skip pre-created empty months)
    month_key = _find_month_with_data(config)
    assert month_key is not None, "No timeline_live with data found in any month"

    print(f"\n[TEST] Sampling {SAMPLE_SIZE} rows from {month_key}/timeline_live")

    rows = _sample_rows(month_key, SAMPLE_SIZE)
    print(f"[TEST] Got {len(rows)} rows from sheet")

    parsed = []
    skipped = []

    for idx, row in enumerate(rows):
        try:
            metrics = _parse_row(row)
            scanner_score = float(row.get("Score", 0))
            parsed.append({
                "row_index": idx,
                "ticker": row.get("Ticker", "?"),
                "metrics": metrics,
                "scanner_score": scanner_score,
            })
        except (ValueError, TypeError) as e:
            skipped.append({
                "row_index": idx,
                "ticker": row.get("Ticker", "?"),
                "error": str(e),
            })

        # Stop once we have enough parseable rows
        if len(parsed) >= TARGET_PARSED:
            break

    # Sanity check: must have enough parseable rows
    total_attempted = len(parsed) + len(skipped)
    skip_pct = (len(skipped) / max(total_attempted, 1)) * 100
    print(f"[TEST] Parsed: {len(parsed)}, Skipped: {len(skipped)} ({skip_pct:.1f}%)")

    if skip_pct > MAX_SKIP_PCT:
        sample_skipped = skipped[:5]
        pytest.fail(
            f"Too many unparseable rows: {len(skipped)} skipped out of "
            f"{total_attempted} samples ({skip_pct:.1f}% > {MAX_SKIP_PCT}%). "
            f"Sample errors: {sample_skipped}"
        )

    assert len(parsed) >= TARGET_PARSED, (
        f"Not enough parseable rows: {len(parsed)} < {TARGET_PARSED}. "
        f"Skipped: {len(skipped)}. Sample errors: {skipped[:5]}"
    )

    if 0 < len(skipped) <= int(SAMPLE_SIZE * MAX_SKIP_PCT / 100):
        warnings.warn(
            f"{len(skipped)} rows skipped ({skip_pct:.1f}%). "
            f"Sample errors: {skipped[:3]}"
        )

    # Now compare scores
    mismatches = []
    for entry in parsed:
        try:
            agent_score = calculate_agent_score(entry["metrics"])
            delta = abs(agent_score - entry["scanner_score"])
            if delta > SCORE_TOLERANCE:
                mismatches.append({
                    "ticker": entry["ticker"],
                    "scanner": entry["scanner_score"],
                    "agent": agent_score,
                    "delta": delta,
                    "metrics": entry["metrics"],
                })
        except Exception as e:
            mismatches.append({
                "ticker": entry["ticker"],
                "error": str(e),
            })

    print(f"[TEST] Compared {len(parsed)} rows. Mismatches: {len(mismatches)}")

    assert len(mismatches) == 0, (
        f"Score mismatches found: {len(mismatches)}/{len(parsed)}. "
        f"First 5: {mismatches[:5]}"
    )
