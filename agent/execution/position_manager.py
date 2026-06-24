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

# Quota-reduction cut (TASK-136 C1): route the per-minute paper_portfolio read
# through the 60s-cached get_sheet_records (TASK-58) instead of an uncached
# get_all_records, so it shares the cache account-state-builder already populated
# in the same run. get_sheet_records returns ALL strings (sheets_manager:441-447);
# the position pipeline expects EntryPrice/TP/SL as float and Quantity as int, so
# _coerce_portfolio_record normalizes the cached records back to the gspread-
# equivalent numeric types before they reach _get_open_positions.

# Portfolio fields the position pipeline consumes numerically (float), plus the
# single int field. Everything else (PositionID, Ticker, Status, IDs, dates) stays
# a string — matching how the writer's PositionID match and Status checks read it.
_PORTFOLIO_FLOAT_FIELDS = (
    "EntryPrice", "ExitPrice", "TPPrice", "SLPrice", "CurrentPrice",
    "UnrealizedPnL", "UnrealizedPnLPct", "RealizedPnL", "RealizedPnLPct",
    "PositionSizeUSD",
)
_PORTFOLIO_INT_FIELDS = ("Quantity",)


def _coerce_portfolio_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a string-valued paper_portfolio record (from the cached
    get_sheet_records reader) to the gspread get_all_records()-equivalent types.

    Numeric whitelist only: prices/PnL → float, Quantity → int (via float so a
    display-formatted "100.0" does not crash int("100.0")). Blank ("") and
    non-numeric values are preserved unchanged (a blank numeric cell is "" under
    gspread too). Returns a NEW dict; the input is not mutated.
    """
    out = dict(rec)
    for k in _PORTFOLIO_FLOAT_FIELDS:
        v = out.get(k)
        if isinstance(v, str) and v.strip() != "":
            try:
                out[k] = float(v)
            except (ValueError, TypeError):
                pass  # leave non-numeric strings as-is (matches gspread)
    for k in _PORTFOLIO_INT_FIELDS:
        v = out.get(k)
        if isinstance(v, str) and v.strip() != "":
            try:
                out[k] = int(float(v))
            except (ValueError, TypeError):
                pass
    return out


def cached_portfolio_reader() -> List[Dict[str, Any]]:
    """Read paper_portfolio via the 60s-cached get_sheet_records (TASK-58) and
    coerce each record to the numeric types the position pipeline expects.

    Wired into PositionManager(sheet_reader=...) by the orchestrator so the
    per-minute position read shares the cache rather than making a duplicate
    uncached API call (TASK-136 C1).
    """
    import sheets_manager
    return [
        _coerce_portfolio_record(r)
        for r in sheets_manager.get_sheet_records("paper_portfolio")
    ]


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
        """Read open positions from paper_portfolio Sheet.

        Each returned dict carries a `_row_number` key — the absolute 1-based
        Sheet row (header = row 1, first data row = 2). This lets the sheet
        writer target the exact row instead of matching by PositionID, which
        is unsafe when duplicate IDs exist (Bug #2 fix 2026-05-16).
        """
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

        # Tag every record with its absolute Sheet row (data starts at row 2).
        open_positions = []
        for idx, r in enumerate(all_rows, start=2):
            if r.get("Status") in (STATUS_OPEN, STATUS_DRY_RUN_OPEN):
                r["_row_number"] = idx
                open_positions.append(r)
        return open_positions

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
            logger.warning(
                "Skipping price update for %s (position %s): "
                "_get_current_price returned None — CurrentPrice will NOT be written to sheet",
                ticker, pos.get("PositionID", "?"),
            )
            return "updated"  # graceful skip

        # DRY_RUN: simulate TP/SL via price comparison (no real bracket fills)
        status = str(pos.get("Status", "")).upper()
        if status == "DRY_RUN_OPEN":
            try:
                tp_price = float(pos.get("TPPrice", 0) or 0)
                sl_price = float(pos.get("SLPrice", 0) or 0)
            except (ValueError, TypeError):
                tp_price = sl_price = 0
            # Short position: SL triggers if price RISES, TP triggers if price DROPS
            if sl_price > 0 and current_price >= sl_price:
                self._update_position(pos, {"CurrentPrice": current_price})
                self._close_position(pos, EXIT_SL_HIT, exit_price=current_price)
                return "closed_sl"
            if tp_price > 0 and current_price <= tp_price:
                self._update_position(pos, {"CurrentPrice": current_price})
                self._close_position(pos, EXIT_TP_HIT, exit_price=current_price)
                return "closed_tp"

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
        """Get current price via data_provider (bar close or quote mid)."""
        if self.data_provider is None:
            return None
        try:
            bar = self.data_provider.get_latest_bar(ticker)
            if bar and bar.get("close"):
                return float(bar["close"])
            quote = self.data_provider.get_latest_quote(ticker)
            if quote:
                bid = quote.get("bid_price") or 0
                ask = quote.get("ask_price") or 0
                if bid and ask:
                    return float((bid + ask) / 2)
            # Both methods failed — log which ones returned nothing
            bar_status = "empty/None" if not bar else "no 'close' key"
            quote_status = "empty/None" if not quote else "no valid bid/ask"
            logger.warning(
                "All price sources failed for %s: get_latest_bar=%s, get_latest_quote=%s",
                ticker, bar_status, quote_status,
            )
            return None
        except Exception as e:
            logger.warning("Failed to get price for %s: %s", ticker, e)
            return None

    def _close_position(self, pos: Dict[str, Any], exit_reason: str,
                        exit_price: Optional[float] = None):
        """Mark position as closed with exit details.

        Args:
            pos: the position row dict.
            exit_reason: EXIT_SL_HIT / EXIT_TP_HIT / EXIT_EOD_CLOSE.
            exit_price: the price that triggered the exit. When provided
                (DRY_RUN TP/SL paths), it is used directly so RealizedPnL,
                ExitPrice and the CurrentPrice already written all agree.
                When None (Alpaca bracket fills, EOD), price is re-fetched.
                Re-fetching after hours can return a stale/wrong value —
                hence callers that already hold the trigger price pass it
                in (Bug #1 fix 2026-05-16).
        """
        ticker = pos.get("Ticker")
        is_dry_run = pos.get("Status") == STATUS_DRY_RUN_OPEN

        # Use the trigger price if the caller supplied it; else re-fetch.
        if exit_price is None:
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
