"""
Writes Decision objects as rows in decision_log Sheet.

41 Decision fields mapped 1:1 to 41 Sheet columns (preserving order).

Strategy:
- Each log() call writes immediately (not batched) — every decision matters
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
from typing import Optional, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sheets_manager
from agent.trader.decision_logic import Decision
from agent.logging.decision_id_generator import DecisionIDGenerator


# Explicit ordered mapping: Decision field -> Sheet column
# IMPORTANT: This order MUST match the headers in create_agent_sheets.py decision_log
# 41 entries, validated by test_field_mapping_has_41_entries
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

    def _decision_to_row(self, decision: Decision) -> List[Any]:
        """Convert Decision to ordered list of 41 values matching Sheet."""
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
            assert len(row) == 41, f"Row has {len(row)} values, expected 41"
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
            return decision.decision_id  # success — NOT an error

        # ENTER decisions: write to sheet (rare event, only when we actually enter)
        try:
            gc = sheets_manager._get_gc()
            ws = gc.open_by_key(self.sheet_id).sheet1
            import sheets_manager as _sm
            _sm.safe_append_row(ws, row, dedup_col=0, dedup_val=decision.decision_id)
            return decision.decision_id
        except Exception as e:
            print(f"[DecisionLogger] Sheet write failed for ENTER {decision.decision_id}: {e}", file=sys.stderr)
            return None
