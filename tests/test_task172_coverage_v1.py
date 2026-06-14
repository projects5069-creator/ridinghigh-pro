"""TASK-172 — borrow coverage: widen universe + borrow_coverage tab.

Tests added task-by-task (TDD). Task 1: borrow_coverage schema registration.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.setup.create_agent_sheets import AGENT_SHEET_HEADERS


def test_borrow_coverage_header_registered():
    cols = AGENT_SHEET_HEADERS["borrow_coverage"]
    assert cols == [
        "CheckDate", "CheckTime", "ScannedUniverse", "WithBorrowData",
        "PctWithBorrowData", "ShortableCount", "PctShortable", "Source",
    ]
