"""
Writes Decision objects as rows in decision_log Sheet.

42 Decision fields mapped 1:1 to 42 Sheet columns (preserving order).

Strategy:
- ENTER: each log() call writes immediately (not batched) — every entry matters
- SKIP (Route B): stdout line per decision (Actions audit) + in-run aggregation;
  flush_skip_summary() writes ONE batched append per run to the skip_summary
  tab (one row per skip-reason) — TASK-125. Max +1 Sheets write per run.
- None -> "" (matches scanner convention via .astype(str))
- bool -> str() ("True"/"False")
- Failures logged to stderr, return None (signal still processed)

Usage:
    from agent.logging.decision_logger import DecisionLogger

    logger = DecisionLogger(sheet_id="...")
    decision_id = logger.log(decision)  # -> "DEC-2026-05-03-00001" or None

Used by: trader.py (M3 wiring in M4), orchestrator.py (M10)
"""

import sys
import os
from datetime import datetime
from typing import Optional, List, Any

import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sheets_manager
from agent.trader.decision_logic import Decision
from agent.logging.decision_id_generator import DecisionIDGenerator

PERU_TZ = pytz.timezone("America/Lima")

# skip_summary tab schema (TASK-125) — must match create_agent_sheets.py
SKIP_SUMMARY_TICKER_CAP = 25


# Explicit ordered mapping: Decision field -> Sheet column
# IMPORTANT: This order MUST match the headers in create_agent_sheets.py decision_log
# 42 entries, validated by test_field_mapping_has_42_entries
FIELD_MAPPING = [
    # Identity (5)
    ("decision_id", "DecisionID"),
    ("timestamp", "Timestamp"),
    ("ticker", "Ticker"),
    ("signal_source", "SignalSource"),
    ("agent_mode", "AgentMode"),
    # Action (3)
    ("action", "Action"),
    ("reason", "Reason"),
    ("skip_reason", "SkipReason"),
    # Signal data (7)
    ("price", "Price"),
    ("volume", "Volume"),
    ("market_cap", "MarketCap"),
    ("float_shares", "Float"),
    ("open_price", "Open"),
    ("high", "High"),
    ("low", "Low"),
    # Metrics (9)
    ("score", "Score"),
    ("mxv", "MxV"),
    ("run_up", "RunUp"),
    ("atrx", "ATRX"),
    ("rsi", "RSI"),
    ("typical_price_dist", "TypicalPriceDist"),
    ("rel_vol", "REL_VOL"),
    ("price_vs_sma20", "PriceVsSMA20"),
    ("scan_change", "ScanChange"),
    ("float_pct", "FloatPct"),
    # Decision timing (1)
    ("decision_time_ms", "DecisionTimeMs"),
    # Quality (1)
    ("confidence_score", "ConfidenceScore"),
    # Tradability (4)
    ("is_shortable", "IsShortable"),
    ("borrow_fee", "BorrowFee"),
    ("borrow_available", "BorrowAvailable"),
    ("locate_status", "LocateStatus"),
    # Position calc (4)
    ("position_size_usd", "PositionSizeUSD"),
    ("quantity", "Quantity"),
    ("tp_price", "TPPrice"),
    ("sl_price", "SLPrice"),
    # Safety (4)
    ("existing_position", "ExistingPosition"),
    ("buying_power", "BuyingPower"),
    ("cold_start_concurrent_remaining", "ColdStartConcurrentLeft"),
    ("cold_start_daily_remaining", "ColdStartDailyLeft"),
    # Execution (3)
    ("order_id", "OrderID"),
    ("order_status", "OrderStatus"),
    ("execution_price", "ExecutionPrice"),
]


