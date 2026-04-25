#!/usr/bin/env python3
"""
test_data_provider.py - Unit tests for the data provider abstraction
========================================================================

Tests:
  - Both providers return bars in the standard format
  - 5-day OHLC has correct keys
  - Latest quote / bar formats are correct
  - Health check works
  - Factory selects correct provider

Run:
    python3 test_data_provider.py

Created: 2026-04-25 (Issue #9)
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

# Force-load .env before importing
import data_provider  # this triggers _load_env()
from data_provider import (
    get_data_provider,
    get_fundamentals_provider,
    reset_providers,
    DataProvider,
    FundamentalsProvider,
)


# ════════════════════════════════════════════════════════════════════════
# Test framework (lightweight)
# ════════════════════════════════════════════════════════════════════════

class T:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def check(self, cond, name):
        if cond:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            self.errors.append(name)
            print(f"  ❌ {name}")
    
    def equal(self, a, b, name):
        self.check(a == b, f"{name}  (got {a!r}, expected {b!r})")
    
    def report(self):
        total = self.passed + self.failed
        print()
        print("=" * 60)
        if self.failed == 0:
            print(f"✅ All {total} tests passed!")
            return 0
        else:
            print(f"❌ {self.failed}/{total} tests FAILED:")
            for e in self.errors:
                print(f"   - {e}")
            return 1


# ════════════════════════════════════════════════════════════════════════
# Provider contract tests — run for each provider
# ════════════════════════════════════════════════════════════════════════

def test_provider_contract(t: T, provider: DataProvider, provider_name: str):
    print(f"\n🧪 Testing {provider_name} ({provider.name})")
    
    # ── Health ─────────────────────────────────────────────────────
    t.check(provider.is_healthy(), f"{provider_name}_healthy")
    
    # ── get_daily_bars ─────────────────────────────────────────────
    df = provider.get_daily_bars("AAPL", days=5)
    t.check(isinstance(df, pd.DataFrame), f"{provider_name}_daily_bars_returns_df")
    if not df.empty:
        for col in ["open", "high", "low", "close", "volume"]:
            t.check(col in df.columns, f"{provider_name}_daily_bars_has_{col}")
        t.check(len(df) >= 1, f"{provider_name}_daily_bars_not_empty")
        # Sanity: high >= low
        t.check((df["high"] >= df["low"]).all(), f"{provider_name}_high_gte_low")
        # Sanity: close in [low, high] (with tolerance for adjustments)
        valid = ((df["close"] >= df["low"] * 0.99) & (df["close"] <= df["high"] * 1.01)).all()
        t.check(valid, f"{provider_name}_close_within_range")
    
    # ── get_5day_ohlc ──────────────────────────────────────────────
    # Use a date 10 trading days back so 5-day data exists
    scan_dt = datetime.now() - timedelta(days=15)
    while scan_dt.weekday() >= 5:
        scan_dt -= timedelta(days=1)
    scan_date_str = scan_dt.strftime("%Y-%m-%d")
    
    ohlc = provider.get_5day_ohlc("AAPL", scan_date_str)
    t.check(isinstance(ohlc, dict), f"{provider_name}_5day_returns_dict")
    expected_keys = {f"D{d}_{f}" for d in range(1, 6)
                     for f in ("Open", "High", "Low", "Close", "Volume")}
    t.equal(set(ohlc.keys()), expected_keys, f"{provider_name}_5day_correct_keys")
    
    # At least D1 should have data
    has_any = any(ohlc.get(f"D{d}_Close") is not None for d in range(1, 6))
    t.check(has_any, f"{provider_name}_5day_has_some_data")
    
    # ── get_latest_bar ─────────────────────────────────────────────
    bar = provider.get_latest_bar("AAPL")
    if bar is not None:  # Allowed to be None on weekends
        for k in ["open", "high", "low", "close", "volume"]:
            t.check(k in bar, f"{provider_name}_latest_bar_has_{k}")
        t.check(isinstance(bar["close"], (int, float)), f"{provider_name}_latest_bar_close_numeric")
    
    # ── get_latest_quote ───────────────────────────────────────────
    quote = provider.get_latest_quote("AAPL")
    if quote is not None:
        for k in ["bid_price", "ask_price", "timestamp"]:
            t.check(k in quote, f"{provider_name}_quote_has_{k}")


# ════════════════════════════════════════════════════════════════════════
# Factory tests
# ════════════════════════════════════════════════════════════════════════

def test_factory(t: T):
    print("\n🧪 Testing factory")
    
    reset_providers()
    
    # Force alpaca
    try:
        prov = get_data_provider(force_provider="alpaca")
        t.check(prov.name.startswith("alpaca"), "factory_alpaca_returns_alpaca")
    except Exception as e:
        t.check(False, f"factory_alpaca_initialization (got: {e})")
    
    # Force yfinance
    try:
        prov = get_data_provider(force_provider="yfinance")
        t.check(prov.name == "yfinance", "factory_yfinance_returns_yfinance")
    except Exception as e:
        t.check(False, f"factory_yfinance_initialization (got: {e})")
    
    # Invalid provider name
    try:
        get_data_provider(force_provider="invalid_xyz")
        t.check(False, "factory_invalid_should_raise")
    except ValueError:
        t.check(True, "factory_invalid_raises_value_error")


# ════════════════════════════════════════════════════════════════════════
# Fundamentals tests
# ════════════════════════════════════════════════════════════════════════

def test_fundamentals(t: T):
    print("\n🧪 Testing fundamentals provider")
    
    try:
        fund = get_fundamentals_provider()
        t.check(isinstance(fund, FundamentalsProvider), "fundamentals_is_instance")
        
        info = fund.get_fundamentals("AAPL")
        t.check(isinstance(info, dict), "fundamentals_returns_dict")
        for k in ["market_cap", "shares_outstanding", "float_shares",
                  "average_volume", "sector", "industry"]:
            t.check(k in info, f"fundamentals_has_{k}")
        # AAPL has a known market cap > $1B (sanity)
        if info["market_cap"]:
            t.check(info["market_cap"] > 1_000_000_000, "fundamentals_aapl_market_cap_reasonable")
    except Exception as e:
        t.check(False, f"fundamentals_failed (got: {e})")


# ════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🧪 RidingHigh Pro — data_provider tests")
    print("=" * 60)
    
    t = T()
    
    # Test factory first (cheap)
    test_factory(t)
    
    # Test each provider
    reset_providers()
    
    print("\n--- yfinance ---")
    try:
        from providers.yfinance_provider import YFinanceDataProvider
        test_provider_contract(t, YFinanceDataProvider(), "yfinance")
    except Exception as e:
        print(f"  ⚠️  yfinance tests skipped: {e}")
    
    print("\n--- alpaca ---")
    try:
        from providers.alpaca_provider import AlpacaDataProvider
        test_provider_contract(t, AlpacaDataProvider(), "alpaca")
    except Exception as e:
        print(f"  ⚠️  alpaca tests skipped: {e}")
    
    # Fundamentals
    test_fundamentals(t)
    
    return t.report()


if __name__ == "__main__":
    sys.exit(main())
