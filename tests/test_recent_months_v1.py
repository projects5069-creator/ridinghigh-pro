"""TASK-124 — recent_months(): month-window selection for the daily workflow.

The daily post_analysis workflow will call backfill_ohlc_v2 --recent 2 so the
cross-month leak is healed permanently without the default all-months scope
growing forever. recent_months is pure: n months descending from the current
one (Peru today by default), intersected with sheets_config month keys.
"""
import importlib.util
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)
_spec = importlib.util.spec_from_file_location(
    "backfill_ohlc_v2", os.path.join(_REPO, "backfill_ohlc_v2.py"))
b2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b2)

CFG = {"2025-12", "2026-01", "2026-04", "2026-05", "2026-06", "2026-07"}


def test_recent_two_months():
    assert b2.recent_months(2, today="2026-06-10", config_months=CFG) == \
        ["2026-06", "2026-05"]


def test_year_boundary():
    assert b2.recent_months(2, today="2026-01-15", config_months=CFG) == \
        ["2026-01", "2025-12"]


def test_n_one_is_current_only():
    assert b2.recent_months(1, today="2026-06-10", config_months=CFG) == \
        ["2026-06"]


def test_month_missing_from_config_is_filtered():
    cfg = {"2026-06", "2026-04"}  # 2026-05 absent
    assert b2.recent_months(3, today="2026-06-10", config_months=cfg) == \
        ["2026-06", "2026-04"]
