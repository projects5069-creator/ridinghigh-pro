"""
Unit tests for PositionManager — all mocked (no real Alpaca/Sheets/data calls).
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.execution.alpaca_broker import AlpacaBroker, SimulatedOrder
from agent.execution.position_manager import (
    PositionManager,
    STATUS_OPEN,
    STATUS_DRY_RUN_OPEN,
    STATUS_CLOSED,
    STATUS_DRY_RUN_CLOSED,
    EXIT_TP_HIT,
    EXIT_SL_HIT,
    EXIT_EOD_CLOSE,
)


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════

@pytest.fixture
def broker():
    return AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=True)


@pytest.fixture
def mock_data_provider():
    dp = MagicMock()
    dp.get_current_price.return_value = 140.0
    return dp


@pytest.fixture
def updates_log():
    """Collects all sheet_writer calls."""
    log = []
    return log


def _make_open_position(**overrides):
    """Create a position dict mimicking paper_portfolio row."""
    defaults = {
        "PositionID": "DEC-2026-05-03-00001",
        "Ticker": "AAPL",
        "EntryDate": "2026-05-03",
        "EntryTime": "10:30:00",
        "EntryPrice": "150.0",
        "Quantity": "7",
        "PositionSizeUSD": "1050.0",
        "Side": "short",
        "EntryOrderID": "SIM-abc123",
        "TPOrderID": "SIM-abc123-tp",
        "SLOrderID": "SIM-abc123-sl",
        "CurrentPrice": "",
        "UnrealizedPnL": "",
        "UnrealizedPnLPct": "",
        "Status": STATUS_DRY_RUN_OPEN,
        "ExitPrice": "",
        "ExitDate": "",
        "ExitTime": "",
        "ExitReason": "",
        "RealizedPnL": "",
        "RealizedPnLPct": "",
        "LastUpdated": "",
    }
    defaults.update(overrides)
    return defaults


# ════════════════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════════════════

class TestNoPositions:
    def test_no_open_positions_returns_empty_stats(self, broker):
        """Empty portfolio returns zeroed stats."""
        pm = PositionManager(
            broker=broker,
            sheet_reader=lambda: [],
        )
        stats = pm.monitor_all()
        assert stats == {"updated": 0, "closed_tp": 0, "closed_sl": 0, "errors": 0}


class TestPriceUpdates:
    def test_open_position_updates_price(self, broker, mock_data_provider, updates_log):
        """Open position gets CurrentPrice updated."""
        pos = _make_open_position()
        mock_data_provider.get_latest_bar.return_value = {"close": 140.0}
        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: [pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        stats = pm.monitor_all()
        assert stats["updated"] == 1
        assert len(updates_log) == 1
        _, updates = updates_log[0]
        assert updates["CurrentPrice"] == 140.0

    def test_pnl_calculation_correct(self, broker, mock_data_provider, updates_log):
        """Short PnL: entry=150, current=140 → profit = (150-140)*7 = 70."""
        pos = _make_open_position(EntryPrice="150.0", Quantity="7")
        mock_data_provider.get_latest_bar.return_value = {"close": 140.0}
        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: [pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        pm.monitor_all()
        _, updates = updates_log[0]
        assert updates["UnrealizedPnL"] == 70.0
        assert abs(updates["UnrealizedPnLPct"] - 6.67) < 0.01


class TestTPSLDetection:
    def test_tp_hit_closes_position(self, broker, mock_data_provider, updates_log):
        """TP order filled → position closed with TP_HIT."""
        pos = _make_open_position(
            Status=STATUS_OPEN,
            TPOrderID="real-tp-order-123",
            SLOrderID="real-sl-order-456",
        )
        # Mock broker: TP filled, SL not
        def mock_get_order(oid):
            o = MagicMock()
            o.status = "filled" if oid == "real-tp-order-123" else "held"
            return o

        broker._trading_client = MagicMock()
        broker.dry_run = False
        broker.get_order = mock_get_order

        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: [pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        stats = pm.monitor_all()
        assert stats["closed_tp"] == 1
        _, updates = updates_log[0]
        assert updates["ExitReason"] == EXIT_TP_HIT
        assert updates["Status"] == STATUS_CLOSED

    def test_sl_hit_closes_position(self, broker, mock_data_provider, updates_log):
        """SL order filled → position closed with SL_HIT."""
        pos = _make_open_position(
            Status=STATUS_OPEN,
            TPOrderID="real-tp-order-123",
            SLOrderID="real-sl-order-456",
        )

        def mock_get_order(oid):
            o = MagicMock()
            o.status = "filled" if oid == "real-sl-order-456" else "held"
            return o

        broker._trading_client = MagicMock()
        broker.dry_run = False
        broker.get_order = mock_get_order

        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: [pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        stats = pm.monitor_all()
        assert stats["closed_sl"] == 1
        _, updates = updates_log[0]
        assert updates["ExitReason"] == EXIT_SL_HIT

    def test_sl_takes_precedence_over_tp(self, broker, mock_data_provider, updates_log):
        """If both TP and SL filled, SL wins (conservative)."""
        pos = _make_open_position(
            Status=STATUS_OPEN,
            TPOrderID="real-tp-123",
            SLOrderID="real-sl-456",
        )

        def mock_get_order(oid):
            o = MagicMock()
            o.status = "filled"  # both filled
            return o

        broker._trading_client = MagicMock()
        broker.dry_run = False
        broker.get_order = mock_get_order

        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: [pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        stats = pm.monitor_all()
        assert stats["closed_sl"] == 1
        assert stats["closed_tp"] == 0


class TestEODClose:
    def test_eod_close_all_marks_eod(self, broker, mock_data_provider, updates_log):
        """EOD close marks all positions with EXIT_EOD_CLOSE."""
        positions = [
            _make_open_position(Ticker="AAPL"),
            _make_open_position(Ticker="TSLA"),
        ]
        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: positions,
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        stats = pm.eod_close_all()
        assert stats["closed"] == 2
        assert stats["errors"] == 0
        for _, updates in updates_log:
            assert updates["ExitReason"] == EXIT_EOD_CLOSE


class TestDryRunSafety:
    def test_dry_run_open_doesnt_call_real_close(self, mock_data_provider, updates_log):
        """DRY_RUN_OPEN positions don't call broker.close_position."""
        broker = AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=True)
        broker.close_position = MagicMock()
        pos = _make_open_position(Status=STATUS_DRY_RUN_OPEN)

        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: [pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        pm.eod_close_all()
        broker.close_position.assert_not_called()
        _, updates = updates_log[0]
        assert updates["Status"] == STATUS_DRY_RUN_CLOSED


class TestGracefulFailures:
    def test_get_current_price_failure_graceful(self, broker, updates_log):
        """If data_provider fails, position still counted as updated."""
        failing_dp = MagicMock()
        failing_dp.get_latest_bar.return_value = None
        failing_dp.get_latest_quote.return_value = None
        pos = _make_open_position()

        pm = PositionManager(
            broker=broker,
            data_provider=failing_dp,
            sheet_reader=lambda: [pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        stats = pm.monitor_all()
        assert stats["updated"] == 1
        assert stats["errors"] == 0
        assert len(updates_log) == 0  # no update written (no price)

    def test_partial_failure_doesnt_block_others(self, broker, mock_data_provider, updates_log):
        """Error in one position doesn't prevent processing others."""
        good_pos = _make_open_position(Ticker="AAPL")
        bad_pos = _make_open_position(Ticker="BAD", EntryPrice="not_a_number")

        # BAD will raise ValueError on float("not_a_number") inside _process_position
        mock_data_provider.get_current_price.return_value = 140.0

        pm = PositionManager(
            broker=broker,
            data_provider=mock_data_provider,
            sheet_reader=lambda: [good_pos, bad_pos],
            sheet_writer=lambda p, u: updates_log.append((p, u)),
        )
        stats = pm.monitor_all()
        # AAPL should succeed, BAD should error (invalid EntryPrice)
        assert stats["updated"] == 1
        assert stats["errors"] == 1
