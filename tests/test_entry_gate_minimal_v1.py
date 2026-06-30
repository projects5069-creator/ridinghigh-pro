"""ENTRY_GATE_MINIMAL — disable 6 universe/protective filters via one reversible flag.

Disabled when ENTRY_GATE_MINIMAL=True: F3 RunUp, F4 Volume, F4c Blacklist, F4d Toxic,
F5 MarketCap, F11 ROCKET. Kept ON: F2 MxV, F4b Price, F6 Quality, F7 Existing,
F8 ColdStart, F9 Reentry, F10 Buying.

RED: the flag is not read yet, so the 6 filters still block -> test_minimal_skips_six_filters
fails (signal SKIPs instead of ENTER). The "kept" tests pass already (those filters are
always active), and the default test passes (filters active when flag off).

Hermetic: evaluate_signal path; score+quality monkeypatched so only the gate set is under
test; check_tradability self-mocks (broker=None) -> no network. (F3 and F11 conflict in one
signal — F3 needs run_up<0, F11 needs run_up high — so (1) exercises 5 of the 6 disabled.)
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
    s = {
        "ticker": "TESTX", "price": 5.0, "volume": 500_000, "market_cap": 10_000_000,
        "mxv": -150.0, "run_up": 5.0, "atrx": 2.0, "rsi": 70.0, "rel_vol": 3.0,
        "change": 10.0, "typical_price_dist": 1.0, "price_vs_sma20": 100.0,
        "price_to_high": 0.0, "open": 5.0, "high": 5.2, "low": 4.8,
    }
    s.update(over)
    return s


def _patch(mp):
    mp.setattr(dl, "calculate_agent_score", lambda m: 80.0)   # Score never blocks (mode-independent)
    mp.setattr(dl, "validate_quality",
               lambda m: {"is_trustworthy": True, "quality_score": 1.0, "flags": []})


def _fails_disabled():
    # Passes the KEPT filters (mxv<=-100, price>=3, quality ok), fails the DISABLED ones:
    # F4 volume<100k, F5 market_cap<5M, F4d toxic (rsi>88 AND sma>250), F11 rocket (run_up & pth high).
    # F3 not exercised here (run_up high passes it; it conflicts with F11 in one signal).
    return _signal(volume=50_000, market_cap=1_000_000, rsi=95.0,
                   price_vs_sma20=300.0, run_up=999.0, price_to_high=999.0)


def test_minimal_skips_six_filters(monkeypatch):
    _patch(monkeypatch)
    monkeypatch.setattr(dl._config, "ENTRY_GATE_MINIMAL", True, raising=False)
    d = dl.evaluate_signal(_fails_disabled(), _ACCT)
    assert d.action == "ENTER", \
        f"minimal must skip the 6 universe/protective filters; got {d.action} / {d.skip_reason}"


def test_default_keeps_six_filters(monkeypatch):
    _patch(monkeypatch)
    monkeypatch.setattr(dl._config, "ENTRY_GATE_MINIMAL", False, raising=False)
    d = dl.evaluate_signal(_fails_disabled(), _ACCT)
    assert d.action == "SKIP"
    assert any(d.skip_reason.startswith(p) for p in
               ("RUNUP", "VOLUME", "MARKET_CAP", "TOXIC", "ROCKET", "BLACKLIST")), d.skip_reason


def test_minimal_keeps_quality_mxv_price(monkeypatch):
    _patch(monkeypatch)
    monkeypatch.setattr(dl._config, "ENTRY_GATE_MINIMAL", True, raising=False)
    # F2 MxV kept:
    d1 = dl.evaluate_signal(_signal(mxv=50.0), _ACCT)
    assert d1.action == "SKIP" and d1.skip_reason.startswith("MXV"), d1.skip_reason
    # F4b Price kept:
    d2 = dl.evaluate_signal(_signal(price=2.0), _ACCT)
    assert d2.action == "SKIP" and d2.skip_reason.startswith("PRICE"), d2.skip_reason
    # F6 Quality kept (override to untrustworthy):
    monkeypatch.setattr(dl, "validate_quality",
                        lambda m: {"is_trustworthy": False, "quality_score": 0.0, "flags": ["bad"]})
    d3 = dl.evaluate_signal(_signal(), _ACCT)
    assert d3.action == "SKIP" and d3.skip_reason.startswith("QUALITY"), d3.skip_reason
