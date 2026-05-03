"""
agent/execution/position_manager.py
────────────────────────────────────
Tracks open positions and enforces exit rules.

Responsibilities:
- Periodic monitoring (every minute during market hours)
- Update CurrentPrice, UnrealizedPnL, UnrealizedPnLPct
- Detect TP/SL fills via Alpaca order status
- EOD close (5 min before market close = 14:55 Peru)
- Mark positions CLOSED with ExitReason

Strategy:
- DRY_RUN: simulated orders never auto-fill TP/SL
- LIVE_PAPER: real Alpaca order status checks
- Each position processed independently (failure in one ≠ block others)
"""

import sys
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, time as dtime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import AGENT_DRY_RUN
from agent.execution.alpaca_broker import AlpacaBroker

logger = logging.getLogger("agent.execution.position_manager")

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
STATUS_DRY_RUN_CLOSED = "DRY_RUN_CLOSED"

# Exit reasons
EXIT_TP_HIT = "TP_HIT"
EXIT_SL_HIT = "SL_HIT"
EXIT_EOD_CLOSE = "EOD_CLOSE"
EXIT_MANUAL = "MANUAL"

# EOD close time (Peru): 14:55 = 5 min before market close 15:00
EOD_CLOSE_TIME = dtime(14, 55)


class PositionManager:
    """
    Monitors open positions and triggers exits.

    Stateless: each call queries fresh data from broker + sheet.
    """

    def __init__(
        self,
        broker: AlpacaBroker,
        data_provider=None,
        sheet_reader=None,
        sheet_writer=None,
        postmortem_engine=None,
    ):
        """
        Args:
            broker: AlpacaBroker instance
            data_provider: object with get_current_price(ticker) method
            sheet_reader: callable() → list of position dicts (from paper_portfolio)
            sheet_writer: callable(pos_dict, updates_dict) → None
            postmortem_engine: optional PostmortemEngine instance (M6)
        """
        self.broker = broker
        self.data_provider = data_provider
        self._sheet_reader = sheet_reader
        self._sheet_writer = sheet_writer
        self._postmortem_engine = postmortem_engine

    def monitor_all(self) -> Dict[str, int]:
        """
        Process all open positions.
        Returns: {"updated": N, "closed_tp": N, "closed_sl": N, "errors": N}
        """
        positions = self._get_open_positions()
        stats = {"updated": 0, "closed_tp": 0, "closed_sl": 0, "errors": 0}

        for pos in positions:
            try:
                result = self._process_position(pos)
                stats[result] = stats.get(result, 0) + 1
            except Exception as e:
                logger.error("Error processing %s: %s", pos.get("Ticker"), e)
                stats["errors"] += 1

        return stats

    def eod_close_all(self) -> Dict[str, int]:
        """Close all open positions before market close."""
        positions = self._get_open_positions()
        stats = {"closed": 0, "errors": 0}

        for pos in positions:
            try:
                self._close_position(pos, EXIT_EOD_CLOSE)
                stats["closed"] += 1
            except Exception as e:
                logger.error("EOD close failed for %s: %s", pos.get("Ticker"), e)
                stats["errors"] += 1

        return stats

    def _get_open_positions(self) -> List[Dict[str, Any]]:
        """Read open positions from paper_portfolio Sheet."""
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

        return [r for r in all_rows if r.get("Status") in (STATUS_OPEN, STATUS_DRY_RUN_OPEN)]

    def _process_position(self, pos: Dict[str, Any]) -> str:
        """
        Process a single position.
        Returns: "updated" / "closed_tp" / "closed_sl"
        """
        ticker = pos.get("Ticker")
        tp_order_id = pos.get("TPOrderID", "")
        sl_order_id = pos.get("SLOrderID", "")

        # Check TP/SL order status
        tp_filled = self._is_order_filled(tp_order_id) if tp_order_id else False
        sl_filled = self._is_order_filled(sl_order_id) if sl_order_id else False

        # SL takes precedence (more conservative)
        if sl_filled:
            self._close_position(pos, EXIT_SL_HIT)
            return "closed_sl"
        if tp_filled:
            self._close_position(pos, EXIT_TP_HIT)
            return "closed_tp"

        # Update current price + PnL
        current_price = self._get_current_price(ticker)
        if current_price is None:
            return "updated"  # graceful skip

        entry_price = float(pos.get("EntryPrice", 0))
        qty = int(pos.get("Quantity", 0))
        # Short PnL: (entry - current) × qty
        unrealized_pnl = (entry_price - current_price) * qty
        unrealized_pnl_pct = (
            (entry_price - current_price) / entry_price * 100
            if entry_price else 0
        )

        self._update_position(pos, {
            "CurrentPrice": current_price,
            "UnrealizedPnL": round(unrealized_pnl, 2),
            "UnrealizedPnLPct": round(unrealized_pnl_pct, 2),
            "LastUpdated": datetime.now(PERU_TZ).isoformat(),
        })
        return "updated"

    def _is_order_filled(self, order_id: str) -> bool:
        """Check if order is filled. DRY_RUN simulated orders never auto-fill."""
        if not order_id or order_id.startswith("SIM-"):
            return False
        try:
            order = self.broker.get_order(order_id)
            return getattr(order, "status", "") == "filled"
        except Exception as e:
            logger.warning("Failed to check order %s: %s", order_id, e)
            return False

    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price via data_provider."""
        if self.data_provider is None:
            return None
        try:
            return float(self.data_provider.get_current_price(ticker))
        except Exception as e:
            logger.warning("Failed to get price for %s: %s", ticker, e)
            return None

    def _close_position(self, pos: Dict[str, Any], exit_reason: str):
        """Mark position as closed with exit details."""
        ticker = pos.get("Ticker")
        is_dry_run = pos.get("Status") == STATUS_DRY_RUN_OPEN

        # Get exit price
        exit_price = self._get_current_price(ticker)
        if exit_price is None:
            exit_price = float(pos.get("EntryPrice", 0))

        entry_price = float(pos.get("EntryPrice", 0))
        qty = int(pos.get("Quantity", 0))
        realized_pnl = (entry_price - exit_price) * qty
        realized_pnl_pct = (
            (entry_price - exit_price) / entry_price * 100
            if entry_price else 0
        )

        # Submit close order to Alpaca (only for non-TP/SL exits in LIVE mode)
        if not is_dry_run and exit_reason not in (EXIT_TP_HIT, EXIT_SL_HIT):
            try:
                self.broker.close_position(ticker)
            except Exception as e:
                logger.error("Failed to close %s on Alpaca: %s", ticker, e)

        # Cancel dangling TP/SL orders on EOD close
        if exit_reason == EXIT_EOD_CLOSE:
            self._cancel_bracket_legs(pos)

        # Update sheet
        now = datetime.now(PERU_TZ)
        updates = {
            "Status": STATUS_DRY_RUN_CLOSED if is_dry_run else STATUS_CLOSED,
            "ExitPrice": exit_price,
            "ExitDate": now.strftime("%Y-%m-%d"),
            "ExitTime": now.strftime("%H:%M:%S"),
            "ExitReason": exit_reason,
            "RealizedPnL": round(realized_pnl, 2),
            "RealizedPnLPct": round(realized_pnl_pct, 2),
            "LastUpdated": now.isoformat(),
        }
        self._update_position(pos, updates)

        # M6: Generate postmortem (optional — only if engine wired)
        if self._postmortem_engine:
            try:
                pos_with_exit = {**pos, **updates}
                self._postmortem_engine.generate(pos_with_exit)
            except Exception as e:
                logger.error("Postmortem generation failed for %s: %s", ticker, e)

    def _cancel_bracket_legs(self, pos: Dict[str, Any]):
        """Cancel TP and SL orders when closing position manually/EOD."""
        for key in ("TPOrderID", "SLOrderID"):
            order_id = pos.get(key, "")
            if order_id and not order_id.startswith("SIM-"):
                try:
                    self.broker.cancel_order(order_id)
                except Exception as e:
                    logger.warning("Failed to cancel %s (%s): %s", key, order_id, e)

    def _update_position(self, pos: Dict[str, Any], updates: Dict[str, Any]):
        """Apply updates to a position row in paper_portfolio."""
        if self._sheet_writer:
            self._sheet_writer(pos, updates)
        else:
            logger.info("Update for %s: %s", pos.get("Ticker"), updates)