def _format_value(value: Any) -> Any:
    """Convert a Decision field value for Sheet writing.

    - None -> "" (matches scanner)
    - bool -> str() ("True"/"False")
    - everything else -> as-is
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    return value


class DecisionLogger:
    """
    Writes Decision objects to decision_log Sheet.

    Stateful: holds DecisionIDGenerator instance with in-memory counter.
    """

    def __init__(self, sheet_id: str):
        """
        Args:
            sheet_id: Google Sheet ID for decision_log
        """
        self.sheet_id = sheet_id
        self.id_generator = DecisionIDGenerator(sheet_id)
        # TASK-125: in-run SKIP aggregation (one container per GH-Actions run;
        # state dies with the container — exactly the intended scope).
        _now = datetime.now(PERU_TZ)
        self.run_start = _now.strftime("%Y-%m-%d %H:%M:%S")
        self.run_id = os.environ.get("GITHUB_RUN_ID") or _now.strftime("%Y%m%d-%H%M%S")
        self._skip_acc = {}  # reason_key -> {count, tickers[], score_min, score_max}

    def _accumulate_skip(self, decision: Decision) -> None:
        """Add one SKIP decision to the in-run accumulator (never raises)."""
        reason_raw = (
            getattr(decision, "skip_reason", "") or getattr(decision, "reason", "") or "UNKNOWN"
        )
        key = reason_raw.split(":")[0].strip() or "UNKNOWN"
        score = float(getattr(decision, "score", 0.0) or 0.0)
        ticker = getattr(decision, "ticker", "?") or "?"
        entry = self._skip_acc.get(key)
        if entry is None:
            self._skip_acc[key] = {
                "count": 1,
                "tickers": [ticker],
                "score_min": score,
                "score_max": score,
            }
        else:
            entry["count"] += 1
            entry["tickers"].append(ticker)
            entry["score_min"] = min(entry["score_min"], score)
            entry["score_max"] = max(entry["score_max"], score)

    def flush_skip_summary(self) -> int:
        """Write the aggregated SKIP counts to the skip_summary tab.

        ONE batched safe_append_rows call per run (one row per skip-reason).
        Worksheet is resolved lazily so a missing tab/config entry can never
        break logger construction. Never raises — visibility must not fail
        the trading run. Returns the number of rows written (0 on no-op/error).
        """
        if not self._skip_acc:
            return 0
        try:
            ws = sheets_manager.get_worksheet("skip_summary")
            if ws is None:
                print("[DecisionLogger] skip_summary worksheet unavailable", file=sys.stderr)
                return 0
            rows = []
            for key, entry in self._skip_acc.items():
                tickers = entry["tickers"]
                if len(tickers) > SKIP_SUMMARY_TICKER_CAP:
                    shown = ",".join(tickers[:SKIP_SUMMARY_TICKER_CAP])
                    tickers_cell = f"{shown} +{len(tickers) - SKIP_SUMMARY_TICKER_CAP} more"
                else:
                    tickers_cell = ",".join(tickers)
                rows.append([
                    self.run_start,
                    self.run_id,
                    key,
                    entry["count"],
                    tickers_cell,
                    round(entry["score_min"], 2),
                    round(entry["score_max"], 2),
                ])
            sheets_manager.safe_append_rows(
                ws, rows, dedup_col=1, dedup_vals={self.run_id}
            )
            self._skip_acc = {}
            return len(rows)
        except Exception as e:
            print(f"[DecisionLogger] skip_summary flush failed (non-fatal): {e}", file=sys.stderr)
            return 0

    def _decision_to_row(self, decision: Decision) -> List[Any]:
        """Convert Decision to ordered list of 42 values matching Sheet."""
        row = []
        for field_name, _sheet_col in FIELD_MAPPING:
            value = getattr(decision, field_name, None)
            row.append(_format_value(value))
        return row

    def log(self, decision: Decision) -> Optional[str]:
        """
        Log a decision to the Sheet.

        Sets decision.decision_id if not already set, then writes the row.

        Returns:
            decision_id (str) on success
            None on failure (stderr logged)
        """
        # Generate ID if not set (ticker embedded for collision-proof IDs — Bug #3 fix)
        if not decision.decision_id:
            _tk = getattr(decision, "ticker", "") or ""
            try:
                decision.decision_id = self.id_generator.generate(_tk)
            except Exception as e:
                print(f"[DecisionLogger] ID generation failed: {e}", file=sys.stderr)
                decision.decision_id = self.id_generator.fallback_timestamp_id()

        # Build row
        try:
            row = self._decision_to_row(decision)
            assert len(row) == len(FIELD_MAPPING), f"Row has {len(row)} values, expected {len(FIELD_MAPPING)}"
        except Exception as e:
            print(f"[DecisionLogger] Row construction failed: {e}", file=sys.stderr)
            return None

        # Write to Sheet
        # Route B: SKIP decisions go to stdout only (audit in Actions logs).
        # Rationale: ~80-100 SKIPs/minute were blowing Sheets API quota (429).
        # Only ENTER decisions reach the sheet — those are rare and meaningful.
        action = str(getattr(decision, "action", "")).upper()
        if action != "ENTER":
            ticker = getattr(decision, "ticker", "?")
            score = getattr(decision, "score", "?")
            reason = getattr(decision, "skip_reason", "") or getattr(decision, "reason", "")
            print(
                f"[SKIP] {decision.decision_id} {ticker} Score={score} -> {reason}",
                file=sys.stdout,
                flush=True,
            )
            # TASK-125: aggregate for the end-of-run skip_summary batch write.
            # Guarded — aggregation must never break the logging path.
            try:
                self._accumulate_skip(decision)
            except Exception as e:
                print(f"[DecisionLogger] skip accumulation failed: {e}", file=sys.stderr)
            return decision.decision_id  # success — NOT an error

        # ENTER decisions: write to sheet (rare event, only when we actually enter)
        try:
            gc = sheets_manager._get_gc()
            ws = gc.open_by_key(self.sheet_id).sheet1
            import sheets_manager as _sm
            _sm.safe_append_row(ws, row, dedup_col=0, dedup_val=decision.decision_id)
            _sm.invalidate_cache("decision_log")  # fresh read next time
            return decision.decision_id
        except Exception as e:
            print(f"[DecisionLogger] Sheet write failed for ENTER {decision.decision_id}: {e}", file=sys.stderr)
            return None
