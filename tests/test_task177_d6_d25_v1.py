"""TASK-177 — extend post_analysis outcome window to scan-anchored D25.

Tests are added task-by-task (TDD). Task 1: config window constants.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

import config
import post_analysis_collector as pac


def test_window_constants_exist_and_split():
    """CLASSIFY_DAYS (official, frozen 5) and COLLECT_DAYS_FORWARD (collection horizon 25)
    are distinct config constants, with collection >= classification."""
    assert config.CLASSIFY_DAYS == 5          # official outcome window — frozen
    assert config.COLLECT_DAYS_FORWARD == 25  # collection horizon (>= classify)
    assert config.COLLECT_DAYS_FORWARD >= config.CLASSIFY_DAYS


# ── Task 2: fetch_ohlc_for_days — full OHLC D1-D5, Close+Low only D6-D25 ──────
class _FakeProvider:
    def get_daily_bars(self, ticker, days, end_date=None):
        idx = pd.bdate_range(end="2026-04-30", periods=days)
        return pd.DataFrame(
            {"open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5}, index=idx
        )


def test_d6_d25_close_low_only_and_d1_d5_full(monkeypatch):
    monkeypatch.setattr(pac, "get_data_provider", lambda: _FakeProvider())
    trading_days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-04-01", periods=25)]
    out = pac.fetch_ohlc_for_days("TEST", trading_days)
    # D1-D5: full OHLC (classification window)
    for i in range(1, 6):
        for s in ("Open", "High", "Low", "Close"):
            assert f"D{i}_{s}" in out, f"D{i}_{s} missing (full OHLC expected for D1-D5)"
    # D6-D25: Close + Low only — NO Open/High
    for i in range(6, 26):
        assert f"D{i}_Close" in out and f"D{i}_Low" in out, f"D{i} Close/Low missing"
        assert f"D{i}_Open" not in out and f"D{i}_High" not in out, \
            f"D{i} must NOT carry Open/High (data-only window)"


# ── Task 3: collector wiring + forward-only cutoff in is_complete ─────────────
def _row(scan_date, days_present):
    """A post_analysis row with D1..days_present Close+Low filled."""
    d = {"Ticker": "T", "ScanDate": scan_date}
    for i in range(1, days_present + 1):
        d[f"D{i}_Close"] = 9.5
        d[f"D{i}_Low"] = 9.0
    return pd.Series(d)


def test_collector_uses_collect_days_forward():
    """The collector's forward horizon is the config SSoT (25), not a literal 5."""
    assert pac.DAYS_FORWARD == config.COLLECT_DAYS_FORWARD == 25


def test_legacy_row_complete_at_d5(monkeypatch):
    """forward-only: a row scanned BEFORE the cutoff is complete with D1-D5 only —
    its missing D6-D25 must NOT trigger a re-fetch (locked, untouched)."""
    monkeypatch.setattr(pac, "is_day_complete", lambda d: True)  # all days settled
    td = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-06-01", periods=25)]
    row = _row("2026-06-01", 5)   # scan BEFORE cutoff; only D1-D5 present
    assert pac.is_complete(row, td) is True


def test_new_row_incomplete_until_d25(monkeypatch):
    """A row scanned ON/AFTER the cutoff with settled D6+ but no D6-D25 values is
    NOT complete — the collector must keep collecting the D6-D25 window."""
    monkeypatch.setattr(pac, "is_day_complete", lambda d: True)  # D6+ settled
    td = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-06-13", periods=25)]
    row = _row("2026-06-13", 5)   # scan ON cutoff; D1-D5 present, D6+ missing
    assert pac.is_complete(row, td) is False


# ── Task 4: REGRESSION GUARD — classification frozen vs tempting D6-D25 ───────
def test_classification_frozen_against_tempting_d6_d25():
    """The official D1-D5 classification must be byte-identical when D6-D25 carry an
    EXTREME low that would dominate MaxDrop/TP/BestDay IF the window leaked past D5.
    If any classification field moves → D6-D25 leaked into the classifier → STOP."""
    from utils import calculate_stats, classify_trade
    scan = 10.0
    base = {
        "D1_Open": 10.0, "D1_High": 10.5, "D1_Low": 9.5, "D1_Close": 9.80,
        "D2_Open": 9.80, "D2_High": 10.0, "D2_Low": 9.2, "D2_Close": 9.40,
        "D3_Open": 9.40, "D3_High": 9.60, "D3_Low": 8.8, "D3_Close": 9.00,  # MaxDrop -12% (D3)
        "D4_Open": 9.00, "D4_High": 9.30, "D4_Low": 9.0, "D4_Close": 9.10,
        "D5_Open": 9.10, "D5_High": 9.40, "D5_Low": 9.3, "D5_Close": 9.35,
    }
    stats_before = calculate_stats(scan, dict(base))
    cls_before = classify_trade(scan, dict(base))

    tempt = dict(base)
    for i in range(6, 26):                 # D6-D25 Close+Low, -90% — must be IGNORED
        tempt[f"D{i}_Low"] = 1.0
        tempt[f"D{i}_Close"] = 1.0
    tempt["D7_Low"] = 1.0                   # explicit extreme tempters
    tempt["D15_Low"] = 1.0
    stats_after = calculate_stats(scan, tempt)
    cls_after = classify_trade(scan, tempt)

    print("\n=== classification BEFORE vs AFTER adding tempting D6-D25 (-90%) ===")
    for k in sorted(set(stats_before) | set(stats_after)):
        flag = "" if stats_before.get(k) == stats_after.get(k) else "  <-- MOVED!"
        print(f"  {k:16} before={str(stats_before.get(k)):>8}  after={str(stats_after.get(k)):>8}{flag}")
    print(f"  classify_trade   before={cls_before}  after={cls_after}"
          f"{'' if cls_before == cls_after else '  <-- MOVED!'}")

    assert stats_after == stats_before, "calculate_stats moved → D6-D25 leaked into classification"
    assert cls_after == cls_before, "classify_trade moved → D6-D25 leaked into classification"


# ── Task 5: ensure_grid_width — grows / never shrinks / no-op when wide enough ─
class _FakeWS2:
    def __init__(self, cols):
        self.col_count = cols
        self.row_count = 100
        self.resized = None

    def resize(self, rows, cols):
        self.row_count, self.col_count = rows, cols
        self.resized = (rows, cols)


def test_ensure_grid_width_grows_when_needed():
    from gsheets_sync import ensure_grid_width
    ws = _FakeWS2(cols=30)
    ensure_grid_width(ws, 80)
    assert ws.col_count == 80 and ws.resized == (100, 80)


def test_ensure_grid_width_never_shrinks():
    """col_count=120, need 80 → must STAY 120 (never truncate existing columns)."""
    from gsheets_sync import ensure_grid_width
    ws = _FakeWS2(cols=120)
    ensure_grid_width(ws, 80)
    assert ws.col_count == 120 and ws.resized is None


def test_ensure_grid_width_noop_when_equal():
    """col_count == n_cols → no redundant resize API call."""
    from gsheets_sync import ensure_grid_width
    ws = _FakeWS2(cols=80)
    ensure_grid_width(ws, 80)
    assert ws.resized is None
