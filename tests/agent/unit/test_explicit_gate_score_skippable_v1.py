"""TASK-128 / Option-B shadow-first (resolves 141+174) — Step 1.

The Score gate (Filter 1, decision_logic.py:277-278 `d.score < AGENT_MIN_SCORE`) is the
ONLY Score-based entry filter. Option B = the SAME filter chain minus Filter 1. To run that
explicit-only gate in SHADOW without duplicating the chain (§10), `_check_filters` gains an
`include_score_gate: bool = True` knob: default True is byte-identical to today; False skips
ONLY the Score gate, leaving filters 2-11 (the proven explicit gates) intact.

Pure/deterministic: builds a Decision directly, no live Sheets.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.trader.decision_logic import _check_filters, Decision


def _passes_all_but_score():
    """A Decision + signal + quality that clears every filter EXCEPT Score (score=30<50)."""
    d = Decision()
    d.ticker = "TEST"
    d.score = 30.0          # < AGENT_MIN_SCORE(50) → Filter 1 blocks when ON
    d.mxv = -300.0          # not > -100 → passes Filter 2
    d.run_up = 45.0         # >= 0 (Filter 3) and < 50 (ROCKET safe)
    d.volume = 5_000_000    # >= 100k (Filter 4)
    d.price = 7.0           # >= $3 (Filter 4b)
    d.rsi = 75.0            # not > 88 → not toxic (Filter 4d)
    d.price_vs_sma20 = 150.0
    d.market_cap = 50_000_000  # in [5M, 2B] (Filter 5)
    d.existing_position = False
    # cold_start / reentry / buying_power left None → those filters are skipped by their guards
    signal = {"price_to_high": -50.0}  # ROCKET pth guard safe
    quality = {"is_trustworthy": True, "quality_score": 0.9, "flags": []}
    return d, signal, quality


def test_check_filters_accepts_include_score_gate_param():
    """The new knob exists; with the Score gate OFF a low score no longer blocks."""
    d, sig, q = _passes_all_but_score()
    assert _check_filters(d, sig, q, include_score_gate=False) is None


def test_score_gate_on_blocks_low_score():
    d, sig, q = _passes_all_but_score()
    reason = _check_filters(d, sig, q, include_score_gate=True)
    assert reason is not None and reason.startswith("SCORE_TOO_LOW")


def test_default_keeps_score_gate_on_byte_identical():
    """Default arg = current behavior: low score still blocks with SCORE_TOO_LOW."""
    d, sig, q = _passes_all_but_score()
    reason = _check_filters(d, sig, q)
    assert reason is not None and reason.startswith("SCORE_TOO_LOW")


def test_score_gate_off_skips_only_score_not_other_filters():
    """With the Score gate OFF a *non*-score filter still fires (only Filter 1 is skipped)."""
    d, sig, q = _passes_all_but_score()
    d.volume = 50  # break Filter 4
    reason = _check_filters(d, sig, q, include_score_gate=False)
    assert reason is not None and reason.startswith("VOLUME_TOO_LOW")


def test_high_score_passes_regardless_of_gate():
    d, sig, q = _passes_all_but_score()
    d.score = 80.0  # above threshold either way
    assert _check_filters(d, sig, q, include_score_gate=True) is None
    assert _check_filters(d, sig, q, include_score_gate=False) is None
