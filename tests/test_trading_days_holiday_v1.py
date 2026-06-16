"""TASK-130 — trading_days_after must be holiday-aware.

Bug: sheets_manager.trading_days_after counts weekdays only (d.weekday() < 5),
so exchange-holiday slots (Good Friday 2026-04-03, Memorial Day 2026-05-25,
Independence Day observed 2026-07-03) are returned as trading days and the
matching post_analysis rows stay PENDING forever.

Fix under test: delegate the per-day check to utils.is_trading_day (the single
holiday source, §10). Tests INJECT a fake is_trading_day with a known holiday
set — hermetic, independent of whether pandas_market_calendars works locally
(on local Python it can fall back to weekday-only).

Weekday facts used (verified): 2026-04-02 Thu, 04-03 Fri, 04-06 Mon;
2026-05-22 Fri, 05-25 Mon, 05-26 Tue; 2026-07-01 Wed, 07-02 Thu, 07-03 Fri,
07-06 Mon; 2026-06-05 Fri, 06-08 Mon, 06-09 Tue.
"""
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sheets_manager

HOLIDAYS_2026 = {"2026-04-03", "2026-05-25", "2026-07-03"}


def _fake_is_trading_day(d):
    """NASDAQ-like: weekday AND not in the known 2026 holiday set."""
    return d.weekday() < 5 and d.strftime("%Y-%m-%d") not in HOLIDAYS_2026


def _weekday_only_is_trading_day(d):
    """mcal-unavailable fallback behavior of utils.is_trading_day."""
    return d.weekday() < 5


def test_good_friday_skipped():
    with patch("utils.is_trading_day", side_effect=_fake_is_trading_day):
        days = sheets_manager.trading_days_after("2026-04-02", 3)
    # 04-03 is Good Friday, 04-04/05 weekend -> Mon/Tue/Wed
    assert days == ["2026-04-06", "2026-04-07", "2026-04-08"]


def test_memorial_day_skipped():
    with patch("utils.is_trading_day", side_effect=_fake_is_trading_day):
        days = sheets_manager.trading_days_after("2026-05-22", 2)
    # 05-23/24 weekend, 05-25 Memorial Day -> Tue/Wed
    assert days == ["2026-05-26", "2026-05-27"]


def test_independence_day_observed_skipped():
    with patch("utils.is_trading_day", side_effect=_fake_is_trading_day):
        days = sheets_manager.trading_days_after("2026-07-01", 2)
    # 07-02 Thu trades, 07-03 observed holiday, 07-04/05 weekend -> Mon
    assert days == ["2026-07-02", "2026-07-06"]


def test_regular_weekend_still_skipped():
    with patch("utils.is_trading_day", side_effect=_fake_is_trading_day):
        days = sheets_manager.trading_days_after("2026-06-05", 2)
    # Fri start: Sat/Sun skipped exactly as before the fix
    assert days == ["2026-06-08", "2026-06-09"]


def test_fallback_weekday_only_keeps_weekend_skip():
    """If mcal is unavailable, is_trading_day degrades to weekday-only —
    the function must still skip weekends (graceful degradation, no crash)."""
    with patch("utils.is_trading_day", side_effect=_weekday_only_is_trading_day):
        days = sheets_manager.trading_days_after("2026-06-05", 2)
    assert days == ["2026-06-08", "2026-06-09"]


# ── TASK-135: orchestrator.is_market_hours + utils.is_day_complete must use the
# same holiday source (utils.is_trading_day), not weekday-only. ──
def test_is_market_hours_skips_weekday_holiday():
    from datetime import datetime
    from agent.orchestrator import is_market_hours, PERU_TZ
    with patch("utils.is_trading_day", side_effect=_fake_is_trading_day):
        # Fri 2026-07-03 (Independence Day observed): weekday & in-hours but a holiday
        holiday = PERU_TZ.localize(datetime(2026, 7, 3, 10, 30))
        assert is_market_hours(holiday) is False
        # control: Mon 2026-07-06 in-hours -> True (normal trading day)
        normal = PERU_TZ.localize(datetime(2026, 7, 6, 10, 30))
        assert is_market_hours(normal) is True


def test_is_day_complete_skips_past_holiday():
    import utils
    with patch("utils.is_trading_day", side_effect=_fake_is_trading_day):
        # Memorial Day Mon 2026-05-25 (past weekday holiday) -> never complete
        assert utils.is_day_complete("2026-05-25") is False
        # control: Tue 2026-05-26 (past trading day) -> complete
        assert utils.is_day_complete("2026-05-26") is True
