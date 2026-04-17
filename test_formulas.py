"""
test_formulas.py v2.0 - Comprehensive tests for all 15 formulas
================================================================

Usage:
    python3 test_formulas.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formulas import (
    # Core (v1.0)
    calculate_mxv,
    calculate_runup,
    calculate_atrx,
    validate_atrx,
    calculate_gap,
    calculate_vwap_dist,
    calculate_rel_vol,
    calculate_float_pct,
    # Extended (v2.0)
    calculate_price_to_high,
    calculate_price_to_52w_high,
    calculate_scan_change,
    calculate_drop_from_high,
    calculate_max_drop,
    calculate_d1_gap,
    calculate_pnl_pct,
    # Constants
    REL_VOL_CAP,
    ATRX_VALIDATION_THRESHOLD,
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
# v1.0 Core Tests (from original file)
# ═══════════════════════════════════════════════════════════════════════

def test_mxv(t):
    print("\n🧪 Testing calculate_mxv()...")
    t.assert_equal(calculate_mxv(100_000_000, 5, 50_000_000), -150.0, "mxv_pump_2.5x")
    t.assert_equal(calculate_mxv(100_000_000, 2, 10_000_000), 80.0, "mxv_low_turnover")
    t.assert_equal(calculate_mxv(100_000_000, 1, 100_000_000), 0.0, "mxv_exact_turnover")
    t.assert_equal(calculate_mxv(1_000_000_000, 10, 100_000_000), 0.0, "mxv_large_cap_match")
    t.assert_equal(calculate_mxv(0, 5, 50_000_000), 0.0, "mxv_zero_market_cap")
    t.assert_equal(calculate_mxv(None, 5, 50_000_000), 0.0, "mxv_none_market_cap")
    t.assert_equal(calculate_mxv(100_000_000, None, 50_000_000), 0.0, "mxv_none_price")
    t.assert_equal(calculate_mxv(100_000_000, 0, 0), 100.0, "mxv_zero_price_and_volume")


def test_runup(t):
    print("\n🧪 Testing calculate_runup()...")
    t.assert_equal(calculate_runup(13.00, 10.00), 30.0, "runup_up_30pct")
    t.assert_equal(calculate_runup(10.00, 10.00), 0.0, "runup_no_change")
    t.assert_equal(calculate_runup(9.00, 10.00), -10.0, "runup_down_10pct")
    t.assert_equal(calculate_runup(20.00, 10.00), 100.0, "runup_doubled")
    t.assert_equal(calculate_runup(10, 0), 0.0, "runup_zero_open")
    t.assert_equal(calculate_runup(10, None), 0.0, "runup_none_open")
    t.assert_equal(calculate_runup(None, 10), 0.0, "runup_none_price")


def test_atrx(t):
    print("\n🧪 Testing calculate_atrx()...")
    t.assert_equal(calculate_atrx(10.0, 8.0, 1.0), 2.0, "atrx_normal_2x")
    t.assert_equal(calculate_atrx(5.0, 3.0, 1.0), 2.0, "atrx_same_range_2x")
    t.assert_equal(calculate_atrx(10.0, 9.0, 1.0), 1.0, "atrx_matches_average")
    t.assert_equal(calculate_atrx(5.0, 5.0, 1.0), 0.0, "atrx_no_range")
    t.assert_equal(calculate_atrx(10.0, 8.0, 0), 0.0, "atrx_zero_atr")
    t.assert_equal(calculate_atrx(None, 8.0, 1.0), 0.0, "atrx_none_high")
    t.assert_equal(calculate_atrx(10.0, None, 1.0), 0.0, "atrx_none_low")


def test_validate_atrx(t):
    print("\n🧪 Testing validate_atrx()...")
    t.assert_equal(validate_atrx(3.0, 0.5, 10), 3.0, "validate_normal_atrx")
    t.assert_equal(validate_atrx(1.5, 0.3, 10), 1.5, "validate_low_atrx")
    t.assert_equal(validate_atrx(5.0, 1.0, 10), 5.0, "validate_high_but_valid")
    t.assert_equal(validate_atrx(25.0, 0.02, 10), 0.0, "validate_yfinance_bug_detected")
    t.assert_equal(validate_atrx(50.0, 0.01, 10), 0.0, "validate_yfinance_bug_extreme")
    t.assert_equal(validate_atrx(2.0, 0.01, 10), 2.0, "validate_low_atr_low_atrx_ok")
    t.assert_equal(validate_atrx(None, 1.0, 10), 0.0, "validate_none_atrx")
    t.assert_equal(validate_atrx(3.0, 1.0, 0), 0.0, "validate_zero_price")


def test_gap(t):
    print("\n🧪 Testing calculate_gap()...")
    t.assert_equal(calculate_gap(12.0, 10.0), 20.0, "gap_up_20pct")
    t.assert_equal(calculate_gap(10.0, 10.0), 0.0, "gap_no_change")
    t.assert_equal(calculate_gap(8.0, 10.0), -20.0, "gap_down_20pct")
    t.assert_equal(calculate_gap(15.0, 10.0), 50.0, "gap_up_50pct")
    t.assert_equal(calculate_gap(10, 0), 0.0, "gap_zero_prev_close")
    t.assert_equal(calculate_gap(10, None), 0.0, "gap_none_prev_close")


def test_vwap_dist(t):
    print("\n🧪 Testing calculate_vwap_dist()...")
    t.assert_equal(calculate_vwap_dist(11.0, 12.0, 9.0), 3.125, "vwap_dist_above_typical")
    t.assert_equal(calculate_vwap_dist(10.0, 12.0, 8.0), 0.0, "vwap_dist_at_typical")
    t.assert_equal(calculate_vwap_dist(None, 10, 8), 0.0, "vwap_none_price")
    t.assert_equal(calculate_vwap_dist(10, None, 8), 0.0, "vwap_none_high")
    t.assert_equal(calculate_vwap_dist(0, 0, 0), 0.0, "vwap_all_zero")


def test_rel_vol(t):
    print("\n🧪 Testing calculate_rel_vol()...")
    t.assert_equal(calculate_rel_vol(1_000_000, 500_000), 2.0, "rel_vol_2x_normal")
    t.assert_equal(calculate_rel_vol(500_000, 500_000), 1.0, "rel_vol_exact_avg")
    t.assert_equal(calculate_rel_vol(100_000, 500_000), 0.2, "rel_vol_below_avg")
    t.assert_equal(calculate_rel_vol(5_000_000, 500_000), 10.0, "rel_vol_10x")
    t.assert_equal(calculate_rel_vol(50_000_000, 500_000), 100.0, "rel_vol_exactly_at_cap")
    t.assert_equal(calculate_rel_vol(5_000_000_000, 10_000), REL_VOL_CAP, "rel_vol_capped_from_extreme")
    t.assert_equal(calculate_rel_vol(1_000_000_000, 100), REL_VOL_CAP, "rel_vol_capped_yfinance_bug")
    t.assert_equal(calculate_rel_vol(1_000_000, 0), 1.0, "rel_vol_zero_avg")
    t.assert_equal(calculate_rel_vol(1_000_000, None), 1.0, "rel_vol_none_avg")
    t.assert_equal(calculate_rel_vol(None, 500_000), 1.0, "rel_vol_none_volume")


def test_float_pct(t):
    print("\n🧪 Testing calculate_float_pct()...")
    t.assert_equal(calculate_float_pct(8_000_000, 10_000_000), 80.0, "float_normal_80pct")
    t.assert_equal(calculate_float_pct(2_000_000, 10_000_000), 20.0, "float_low_20pct")
    t.assert_equal(calculate_float_pct(10_000_000, 10_000_000), 100.0, "float_full_100pct")
    t.assert_equal(calculate_float_pct(0, 10_000_000), 0.0, "float_zero_float")
    t.assert_equal(calculate_float_pct(5_000_000, 0), 0.0, "float_zero_shares")
    t.assert_equal(calculate_float_pct(None, 10_000_000), 0.0, "float_none_float")
    t.assert_equal(calculate_float_pct(5_000_000, None), 0.0, "float_none_shares")


# ═══════════════════════════════════════════════════════════════════════
# v2.0 Extended Tests (NEW)
# ═══════════════════════════════════════════════════════════════════════

def test_price_to_high(t):
    print("\n🧪 Testing calculate_price_to_high() [NEW v2.0]...")
    t.assert_equal(calculate_price_to_high(9.0, 10.0), -10.0, "pth_10pct_below_high")
    t.assert_equal(calculate_price_to_high(10.0, 10.0), 0.0, "pth_at_high")
    t.assert_equal(calculate_price_to_high(8.5, 10.0), -15.0, "pth_15pct_below")
    t.assert_equal(calculate_price_to_high(11.0, 10.0), 10.0, "pth_above_high_unusual")
    t.assert_equal(calculate_price_to_high(5.0, 0), 0.0, "pth_zero_high")
    t.assert_equal(calculate_price_to_high(None, 10.0), 0.0, "pth_none_price")
    t.assert_equal(calculate_price_to_high(10.0, None), 0.0, "pth_none_high")


def test_price_to_52w_high(t):
    print("\n🧪 Testing calculate_price_to_52w_high() [NEW v2.0]...")
    t.assert_equal(calculate_price_to_52w_high(5.0, 10.0), -50.0, "p52w_50pct_below")
    t.assert_equal(calculate_price_to_52w_high(10.0, 10.0), 0.0, "p52w_at_high")
    t.assert_equal(calculate_price_to_52w_high(1.0, 10.0), -90.0, "p52w_beaten_down")
    t.assert_equal(calculate_price_to_52w_high(5.0, 0), 0.0, "p52w_zero_52whigh")
    t.assert_equal(calculate_price_to_52w_high(None, 10.0), 0.0, "p52w_none_price")


def test_scan_change(t):
    print("\n🧪 Testing calculate_scan_change() [NEW v2.0]...")
    t.assert_equal(calculate_scan_change(15.0, 10.0), 50.0, "scan_change_up_50")
    t.assert_equal(calculate_scan_change(10.0, 10.0), 0.0, "scan_change_no_change")
    t.assert_equal(calculate_scan_change(9.0, 10.0), -10.0, "scan_change_down_10")
    t.assert_equal(calculate_scan_change(30.0, 10.0), 200.0, "scan_change_extreme_pump")
    t.assert_equal(calculate_scan_change(10, 0), 0.0, "scan_change_zero_prev")
    t.assert_equal(calculate_scan_change(None, 10), 0.0, "scan_change_none_price")


def test_drop_from_high(t):
    print("\n🧪 Testing calculate_drop_from_high() [NEW v2.0]...")
    t.assert_equal(calculate_drop_from_high(8.0, 10.0), 20.0, "drop_20pct_from_high")
    t.assert_equal(calculate_drop_from_high(10.0, 10.0), 0.0, "drop_at_high")
    t.assert_equal(calculate_drop_from_high(5.0, 10.0), 50.0, "drop_50pct_from_high")
    # Edge: current above "high" (can happen in live tracking)
    t.assert_equal(calculate_drop_from_high(11.0, 10.0), 0.0, "drop_above_high_returns_0")
    t.assert_equal(calculate_drop_from_high(None, 10.0), 0.0, "drop_none_current")
    t.assert_equal(calculate_drop_from_high(10.0, 0), 0.0, "drop_zero_high")


def test_max_drop(t):
    print("\n🧪 Testing calculate_max_drop() [NEW v2.0]...")
    t.assert_equal(calculate_max_drop(9.0, 10.0), -10.0, "max_drop_10pct")
    t.assert_equal(calculate_max_drop(7.0, 10.0), -30.0, "max_drop_30pct")
    t.assert_equal(calculate_max_drop(10.0, 10.0), 0.0, "max_drop_no_drop")
    t.assert_equal(calculate_max_drop(10.5, 10.0), 5.0, "max_drop_positive_price_rose")
    t.assert_equal(calculate_max_drop(5.0, 10.0), -50.0, "max_drop_50pct_huge")
    t.assert_equal(calculate_max_drop(9.0, 0), 0.0, "max_drop_zero_scan")
    t.assert_equal(calculate_max_drop(None, 10.0), 0.0, "max_drop_none_min")


def test_d1_gap(t):
    print("\n🧪 Testing calculate_d1_gap() [NEW v2.0]...")
    t.assert_equal(calculate_d1_gap(9.5, 10.0), -5.0, "d1_gap_down_5pct")
    t.assert_equal(calculate_d1_gap(10.0, 10.0), 0.0, "d1_gap_no_gap")
    t.assert_equal(calculate_d1_gap(12.0, 10.0), 20.0, "d1_gap_up_20pct")
    t.assert_equal(calculate_d1_gap(8.0, 10.0), -20.0, "d1_gap_down_20pct")
    t.assert_equal(calculate_d1_gap(None, 10.0), 0.0, "d1_gap_none_d1")
    t.assert_equal(calculate_d1_gap(9.5, 0), 0.0, "d1_gap_zero_scan")


def test_pnl_pct(t):
    print("\n🧪 Testing calculate_pnl_pct() [NEW v2.0]...")
    # Short positions
    t.assert_equal(calculate_pnl_pct(10.0, 9.0, is_short=True), 10.0, "pnl_short_profit")
    t.assert_equal(calculate_pnl_pct(10.0, 11.0, is_short=True), -10.0, "pnl_short_loss")
    t.assert_equal(calculate_pnl_pct(10.0, 10.0, is_short=True), 0.0, "pnl_short_break_even")
    # Long positions
    t.assert_equal(calculate_pnl_pct(10.0, 11.0, is_short=False), 10.0, "pnl_long_profit")
    t.assert_equal(calculate_pnl_pct(10.0, 9.0, is_short=False), -10.0, "pnl_long_loss")
    # Edge cases
    t.assert_equal(calculate_pnl_pct(0, 10), 0.0, "pnl_zero_entry")
    t.assert_equal(calculate_pnl_pct(10, None), 0.0, "pnl_none_exit")


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests (real-world scenarios)
# ═══════════════════════════════════════════════════════════════════════

def test_real_world_scenarios(t):
    print("\n🧪 Testing real-world scenarios...")
    
    # Scenario 1: Full pump-and-dump cycle
    scan_price = 5.00
    prev_close = 2.00
    high_today = 6.00
    
    scan_change = calculate_scan_change(scan_price, prev_close)
    t.assert_equal(scan_change, 150.0, "scenario_pump_scan_change_150pct")
    
    price_to_high = calculate_price_to_high(scan_price, high_today)
    # Stock dropped from 6 to 5 = -16.67%
    expected = (5 - 6) / 6 * 100  # -16.666...
    t.assert_equal(abs(price_to_high - expected) < 0.01, True, "scenario_pump_dropped_from_peak")
    
    # Scenario 2: Short trade lifecycle
    entry = 5.00  # scanned at $5
    d1_open = 4.50  # opened lower next day
    min_low = 3.50  # lowest point reached
    
    d1_gap = calculate_d1_gap(d1_open, entry)
    t.assert_equal(d1_gap, -10.0, "scenario_short_d1_favorable_gap")
    
    max_drop = calculate_max_drop(min_low, entry)
    t.assert_equal(max_drop, -30.0, "scenario_short_max_drop_30pct")
    
    # Short PnL at min_low (would be 30% profit if exited at bottom)
    max_pnl = calculate_pnl_pct(entry, min_low, is_short=True)
    t.assert_equal(max_pnl, 30.0, "scenario_short_max_pnl")


# ═══════════════════════════════════════════════════════════════════════
# Main Test Runner
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🧪 RidingHigh Pro - Formula Unit Tests v2.0")
    print("=" * 60)
    
    t = TestResult()
    
    # v1.0 tests
    print("\n━━━ v1.0 Core Tests ━━━")
    test_mxv(t)
    test_runup(t)
    test_atrx(t)
    test_validate_atrx(t)
    test_gap(t)
    test_vwap_dist(t)
    test_rel_vol(t)
    test_float_pct(t)
    
    # v2.0 tests (new)
    print("\n━━━ v2.0 Extended Tests (NEW) ━━━")
    test_price_to_high(t)
    test_price_to_52w_high(t)
    test_scan_change(t)
    test_drop_from_high(t)
    test_max_drop(t)
    test_d1_gap(t)
    test_pnl_pct(t)
    
    # Integration
    print("\n━━━ Integration Tests ━━━")
    test_real_world_scenarios(t)
    
    success = t.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
