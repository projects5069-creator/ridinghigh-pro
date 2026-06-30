"""is_market_hours must be DST-aware — NYSE runs in ET (DST), Peru has no DST.

NYSE is 09:30-16:00 ET. In Peru terms (UTC-5, no DST):
  - Summer / EDT (ET=UTC-4): 08:30-15:00 Peru
  - Winter / EST (ET=UTC-5): 09:30-16:00 Peru

Current utils.is_market_hours hardcodes 08:30-15:00 Peru -> correct in summer, WRONG in
winter (opens an hour early, closes an hour early). RED: the two winter-boundary cases fail.

Hermetic: monkeypatch utils.get_peru_time (frozen instant) + utils.is_trading_day (always
a trading day), so only the open/close window is under test. No network, no real clock.
"""
import datetime as dt
import importlib

import pytz

utils = importlib.import_module("utils")
PERU = pytz.timezone("America/Lima")


def _peru(y, m, d, hh, mm):
    return PERU.localize(dt.datetime(y, m, d, hh, mm))


def _freeze(monkeypatch, when):
    monkeypatch.setattr(utils, "get_peru_time", lambda: when)
    monkeypatch.setattr(utils, "is_trading_day", lambda _d=None: True)


# ── Summer / EDT (June) — current code already correct: anchors ──
def test_summer_open_at_0830(monkeypatch):
    _freeze(monkeypatch, _peru(2026, 6, 16, 8, 30))
    assert utils.is_market_hours() is True


def test_summer_closed_before_0830(monkeypatch):
    _freeze(monkeypatch, _peru(2026, 6, 16, 8, 29))
    assert utils.is_market_hours() is False


def test_summer_open_at_1459(monkeypatch):
    _freeze(monkeypatch, _peru(2026, 6, 16, 14, 59))
    assert utils.is_market_hours() is True


# ── Winter / EST (January) — market is 09:30-16:00 Peru: RED on current code ──
def test_winter_closed_at_0830(monkeypatch):
    # 08:30 Peru in winter is BEFORE the 09:30 open -> must be CLOSED
    _freeze(monkeypatch, _peru(2026, 1, 13, 8, 30))
    assert utils.is_market_hours() is False


def test_winter_open_at_1559(monkeypatch):
    # 15:59 Peru in winter is BEFORE the 16:00 close -> must be OPEN
    _freeze(monkeypatch, _peru(2026, 1, 13, 15, 59))
    assert utils.is_market_hours() is True
