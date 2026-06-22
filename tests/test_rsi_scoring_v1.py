"""
TASK-188 — RSI-semantics regression guard (characterization test).

Locks the LIVE RSI scoring behavior of formulas.calculate_score:
it is **overbought-only graded**, NOT a bell curve.

    rsi >= 90 -> full 10 pts
    rsi >= 85 -> 7 pts (0.7 * weight)
    rsi >= 80 -> 4 pts (0.4 * weight)
    rsi <  80 -> 0 pts

The PK §18/§36 "bell curve centered 50-70" claim was drift (TASK-188);
these tests prove the bell-curve peak band (50-70) contributes ZERO,
and guard the behavior against the dead-config removal in the same task.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCORE_WEIGHTS_V2
from formulas import calculate_score


def _rsi_only_metrics(rsi):
    """Metrics dict where ONLY rsi can contribute (all others zeroed out)."""
    return {
        "mxv": 0,                  # needs < 0 to score -> 0
        "run_up": 0,               # needs > 0 -> 0
        "atrx": 0,                 # min(0/cap,1)*w -> 0
        "rsi": rsi,
        "typical_price_dist": 0,   # needs > 0 -> 0
        "change": 0,               # needs > 0 -> 0
        "rel_vol": 0,              # min(0/cap,1)*w -> 0
    }


def _rsi_contribution(rsi):
    return calculate_score(_rsi_only_metrics(rsi))


W = SCORE_WEIGHTS_V2["RSI"]  # 10


def test_rsi_90_plus_full_weight():
    assert _rsi_contribution(90) == round(W, 2)
    assert _rsi_contribution(95) == round(W, 2)


def test_rsi_85_to_89_is_07_weight():
    assert _rsi_contribution(85) == round(W * 0.7, 2)
    assert _rsi_contribution(89) == round(W * 0.7, 2)


def test_rsi_80_to_84_is_04_weight():
    assert _rsi_contribution(80) == round(W * 0.4, 2)
    assert _rsi_contribution(84) == round(W * 0.4, 2)


def test_rsi_below_80_zero():
    assert _rsi_contribution(79) == 0.0


def test_bell_curve_peak_band_contributes_zero():
    # If this were a bell curve peaking at 50-70, these would score high.
    # Overbought-only => zero. This is the core TASK-188 assertion.
    assert _rsi_contribution(50) == 0.0
    assert _rsi_contribution(60) == 0.0
    assert _rsi_contribution(70) == 0.0
