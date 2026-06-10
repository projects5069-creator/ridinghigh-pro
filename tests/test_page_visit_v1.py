"""TASK-43 — page-visit counter (pure helper in dashboard.py).

Only the pure dict-counter is unit-tested; the Streamlit wiring (session_state
+ [PAGE_VISIT] print to the Streamlit Cloud log) is manual-verification per
PK §33. Importing dashboard requires streamlit (requirements.txt:1).
"""
import os
import sys

import pytest

pytest.importorskip("streamlit")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashboard


def test_first_visit_counts_one():
    visits = {}
    assert dashboard._record_page_visit(visits, "🏠 Home") == 1
    assert visits == {"🏠 Home": 1}


def test_second_visit_increments():
    visits = {"🏠 Home": 1}
    assert dashboard._record_page_visit(visits, "🏠 Home") == 2


def test_pages_have_separate_counters():
    visits = {}
    dashboard._record_page_visit(visits, "🏠 Home")
    dashboard._record_page_visit(visits, "💼 Portfolio Tracker")
    dashboard._record_page_visit(visits, "💼 Portfolio Tracker")
    assert visits == {"🏠 Home": 1, "💼 Portfolio Tracker": 2}


def test_empty_dict_does_not_crash():
    assert dashboard._record_page_visit({}, "🧠 Score Brain") == 1
