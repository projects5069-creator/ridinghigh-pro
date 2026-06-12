"""TASK-155 Phase 1 — cached intraday fetch. Network-free (monkeypatch the
provider). Cache once per (ticker, settled-day, timeframe); never re-fetch a
cached settled day; never cache today (still moving); never cache an empty result."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data_provider
import intraday_cache


def _bars(n=3):
    idx = pd.to_datetime(
        ["2026-05-13 13:30:00", "2026-05-13 13:31:00", "2026-05-13 13:32:00"], utc=True
    )[:n]
    return pd.DataFrame(
        {"open": [1.0, 2.0, 3.0][:n], "high": [1.1, 2.2, 3.3][:n],
         "low": [0.9, 1.8, 2.7][:n], "close": [1.0, 2.0, 3.0][:n],
         "volume": [10.0, 20.0, 30.0][:n]},
        index=idx,
    )


def _fake_provider(counter):
    def fake(ticker, date, timeframe="1Min"):
        counter["n"] += 1
        return _bars()
    return fake


def test_cache_miss_fetches_and_writes(tmp_path, monkeypatch):
    c = {"n": 0}
    monkeypatch.setattr(data_provider, "get_intraday_bars", _fake_provider(c))
    out = intraday_cache.get_intraday_bars_cached(
        "AEHL", "2026-05-13", cache_dir=str(tmp_path), today="2026-06-12")
    assert len(out) == 3 and c["n"] == 1
    assert os.path.exists(os.path.join(str(tmp_path), "AEHL_2026-05-13_1Min.json"))


def test_cache_hit_no_refetch(tmp_path, monkeypatch):
    c = {"n": 0}
    monkeypatch.setattr(data_provider, "get_intraday_bars", _fake_provider(c))
    intraday_cache.get_intraday_bars_cached(
        "AEHL", "2026-05-13", cache_dir=str(tmp_path), today="2026-06-12")
    out2 = intraday_cache.get_intraday_bars_cached(
        "AEHL", "2026-05-13", cache_dir=str(tmp_path), today="2026-06-12")
    assert c["n"] == 1                 # second call served from disk, provider NOT re-called
    assert len(out2) == 3
    assert list(out2["high"]) == [1.1, 2.2, 3.3]   # values survive round-trip
    assert str(out2.index.tz) == "UTC"             # tz-aware index restored


def test_today_not_cached(tmp_path, monkeypatch):
    c = {"n": 0}
    monkeypatch.setattr(data_provider, "get_intraday_bars", _fake_provider(c))
    intraday_cache.get_intraday_bars_cached(
        "AEHL", "2026-06-12", cache_dir=str(tmp_path), today="2026-06-12")
    intraday_cache.get_intraday_bars_cached(
        "AEHL", "2026-06-12", cache_dir=str(tmp_path), today="2026-06-12")
    assert c["n"] == 2                 # today is still moving -> fetched each time
    assert not os.path.exists(os.path.join(str(tmp_path), "AEHL_2026-06-12_1Min.json"))


def test_empty_not_written(tmp_path, monkeypatch):
    monkeypatch.setattr(
        data_provider, "get_intraday_bars",
        lambda t, d, timeframe="1Min": pd.DataFrame(columns=["open", "high", "low", "close", "volume"]))
    out = intraday_cache.get_intraday_bars_cached(
        "ZZZZ", "2026-05-13", cache_dir=str(tmp_path), today="2026-06-12")
    assert out.empty
    assert not os.path.exists(os.path.join(str(tmp_path), "ZZZZ_2026-05-13_1Min.json"))
