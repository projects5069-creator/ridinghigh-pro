"""TASK-128 / Option-B shadow-first (resolves 141+174) — Step 2: shadow observer.

The observer measures, forward, what the explicit-only gate (Score decoupled) would
decide — WITHOUT touching the live action. It mirrors the Sentinel shadow pattern
(config.SENTINEL_MODE): EXPLICIT_GATE_MODE ∈ shadow|active|off, default shadow.
The only divergence Score-removal creates: a signal the live logic SKIPs as
SCORE_TOO_LOW that the explicit proven-filter gate (filters 2-11) would ALLOW.

Pure/deterministic: constructs Decision directly, no live Sheets.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.trader import decision_logic
from agent.trader.decision_logic import _observe_explicit_gate, evaluate_signal, Decision


def _passes_all_but_score():
    """Decision + signal + quality that clears every explicit filter; score=30 (<50)."""
    d = Decision()
    d.ticker = "TEST"
    d.score = 30.0
    d.mxv = -300.0
    d.run_up = 45.0
    d.volume = 5_000_000
    d.price = 7.0
    d.rsi = 75.0
    d.price_vs_sma20 = 150.0
    d.market_cap = 50_000_000
    d.existing_position = False
    signal = {"price_to_high": -50.0}
    quality = {"is_trustworthy": True, "quality_score": 0.9, "flags": []}
    return d, signal, quality


# ── observer unit ──────────────────────────────────────────────────────────

def test_shadow_records_score_divergence_would_allow():
    d, sig, q = _passes_all_but_score()
    _observe_explicit_gate(d, sig, q, "SCORE_TOO_LOW: 30.00 < 50")
    assert d.shadow_explicit_skip_reason is None      # explicit gate would ALLOW
    assert d.shadow_explicit_divergence is True
    assert d.action == ""                             # observer NEVER sets the live action


def test_no_divergence_when_explicit_also_blocks():
    d, sig, q = _passes_all_but_score()
    d.volume = 50                                     # explicit gate also blocks (volume)
    _observe_explicit_gate(d, sig, q, "SCORE_TOO_LOW: 30.00 < 50")
    assert d.shadow_explicit_skip_reason.startswith("VOLUME_TOO_LOW")
    assert d.shadow_explicit_divergence is False


def test_divergence_requires_score_block_not_other_skip():
    d, sig, q = _passes_all_but_score()
    d.volume = 50                                     # live blocked on volume, not score
    _observe_explicit_gate(d, sig, q, "VOLUME_TOO_LOW: 50 < 100000")
    assert d.shadow_explicit_divergence is False


def test_mode_off_is_full_noop(monkeypatch):
    monkeypatch.setattr(decision_logic._config, "EXPLICIT_GATE_MODE", "off")
    d, sig, q = _passes_all_but_score()
    _observe_explicit_gate(d, sig, q, "SCORE_TOO_LOW: 30.00 < 50")
    assert d.shadow_explicit_skip_reason is None      # not even computed
    assert d.shadow_explicit_divergence is False


# ── integration via evaluate_signal: live action is never altered ───────────

def _enter_signal():
    return {
        "ticker": "TEST", "price": 7.0, "volume": 5_000_000, "market_cap": 50_000_000,
        "open": 6.3, "high": 7.35, "low": 5.95, "mxv": -500.0, "run_up": 35.0,
        "atrx": 2.5, "rsi": 75.0, "rel_vol": 8.0, "change": 25.0, "typical_price_dist": 0.05,
    }


def test_evaluate_signal_enter_unchanged_and_observed():
    d = evaluate_signal(_enter_signal())
    assert d.action == "ENTER"                        # live ENTER preserved
    assert d.shadow_explicit_divergence is False      # live didn't score-block → no divergence


def test_evaluate_signal_skip_action_never_changed_by_shadow():
    sig = _enter_signal()
    sig["volume"] = 50                                # SKIP on volume
    d = evaluate_signal(sig)
    assert d.action == "SKIP"                         # shadow observer must not flip this
    assert d.skip_reason.startswith("VOLUME_TOO_LOW")
