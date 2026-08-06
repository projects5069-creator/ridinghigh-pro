"""
tests/agent/unit/test_sma20_batch_v1.py
───────────────────────────────────────
TASK-259 · batch the SMA20 enrichment into ONE provider request.

Measured 2026-08-05 (reports/2026-08-05_1937_task259_shortening.md): the agent
asks the provider for daily bars once per ticker, 60 times per run. Locally that
is 9.05s serial vs 0.67s batched for the same 60 real tickers.

The dangerous failure mode is NOT slowness — it is mis-attribution. A batch
response is a MultiIndex frame keyed by symbol; if the mapping slips, ticker A
gets ticker B's SMA and Filter 4d (TOXIC_PROFILE) silently judges the wrong
stock. The live measurement also showed that a symbol with no data is simply
ABSENT from the batch frame — no exception, no empty row. Both are covered here.

Mock-only. No network. No Sheets.
"""
import json
import os
import sys
import tempfile
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# ── helpers ──────────────────────────────────────────────────────────────

def _bars(closes):
    """A daily-bars frame shaped like the provider returns (single-index)."""
    idx = pd.date_range("2026-07-01", periods=len(closes), freq="D")
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c * 1.01 for c in closes],
            "low": [c * 0.99 for c in closes],
            "close": closes,
            "volume": [1_000_000] * len(closes),
        },
        index=idx,
    )


def _sma(closes):
    """Same arithmetic as sma20_cache: mean of the last <=20 closes."""
    return sum(closes[-20:]) / min(len(closes), 20)


@pytest.fixture
def isolated_cache(monkeypatch):
    """Point CACHE_PATH at a throwaway file so no repo state is touched."""
    from agent.enrichment import sma20_cache as mod
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setattr(mod, "CACHE_PATH", os.path.join(d, "sma20_cache.json"))
        yield mod


class _BatchProvider:
    """Provider double exposing the batch API. Records how it was called."""

    def __init__(self, table):
        self.table = table            # {ticker: [closes]} — absent key = no data
        self.batch_calls = []
        self.single_calls = []

    def get_daily_bars_batch(self, tickers, days=60, end_date=None):
        self.batch_calls.append(list(tickers))
        return {t: _bars(self.table[t]) for t in tickers if t in self.table}

    def get_daily_bars(self, ticker, days=60, end_date=None):
        self.single_calls.append(ticker)
        if ticker not in self.table:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        return _bars(self.table[ticker])


# ── 1 · symbol→value mapping must not slip ───────────────────────────────

def test_batch_maps_each_symbol_to_its_own_sma_not_a_neighbours(isolated_cache):
    """Three symbols with deliberately far-apart price levels. If the mapping
    slipped, the assertions below would pick up a neighbour's SMA."""
    mod = isolated_cache
    table = {
        "AAA": [10.0] * 25,
        "BBB": [100.0] * 25,
        "CCC": [1000.0] * 25,
    }
    p = _BatchProvider(table)

    mod.prime_sma20_cache(["AAA", "BBB", "CCC"], provider=p)

    assert p.batch_calls == [["AAA", "BBB", "CCC"]], "expected exactly ONE batch request"
    assert p.single_calls == [], "batch path must not fall back to per-ticker calls"

    # price == SMA -> 0.0 %; a slipped mapping would give a huge non-zero number
    assert mod.get_price_vs_sma20("AAA", 10.0, provider=p) == 0.0
    assert mod.get_price_vs_sma20("BBB", 100.0, provider=p) == 0.0
    assert mod.get_price_vs_sma20("CCC", 1000.0, provider=p) == 0.0

    # and the cached SMA itself is the right one per symbol
    cache = json.load(open(mod.CACHE_PATH))
    vals = {k.split(":")[0]: v["sma20"] for k, v in cache.items()}
    assert vals["AAA"] == pytest.approx(_sma(table["AAA"]))
    assert vals["BBB"] == pytest.approx(_sma(table["BBB"]))
    assert vals["CCC"] == pytest.approx(_sma(table["CCC"]))

    # no extra provider traffic after priming
    assert p.single_calls == []


# ── 2 · a symbol absent from the batch is None, not a wrong number ────────

def test_symbol_absent_from_batch_returns_none_without_raising(isolated_cache, capsys):
    """Live measurement: a bogus symbol is silently missing from the frame."""
    mod = isolated_cache
    p = _BatchProvider({"AAA": [10.0] * 25, "BBB": [100.0] * 25})

    mod.prime_sma20_cache(["AAA", "ZZZZNOTREAL", "BBB"], provider=p)

    assert mod.get_price_vs_sma20("ZZZZNOTREAL", 55.0, provider=p) is None
    # the neighbours are unaffected
    assert mod.get_price_vs_sma20("AAA", 10.0, provider=p) == 0.0
    assert mod.get_price_vs_sma20("BBB", 100.0, provider=p) == 0.0
    # the missing symbol must not trigger a per-ticker retry
    assert p.single_calls == []
    # and it must be reported, not swallowed
    assert "BARS_INSUFFICIENT: ZZZZNOTREAL" in capsys.readouterr().out


