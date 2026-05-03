"""
Unit tests for AlpacaBroker — all run in DRY_RUN mode (no real API calls).
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.execution.alpaca_broker import AlpacaBroker, SimulatedOrder


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════

@pytest.fixture
def broker():
    """Create a DRY_RUN broker (no API calls)."""
    return AlpacaBroker(api_key="PK_TEST_KEY", secret_key="test_secret", dry_run=True)


# ════════════════════════════════════════════════════════════════════════
# Safety checks
# ════════════════════════════════════════════════════════════════════════

class TestSafetyChecks:
    """Verify safety assertions block non-paper usage."""

    def test_rejects_non_paper_key(self):
        """API key not starting with PK is blocked."""
        with pytest.raises(RuntimeError, match="SAFETY BLOCK.*PK"):
            AlpacaBroker(api_key="LIVE_KEY_123", secret_key="sec", dry_run=True)

    def test_accepts_paper_key(self):
        """Paper key (PK prefix) is accepted."""
        broker = AlpacaBroker(api_key="PKtest123", secret_key="sec", dry_run=True)
        assert broker.api_key == "PKtest123"

    def test_empty_key_allowed(self):
        """Empty key is allowed (for DRY_RUN where no real calls happen)."""
        broker = AlpacaBroker(api_key="", secret_key="", dry_run=True)
        assert broker.dry_run is True

    def test_base_url_is_paper(self, broker):
        """Base URL must contain 'paper'."""
        assert "paper" in broker.base_url


# ════════════════════════════════════════════════════════════════════════
# DRY_RUN bracket order
# ════════════════════════════════════════════════════════════════════════

class TestDryRunBracketOrder:
    """Test bracket order simulation in DRY_RUN mode."""

    def test_returns_simulated_order(self, broker):
        """Bracket order returns SimulatedOrder with correct fields."""
        order = broker.submit_bracket_order(
            ticker="AAPL", qty=10, limit_price=150.0,
            tp_price=135.0, sl_price=165.0,
        )
        assert isinstance(order, SimulatedOrder)
        assert order.status == "filled"
        assert order.symbol == "AAPL"
        assert order.side == "sell"
        assert order.qty == "10"
        assert order.filled_avg_price == 150.0
        assert order.order_class == "bracket"

    def test_has_tp_and_sl_legs(self, broker):
        """Bracket order has exactly 2 legs (TP + SL)."""
        order = broker.submit_bracket_order(
            ticker="TSLA", qty=5, limit_price=200.0,
            tp_price=180.0, sl_price=220.0,
        )
        assert len(order.legs) == 2
        tp_leg, sl_leg = order.legs
        assert "tp" in tp_leg.id
        assert "sl" in sl_leg.id
        assert tp_leg.status == "held"
        assert sl_leg.status == "held"

    def test_order_id_has_sim_prefix(self, broker):
        """Simulated order IDs start with SIM-."""
        order = broker.submit_bracket_order(
            ticker="NVDA", qty=3, limit_price=500.0,
            tp_price=450.0, sl_price=550.0,
        )
        assert order.id.startswith("SIM-")


# ════════════════════════════════════════════════════════════════════════
# DRY_RUN other methods
# ════════════════════════════════════════════════════════════════════════

class TestDryRunMethods:
    """Test all other methods in DRY_RUN mode."""

    def test_get_order_returns_filled(self, broker):
        """get_order in DRY_RUN returns filled status."""
        order = broker.get_order("SIM-abc123")
        assert order.status == "filled"
        assert order.id == "SIM-abc123"

    def test_cancel_order_returns_true(self, broker):
        """cancel_order in DRY_RUN always succeeds."""
        assert broker.cancel_order("SIM-abc123") is True

    def test_get_position_returns_none(self, broker):
        """No positions exist in DRY_RUN."""
        assert broker.get_position("AAPL") is None

    def test_list_positions_empty(self, broker):
        """No positions in DRY_RUN."""
        assert broker.list_positions() == []

    def test_get_account_simulated(self, broker):
        """Account returns simulated values."""
        account = broker.get_account()
        assert account["status"] == "ACTIVE"
        assert float(account["buying_power"]) > 0

    def test_is_shortable_always_true(self, broker):
        """DRY_RUN: all tickers are shortable."""
        assert broker.is_shortable("AAPL") is True
        assert broker.is_shortable("OBSCURE_TICKER") is True

    def test_get_asset_info(self, broker):
        """DRY_RUN: asset info returns mock values."""
        info = broker.get_asset_info("TSLA")
        assert info["symbol"] == "TSLA"
        assert info["shortable"] is True
        assert info["easy_to_borrow"] is True

    def test_close_position_simulated(self, broker):
        """DRY_RUN: close_position returns simulated order."""
        result = broker.close_position("AAPL")
        assert isinstance(result, SimulatedOrder)
        assert result.status == "filled"
        assert "AAPL" in result.id


# ════════════════════════════════════════════════════════════════════════
# LIVE_PAPER guard
# ════════════════════════════════════════════════════════════════════════

class TestLivePaperGuard:
    """Verify that real submissions are blocked when AGENT_LIVE_PAPER=False."""

    @patch("agent.execution.alpaca_broker.AGENT_LIVE_PAPER", False)
    @patch("agent.execution.alpaca_broker.AGENT_DRY_RUN", False)
    def test_bracket_order_blocked_without_live_paper(self):
        """Real bracket order raises if AGENT_LIVE_PAPER is False."""
        broker = AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=False)
        # Mock the client so we don't actually connect
        broker._trading_client = MagicMock()
        with pytest.raises(RuntimeError, match="AGENT_LIVE_PAPER"):
            broker.submit_bracket_order("AAPL", 10, 150.0, 135.0, 165.0)

    @patch("agent.execution.alpaca_broker.AGENT_LIVE_PAPER", False)
    @patch("agent.execution.alpaca_broker.AGENT_DRY_RUN", False)
    def test_close_position_blocked_without_live_paper(self):
        """close_position raises if AGENT_LIVE_PAPER is False."""
        broker = AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=False)
        broker._trading_client = MagicMock()
        with pytest.raises(RuntimeError, match="AGENT_LIVE_PAPER"):
            broker.close_position("AAPL")
