"""
agent/execution/reconciler.py
──────────────────────────────
Synchronizes paper_portfolio Sheet with Alpaca positions reality.

Strategy:
- Alpaca is the source of truth for actual positions
- Sheet is the log of what we believe is happening
- When they conflict, Alpaca wins, Sheet gets corrected
- Discrepancies logged to system_events for investigation

Run schedule:
- Once after market close (post-EOD)
- On-demand via dashboard button (M9)

DRY_RUN positions are skipped (no Alpaca counterpart).
"""

import sys
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.execution.alpaca_broker import AlpacaBroker

logger = logging.getLogger("agent.execution.reconciler")

try:
    import pytz
    PERU_TZ = pytz.timezone("America/Lima")
except ImportError:
    from datetime import timezone, timedelta
    PERU_TZ = timezone(timedelta(hours=-5))

# Status values
STATUS_OPEN = "OPEN"
STATUS_DRY_RUN_OPEN = "DRY_RUN_OPEN"
STATUS_CLOSED = "CLOSED"

# Drift types
DRIFT_OK = "OK"
DRIFT_PHANTOM_OPEN = "PHANTOM_OPEN"
DRIFT_ORPHAN_POSITION = "ORPHAN_POSITION"


class Reconciler:
    """
    Compares Sheet state vs Alpaca state, corrects/alerts on drift.
    """

    def __init__(
        self,
        broker: AlpacaBroker,
        sheet_reader=None,
        sheet_writer=None,
        alert_writer=None,
    ):
        """
        Args:
            broker: AlpacaBroker instance
            sheet_reader: callable() → list of position dicts from paper_portfolio
            sheet_writer: callable(pos, updates) → None
            alert_writer: callable(event_dict) → None (writes to system_events)
        """
        self.broker = broker
        self._sheet_reader = sheet_reader
        self._sheet_writer = sheet_writer
        self._alert_writer = alert_writer

    def reconcile(self) -> Dict[str, Any]:
        """
        Compare Sheet vs Alpaca, return drift report.

        Returns:
            {
                "ok": int,
                "phantom_open": int,
                "orphan_position": int,
                "skipped_dry_run": int,
                "details": [list of drift events]
            }
        """
        sheet_positions = self._get_sheet_open_positions()
        alpaca_positions = self._get_alpaca_positions()

        # Index Alpaca positions by ticker
        alpaca_by_ticker = {
            p.get("symbol", "").upper(): p for p in alpaca_positions
        }
        # Track which Sheet tickers are LIVE (not DRY_RUN)
        sheet_live_tickers = set()

        report = {
            "ok": 0,
            "phantom_open": 0,
            "orphan_position": 0,
            "skipped_dry_run": 0,
            "details": [],
        }

        # Check each Sheet position against Alpaca
        for pos in sheet_positions:
            ticker = pos.get("Ticker", "").upper()
            status = pos.get("Status")

            if status == STATUS_DRY_RUN_OPEN:
                report["skipped_dry_run"] += 1
                continue

            sheet_live_tickers.add(ticker)

            if ticker in alpaca_by_ticker:
                report["ok"] += 1
            else:
                report["phantom_open"] += 1
                self._handle_phantom_open(pos, report)

        # Check for orphan Alpaca positions (not tracked in Sheet)
        for ticker, alpaca_pos in alpaca_by_ticker.items():
            if ticker not in sheet_live_tickers:
                report["orphan_position"] += 1
                self._handle_orphan(ticker, alpaca_pos, report)

        return report

    def _get_sheet_open_positions(self) -> List[Dict[str, Any]]:
        """Read OPEN/DRY_RUN_OPEN positions from paper_portfolio."""
        if self._sheet_reader:
            all_rows = self._sheet_reader()
        else:
            try:
                import sheets_manager
                ws = sheets_manager.get_worksheet("paper_portfolio")
                all_rows = ws.get_all_records() if ws else []
            except Exception as e:
                logger.error("Failed to read paper_portfolio: %s", e)
                return []

        return [
            r for r in all_rows
            if r.get("Status") in (STATUS_OPEN, STATUS_DRY_RUN_OPEN)
        ]

    def _get_alpaca_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions from Alpaca as dicts."""
        try:
            positions = self.broker.list_positions()
            result = []
            for p in positions:
                if hasattr(p, "symbol"):
                    result.append({
                        "symbol": p.symbol,
                        "qty": getattr(p, "qty", "0"),
                        "side": getattr(p, "side", "short"),
                        "avg_entry_price": getattr(p, "avg_entry_price", "0"),
                    })
                elif isinstance(p, dict):
                    result.append(p)
            return result
        except Exception as e:
            logger.error("Failed to fetch Alpaca positions: %s", e)
            return []

    def _handle_phantom_open(self, pos: Dict[str, Any], report: Dict[str, Any]):
        """Sheet says OPEN, but no Alpaca position. Mark CLOSED + alert."""
        ticker = pos.get("Ticker")
        now = datetime.now(PERU_TZ)

        event = {
            "type": DRIFT_PHANTOM_OPEN,
            "ticker": ticker,
            "decision_id": pos.get("PositionID"),
            "action_taken": "marked_closed",
            "timestamp": now.isoformat(),
            "details": (
                f"Position OPEN in Sheet but missing in Alpaca. "
                f"Likely TP/SL filled outside monitoring window."
            ),
        }
        report["details"].append(event)

        # Correct Sheet: mark as CLOSED
        if self._sheet_writer:
            self._sheet_writer(pos, {
                "Status": STATUS_CLOSED,
                "ExitReason": "RECONCILER_PHANTOM",
                "ExitDate": now.strftime("%Y-%m-%d"),
                "ExitTime": now.strftime("%H:%M:%S"),
                "LastUpdated": now.isoformat(),
            })

        # Alert
        if self._alert_writer:
            self._alert_writer(event)

    def _handle_orphan(self, ticker: str, alpaca_pos: Dict, report: Dict[str, Any]):
        """Alpaca has position not tracked in Sheet. Alert only (don't auto-fix)."""
        now = datetime.now(PERU_TZ)

        event = {
            "type": DRIFT_ORPHAN_POSITION,
            "ticker": ticker,
            "alpaca_qty": alpaca_pos.get("qty", "0"),
            "alpaca_avg_price": alpaca_pos.get("avg_entry_price", "0"),
            "action_taken": "alert_only",
            "timestamp": now.isoformat(),
            "details": (
                f"Alpaca has {alpaca_pos.get('qty')} shares of {ticker}, "
                f"but no OPEN record in paper_portfolio. INVESTIGATE."
            ),
        }
        report["details"].append(event)

        if self._alert_writer:
            self._alert_writer(event)
