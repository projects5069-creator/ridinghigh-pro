"""
Unit tests for Reconciler — all mocked (no real Alpaca/Sheets calls).
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.execution.alpaca_broker import AlpacaBroker
from agent.execution.reconciler import (
    Reconciler,
    STATUS_OPEN,
    STATUS_DRY_RUN_OPEN,
    STATUS_CLOSED,
    DRIFT_PHANTOM_OPEN,
    DRIFT_ORPHAN_POSITION,
)


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════

@pytest.fixture
def broker():
    return AlpacaBroker(api_key="PKtest", secret_key="sec", dry_run=True)


@pytest.fixture
def alerts():
    """Collector for alert_writer calls."""
    return []


@pytest.fixture
def sheet_updates():
    """Collector for sheet_writer calls."""
    return []


def _sheet_pos(ticker, status=STATUS_OPEN):
    """Create a sheet position dict."""
    return {
        "PositionID": f"DEC-{ticker}-001",
        "Ticker": ticker,
        "Status": status,
        "EntryPrice": "100.0",
        "Quantity": "10",
    }


def _alpaca_pos(ticker, qty="10"):
    """Create an Alpaca position dict."""
    return {"symbol": ticker, "qty": qty, "side": "short", "avg_entry_price": "100.0"}


# ════════════════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════════════════

class TestNodrift:
    def test_no_drift_when_aligned(self, broker, alerts, sheet_updates):
        """Sheet OPEN + Alpaca exists → ok, no drift."""
        broker.list_positions = lambda: [_alpaca_pos("AAPL")]

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [_sheet_pos("AAPL")],
            sheet_writer=lambda p, u: sheet_updates.append((p, u)),
            alert_writer=lambda e: alerts.append(e),
        )
        report = rec.reconcile()
        assert report["ok"] == 1
        assert report["phantom_open"] == 0
        assert report["orphan_position"] == 0
        assert len(alerts) == 0
        assert len(sheet_updates) == 0

    def test_empty_sheet_and_alpaca_returns_zero(self, broker, alerts):
        """No positions anywhere → all zeros."""
        broker.list_positions = lambda: []

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [],
            alert_writer=lambda e: alerts.append(e),
        )
        report = rec.reconcile()
        assert report["ok"] == 0
        assert report["phantom_open"] == 0
        assert report["orphan_position"] == 0
        assert report["skipped_dry_run"] == 0
        assert len(alerts) == 0


class TestPhantomOpen:
    def test_phantom_open_marked_closed(self, broker, alerts, sheet_updates):
        """Sheet OPEN + Alpaca empty → mark CLOSED."""
        broker.list_positions = lambda: []  # nothing in Alpaca

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [_sheet_pos("AAPL")],
            sheet_writer=lambda p, u: sheet_updates.append((p, u)),
            alert_writer=lambda e: alerts.append(e),
        )
        report = rec.reconcile()
        assert report["phantom_open"] == 1
        assert len(sheet_updates) == 1
        _, updates = sheet_updates[0]
        assert updates["Status"] == STATUS_CLOSED
        assert updates["ExitReason"] == "RECONCILER_PHANTOM"

    def test_phantom_open_calls_alert_writer(self, broker, alerts, sheet_updates):
        """Phantom open event is written to system_events via alert_writer."""
        broker.list_positions = lambda: []

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [_sheet_pos("TSLA")],
            sheet_writer=lambda p, u: sheet_updates.append((p, u)),
            alert_writer=lambda e: alerts.append(e),
        )
        rec.reconcile()
        assert len(alerts) == 1
        assert alerts[0]["type"] == DRIFT_PHANTOM_OPEN
        assert alerts[0]["ticker"] == "TSLA"


class TestOrphanPosition:
    def test_orphan_position_alerts_only(self, broker, alerts, sheet_updates):
        """Alpaca has position not in Sheet → alert, no sheet modification."""
        broker.list_positions = lambda: [_alpaca_pos("NVDA", qty="5")]

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [],  # empty sheet
            sheet_writer=lambda p, u: sheet_updates.append((p, u)),
            alert_writer=lambda e: alerts.append(e),
        )
        report = rec.reconcile()
        assert report["orphan_position"] == 1
        assert len(sheet_updates) == 0  # don't auto-fix orphans
        assert len(alerts) == 1

    def test_orphan_position_calls_alert_writer(self, broker, alerts):
        """Orphan event includes ticker and qty."""
        broker.list_positions = lambda: [_alpaca_pos("GME", qty="20")]

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [],
            alert_writer=lambda e: alerts.append(e),
        )
        rec.reconcile()
        assert alerts[0]["type"] == DRIFT_ORPHAN_POSITION
        assert alerts[0]["ticker"] == "GME"
        assert alerts[0]["alpaca_qty"] == "20"


class TestDryRunSkip:
    def test_dry_run_positions_skipped(self, broker, alerts, sheet_updates):
        """DRY_RUN_OPEN positions are counted but not checked against Alpaca."""
        broker.list_positions = lambda: []

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [
                _sheet_pos("AAPL", status=STATUS_DRY_RUN_OPEN),
                _sheet_pos("TSLA", status=STATUS_DRY_RUN_OPEN),
            ],
            sheet_writer=lambda p, u: sheet_updates.append((p, u)),
            alert_writer=lambda e: alerts.append(e),
        )
        report = rec.reconcile()
        assert report["skipped_dry_run"] == 2
        assert report["phantom_open"] == 0
        assert len(alerts) == 0
        assert len(sheet_updates) == 0


class TestMultipleDrifts:
    def test_multiple_drifts_all_detected(self, broker, alerts, sheet_updates):
        """Mix of ok, phantom, and orphan — all counted correctly."""
        # Sheet: AAPL (OPEN), TSLA (OPEN), MSFT (DRY_RUN_OPEN)
        # Alpaca: AAPL (exists), NVDA (orphan)
        # → AAPL=ok, TSLA=phantom, MSFT=dry_run skip, NVDA=orphan
        broker.list_positions = lambda: [
            _alpaca_pos("AAPL"),
            _alpaca_pos("NVDA"),
        ]

        rec = Reconciler(
            broker=broker,
            sheet_reader=lambda: [
                _sheet_pos("AAPL", status=STATUS_OPEN),
                _sheet_pos("TSLA", status=STATUS_OPEN),
                _sheet_pos("MSFT", status=STATUS_DRY_RUN_OPEN),
            ],
            sheet_writer=lambda p, u: sheet_updates.append((p, u)),
            alert_writer=lambda e: alerts.append(e),
        )
        report = rec.reconcile()
        assert report["ok"] == 1
        assert report["phantom_open"] == 1
        assert report["orphan_position"] == 1
        assert report["skipped_dry_run"] == 1
        assert len(alerts) == 2  # phantom + orphan
        assert len(report["details"]) == 2
