"""TASK-206 — extend get_fundamentals with 8 structural/fundamental fields.

RED: current provider returns 7 keys. We require 8 NEW normalized keys,
present in BOTH the success dict AND the empty/exception fallback dict
(the provider builds two dicts in lockstep — both must carry the new keys).
Hermetic: inject a fake yf SDK via prov._yf, no network.
"""
import importlib

mod = importlib.import_module("providers.yfinance_provider")
Provider = mod.YFinanceFundamentalsProvider

NEW_KEYS = ["short_float", "days_to_cover", "inst_own", "insider_own",
            "beta", "roe", "profit_margin", "pe"]

FAKE_INFO = {
    "marketCap": 1_000_000, "sharesOutstanding": 500_000,
    "floatShares": 400_000, "averageVolume": 100_000,
    "sector": "Technology", "industry": "Software",
    "shortPercentOfFloat": 0.21, "shortRatio": 4.5,
    "heldPercentInstitutions": 0.05, "heldPercentInsiders": 0.34,
    "beta": 4.1, "returnOnEquity": -0.12,
    "profitMargins": -0.30, "trailingPE": None,
}


class _FakeTicker:
    def __init__(self, info): self.info = info


class _FakeYF:
    def __init__(self, info): self._info = info
    def Ticker(self, _t): return _FakeTicker(self._info)


class _ExplodingYF:
    def Ticker(self, _t): raise RuntimeError("simulated yfinance failure")


def test_get_fundamentals_exposes_new_fields():
    prov = Provider()
    prov._yf = _FakeYF(FAKE_INFO)
    out = prov.get_fundamentals("FAKE")
    for k in NEW_KEYS:
        assert k in out, f"new field missing from success dict: {k}"
    # spot-check a couple of values are mapped, not just present
    assert out["short_float"] == 0.21
    assert out["days_to_cover"] == 4.5
    assert out["insider_own"] == 0.34


def test_empty_fallback_carries_new_fields():
    prov = Provider()
    prov._yf = _ExplodingYF()
    out = prov.get_fundamentals("FAKE")
    for k in NEW_KEYS:
        assert k in out, f"new field missing from fallback dict: {k}"
        assert out[k] is None, f"fallback {k} should be None, got {out[k]}"


def test_get_fundamentals_carries_raw_info():
    """TASK-206 (beta): raw key must carry the FULL .info dict for the JSON catch-all."""
    prov = Provider()
    prov._yf = _FakeYF(FAKE_INFO)
    out = prov.get_fundamentals("FAKE")
    assert "raw" in out, "raw (full .info) missing from success dict"
    assert isinstance(out["raw"], dict)
    # raw must contain fields we did NOT promote to columns (the whole point of catch-all)
    assert out["raw"].get("shortPercentOfFloat") == 0.21
    assert out["raw"].get("sector") == "Technology"


def test_empty_fallback_raw_is_none():
    prov = Provider()
    prov._yf = _ExplodingYF()
    out = prov.get_fundamentals("FAKE")
    assert "raw" in out, "raw missing from fallback dict"
    assert out["raw"] is None
