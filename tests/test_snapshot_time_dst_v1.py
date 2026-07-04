"""auto_scanner.is_snapshot_time must be DST-aware — the daily snapshot must
fire ~1 minute before the NYSE close, which runs in ET (observes DST) while
Peru has no DST.

NYSE close = 16:00 ET. In Peru terms (UTC-5, no DST):
  - Summer / EDT (ET=UTC-4): close = 15:00 Peru  -> snapshot window 14:55-15:05
  - Winter / EST (ET=UTC-5): close = 16:00 Peru  -> snapshot window 15:55-16:05

Current auto_scanner.is_snapshot_time hardcodes 14:55-15:05 Peru -> correct in
summer, WRONG in winter (fires an HOUR before close -> mid-session data lands in
end-of-day daily_snapshots columns). RED: the two winter-boundary cases fail.

Hermetic: monkeypatch auto_scanner.get_peru_time (frozen instant) so only the
window logic is under test. No network, no real clock. TASK-223.
"""
import datetime as dt
import importlib

import pytz

auto_scanner = importlib.import_module("auto_scanner")
PERU = pytz.timezone("America/Lima")


def _peru(y, m, d, hh, mm):
    return PERU.localize(dt.datetime(y, m, d, hh, mm))


def _freeze(monkeypatch, when):
    monkeypatch.setattr(auto_scanner, "get_peru_time", lambda: when)


# ── Summer / EDT (June) — close = 15:00 Peru; current code already correct ──
def test_summer_fires_at_1459(monkeypatch):
    _freeze(monkeypatch, _peru(2026, 6, 16, 14, 59))
    assert auto_scanner.is_snapshot_time() is True


def test_summer_silent_before_window(monkeypatch):
    _freeze(monkeypatch, _peru(2026, 6, 16, 14, 54))
    assert auto_scanner.is_snapshot_time() is False


def test_summer_silent_after_window(monkeypatch):
    _freeze(monkeypatch, _peru(2026, 6, 16, 15, 5))
    assert auto_scanner.is_snapshot_time() is False


# ── Winter / EST (January) — close = 16:00 Peru; RED on current hardcoded code ──
def test_winter_silent_at_1459(monkeypatch):
    # 14:59 Peru in winter is an HOUR before the 16:00 close -> must NOT fire
    _freeze(monkeypatch, _peru(2026, 1, 13, 14, 59))
    assert auto_scanner.is_snapshot_time() is False


def test_winter_fires_at_1559(monkeypatch):
    # 15:59 Peru in winter is ~1 min before the 16:00 close -> must fire
    _freeze(monkeypatch, _peru(2026, 1, 13, 15, 59))
    assert auto_scanner.is_snapshot_time() is True
