"""
AlpacaBroker — Thin wrapper around alpaca-py SDK for ORDER execution only.

Market data goes through data_provider.py. This module handles:
- Bracket orders (entry + TP + SL as OCO)
- Order status queries
- Position queries
- Account info
- Asset shortability checks

Safety:
- ONLY paper trading (asserts paper URL)
- DRY_RUN mode returns simulated results without hitting Alpaca
- AGENT_LIVE_PAPER must be True for real submissions

Created: M5 (Alpaca Execution)
"""

import logging
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import AGENT_DRY_RUN, AGENT_LIVE_PAPER

logger = logging.getLogger("agent.execution.alpaca_broker")

# ════════════════════════════════════════════════════════════════════════
# Simulated result for DRY_RUN mode
# ════════════════════════════════════════════════════════════════════════

@dataclass
class SimulatedOrder:
    """Fake order returned in DRY_RUN mode."""
    id: str
    status: str = "filled"
    filled_avg_price: Optional[float] = None
    qty: Optional[str] = None
    side: Optional[str] = None
    symbol: Optional[str] = None
    order_class: Optional[str] = None
    legs: List[Any] = field(default_factory=list)


@dataclass
class SimulatedPosition:
    """Fake position returned in DRY_RUN mode."""
    symbol: str
    qty: str
    side: str = "short"
    avg_entry_price: str = "0.00"
    current_price: str = "0.00"
    unrealized_pl: str = "0.00"
    market_value: str = "0.00"


# ════════════════════════════════════════════════════════════════════════
# AlpacaBroker
# ════════════════════════════════════════════════════════════════════════

