"""TASK-137 — Wilder RSI/ATR canonical helpers (ta_helpers.py).

Proves: (1) helpers == direct ta (the D0 method); (2) Wilder != SMA on a trend;
(3) COMPARABILITY [RED until wiring] — the live follow-up SMA method does NOT
match the D0 Wilder method, so D1-D3 are incomparable to D0 (this is the bug);
(4) short-history -> fallback (mirrors the D0 guard).

Needs the `ta` package -> run via `uv run --with-requirements requirements.txt
--with pytest pytest`. ta is absent from the bare interpreter.
"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ta_helpers
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange


def _trend(n=40, start=10.0, step=0.5):
    """A monotonically rising close series — SMA and Wilder diverge clearly here."""
    return [start + i * step for i in range(n)]


def _sma_rsi_last(closes):
    """Replica of the LIVE follow-up RSI block (auto_scanner.py:880-886) — SMA, the bug."""
    s = pd.Series(closes)
    delta = s.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 0
    return float(100 - 100 / (1 + rs))


def _sma_atr_last(high, low, close):
    """Replica of the LIVE follow-up ATR block (auto_scanner.py:865-870) — SMA, the bug."""
    h, l, c = pd.Series(high), pd.Series(low), pd.Series(close)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(14).mean().iloc[-1])


# ── 1. helper == direct ta (the D0 canonical method) ──
def test_rsi14_wilder_matches_ta_direct():
    s = pd.Series(_trend())
    expected = float(RSIIndicator(close=s, window=14).rsi().iloc[-1])
    assert ta_helpers.rsi14_wilder(s) == pytest.approx(expected)


def test_atr14_wilder_matches_ta_direct():
    closes = _trend()
    high = [c + 0.4 for c in closes]
    low = [c - 0.4 for c in closes]
    expected = float(AverageTrueRange(
        high=pd.Series(high), low=pd.Series(low), close=pd.Series(closes), window=14
    ).average_true_range().iloc[-1])
    assert ta_helpers.atr14_wilder(high, low, closes) == pytest.approx(expected)


# ── 2. Wilder != SMA on a trend (proves the methods diverge) ──
def test_wilder_rsi_differs_from_sma_on_trend():
    s = _trend()
    assert abs(ta_helpers.rsi14_wilder(s) - _sma_rsi_last(s)) > 0.5


# ── 3. COMPARABILITY (source-level) — follow-up must route through the canonical
# Wilder helper, NOT the old SMA rolling(14).mean(). A value-level test can't reach
# the inline production block (Sheets/network), so we assert the source contract:
# RED on the pre-wiring backup (SMA present), GREEN once update_ticker_follow_up
# calls ta_helpers. This is the durable regression guard against reverting to SMA.
import re

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _followup_src():
    src = open(os.path.join(_REPO, "auto_scanner.py"), encoding="utf-8").read()
    m = re.search(r"\ndef update_ticker_follow_up.*?(?=\ndef |\Z)", src, re.S)
    assert m, "update_ticker_follow_up not found in auto_scanner.py"
    return m.group(0)


def test_followup_rsi_routed_through_wilder_helper():
    body = _followup_src()
    assert "ta_helpers.rsi14_wilder" in body, "follow-up RSI not routed through Wilder helper"
    assert "rolling(14).mean()" not in body, "SMA rolling(14).mean() still present in follow-up"


def test_followup_atr_routed_through_wilder_helper():
    body = _followup_src()
    assert "ta_helpers.atr14_wilder" in body, "follow-up ATR not routed through Wilder helper"


# ── TASK-137 pt2: typical_price_dist must route through the canonical formulas
# function (same as D0:227), not the inline (price-typical)/typical duplicate.
# Value-preserving (see test_formulas.test_vwap_dist); this guards the DRY/§10 wiring.
def test_followup_typical_price_dist_routed_through_formula():
    body = _followup_src()
    assert "calculate_typical_price_dist(price, high_today, low_today)" in body, \
        "follow-up typical_price_dist not routed through canonical formula"
    assert "(price - typical_price) / typical_price * 100" not in body, \
        "inline typical_price_dist duplicate still present in follow-up"


# ── 4. short history -> fallback (mirrors D0 len>=14 guard) ──
def test_rsi_short_history_returns_fallback():
    assert ta_helpers.rsi14_wilder([10, 11, 12], fallback=50.0) == 50.0


def test_atr_short_history_returns_fallback():
    assert ta_helpers.atr14_wilder([10, 11], [9, 10], [9.5, 10.5], fallback=1.23) == 1.23
