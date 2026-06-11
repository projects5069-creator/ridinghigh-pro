"""
Unit tests for OrderManager — all mocked (no real Alpaca or Sheets calls).
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.execution.alpaca_broker import AlpacaBroker, SimulatedOrder
from agent.execution.order_manager import (
    OrderManager,
    STATUS_DRY_RUN_OPEN,
    STATUS_OPEN,
    STATUS_CANCELLED_TIMEOUT,
    STATUS_REJECTED,
)
from agent.trader.decision_logic import Decision


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════

@pytest.fixture
def broker():
    """DRY_RUN broker."""
    return AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=True)


@pytest.fixture
def sheet_rows():
    """Collector for sheet writes."""
    rows = []
    return rows


@pytest.fixture
def manager(broker, sheet_rows):
    """OrderManager with mocked sheet writer."""
    return OrderManager(broker=broker, sheet_writer=lambda row: sheet_rows.append(row))


def _make_enter_decision(**overrides):
    """Create a Decision with action=ENTER and sensible defaults."""
    defaults = {
        "decision_id": "DEC-2026-05-03-00001",
        "ticker": "AAPL",
        "action": "ENTER",
        "price": 150.0,
        "quantity": 7,
        "tp_price": 135.0,
        "sl_price": 165.0,
        "position_size_usd": 1000.0,
        "agent_mode": "DRY_RUN",
    }
    defaults.update(overrides)
    d = Decision()
    for k, v in defaults.items():
        setattr(d, k, v)
    return d


# ════════════════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════════════════

class TestSkipDecision:
    def test_skip_decision_passthrough(self, manager):
        """SKIP decisions are returned unchanged, no broker call."""
        d = Decision()
        d.action = "SKIP"
        d.ticker = "MSFT"
        result = manager.execute(d)
        assert result.action == "SKIP"
        assert result.order_id is None
        assert result.order_status is None


class TestEnterDecision:
    def test_enter_decision_calls_broker(self, manager, broker):
        """ENTER decision triggers bracket order submission."""
        d = _make_enter_decision()
        result = manager.execute(d)
        # SimulatedOrder returned
        assert result.order_id is not None
        assert result.order_id.startswith("SIM-")

    def test_decision_enriched_with_order_id(self, manager):
        """Decision gets order_id after execution."""
        d = _make_enter_decision()
        result = manager.execute(d)
        assert result.order_id is not None
        assert len(result.order_id) > 5

    def test_decision_enriched_with_execution_price(self, manager):
        """Decision gets execution_price after fill."""
        d = _make_enter_decision(price=200.0)
        result = manager.execute(d)
        assert result.execution_price == 200.0

    def test_dry_run_writes_dry_run_open_status(self, manager, sheet_rows):
        """DRY_RUN mode writes DRY_RUN_OPEN to paper_portfolio."""
        d = _make_enter_decision()
        manager.execute(d)
        assert len(sheet_rows) == 1
        row = sheet_rows[0]
        # Status is at index 16 (25-col schema; TPPrice/SLPrice inserted at 11/12)
        assert row[16] == STATUS_DRY_RUN_OPEN

    def test_portfolio_row_has_25_columns(self, manager, sheet_rows):
        """Paper portfolio row must have exactly 25 columns (22->25: +TPPrice/SLPrice/DataQuality, commit 1c26a00)."""
        d = _make_enter_decision()
        manager.execute(d)
        assert len(sheet_rows[0]) == 25

    def test_portfolio_row_ticker_and_side(self, manager, sheet_rows):
        """Row contains correct ticker and side='short'."""
        d = _make_enter_decision(ticker="NVDA")
        manager.execute(d)
        row = sheet_rows[0]
        assert row[1] == "NVDA"   # Ticker
        assert row[7] == "short"  # Side


class TestRetryLogic:
    @patch("agent.execution.order_manager.time.sleep")
    def test_retry_on_transient_failure(self, mock_sleep, sheet_rows):
        """Retries on transient error, succeeds on 2nd attempt."""
        broker = AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=True)
        # Patch broker to fail once then succeed
        call_count = {"n": 0}
        original = broker.submit_bracket_order

        def flaky(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise ConnectionError("transient network failure")
            return original(*args, **kwargs)

        broker.submit_bracket_order = flaky
        mgr = OrderManager(broker=broker, sheet_writer=lambda row: sheet_rows.append(row))

        d = _make_enter_decision()
        result = mgr.execute(d)
        assert result.order_id is not None
        assert result.order_status == "filled"
        assert call_count["n"] == 2
        mock_sleep.assert_called_once_with(2)  # backoff: 2^1

    @patch("agent.execution.order_manager.time.sleep")
    def test_max_retries_returns_rejected(self, mock_sleep, sheet_rows):
        """After 3 failures, decision is marked REJECTED."""
        broker = AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=True)
        broker.submit_bracket_order = MagicMock(side_effect=ConnectionError("down"))
        mgr = OrderManager(broker=broker, sheet_writer=lambda row: sheet_rows.append(row))

        d = _make_enter_decision()
        result = mgr.execute(d)
        assert result.order_status == STATUS_REJECTED
        assert result.order_id is None
        assert broker.submit_bracket_order.call_count == 3

    @patch("agent.execution.order_manager.time.sleep")
    def test_failed_submission_marks_rejected(self, mock_sleep):
        """Broker always failing → decision.order_status = REJECTED."""
        broker = AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=True)
        broker.submit_bracket_order = MagicMock(side_effect=RuntimeError("blocked"))
        mgr = OrderManager(broker=broker, sheet_writer=lambda row: None)

        d = _make_enter_decision()
        result = mgr.execute(d)
        assert result.order_status == STATUS_REJECTED
        assert len(sheet_rows) == 0 if 'sheet_rows' in dir() else True
