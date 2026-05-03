"""
agent/execution/order_manager.py
─────────────────────────────────
Orchestrator for order submission. Sits between Trader (M3) and
AlpacaBroker (M5).

Responsibilities:
- Submit bracket orders (entry limit + TP + SL)
- Retry on transient failures (network, rate limit)
- Handle limit order timeout (60s) — cancel if not filled
- Write to paper_portfolio Sheet (both LIVE and DRY_RUN with markers)
- Update Decision with order_id, order_status, execution_price
- Pre-flight checks: market open validation

Strategy:
- DRY_RUN: simulated orders, write to paper_portfolio with DRY_RUN_OPEN status
- LIVE_PAPER: real Alpaca calls, write real order_ids
- Retry: 3 attempts, exponential backoff (2, 4, 8s)
- Timeout: 60s polling for fill, then cancel
"""

import sys
import os
import time
import logging
from typing import Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import AGENT_DRY_RUN
from agent.execution.alpaca_broker import AlpacaBroker, SimulatedOrder
from agent.trader.decision_logic import Decision

logger = logging.getLogger("agent.execution.order_manager")

try:
    import pytz
    PERU_TZ = pytz.timezone("America/Lima")
except ImportError:
    from datetime import timezone, timedelta
    PERU_TZ = timezone(timedelta(hours=-5))

# ════════════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════════════

MAX_RETRIES = 3
BACKOFF_BASE = 2          # seconds (2, 4, 8)
ORDER_FILL_TIMEOUT = 60   # seconds
POLL_INTERVAL = 5         # seconds

# Status values for paper_portfolio
STATUS_DRY_RUN_OPEN = "DRY_RUN_OPEN"
STATUS_OPEN = "OPEN"
STATUS_CANCELLED_TIMEOUT = "CANCELLED_TIMEOUT"
STATUS_REJECTED = "REJECTED"


# ════════════════════════════════════════════════════════════════════════
# OrderManager
# ════════════════════════════════════════════════════════════════════════

