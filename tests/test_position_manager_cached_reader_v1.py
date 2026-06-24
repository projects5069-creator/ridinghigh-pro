"""TASK-136 (cut C1) — position_manager shares the paper_portfolio read cache.

The orchestrator builds PositionManager with no `sheet_reader`, so
`_get_open_positions` falls back to an UNCACHED `get_worksheet(...).get_all_records()`
every minute (position_manager.py:128-131) — a duplicate API read of paper_portfolio
which account-state-builder already reads cached in the same run
(orchestrator.py:222, get_sheet_records). The cut injects a cached reader that routes
through `sheets_manager.get_sheet_records("paper_portfolio")` (60s cache, TASK-58),
collapsing the 2nd API read into a cache hit.

Risk being pinned here: gspread `get_all_records()` type-coerces numeric cells to
int/float, whereas `get_sheet_records()` returns ALL strings (sheets_manager.py:441-447).
The position pipeline consumes EntryPrice/TPPrice/SLPrice as float and Quantity as int
(position_manager.py:179-180,193-194,269-272). `_coerce_portfolio_record` normalizes the
cached string records back to the gspread-equivalent numeric types (and hardens the
Quantity path against a display-formatted "100.0" that would crash int("100.0")), so the
cut is behavior-preserving. Row order — and thus the positional `_row_number` write
target — is preserved by both paths (rows[1:] in order), verified below.

Pure/deterministic: no live Sheets, no credentials.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.execution.position_manager import (
    PositionManager,
    _coerce_portfolio_record,
    cached_portfolio_reader,
)


# ── _coerce_portfolio_record: string records → gspread-equivalent numeric types ──

def test_coerce_price_fields_to_float():
    out = _coerce_portfolio_record({"EntryPrice": "3.41", "TPPrice": "3.0", "SLPrice": "5.0"})
    assert out["EntryPrice"] == 3.41 and isinstance(out["EntryPrice"], float)
    assert out["TPPrice"] == 3.0 and isinstance(out["TPPrice"], float)
    assert out["SLPrice"] == 5.0 and isinstance(out["SLPrice"], float)


def test_coerce_quantity_to_int_including_decimal_string():
    out = _coerce_portfolio_record({"Quantity": "100"})
    assert out["Quantity"] == 100 and isinstance(out["Quantity"], int)
    # A display-formatted "100.0" must NOT crash int("100.0"); coerce via float.
    out2 = _coerce_portfolio_record({"Quantity": "100.0"})
    assert out2["Quantity"] == 100 and isinstance(out2["Quantity"], int)


def test_coerce_preserves_strings_blanks_and_rownumber():
    rec = {"PositionID": "P-001", "Ticker": "FOO", "Status": "DRY_RUN_OPEN",
           "EntryPrice": "", "_row_number": 7}
    out = _coerce_portfolio_record(rec)
    assert out["PositionID"] == "P-001"   # digit-free string untouched
    assert out["Ticker"] == "FOO"
    assert out["Status"] == "DRY_RUN_OPEN"
    assert out["EntryPrice"] == ""        # blank numeric preserved (gspread empty cell == "")
    assert out["_row_number"] == 7


def test_coerce_is_idempotent_on_already_numeric():
    out = _coerce_portfolio_record({"EntryPrice": 3.41, "Quantity": 100})
    assert out["EntryPrice"] == 3.41 and isinstance(out["EntryPrice"], float)
    assert out["Quantity"] == 100 and isinstance(out["Quantity"], int)


def test_coerce_non_numeric_in_numeric_field_is_preserved_not_crashed():
    out = _coerce_portfolio_record({"EntryPrice": "N/A"})
    assert out["EntryPrice"] == "N/A"


def test_coerce_does_not_mutate_input():
    rec = {"EntryPrice": "4.0"}
    _coerce_portfolio_record(rec)
    assert rec["EntryPrice"] == "4.0"     # original dict untouched


# ── cached_portfolio_reader: reads via the cached get_sheet_records + coerces ──

def test_cached_reader_routes_through_get_sheet_records_and_coerces(monkeypatch):
    import sheets_manager
    calls = {"tab": None}

    def _fake_records(tab, *a, **k):
        calls["tab"] = tab
        return [{"EntryPrice": "4.0", "Quantity": "100", "Status": "OPEN", "Ticker": "FOO"}]

    monkeypatch.setattr(sheets_manager, "get_sheet_records", _fake_records)
    rows = cached_portfolio_reader()
    assert calls["tab"] == "paper_portfolio"          # uses the cached helper, not raw get_all_records
    assert rows[0]["EntryPrice"] == 4.0 and isinstance(rows[0]["EntryPrice"], float)
    assert rows[0]["Quantity"] == 100 and isinstance(rows[0]["Quantity"], int)


# ── behavioral equivalence: string-sourced (coerced) records flow identically ──

class _StubProvider:
    def __init__(self, price):
        self._p = price

    def get_latest_bar(self, ticker):
        return {"close": self._p}

    def get_latest_quote(self, ticker):
        return None


def test_get_open_positions_filters_and_tags_rownumber_in_order():
    rows = [
        {"Status": "DRY_RUN_OPEN", "Ticker": "FOO"},   # sheet row 2
        {"Status": "CLOSED", "Ticker": "BAR"},         # sheet row 3 (filtered out)
        {"Status": "OPEN", "Ticker": "BAZ"},           # sheet row 4
    ]
    pm = PositionManager(broker=object(), data_provider=_StubProvider(1.0),
                         sheet_reader=lambda: rows)
    open_pos = pm._get_open_positions()
    assert [p["Ticker"] for p in open_pos] == ["FOO", "BAZ"]
    assert [p["_row_number"] for p in open_pos] == [2, 4]   # positional target preserved


def test_updated_path_computes_pnl_from_coerced_string_record():
    raw = {"Status": "OPEN", "Ticker": "FOO", "PositionID": "P1",
           "TPPrice": "0", "SLPrice": "0", "EntryPrice": "4.0", "Quantity": "100",
           "TPOrderID": "", "SLOrderID": "", "_row_number": 2}
    rec = _coerce_portfolio_record(raw)
    captured = {}
    pm = PositionManager(broker=object(), data_provider=_StubProvider(3.0),
                         sheet_reader=lambda: [rec],
                         sheet_writer=lambda pos, upd: captured.update(upd))
    result = pm._process_position(rec)
    assert result == "updated"
    # Short PnL: (entry 4.0 - current 3.0) * 100 = 100.0 — proves float/int coercion held.
    assert captured["CurrentPrice"] == 3.0
    assert captured["UnrealizedPnL"] == 100.0
