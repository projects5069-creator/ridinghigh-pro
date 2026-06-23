"""TASK-172 — borrow_coverage was in AGENT_SHEET_HEADERS but missing from
AGENT_SHEET_NAMES, so create_agent_sheets never created/registered the tab and
collect_borrow_coverage always returned None on live runs (AC#3 live-verify
exposed this 2026-06-22). These tests lock the fix + guard against future gaps.

monthly_summary is a DELIBERATE exception (per-year global, not month-rotation —
see test_monthly_not_yet_in_rotation), so the invariant excludes it.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

cs = importlib.import_module("agent.setup.create_agent_sheets")

# HEADERS keys that are intentionally NOT month-rotation tabs:
KNOWN_GLOBAL_EXCEPTIONS = {"monthly_summary"}


def test_borrow_coverage_in_names():
    assert "borrow_coverage" in cs.AGENT_SHEET_NAMES


def test_no_header_orphans_outside_known_globals():
    """Every AGENT_SHEET_HEADERS key must be in AGENT_SHEET_NAMES (so it gets
    created + registered), except known per-year globals. Catches future
    HEADERS-without-NAMES wiring gaps like the borrow_coverage one."""
    orphan = set(cs.AGENT_SHEET_HEADERS) - set(cs.AGENT_SHEET_NAMES) - KNOWN_GLOBAL_EXCEPTIONS
    assert orphan == set(), f"HEADERS keys never created (missing from NAMES): {sorted(orphan)}"