class OrderManager:
    """
    Submits bracket orders and tracks them in paper_portfolio Sheet.

    Stateless: each execute() call is independent. State lives in
    Sheet (paper_portfolio) and Alpaca (positions).
    """

    def __init__(self, broker: AlpacaBroker, sheet_writer=None):
        """
        Args:
            broker: AlpacaBroker instance (DRY_RUN or live)
            sheet_writer: callable(row: list) to append row to paper_portfolio.
                          If None, uses sheets_manager.get_worksheet().
        """
        self.broker = broker
        self._sheet_writer = sheet_writer

    def execute(self, decision: Decision) -> Decision:
        """
        Execute a Decision (action='ENTER'). Returns enriched decision.

        For SKIP decisions: no-op, returns decision unchanged.
        For ENTER decisions: submits bracket order, polls for fill,
                              writes to paper_portfolio.
        """
        if decision.action != "ENTER":
            return decision

        # Submit with retry
        order = self._submit_with_retry(decision)
        if order is None:
            decision.order_status = STATUS_REJECTED
            return decision

        # Wait for fill (or timeout)
        final_order = self._wait_for_fill(order)

        # Handle timeout (cancelled)
        if getattr(final_order, "status", "") == STATUS_CANCELLED_TIMEOUT:
            decision.order_id = getattr(final_order, "id", None)
            decision.order_status = STATUS_CANCELLED_TIMEOUT
            return decision

        # Handle rejection from Alpaca
        if getattr(final_order, "status", "") in ("rejected", "canceled"):
            decision.order_id = getattr(final_order, "id", None)
            decision.order_status = str(final_order.status).upper()
            return decision

        # Success — enrich decision
        decision.order_id = final_order.id
        decision.order_status = str(final_order.status)
        decision.execution_price = (
            float(final_order.filled_avg_price)
            if final_order.filled_avg_price else decision.price
        )

        # Extract TP/SL order IDs from bracket legs
        tp_order_id, sl_order_id = self._extract_leg_ids(final_order)

        # Write to paper_portfolio
        self._write_to_portfolio(decision, final_order, tp_order_id, sl_order_id)

        return decision

    # ════════════════════════════════════════════════════════════════════
    # Retry logic (Spec §8.4)
    # ════════════════════════════════════════════════════════════════════

    def _submit_with_retry(self, decision: Decision):
        """Submit bracket order with exponential backoff."""
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                order = self.broker.submit_bracket_order(
                    ticker=decision.ticker,
                    qty=decision.quantity,
                    limit_price=decision.price,
                    tp_price=decision.tp_price,
                    sl_price=decision.sl_price,
                )
                return order
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait = BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "Retry %d/%d for %s after %ds: %s",
                        attempt + 1, MAX_RETRIES, decision.ticker, wait, e,
                    )
                    time.sleep(wait)

        logger.error(
            "All %d retries exhausted for %s: %s",
            MAX_RETRIES, decision.ticker, last_error,
        )
        return None

    # ════════════════════════════════════════════════════════════════════
    # Fill polling + timeout
    # ════════════════════════════════════════════════════════════════════

    def _wait_for_fill(self, order):
        """Poll order status until filled, rejected, or timeout."""
        if isinstance(order, SimulatedOrder):
            return order  # DRY_RUN: already "filled"

        elapsed = 0
        while elapsed < ORDER_FILL_TIMEOUT:
            current = self.broker.get_order(order.id)
            if getattr(current, "status", "") in ("filled", "rejected", "canceled"):
                return current
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

        # Timeout — cancel the unfilled order
        logger.warning("Order %s timed out after %ds — cancelling", order.id, ORDER_FILL_TIMEOUT)
        self.broker.cancel_order(order.id)
        order.status = STATUS_CANCELLED_TIMEOUT
        return order

    # ════════════════════════════════════════════════════════════════════
    # Bracket leg extraction
    # ════════════════════════════════════════════════════════════════════

    def _extract_leg_ids(self, order) -> tuple:
        """Extract TP and SL order IDs from bracket order legs."""
        tp_id = ""
        sl_id = ""
        legs = getattr(order, "legs", None) or []
        if len(legs) >= 2:
            tp_id = str(legs[0].id)
            sl_id = str(legs[1].id)
        elif len(legs) == 1:
            tp_id = str(legs[0].id)
        return tp_id, sl_id

    # ════════════════════════════════════════════════════════════════════
    # Sheet writing
    # ════════════════════════════════════════════════════════════════════

    def _write_to_portfolio(self, decision: Decision, order, tp_order_id: str, sl_order_id: str):
        """Write a row to paper_portfolio Sheet (22 columns)."""
        is_dry_run = AGENT_DRY_RUN or isinstance(order, SimulatedOrder)
        status = STATUS_DRY_RUN_OPEN if is_dry_run else STATUS_OPEN

        now = datetime.now(PERU_TZ)
        entry_date = now.strftime("%Y-%m-%d")
        entry_time = now.strftime("%H:%M:%S")

        # paper_portfolio schema (22 cols):
        # PositionID, Ticker, EntryDate, EntryTime,
        # EntryPrice, Quantity, PositionSizeUSD, Side,
        # EntryOrderID, TPOrderID, SLOrderID,
        # CurrentPrice, UnrealizedPnL, UnrealizedPnLPct, Status,
        # ExitPrice, ExitDate, ExitTime, ExitReason,
        # RealizedPnL, RealizedPnLPct, LastUpdated
        row = [
            decision.decision_id or "",       # PositionID (same as DecisionID)
            decision.ticker,                  # Ticker
            entry_date,                       # EntryDate
            entry_time,                       # EntryTime
            decision.execution_price or decision.price,  # EntryPrice
            decision.quantity,                # Quantity
            decision.position_size_usd,       # PositionSizeUSD
            "short",                          # Side
            order.id,                         # EntryOrderID
            tp_order_id,                      # TPOrderID
            sl_order_id,                      # SLOrderID
            "",                               # CurrentPrice
            "",                               # UnrealizedPnL
            "",                               # UnrealizedPnLPct
            status,                           # Status
            "",                               # ExitPrice
            "",                               # ExitDate
            "",                               # ExitTime
            "",                               # ExitReason
            "",                               # RealizedPnL
            "",                               # RealizedPnLPct
            now.isoformat(),                  # LastUpdated
        ]

        if self._sheet_writer:
            try:
                self._sheet_writer(row)
            except Exception as e:
                logger.error("paper_portfolio write failed: %s", e)
        else:
            self._default_sheet_write(row)

    def _default_sheet_write(self, row: list):
        """Write row using sheets_manager (production path)."""
        try:
            import sheets_manager
            ws = sheets_manager.get_worksheet("paper_portfolio")
            if ws:
                ws.append_row(row, value_input_option="USER_ENTERED")
            else:
                logger.error("paper_portfolio worksheet not available")
        except Exception as e:
            logger.error("paper_portfolio write failed: %s", e)
