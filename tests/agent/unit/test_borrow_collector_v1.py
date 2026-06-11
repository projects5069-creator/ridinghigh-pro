"""Unit tests for agent/perception/borrow_collector.py — TASK-139 [BORROW] layer 1.

Written test-first (RED) before the collector exists. These tests pin the
contract the collector must satisfy:

  build_borrow_row(ticker, asset_info, check_dt) -> 9-value row in schema order
  collect_borrow_data(tickers, broker, check_dt=None) -> int rows written

Design mirrors decision_logger.flush_skip_summary: lazy worksheet resolve via
the module-global `sheets_manager`, ONE batched safe_append_rows, never raises,
returns rows-written (0 on no-op/error).
"""

import sys
import os
import importlib
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.perception import borrow_collector as bc

# Schema source of truth lives in create_agent_sheets (tab definition).
cs = importlib.import_module("agent.setup.create_agent_sheets")

EXPECTED_BORROW_HEADERS = [
    "Ticker", "CheckDate", "CheckTime", "IsShortable",
    "IsETB", "IsHTB", "BorrowFeePct", "SharesAvailable",
    "Source",
]

FIXED_DT = datetime(2026, 6, 11, 16, 0, 0)   # 16:00:00 Peru, EOD slot
TODAY = "2026-06-11"


def _asset(shortable=True, etb=True, **extra):
    """Build an asset_info dict shaped like AlpacaBroker.get_asset_info()."""
    info = {"symbol": "X", "shortable": shortable, "easy_to_borrow": etb,
            "tradable": True, "status": "active"}
    info.update(extra)
    return info


def _broker(asset_info=None, side_effect=None):
    b = MagicMock()
    if side_effect is not None:
        b.get_asset_info.side_effect = side_effect
    else:
        b.get_asset_info.return_value = asset_info if asset_info is not None else _asset()
    return b


def _ws(existing_rows=None):
    """Mock worksheet. get_all_values() returns header + any existing data rows."""
    ws = MagicMock()
    rows = [EXPECTED_BORROW_HEADERS] + (existing_rows or [])
    ws.get_all_values.return_value = rows
    return ws


# ─────────────────────────── schema ───────────────────────────

def test_borrow_data_schema_is_9_columns():
    """The borrow_data tab is exactly the 9 expected columns, in order."""
    assert cs.AGENT_SHEET_HEADERS.get("borrow_data") == EXPECTED_BORROW_HEADERS


def test_build_row_has_9_values_in_schema_order():
    """build_borrow_row emits 9 values matching the schema positions."""
    row = bc.build_borrow_row("AAPL", _asset(shortable=True, etb=True), FIXED_DT)
    assert len(row) == 9
    assert row[0] == "AAPL"          # Ticker
    assert row[1] == TODAY           # CheckDate (Peru)
    assert row[2] == "16:00:00"      # CheckTime (Peru)
    assert row[3] is True            # IsShortable
    assert row[4] is True            # IsETB
    assert row[8] == "ALPACA"        # Source


# ─────────────────────────── field semantics ───────────────────────────

def test_borrow_fee_pct_is_null_not_constant():
    """BorrowFeePct is an explicit NULL (empty cell) — never 12.5 or 0.0."""
    row = bc.build_borrow_row("AAPL", _asset(), FIXED_DT)
    assert row[6] == ""              # BorrowFeePct NULL
    assert row[6] != 12.5
    assert row[6] != 0.0


def test_is_htb_derived_shortable_and_not_etb():
    """IsHTB = IsShortable AND NOT IsETB."""
    # shortable + hard to borrow (not ETB) -> HTB True
    assert bc.build_borrow_row("A", _asset(shortable=True, etb=False), FIXED_DT)[5] is True
    # shortable + easy to borrow -> HTB False
    assert bc.build_borrow_row("B", _asset(shortable=True, etb=True), FIXED_DT)[5] is False
    # not shortable -> HTB False
    assert bc.build_borrow_row("C", _asset(shortable=False, etb=False), FIXED_DT)[5] is False


def test_shares_available_null_when_not_exposed_else_value():
    """SharesAvailable = NULL when API does not expose it; the value when it does."""
    row_null = bc.build_borrow_row("A", _asset(), FIXED_DT)
    assert row_null[7] == ""                                   # not exposed -> NULL
    row_val = bc.build_borrow_row("B", _asset(shares_available=5000), FIXED_DT)
    assert row_val[7] == 5000                                  # exposed -> value


# ─────────────────────────── batch write ───────────────────────────