class AlpacaBroker:
    """
    Broker interface for Alpaca paper trading.

    In DRY_RUN mode: all methods return simulated results, no API calls.
    In LIVE_PAPER mode: submits real orders to Alpaca paper environment.
    """

    PAPER_BASE_URL = "https://paper-api.alpaca.markets"

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        self.api_key = api_key or os.environ.get("ALPACA_API_KEY_ID", "")
        self.secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        self.dry_run = dry_run if dry_run is not None else AGENT_DRY_RUN
        self.base_url = self.PAPER_BASE_URL

        # ── Safety checks ──
        self._assert_paper_only()

        # ── SDK client (lazy init for DRY_RUN) ──
        self._trading_client = None
        if not self.dry_run:
            self._init_trading_client()

        logger.info(
            "AlpacaBroker initialized (dry_run=%s, base_url=%s)",
            self.dry_run, self.base_url,
        )

    def _assert_paper_only(self):
        """Safety: ensure we never connect to live trading."""
        if "paper" not in self.base_url:
            raise RuntimeError(
                f"SAFETY BLOCK: base_url must be paper. Got: {self.base_url}"
            )
        if self.api_key and not self.api_key.startswith("PK"):
            raise RuntimeError(
                "SAFETY BLOCK: API key does not start with 'PK' (paper key convention). "
                "Refusing to proceed — verify you're using paper credentials."
            )

    def _init_trading_client(self):
        """Initialize the alpaca-py TradingClient."""
        from alpaca.trading.client import TradingClient
        self._trading_client = TradingClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
            paper=True,
        )

    @property
    def client(self):
        """Get or lazily init the trading client."""
        if self._trading_client is None:
            self._init_trading_client()
        return self._trading_client

    # ════════════════════════════════════════════════════════════════════
    # Orders
    # ════════════════════════════════════════════════════════════════════

    def submit_bracket_order(
        self,
        ticker: str,
        qty: int,
        limit_price: float,
        tp_price: float,
        sl_price: float,
    ) -> Any:
        """
        Submit a bracket order: short entry (limit) + TP (limit buy) + SL (stop buy).

        Args:
            ticker: stock symbol
            qty: number of shares to short
            limit_price: entry limit price for short sell
            tp_price: take-profit price (buy limit, below entry)
            sl_price: stop-loss price (buy stop, above entry)

        Returns:
            Order object (real) or SimulatedOrder (DRY_RUN)
        """
        if self.dry_run:
            return self._sim_bracket_order(ticker, qty, limit_price, tp_price, sl_price)

        if not AGENT_LIVE_PAPER:
            raise RuntimeError(
                "AGENT_LIVE_PAPER is False — cannot submit real orders. "
                "Set AGENT_LIVE_PAPER=True (M10) to enable."
            )

        from alpaca.trading.requests import (
            LimitOrderRequest,
            TakeProfitRequest,
            StopLossRequest,
        )
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

        request = LimitOrderRequest(
            symbol=ticker,
            qty=qty,
            side=OrderSide.SELL,
            type="limit",
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=tp_price),
            stop_loss=StopLossRequest(stop_price=sl_price),
        )

        logger.info(
            "Submitting bracket order: %s %d shares @ $%.2f (TP=%.2f, SL=%.2f)",
            ticker, qty, limit_price, tp_price, sl_price,
        )
        order = self.client.submit_order(request)
        logger.info("Order submitted: id=%s status=%s", order.id, order.status)
        return order

    def get_order(self, order_id: str) -> Any:
        """Get order status by ID."""
        if self.dry_run:
            return SimulatedOrder(id=order_id, status="filled")

        from alpaca.trading.requests import GetOrderByIdRequest
        return self.client.get_order_by_id(order_id)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order. Returns True if cancelled successfully."""
        if self.dry_run:
            logger.info("DRY_RUN: would cancel order %s", order_id)
            return True

        try:
            self.client.cancel_order_by_id(order_id)
            logger.info("Cancelled order: %s", order_id)
            return True
        except Exception as e:
            logger.error("Failed to cancel order %s: %s", order_id, e)
            return False

    # ════════════════════════════════════════════════════════════════════
    # Positions
    # ════════════════════════════════════════════════════════════════════

    def get_position(self, ticker: str) -> Any:
        """Get current position for a ticker, or None if no position."""
        if self.dry_run:
            return None  # No simulated positions in DRY_RUN

        try:
            return self.client.get_open_position(ticker)
        except Exception:
            return None

    def list_positions(self) -> List[Any]:
        """List all open positions."""
        if self.dry_run:
            return []

        return self.client.get_all_positions()

    # ════════════════════════════════════════════════════════════════════
    # Account
    # ════════════════════════════════════════════════════════════════════

    def get_account(self) -> Dict[str, Any]:
        """Get account info (buying power, equity, etc.)."""
        if self.dry_run:
            return {
                "buying_power": "200000.00",
                "equity": "100000.00",
                "cash": "100000.00",
                "status": "ACTIVE",
            }

        account = self.client.get_account()
        return {
            "buying_power": str(account.buying_power),
            "equity": str(account.equity),
            "cash": str(account.cash),
            "status": str(account.status),
        }

    # ════════════════════════════════════════════════════════════════════
    # Asset info (for tradability)
    # ════════════════════════════════════════════════════════════════════

    def is_shortable(self, ticker: str) -> bool:
        """Check if a ticker is shortable on Alpaca."""
        if self.dry_run:
            return True  # Mock: always shortable

        asset = self.client.get_asset(ticker)
        return asset.shortable

    def get_asset_info(self, ticker: str) -> Dict[str, Any]:
        """Get full asset info including shortability and borrow status."""
        if self.dry_run:
            return {
                "symbol": ticker,
                "shortable": True,
                "easy_to_borrow": True,
                "tradable": True,
                "status": "active",
            }

        asset = self.client.get_asset(ticker)
        return {
            "symbol": asset.symbol,
            "shortable": asset.shortable,
            "easy_to_borrow": asset.easy_to_borrow,
            "tradable": asset.tradable,
            "status": str(asset.status),
        }

    # ════════════════════════════════════════════════════════════════════
    # Close positions (for cleanup / EOD)
    # ════════════════════════════════════════════════════════════════════

    def close_position(self, ticker: str) -> Any:
        """Close an open position (market order to cover short)."""
        if self.dry_run:
            logger.info("DRY_RUN: would close position for %s", ticker)
            return SimulatedOrder(
                id=f"SIM-close-{ticker}-{uuid.uuid4().hex[:8]}",
                status="filled",
                symbol=ticker,
                side="buy",
            )

        if not AGENT_LIVE_PAPER:
            raise RuntimeError("AGENT_LIVE_PAPER is False — cannot close positions.")

        return self.client.close_position(ticker)

    def close_all_positions(self) -> List[Any]:
        """Close all open positions (emergency / EOD)."""
        if self.dry_run:
            logger.info("DRY_RUN: would close all positions")
            return []

        if not AGENT_LIVE_PAPER:
            raise RuntimeError("AGENT_LIVE_PAPER is False — cannot close positions.")

        return self.client.close_all_positions()

    # ════════════════════════════════════════════════════════════════════
    # DRY_RUN simulation helpers
    # ════════════════════════════════════════════════════════════════════

    def _sim_bracket_order(
        self, ticker: str, qty: int, limit_price: float,
        tp_price: float, sl_price: float,
    ) -> SimulatedOrder:
        """Create a simulated bracket order for DRY_RUN mode."""
        sim_id = f"SIM-{uuid.uuid4().hex[:12]}"
        logger.info(
            "DRY_RUN: simulated bracket order %s: %s %d @ $%.2f (TP=%.2f, SL=%.2f)",
            sim_id, ticker, qty, limit_price, tp_price, sl_price,
        )
        tp_leg = SimulatedOrder(
            id=f"{sim_id}-tp",
            status="held",
            symbol=ticker,
            side="buy",
            qty=str(qty),
        )
        sl_leg = SimulatedOrder(
            id=f"{sim_id}-sl",
            status="held",
            symbol=ticker,
            side="buy",
            qty=str(qty),
        )
        return SimulatedOrder(
            id=sim_id,
            status="filled",
            filled_avg_price=limit_price,
            qty=str(qty),
            side="sell",
            symbol=ticker,
            order_class="bracket",
            legs=[tp_leg, sl_leg],
        )
