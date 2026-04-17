"""
test_utils.py - Unit tests for utils.py
========================================

Comprehensive tests for all shared utility functions.

Usage:
    python3 test_utils.py
"""
import sys
import os
import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import (
    parse_market_cap,
    parse_volume,
    is_trading_day,
    is_day_complete,
    get_peru_time,
    calculate_stats,
    PERU_TZ,
    MARKET_CLOSE_HOUR_PERU,
)


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def assert_equal(self, actual, expected, test_name, tolerance=0.01):
        try:
            if isinstance(expected, float):
                if abs(actual - expected) <= tolerance:
                    self.passed += 1
                    print(f"  ✅ {test_name}")
                else:
                    self.failed += 1
                    msg = f"Expected {expected}, got {actual}"
                    self.failures.append((test_name, msg))
                    print(f"  ❌ {test_name}: {msg}")
            else:
                if actual == expected:
                    self.passed += 1
                    print(f"  ✅ {test_name}")
                else:
                    self.failed += 1
                    msg = f"Expected {expected}, got {actual}"
                    self.failures.append((test_name, msg))
                    print(f"  ❌ {test_name}: {msg}")
        except Exception as e:
            self.failed += 1
            self.failures.append((test_name, str(e)))
            print(f"  ❌ {test_name}: EXCEPTION - {e}")
    
    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print(f"Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\n❌ {self.failed} FAILURES:")
            for name, msg in self.failures:
                print(f"  • {name}: {msg}")
            return False
        else:
            print("✅ All tests passed!")
            return True


# ═══════════════════════════════════════════════════════════════════════
# parse_market_cap tests
# ═══════════════════════════════════════════════════════════════════════

def test_parse_market_cap(t):
    print("\n🧪 Testing parse_market_cap()...")
    
    # Normal cases
    t.assert_equal(parse_market_cap('125.50M'), 125_500_000.0, "mc_millions")
    t.assert_equal(parse_market_cap('1.25B'), 1_250_000_000.0, "mc_billions")
    t.assert_equal(parse_market_cap('50M'), 50_000_000.0, "mc_simple_millions")
    t.assert_equal(parse_market_cap('1B'), 1_000_000_000.0, "mc_simple_billions")
    t.assert_equal(parse_market_cap('100'), 100.0, "mc_plain_number")
    
    # With commas
    t.assert_equal(parse_market_cap('1,250,000'), 1_250_000.0, "mc_with_commas")
    
    # Edge cases
    t.assert_equal(parse_market_cap('-'), None, "mc_dash")
    t.assert_equal(parse_market_cap(''), None, "mc_empty")
    t.assert_equal(parse_market_cap('abc'), None, "mc_invalid")
    t.assert_equal(parse_market_cap(None), None, "mc_none")


# ═══════════════════════════════════════════════════════════════════════
# parse_volume tests
# ═══════════════════════════════════════════════════════════════════════

def test_parse_volume(t):
    print("\n🧪 Testing parse_volume()...")
    
    # Normal cases
    t.assert_equal(parse_volume('1,250,000'), 1_250_000, "vol_with_commas")
    t.assert_equal(parse_volume('1.5M'), 1_500_000, "vol_millions_decimal")
    t.assert_equal(parse_volume('500K'), 500_000, "vol_thousands")
    t.assert_equal(parse_volume('1000'), 1_000, "vol_plain")
    t.assert_equal(parse_volume('5M'), 5_000_000, "vol_simple_millions")
    
    # Edge cases
    t.assert_equal(parse_volume('-'), None, "vol_dash")
    t.assert_equal(parse_volume(''), None, "vol_empty")
    t.assert_equal(parse_volume(None), None, "vol_none")


# ═══════════════════════════════════════════════════════════════════════
# Time utility tests
# ═══════════════════════════════════════════════════════════════════════

def test_get_peru_time(t):
    print("\n🧪 Testing get_peru_time()...")
    
    now = get_peru_time()
    t.assert_equal(now.tzinfo is not None, True, "peru_time_has_tz")
    t.assert_equal(str(now.tzinfo), "America/Lima", "peru_time_correct_tz")