# ── 3 · too few bars keeps the BARS_INSUFFICIENT behaviour ───────────────

def test_symbol_with_too_few_bars_returns_none_and_reports(isolated_cache, capsys):
    mod = isolated_cache
    p = _BatchProvider({"AAA": [10.0] * 25, "SHORTY": [7.0] * 5})   # 5 < 15

    mod.prime_sma20_cache(["AAA", "SHORTY"], provider=p)

    assert mod.get_price_vs_sma20("SHORTY", 7.0, provider=p) is None
    assert "BARS_INSUFFICIENT: SHORTY" in capsys.readouterr().out
    assert p.single_calls == []


# ── 4 · batched result is identical to the serial path ───────────────────

def test_batched_result_matches_serial_path_exactly(isolated_cache, monkeypatch):
    """Same mock input through both paths must give the same numbers."""
    mod = isolated_cache
    table = {
        "AAA": [10.0 + i for i in range(25)],
        "BBB": [100.0 - i for i in range(25)],
        "CCC": [50.0] * 18,
        "DDD": [3.0] * 4,          # too few bars
    }
    prices = {"AAA": 40.0, "BBB": 70.0, "CCC": 55.0, "DDD": 3.0}
    tickers = ["AAA", "BBB", "CCC", "DDD"]

    # serial path — one provider call per ticker, no priming
    p_serial = _BatchProvider(table)
    serial = {t: mod.get_price_vs_sma20(t, prices[t], provider=p_serial) for t in tickers}
    assert p_serial.single_calls == tickers, "serial path should call once per ticker"

    # batch path — fresh cache, one request
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setattr(mod, "CACHE_PATH", os.path.join(d, "sma20_cache.json"))
        p_batch = _BatchProvider(table)
        mod.prime_sma20_cache(tickers, provider=p_batch)
        batched = {t: mod.get_price_vs_sma20(t, prices[t], provider=p_batch) for t in tickers}
        assert p_batch.single_calls == [], "batch path must issue no per-ticker calls"

    assert batched == serial
    assert serial["DDD"] is None and batched["DDD"] is None


# ── 4b · rounding must not shift the value (TASK-259, measured 2026-08-05) ──

def test_cached_sma_is_not_rounded_so_the_percentage_is_unchanged(isolated_cache):
    """The live run of 60 real tickers showed 8 of them differing by up to 0.03
    percentage points between the serial and the batched path.

    Root cause was NOT the batching: sma20_cache stored round(sma20, 4), so the
    first call of the day computed the percentage from the UNROUNDED mean while
    every later call read the ROUNDED one. On a GitHub runner the cache is always
    cold, so production always took the unrounded branch — priming would have
    silently moved every ticker onto the rounded one.

    1.81025 is BEEP's real SMA20 on 2026-08-05, chosen because it is exactly the
    magnitude where the 4th decimal bites: 452.41 unrounded vs 452.43 rounded.
    test_batched_result_matches_serial_path_exactly does NOT catch this — its
    mock closes are round numbers.
    """
    mod = isolated_cache
    closes = [1.81025] * 25
    price = 10.0
    p = _BatchProvider({"BEEPY": closes})

    sma_exact = _sma(closes)
    expected = round((price - sma_exact) / sma_exact * 100, 2)

    mod.prime_sma20_cache(["BEEPY"], provider=p)

    assert mod.get_price_vs_sma20("BEEPY", price, provider=p) == expected

    # and the stored value itself must be the full-precision mean
    cache = json.load(open(mod.CACHE_PATH))
    assert cache["BEEPY:" + list(cache)[0].split(":")[1]]["sma20"] == pytest.approx(
        sma_exact, abs=0.0
    ), "the cache must keep the unrounded SMA"


# ── 5 · a total batch failure falls back to serial, loudly ───────────────

def test_batch_failure_falls_back_to_serial_and_is_reported(isolated_cache, capsys):
    mod = isolated_cache

    class _Exploding(_BatchProvider):
        def get_daily_bars_batch(self, tickers, days=60, end_date=None):
            self.batch_calls.append(list(tickers))
            raise RuntimeError("alpaca is down")

    p = _Exploding({"AAA": [10.0] * 25, "BBB": [100.0] * 25})
    mod.prime_sma20_cache(["AAA", "BBB"], provider=p)

    assert p.batch_calls == [["AAA", "BBB"]]
    assert p.single_calls == ["AAA", "BBB"], "must fall back to the serial path"
    out = capsys.readouterr().out
    assert "SMA20_BATCH_FAILED" in out, "a total batch failure must be reported, not silent"
    assert mod.get_price_vs_sma20("AAA", 10.0, provider=p) == 0.0


# ── 6 · priming is skipped for tickers already cached today ──────────────

def test_prime_only_requests_uncached_tickers(isolated_cache):
    mod = isolated_cache
    p = _BatchProvider({"AAA": [10.0] * 25, "BBB": [100.0] * 25})

    mod.prime_sma20_cache(["AAA"], provider=p)
    mod.prime_sma20_cache(["AAA", "BBB"], provider=p)

    assert p.batch_calls == [["AAA"], ["BBB"]], "second prime must ask only for BBB"
