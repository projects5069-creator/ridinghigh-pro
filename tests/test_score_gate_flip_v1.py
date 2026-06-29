"""TASK-194 Stage-1 — the live Score gate must honor EXPLICIT_GATE_MODE.

RED: today decision_logic.py:295 hardcodes `_check_filters(..., include_score_gate=True)`,
so a low-Score signal is SKIP=SCORE_TOO_LOW regardless of EXPLICIT_GATE_MODE. After GREEN,
"active" must drop Filter 1 and let the explicit filters 2-11 decide.

Runs through evaluate_signal (the LIVE path), NOT _check_filters directly — so it catches
the line-295 wiring (a direct _check_filters test would pass on the existing seam and miss it).

Hermetic: score + quality are monkeypatched so only the gate behavior is under test;
check_tradability self-mocks (broker=None) so the ENTER path makes no network call.
"""
import importlib

dl = importlib.import_module("agent.trader.decision_logic")

_ACCT = {
    "existing_positions": [],
    "buying_power": 100_000.0,
    "cold_start_concurrent_used": 0,
    "cold_start_daily_used": 0,
}


def _signal(**over):
    """A signal that passes filters 2-11 (mxv<=-100, runup>=0, vol>=100k, price>=$3,
    mcap in range, not toxic, not rocket) — only Score (mocked to 40 < 50) can block it."""
    s = {
        "ticker": "TESTX", "price": 5.0, "volume": 500_000, "market_cap": 10_000_000,
        "mxv": -150.0, "run_up": 5.0, "atrx": 2.0, "rsi": 70.0, "rel_vol": 3.0,
        "change": 10.0, "typical_price_dist": 1.0, "price_vs_sma20": 100.0,
        "open": 5.0, "high": 5.2, "low": 4.8,
    }
    s.update(over)
    return s


def _patch_common(mp):
    # Deterministic low Score (< AGENT_MIN_SCORE=50) — isolates the gate from the formula.
    mp.setattr(dl, "calculate_agent_score", lambda m: 40.0)
    # Quality always trustworthy so Filter 6 never confounds the ENTER assertion.
    mp.setattr(dl, "validate_quality",
               lambda m: {"is_trustworthy": True, "quality_score": 1.0, "flags": []})


def test_shadow_mode_score_still_gates(monkeypatch):
    """shadow (current live): Score blocks the low-Score signal — byte-identical to today."""
    _patch_common(monkeypatch)
    monkeypatch.setattr(dl._config, "EXPLICIT_GATE_MODE", "shadow")
    d = dl.evaluate_signal(_signal(), _ACCT)
    assert d.action == "SKIP"
    assert (d.skip_reason or "").startswith("SCORE_TOO_LOW"), d.skip_reason


def test_active_mode_drops_score_gate_enters(monkeypatch):
    """active: Filter 1 dropped, explicit filters 2-11 pass -> ENTER. (RED today.)"""
    _patch_common(monkeypatch)
    monkeypatch.setattr(dl._config, "EXPLICIT_GATE_MODE", "active")
    d = dl.evaluate_signal(_signal(), _ACCT)
    assert d.action == "ENTER", f"active should drop Score gate; got {d.action} / {d.skip_reason}"


def test_active_mode_does_not_open_other_gates(monkeypatch):
    """active must drop ONLY Filter 1 — a sub-$3 price still fails PRICE_TOO_LOW."""
    _patch_common(monkeypatch)
    monkeypatch.setattr(dl._config, "EXPLICIT_GATE_MODE", "active")
    d = dl.evaluate_signal(_signal(price=2.0), _ACCT)
    assert d.action == "SKIP"
    assert (d.skip_reason or "").startswith("PRICE_TOO_LOW"), \
        f"flip must not bypass non-Score filters; got {d.skip_reason}"
