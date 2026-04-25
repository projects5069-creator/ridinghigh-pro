#!/usr/bin/env python3
"""
migrate_sl_hit_d5.py — Issue #1 SL Unification migration
=========================================================

One-time migration script that:
1. Renames the SL7_Hit_D1 column → SL_Hit_D5 in post_analysis Sheet
2. Recalculates SL_Hit_D5 for all rows using:
   - New threshold: SL_THRESHOLD_PCT (now 10%, was 7%)
   - New window: D1-D5 (was only D1)

Run from ~/RidingHighPro/. Uses google_credentials.json (Service Account).

Created: 2026-04-25
Author: Issue #1 SL Unification
"""

import sys
import json
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SL_THRESHOLD_FRAC, SL_THRESHOLD_PCT


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

OLD_COL_NAME = "SL7_Hit_D1"
NEW_COL_NAME = "SL_Hit_D5"


def get_post_analysis_sheet():
    """Open the post_analysis Sheet for the active month."""
    creds = Credentials.from_service_account_file("google_credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)

    config = json.load(open("sheets_config.json"))
    # Use the month that has actual data (not empty future months)
    months = sorted(config.keys())
    active_month = None
    for m in reversed(months):
        test_id = config[m].get("post_analysis")
        if test_id:
            try:
                test_ws = gc.open_by_key(test_id).sheet1
                if len(test_ws.row_values(1)) > 0:
                    active_month = m
                    break
            except Exception:
                continue
    if not active_month:
        active_month = months[-1] if months else None
    if not active_month:
        raise RuntimeError("No months found in sheets_config.json")

    sheets = config[active_month]
    sheet_id = sheets.get("post_analysis")
    if not sheet_id:
        raise RuntimeError(f"No post_analysis sheet configured for {active_month}")

    print(f"[migrate] Active month: {active_month}")
    print(f"[migrate] Opening post_analysis sheet: {sheet_id}")

    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1
    return ws, active_month


def get_column_index(headers, name):
    """1-based column index. Returns None if not found."""
    try:
        return headers.index(name) + 1
    except ValueError:
        return None


def recalculate_sl_hit_d5(row, headers):
    """
    Calculate SL_Hit_D5 from a single row using D1-D5 highs.
    Returns: 1 if SL hit, 0 if not, None if data missing.
    """
    def get_val(col_name):
        idx = get_column_index(headers, col_name)
        if idx is None:
            return None
        val = row[idx - 1] if idx - 1 < len(row) else None
        try:
            return float(val) if val not in (None, "", "None") else None
        except (TypeError, ValueError):
            return None

    scan_price = get_val("ScanPrice")
    if not scan_price or scan_price <= 0:
        return None

    sl_threshold_price = scan_price * (1 + SL_THRESHOLD_FRAC)

    for day in range(1, 6):
        high = get_val(f"D{day}_High")
        if high is not None and high >= sl_threshold_price:
            return 1

    # Check we had at least D1 data — if all D-day highs are missing → unknown
    has_any_high = any(get_val(f"D{d}_High") is not None for d in range(1, 6))
    if not has_any_high:
        return None

    return 0


def main():
    print(f"[migrate] SL Unification migration starting")
    print(f"[migrate] Threshold: {SL_THRESHOLD_PCT}% (frac={SL_THRESHOLD_FRAC})")
    print(f"[migrate] Window: D1-D5 (was D1 only)")
    print(f"[migrate] Renaming: {OLD_COL_NAME} → {NEW_COL_NAME}")
    print()

    ws, active_month = get_post_analysis_sheet()

    # Read all data
    all_values = ws.get_all_values()
    if not all_values:
        print("[migrate] Sheet is empty — nothing to migrate")
        return

    headers = all_values[0]
    rows = all_values[1:]

    print(f"[migrate] Headers: {len(headers)} columns")
    print(f"[migrate] Data rows: {len(rows)}")

    # ── Step 1: Rename column ─────────────────────────────────────────────
    if OLD_COL_NAME in headers:
        old_idx = headers.index(OLD_COL_NAME)
        print(f"[migrate] Step 1: Renaming column {OLD_COL_NAME} (col {old_idx + 1}) → {NEW_COL_NAME}")
        # Update header cell
        from gspread.utils import rowcol_to_a1
        cell_ref = rowcol_to_a1(1, old_idx + 1)
        ws.update(values=[[NEW_COL_NAME]], range_name=cell_ref)
        headers[old_idx] = NEW_COL_NAME
        print(f"[migrate] Step 1: ✅ Renamed in cell {cell_ref}")
    elif NEW_COL_NAME in headers:
        print(f"[migrate] Step 1: Column already named {NEW_COL_NAME} — skipping rename")
    else:
        print(f"[migrate] Step 1: ⚠️  Neither {OLD_COL_NAME} nor {NEW_COL_NAME} found in headers")
        print(f"[migrate] Headers: {headers}")
        return

    # ── Step 2: Recalculate values for all rows ───────────────────────────
    sl_col_idx = headers.index(NEW_COL_NAME)
    print(f"\n[migrate] Step 2: Recalculating {NEW_COL_NAME} for {len(rows)} rows")

    new_values = []
    stats = {"hit": 0, "no_hit": 0, "unknown": 0, "unchanged": 0, "changed": 0}

    for row in rows:
        old_val = row[sl_col_idx] if sl_col_idx < len(row) else ""
        new_val = recalculate_sl_hit_d5(row, headers)

        if new_val == 1:
            stats["hit"] += 1
        elif new_val == 0:
            stats["no_hit"] += 1
        else:
            stats["unknown"] += 1

        new_str = "" if new_val is None else str(new_val)
        if str(old_val).strip() != new_str:
            stats["changed"] += 1
        else:
            stats["unchanged"] += 1

        new_values.append([new_str])

    # Bulk update column
    from gspread.utils import rowcol_to_a1
    range_start = rowcol_to_a1(2, sl_col_idx + 1)
    range_end = rowcol_to_a1(len(rows) + 1, sl_col_idx + 1)
    range_str = f"{range_start}:{range_end}"

    print(f"[migrate] Step 2: Writing {len(new_values)} values to {range_str}")
    ws.update(values=new_values, range_name=range_str, value_input_option="RAW")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"[migrate] ✅ DONE")
    print("=" * 60)
    print(f"  Hit (price rose ≥{SL_THRESHOLD_PCT}% on D1-D5): {stats['hit']}")
    print(f"  No hit:                                       {stats['no_hit']}")
    print(f"  Unknown (no D-day data):                      {stats['unknown']}")
    print(f"  Values changed:                               {stats['changed']}")
    print(f"  Values unchanged:                             {stats['unchanged']}")
    print()
    print(f"  Win rate (TP10) impact: SL hit count moved")
    print(f"  from old D1-only/7% → new D1-D5/{SL_THRESHOLD_PCT}%")


if __name__ == "__main__":
    main()
