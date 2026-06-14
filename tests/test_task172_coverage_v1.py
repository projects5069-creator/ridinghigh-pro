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