def test_collect_writes_one_batched_append_for_all_tickers():
    """collect_borrow_data makes exactly ONE safe_append_rows call, with one row per ticker."""
    sm = MagicMock()
    sm.get_worksheet.return_value = _ws()
    with patch.object(bc, "sheets_manager", sm):
        n = bc.collect_borrow_data(["AAA", "BBB", "CCC"], _broker(), check_dt=FIXED_DT)
    assert n == 3
    assert sm.safe_append_rows.call_count == 1
    rows_written = sm.safe_append_rows.call_args.args[1]
    assert len(rows_written) == 3
    assert [r[0] for r in rows_written] == ["AAA", "BBB", "CCC"]


def test_collect_dedups_on_ticker_and_checkdate():
    """A ticker already written for today is not appended again (dedup on Ticker+CheckDate)."""
    sm = MagicMock()
    sm.get_worksheet.return_value = _ws(existing_rows=[
        ["AAA", TODAY, "09:00:00", True, True, False, "", "", "ALPACA"],
    ])
    with patch.object(bc, "sheets_manager", sm):
        n = bc.collect_borrow_data(["AAA", "BBB"], _broker(), check_dt=FIXED_DT)
    rows_written = sm.safe_append_rows.call_args.args[1]
    assert [r[0] for r in rows_written] == ["BBB"]   # AAA skipped (already today)
    assert n == 1


def test_collect_noop_when_all_tickers_already_collected_today():
    """already-written-today guard: nothing to write -> no append call, returns 0."""
    sm = MagicMock()
    sm.get_worksheet.return_value = _ws(existing_rows=[
        ["AAA", TODAY, "09:00:00", True, True, False, "", "", "ALPACA"],
    ])
    with patch.object(bc, "sheets_manager", sm):
        n = bc.collect_borrow_data(["AAA"], _broker(), check_dt=FIXED_DT)
    assert n == 0
    assert sm.safe_append_rows.call_count == 0


# ─────────────────────────── non-fatal failures ───────────────────────────

def test_broker_failure_is_non_fatal_other_tickers_still_written():
    """A broker error on one ticker is skipped; the run does not crash and others are written."""
    def boom(ticker):
        if ticker == "BBB":
            raise RuntimeError("alpaca timeout")
        return _asset()
    sm = MagicMock()
    sm.get_worksheet.return_value = _ws()
    with patch.object(bc, "sheets_manager", sm):
        n = bc.collect_borrow_data(["AAA", "BBB", "CCC"], _broker(side_effect=boom), check_dt=FIXED_DT)
    rows_written = sm.safe_append_rows.call_args.args[1]
    assert [r[0] for r in rows_written] == ["AAA", "CCC"]   # BBB dropped, not fatal
    assert n == 2


def test_sheets_failure_is_non_fatal_returns_zero_and_does_not_raise():
    """A Sheets write failure never raises and is not counted as an error (returns 0)."""
    sm = MagicMock()
    sm.get_worksheet.return_value = _ws()
    sm.safe_append_rows.side_effect = Exception("429 quota")
    with patch.object(bc, "sheets_manager", sm):
        n = bc.collect_borrow_data(["AAA", "BBB"], _broker(), check_dt=FIXED_DT)   # must not raise
    assert n == 0


def test_missing_worksheet_is_non_fatal_returns_zero():
    """If the borrow_data worksheet is unavailable, collect returns 0 without raising."""
    sm = MagicMock()
    sm.get_worksheet.return_value = None
    with patch.object(bc, "sheets_manager", sm):
        n = bc.collect_borrow_data(["AAA"], _broker(), check_dt=FIXED_DT)
    assert n == 0


# ─────────────────────────── AC#6: real read even under DRY_RUN ───────────────────────────

def test_collector_reads_real_broker_even_in_dry_run():
    """Collector calls broker.get_asset_info() directly (real read) regardless of AGENT_DRY_RUN —
    it must NOT route through the mocked tradability path that would fabricate is_shortable=True."""
    sm = MagicMock()
    sm.get_worksheet.return_value = _ws()
    broker = _broker(_asset(shortable=False, etb=False))
    with patch("config.AGENT_DRY_RUN", True), patch.object(bc, "sheets_manager", sm):
        bc.collect_borrow_data(["AAA"], broker, check_dt=FIXED_DT)
    broker.get_asset_info.assert_called_once_with("AAA")
    rows_written = sm.safe_append_rows.call_args.args[1]
    assert rows_written[0][3] is False   # real shortable=False landed, not a mock True
