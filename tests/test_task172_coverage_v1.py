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
