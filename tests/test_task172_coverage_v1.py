"""TASK-172 — borrow coverage: widen universe + borrow_coverage tab.

Tests added task-by-task (TDD). Task 1: borrow_coverage schema registration.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from agent.setup.create_agent_sheets import AGENT_SHEET_HEADERS
from agent.perception import borrow_collector as bc


def test_borrow_coverage_header_registered():
    cols = AGENT_SHEET_HEADERS["borrow_coverage"]
    assert cols == [
        "CheckDate", "CheckTime", "ScannedUniverse", "WithBorrowData",
        "PctWithBorrowData", "ShortableCount", "PctShortable", "Source",
    ]


# ── Task 2: get_scanned_universe — Score>=min tickers from a snapshots df ──
def test_get_scanned_universe_filters_by_min_score():
    df = pd.DataFrame({"Ticker": ["AAA", "BBB", "CCC"], "Score": [75, 60, 59]})
    assert bc.get_scanned_universe(df, min_score=60) == {"AAA", "BBB"}


def test_get_scanned_universe_empty_or_missing_cols():
    assert bc.get_scanned_universe(pd.DataFrame(), min_score=60) == set()
    assert bc.get_scanned_universe(pd.DataFrame({"Ticker": ["X"]}), min_score=60) == set()



# ── Task 3: compute_coverage — counts + two separate pcts over universe denom ──
# borrow_rows are borrow_data sheet rows: idx0=Ticker, idx3=IsShortable (bool or "True"/"False")
def test_compute_coverage_basic():
    universe = {"AAA", "BBB", "CCC", "DDD"}
    borrow_rows = [
        ["AAA", "2026-06-14", "09:00:00", True, False, True, "", "", "ALPACA"],
        ["BBB", "2026-06-14", "09:00:00", "True", "True", "False", "", "", "ALPACA"],
        ["CCC", "2026-06-14", "09:00:00", False, False, False, "", "", "ALPACA"],
    ]
    r = bc.compute_coverage(universe, borrow_rows)
    assert r["ScannedUniverse"] == 4
    assert r["WithBorrowData"] == 3
    assert r["ShortableCount"] == 2          # AAA(True) + BBB("True"); CCC False
    assert r["PctWithBorrowData"] == 75.0    # 3/4
    assert r["PctShortable"] == 50.0         # 2/4 (denom = universe)


def test_compute_coverage_ignores_rows_outside_universe():
    universe = {"AAA"}
    borrow_rows = [
        ["AAA", "d", "t", True, False, True, "", "", "ALPACA"],
        ["ZZZ", "d", "t", True, False, True, "", "", "ALPACA"],  # not in universe
    ]
    r = bc.compute_coverage(universe, borrow_rows)
    assert r["ScannedUniverse"] == 1
    assert r["WithBorrowData"] == 1
    assert r["ShortableCount"] == 1
    assert r["PctWithBorrowData"] == 100.0
    assert r["PctShortable"] == 100.0


def test_compute_coverage_empty_universe():
    r = bc.compute_coverage(set(), [])
    assert r["ScannedUniverse"] == 0
    assert r["WithBorrowData"] == 0
    assert r["ShortableCount"] == 0
    assert r["PctWithBorrowData"] == 0.0
    assert r["PctShortable"] == 0.0



# ── Task 4: build_coverage_row — cov dict + check_dt → 8-value row in schema order ──
def test_build_coverage_row_schema_order():
    import datetime
    cov = {
        "ScannedUniverse": 4, "WithBorrowData": 3, "ShortableCount": 2,
        "PctWithBorrowData": 75.0, "PctShortable": 50.0,
    }
    dt = datetime.datetime(2026, 6, 14, 9, 30, 0)
    row = bc.build_coverage_row(cov, dt)
    assert row == [
        "2026-06-14", "09:30:00", 4, 3, 75.0, 2, 50.0, "ALPACA",
    ]


def test_build_coverage_row_matches_header_length():
    import datetime
    from agent.setup.create_agent_sheets import AGENT_SHEET_HEADERS
    cov = bc.compute_coverage(set(), [])
    row = bc.build_coverage_row(cov, datetime.datetime(2026, 6, 14, 9, 30, 0))
    assert len(row) == len(AGENT_SHEET_HEADERS["borrow_coverage"]) == 8



# ── Task 5: collect_borrow_coverage — read today borrow_data, write 1 coverage row ──
class _FakeWS:
    def __init__(self, values):
        self._values = values
        self.appended = []
    def get_all_values(self):
        return self._values

def test_collect_borrow_coverage_writes_one_row(monkeypatch):
    import datetime
    import agent.perception.borrow_collector as m
    universe = {"AAA", "BBB", "CCC", "DDD"}
    dt = datetime.datetime(2026, 6, 14, 9, 30, 0)
    header = ["Ticker", "CheckDate", "CheckTime", "IsShortable", "IsETB", "IsHTB", "BorrowFeePct", "SharesAvailable", "Source"]
    borrow_ws = _FakeWS([
        header,
        ["AAA", "2026-06-14", "09:00:00", "True", "False", "True", "", "", "ALPACA"],
        ["BBB", "2026-06-14", "09:00:00", "True", "True", "False", "", "", "ALPACA"],
        ["CCC", "2026-06-14", "09:00:00", "False", "False", "False", "", "", "ALPACA"],
        ["OLD", "2026-06-13", "09:00:00", "True", "False", "True", "", "", "ALPACA"],  # different day, ignored
    ])
    cov_ws = _FakeWS([])
    def fake_get_ws(tab, *a, **k):
        return {"borrow_data": borrow_ws, "borrow_coverage": cov_ws}.get(tab)
    captured = {}
    def fake_append(ws, rows, **k):
        captured["ws"] = ws; captured["rows"] = rows; captured["kwargs"] = k
    monkeypatch.setattr(m.sheets_manager, "get_worksheet", fake_get_ws)
    monkeypatch.setattr(m.sheets_manager, "safe_append_rows", fake_append)
    cov = m.collect_borrow_coverage(universe, check_dt=dt)
    assert cov["ScannedUniverse"] == 4
    assert cov["WithBorrowData"] == 3
    assert cov["ShortableCount"] == 2
    assert cov["PctWithBorrowData"] == 75.0
    assert cov["PctShortable"] == 50.0
    assert captured["ws"] is cov_ws
    assert len(captured["rows"]) == 1
    assert captured["rows"][0] == ["2026-06-14", "09:30:00", 4, 3, 75.0, 2, 50.0, "ALPACA"]
    assert captured["kwargs"].get("dedup_col") == 0
    assert captured["kwargs"].get("dedup_vals") == {"2026-06-14"}

def test_collect_borrow_coverage_nonfatal_on_missing_ws(monkeypatch):
    import datetime
    import agent.perception.borrow_collector as m
    monkeypatch.setattr(m.sheets_manager, "get_worksheet", lambda *a, **k: None)
    cov = m.collect_borrow_coverage({"AAA"}, check_dt=datetime.datetime(2026,6,14,9,30,0))
    assert cov is None  # graceful: no worksheet -> None, never raises