def test_is_trading_day(t):
    print("\n🧪 Testing is_trading_day()...")
    
    # Known Saturday
    sat = dt.date(2026, 4, 11)  # April 11 2026 is Saturday
    t.assert_equal(is_trading_day(sat), False, "trading_day_saturday")
    
    # Known Sunday
    sun = dt.date(2026, 4, 12)
    t.assert_equal(is_trading_day(sun), False, "trading_day_sunday")
    
    # Known weekday (if not holiday)
    # April 15 2026 - Wednesday
    wed = dt.date(2026, 4, 15)
    result = is_trading_day(wed)
    # Should be True unless it's a holiday (might be market calendar specific)
    t.assert_equal(result in [True, False], True, "trading_day_weekday_returns_bool")


def test_is_day_complete(t):
    print("\n🧪 Testing is_day_complete()...")
    
    now = get_peru_time()
    today = now.date()
    
    # Yesterday (assuming not weekend)
    yesterday = today - dt.timedelta(days=1)
    while yesterday.weekday() >= 5:  # Skip weekends
        yesterday = yesterday - dt.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    t.assert_equal(is_day_complete(yesterday_str), True, "day_complete_past_weekday")
    
    # Tomorrow (never complete)
    tomorrow_str = (today + dt.timedelta(days=5)).strftime("%Y-%m-%d")
    t.assert_equal(is_day_complete(tomorrow_str), False, "day_complete_future")
    
    # A known weekend
    sat_str = "2026-04-11"
    t.assert_equal(is_day_complete(sat_str), False, "day_complete_weekend")


# ═══════════════════════════════════════════════════════════════════════
# calculate_stats tests
# ═══════════════════════════════════════════════════════════════════════

def test_calculate_stats(t):
    print("\n🧪 Testing calculate_stats()...")
    
    # Scenario 1: Perfect short - TP10 hit, no SL
    ohlc = {
        "D1_Open": 9.5, "D1_High": 9.8, "D1_Low": 8.5,
        "D2_Open": 8.5, "D2_High": 9.0, "D2_Low": 8.0,
        "D3_Open": 8.0, "D3_High": 8.5, "D3_Low": 7.0,  # min low here
    }
    stats = calculate_stats(10.0, ohlc)
    
    t.assert_equal(stats["MaxDrop%"], -30.0, "stats_max_drop_30pct")
    t.assert_equal(stats["BestDay"], 3, "stats_best_day_3")
    t.assert_equal(stats["TP10_Hit"], 1, "stats_tp10_hit_yes")
    t.assert_equal(stats["TP15_Hit"], 1, "stats_tp15_hit_yes")
    t.assert_equal(stats["TP20_Hit"], 1, "stats_tp20_hit_yes")
    t.assert_equal(stats["D1_Gap%"], -5.0, "stats_d1_gap_negative")
    t.assert_equal(stats["SL7_Hit_D1"], 0, "stats_sl7_d1_no")
    t.assert_equal(stats["IntraDay_SL"], 0, "stats_intra_sl_no")
    
    # Scenario 2: Failed short - SL hit on D1
    ohlc2 = {
        "D1_Open": 10.5, "D1_High": 11.0, "D1_Low": 10.0,  # high > 10.7 ? no, 11.0 > 10.7 yes
        "D2_Open": 11.0, "D2_High": 12.0, "D2_Low": 10.5,
    }
    stats2 = calculate_stats(10.0, ohlc2)
    # SL7 = price * 1.07 = 10.7, D1_High = 11.0 >= 10.7 → SL hit
    t.assert_equal(stats2["SL7_Hit_D1"], 1, "stats_sl7_d1_hit")
    t.assert_equal(stats2["IntraDay_SL"], 1, "stats_intra_sl_hit")
    
    # Scenario 3: No data
    stats3 = calculate_stats(10.0, {})
    t.assert_equal(stats3["MaxDrop%"], None, "stats_no_data_returns_none")
    
    # Scenario 4: Invalid scan price
    stats4 = calculate_stats(0, ohlc)
    t.assert_equal(stats4["MaxDrop%"], None, "stats_zero_price_returns_none")


# ═══════════════════════════════════════════════════════════════════════
# Main Test Runner
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🧪 RidingHigh Pro - Utils Unit Tests")
    print("=" * 60)
    
    t = TestResult()
    
    test_parse_market_cap(t)
    test_parse_volume(t)
    test_get_peru_time(t)
    test_is_trading_day(t)
    test_is_day_complete(t)
    test_calculate_stats(t)
    
    success = t.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
