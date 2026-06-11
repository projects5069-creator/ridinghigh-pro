"""TASK-140 collector step — net-PnL folded into calculate_stats (shared SSoT).

Written test-first (RED) before utils.calculate_stats is changed. calculate_stats
gains 4 keys computed from classify_trade(scan,ohlc) -> (cls,day) + calculate_net_pnl:
    NetPnL_SlipOnly, NetPnL_Borrow50, NetPnL_Borrow200, NetPnL_Borrow500

scan=100 → tp=90, sl=110, slip=0.01.
  WIN  gross = (0.99 - 0.909)/0.99 =  0.0818182
  LOSS gross = (0.99 - 1.111)/0.99 = -0.122222
  borrow cost = rate * resolution_day / 365   (day=1 in the WIN/LOSS fixtures below)
Existing 8 keys must remain (no schema break).
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import calculate_stats

NET_KEYS = ["NetPnL_SlipOnly", "NetPnL_Borrow50", "NetPnL_Borrow200", "NetPnL_Borrow500"]
EXISTING_KEYS = ["MaxDrop%", "BestDay", "TP10_Hit", "TP15_Hit", "TP20_Hit",
                 "D1_Gap%", "SL_Hit_D5", "IntraDay_SL"]
NEUTRAL = (95.0, 105.0)   # never hits TP(90) or SL(110)
WIN_GROSS = 0.0818182
LOSS_GROSS = -0.122222


def _ohlc(*days):
    d = {}
    for i, (lo, hi) in enumerate(days, start=1):
        d[f"D{i}_Low"] = lo
        d[f"D{i}_High"] = hi
    return d


# ───────────────── WIN (resolves D1, day=1) ─────────────────

def test_win_net_pnl_keys_present_and_correct():
    """WIN on D1 → 4 NetPnL keys with slip-only gross minus borrow*day/365."""
    ohlc = _ohlc((89.0, 105.0), NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL)
    s = calculate_stats(100.0, ohlc)
    assert s["NetPnL_SlipOnly"] == pytest.approx(WIN_GROSS, rel=1e-3)
    assert s["NetPnL_Borrow50"] == pytest.approx(WIN_GROSS - 0.50 * 1 / 365, rel=1e-3)
    assert s["NetPnL_Borrow200"] == pytest.approx(WIN_GROSS - 2.00 * 1 / 365, rel=1e-3)
    assert s["NetPnL_Borrow500"] == pytest.approx(WIN_GROSS - 5.00 * 1 / 365, rel=1e-3)


# ───────────────── LOSS (resolves D1, day=1) ─────────────────

def test_loss_net_pnl_negative():
    """LOSS on D1 → 4 NetPnL keys negative; borrow makes them more negative."""
    ohlc = _ohlc((95.0, 111.0), NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL)
    s = calculate_stats(100.0, ohlc)
    assert s["NetPnL_SlipOnly"] == pytest.approx(LOSS_GROSS, rel=1e-3)
    assert s["NetPnL_Borrow500"] == pytest.approx(LOSS_GROSS - 5.00 * 1 / 365, rel=1e-3)
    assert all(s[k] < 0 for k in NET_KEYS)


# ───────────────── non-WIN/LOSS → NULL ─────────────────

def test_pending_incomplete_ohlc_net_pnl_none():
    """Fewer than 5 days → classify PENDING → all 4 NetPnL = None (but stats still computed)."""
    s = calculate_stats(100.0, _ohlc(NEUTRAL, NEUTRAL))   # only D1-D2
    assert all(s[k] is None for k in NET_KEYS)


def test_whipsaw_net_pnl_none():
    """WHIPSAW (D1 hits both) → all 4 NetPnL = None."""
    s = calculate_stats(100.0, _ohlc((89.0, 111.0), NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL))
    assert all(s[k] is None for k in NET_KEYS)


def test_no_touch_net_pnl_none():
    """NO_TOUCH (5 neutral days) → all 4 NetPnL = None."""
    s = calculate_stats(100.0, _ohlc(NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL))
    assert all(s[k] is None for k in NET_KEYS)


def test_empty_ohlc_net_pnl_none():
    """Empty OHLC (early-return branch) → 4 NetPnL = None."""
    s = calculate_stats(100.0, {})
    assert all(s[k] is None for k in NET_KEYS)


# ───────────────── regression guard: existing schema intact ─────────────────

def test_existing_stats_keys_preserved():
    """All 8 pre-existing keys must still be present (both branches)."""
    full = calculate_stats(100.0, _ohlc((89.0, 105.0), NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL))
    empty = calculate_stats(100.0, {})
    for k in EXISTING_KEYS:
        assert k in full, f"missing {k} in full-stats"
        assert k in empty, f"missing {k} in empty-stats"
