"""ta_helpers.py — canonical Wilder RSI/ATR wrappers (TASK-137).

Single source of truth for 14-period Wilder RSI / ATR, wrapping the `ta`
library exactly as the D0 scan path does (auto_scanner.py:183 / :190). Lives in
its own module because formulas.py / utils.py are intentionally pandas-free
(scalar-only, see PK v3.25); these helpers are pandas+ta based.

Mirrors the D0 guards: window=14, len>=window required, NaN/empty -> fallback.
A pure function cannot "keep the prior value" the way the inline D0 block does,
so the caller passes an explicit `fallback` (D0-RSI keeps prior; follow-up uses
50.0; D0-ATR uses high-low). Routing ticker_follow_up through these makes its
D1-D3 RSI/ATR methodologically identical to D0 (Wilder, not SMA).
"""
import pandas as pd
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

WINDOW = 14


def rsi14_wilder(close, window=WINDOW, fallback=None):
    """14-period Wilder RSI of the last bar. Returns float, or `fallback` if the
    series is too short / non-numeric / the last value is NaN. Same method as
    the D0 path (ta.RSIIndicator), unlike the old SMA rolling(14).mean()."""
    s = pd.to_numeric(pd.Series(close), errors="coerce").dropna()
    if len(s) < window:
        return fallback
    vals = RSIIndicator(close=s, window=window).rsi()
    if vals.empty or pd.isna(vals.iloc[-1]):
        return fallback
    return float(vals.iloc[-1])


def atr14_wilder(high, low, close, window=WINDOW, fallback=None):
    """14-period Wilder ATR of the last bar. Returns float, or `fallback` if the
    series is too short / the last value is NaN. Same method as the D0 path
    (ta.AverageTrueRange), unlike the old SMA TR rolling(14).mean()."""
    h = pd.to_numeric(pd.Series(high), errors="coerce")
    l = pd.to_numeric(pd.Series(low), errors="coerce")
    c = pd.to_numeric(pd.Series(close), errors="coerce")
    if len(c.dropna()) < window:
        return fallback
    vals = AverageTrueRange(high=h, low=l, close=c, window=window).average_true_range()
    if vals.empty or pd.isna(vals.iloc[-1]):
        return fallback
    return float(vals.iloc[-1])
