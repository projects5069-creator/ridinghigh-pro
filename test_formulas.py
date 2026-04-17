"""
test_formulas.py - RidingHigh Pro Formula Tests
================================================

Comprehensive unit tests for all formulas in formulas.py.

Purpose:
--------
1. Verify formulas return correct values for normal inputs
2. Verify edge cases are handled (zero, None, negative)
3. Verify validation logic (caps, bad data detection)
4. Prevent regression bugs when formulas are modified

Usage:
------
    python3 test_formulas.py              # Run all tests
    python3 -m pytest test_formulas.py    # Run with pytest (if installed)

Test Naming Convention:
-----------------------
    test_<function>_<scenario>()

    Examples:
        test_mxv_normal_pump()       - Normal pump scenario
        test_mxv_zero_market_cap()   - Edge case: market cap is 0
        test_atrx_yfinance_bad_data() - Bad data detection

Created: 2026-04-17
"""

import sys
import os

# Add parent directory so we can import formulas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formulas import (
    calculate_mxv,
    calculate_runup,
    calculate_atrx,
    validate_atrx,
    calculate_gap,
    calculate_vwap_dist,
    calculate_rel_vol,
    calculate_float_pct,
    REL_VOL_CAP,
    ATRX_VALIDATION_THRESHOLD,
)


# ═══════════════════════════════════════════════════════════════════════
# Test Infrastructure
# ═══════════════════════════════════════════════════════════════════════

class TestResult:
    """Simple test result tracker."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.failures = []
    
    def assert_equal(self, actual, expected, test_name, tolerance=0.01):
        """Assert two values are equal (with optional tolerance for floats)."""
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
# MxV Tests
# ═══════════════════════════════════════════════════════════════════════

def test_mxv(t):
    """Test calculate_mxv with various scenarios."""
    print("\n🧪 Testing calculate_mxv()...")
    
    # Normal cases
    t.assert_equal(
        calculate_mxv(100_000_000, 5, 50_000_000),
        -150.0,
        "mxv_pump_2.5x"  # P×V = 250M, MC = 100M → (100-250)/100 × 100
    )
    
    t.assert_equal(
        calculate_mxv(100_000_000, 2, 10_000_000),
        80.0,
        "mxv_low_turnover"  # P×V = 20M, MC = 100M → (100-20)/100 × 100
    )
    
    t.assert_equal(
        calculate_mxv(100_000_000, 1, 100_000_000),
        0.0,
        "mxv_exact_turnover"  # P×V = 100M, MC = 100M
    )
    
    t.assert_equal(
        calculate_mxv(1_000_000_000, 10, 100_000_000),
        0.0,
        "mxv_large_cap_match"  # P×V = 1B, MC = 1B
    )
    
    # Edge cases
    t.assert_equal(
        calculate_mxv(0, 5, 50_000_000),
        0.0,
        "mxv_zero_market_cap"
    )
    
    t.assert_equal(
        calculate_mxv(None, 5, 50_000_000),
        0.0,
        "mxv_none_market_cap"
    )
    
    t.assert_equal(
        calculate_mxv(100_000_000, None, 50_000_000),
        0.0,
        "mxv_none_price"
    )
    
    t.assert_equal(
        calculate_mxv(100_000_000, 0, 0),
        100.0,
        "mxv_zero_price_and_volume"  # (100-0)/100 × 100 = 100
    )


# ═══════════════════════════════════════════════════════════════════════
# RunUp Tests
# ═══════════════════════════════════════════════════════════════════════

def test_runup(t):
    """Test calculate_runup with various scenarios."""
    print("\n🧪 Testing calculate_runup()...")
    
    # Normal cases
    t.assert_equal(calculate_runup(13.00, 10.00), 30.0, "runup_up_30pct")
    t.assert_equal(calculate_runup(10.00, 10.00), 0.0, "runup_no_change")
    t.assert_equal(calculate_runup(9.00, 10.00), -10.0, "runup_down_10pct")
    t.assert_equal(calculate_runup(20.00, 10.00), 100.0, "runup_doubled")
    
    # Edge cases
    t.assert_equal(calculate_runup(10, 0), 0.0, "runup_zero_open")
    t.assert_equal(calculate_runup(10, None), 0.0, "runup_none_open")
    t.assert_equal(calculate_runup(None, 10), 0.0, "runup_none_price")


# ═══════════════════════════════════════════════════════════════════════
# ATRX Tests
# ═══════════════════════════════════════════════════════════════════════

def test_atrx(t):
    """Test calculate_atrx - returns RATIO, not percentage."""
    print("\n🧪 Testing calculate_atrx()...")
    
    # Normal cases
    t.assert_equal(calculate_atrx(10.0, 8.0, 1.0), 2.0, "atrx_normal_2x")
    t.assert_equal(calculate_atrx(5.0, 3.0, 1.0), 2.0, "atrx_same_range_2x")
    t.assert_equal(calculate_atrx(10.0, 9.0, 1.0), 1.0, "atrx_matches_average")
    t.assert_equal(calculate_atrx(5.0, 5.0, 1.0), 0.0, "atrx_no_range")
    
    # Edge cases
    t.assert_equal(calculate_atrx(10.0, 8.0, 0), 0.0, "atrx_zero_atr")
    t.assert_equal(calculate_atrx(None, 8.0, 1.0), 0.0, "atrx_none_high")
    t.assert_equal(calculate_atrx(10.0, None, 1.0), 0.0, "atrx_none_low")


# ═══════════════════════════════════════════════════════════════════════
# Validate ATRX Tests (yfinance bug detection)
# ═══════════════════════════════════════════════════════════════════════

def test_validate_atrx(t):
    """Test ATRX validation for bad yfinance data."""
    print("\n🧪 Testing validate_atrx()...")
    
    # Normal cases - should pass through unchanged
    t.assert_equal(validate_atrx(3.0, 0.5, 10), 3.0, "validate_normal_atrx")
    t.assert_equal(validate_atrx(1.5, 0.3, 10), 1.5, "validate_low_atrx")
    t.assert_equal(validate_atrx(5.0, 1.0, 10), 5.0, "validate_high_but_valid")
    
    # Bad data patterns - should return 0
    t.assert_equal(
        validate_atrx(25.0, 0.02, 10),  # ATR 0.2% of price + ATRX 25
        0.0,
        "validate_yfinance_bug_detected"
    )
    
    t.assert_equal(
        validate_atrx(50.0, 0.01, 10),  # ATR 0.1% of price + ATRX 50
        0.0,
        "validate_yfinance_bug_extreme"
    )
    
    # Edge cases - low ATR but reasonable ATRX → OK
    t.assert_equal(
        validate_atrx(2.0, 0.01, 10),  # Low ATR but ATRX not too high
        2.0,
        "validate_low_atr_low_atrx_ok"
    )
    
    t.assert_equal(validate_atrx(None, 1.0, 10), 0.0, "validate_none_atrx")
    t.assert_equal(validate_atrx(3.0, 1.0, 0), 0.0, "validate_zero_price")


# ═══════════════════════════════════════════════════════════════════════
# Gap Tests
# ═══════════════════════════════════════════════════════════════════════

def test_gap(t):
    """Test calculate_gap."""
    print("\n🧪 Testing calculate_gap()...")
    
    # Normal cases
    t.assert_equal(calculate_gap(12.0, 10.0), 20.0, "gap_up_20pct")
    t.assert_equal(calculate_gap(10.0, 10.0), 0.0, "gap_no_change")
    t.assert_equal(calculate_gap(8.0, 10.0), -20.0, "gap_down_20pct")
    t.assert_equal(calculate_gap(15.0, 10.0), 50.0, "gap_up_50pct")
    
    # Edge cases
    t.assert_equal(calculate_gap(10, 0), 0.0, "gap_zero_prev_close")
    t.assert_equal(calculate_gap(10, None), 0.0, "gap_none_prev_close")


# ═══════════════════════════════════════════════════════════════════════
# VWAP Dist Tests
# ═══════════════════════════════════════════════════════════════════════

def test_vwap_dist(t):
    """Test calculate_vwap_dist (actually Typical Price)."""
    print("\n🧪 Testing calculate_vwap_dist()...")
    
    # Normal cases
    # typical = (12+9+11)/3 = 10.67, price = 11 → (11/10.67 - 1)*100 = 3.125
    t.assert_equal(
        calculate_vwap_dist(11.0, 12.0, 9.0),
        3.125,
        "vwap_dist_above_typical"
    )
    
    # typical = (12+8+10)/3 = 10, price = 10 → 0
    t.assert_equal(
        calculate_vwap_dist(10.0, 12.0, 8.0),
        0.0,
        "vwap_dist_at_typical"
    )
    
    # Edge cases
    t.assert_equal(calculate_vwap_dist(None, 10, 8), 0.0, "vwap_none_price")
    t.assert_equal(calculate_vwap_dist(10, None, 8), 0.0, "vwap_none_high")
    t.assert_equal(calculate_vwap_dist(0, 0, 0), 0.0, "vwap_all_zero")


# ═══════════════════════════════════════════════════════════════════════
# REL_VOL Tests (most critical - has cap)
# ═══════════════════════════════════════════════════════════════════════

def test_rel_vol(t):
    """Test calculate_rel_vol - critical for preventing yfinance outliers."""
    print("\n🧪 Testing calculate_rel_vol()...")
    
    # Normal cases
    t.assert_equal(calculate_rel_vol(1_000_000, 500_000), 2.0, "rel_vol_2x_normal")
    t.assert_equal(calculate_rel_vol(500_000, 500_000), 1.0, "rel_vol_exact_avg")
    t.assert_equal(calculate_rel_vol(100_000, 500_000), 0.2, "rel_vol_below_avg")
    t.assert_equal(calculate_rel_vol(5_000_000, 500_000), 10.0, "rel_vol_10x")
    
    # Cap logic (critical!)
    t.assert_equal(
        calculate_rel_vol(50_000_000, 500_000),  # Would be 100 exactly
        100.0,
        "rel_vol_exactly_at_cap"
    )
    
    t.assert_equal(
        calculate_rel_vol(5_000_000_000, 10_000),  # Would be 500,000
        REL_VOL_CAP,
        "rel_vol_capped_from_extreme"
    )
    
    t.assert_equal(
        calculate_rel_vol(1_000_000_000, 100),  # Would be 10M
        REL_VOL_CAP,
        "rel_vol_capped_yfinance_bug"
    )
    
    # Edge cases
    t.assert_equal(calculate_rel_vol(1_000_000, 0), 1.0, "rel_vol_zero_avg")
    t.assert_equal(calculate_rel_vol(1_000_000, None), 1.0, "rel_vol_none_avg")
    t.assert_equal(calculate_rel_vol(None, 500_000), 1.0, "rel_vol_none_volume")


# ═══════════════════════════════════════════════════════════════════════
# Float% Tests (formula was wrong in dashboard - critical to test!)
# ═══════════════════════════════════════════════════════════════════════

def test_float_pct(t):
    """Test calculate_float_pct - MUST be FloatShares/SharesOut, not Volume/SharesOut."""
    print("\n🧪 Testing calculate_float_pct()...")
    
    # Normal cases
    t.assert_equal(
        calculate_float_pct(8_000_000, 10_000_000),
        80.0,
        "float_normal_80pct"
    )
    
    t.assert_equal(
        calculate_float_pct(2_000_000, 10_000_000),
        20.0,
        "float_low_20pct"
    )
    
    t.assert_equal(
        calculate_float_pct(10_000_000, 10_000_000),
        100.0,
        "float_full_100pct"
    )
    
    # Edge cases
    t.assert_equal(calculate_float_pct(0, 10_000_000), 0.0, "float_zero_float")
    t.assert_equal(calculate_float_pct(5_000_000, 0), 0.0, "float_zero_shares")
    t.assert_equal(calculate_float_pct(None, 10_000_000), 0.0, "float_none_float")
    t.assert_equal(calculate_float_pct(5_000_000, None), 0.0, "float_none_shares")


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests (real-world scenarios)
# ═══════════════════════════════════════════════════════════════════════

def test_real_world_scenarios(t):
    """Test combinations mirroring real pump/normal stocks."""
    print("\n🧪 Testing real-world scenarios...")
    
    # Scenario 1: Normal micro-cap pump
    # Stock: MC=$50M, Price=$3.50, Vol=100M, Open=$2.00
    mxv = calculate_mxv(50_000_000, 3.50, 100_000_000)
    # P×V = 350M, MC = 50M → (50-350)/50 × 100 = -600
    t.assert_equal(mxv, -600.0, "scenario_micro_pump_mxv")
    
    runup = calculate_runup(3.50, 2.00)
    t.assert_equal(runup, 75.0, "scenario_micro_pump_runup")
    
    # Scenario 2: Large cap normal day
    # Stock: MC=$10B, Price=$100, Vol=5M
    mxv = calculate_mxv(10_000_000_000, 100, 5_000_000)
    # P×V = 500M, MC = 10B → (10000-500)/10000 × 100 = 95
    t.assert_equal(mxv, 95.0, "scenario_large_cap_quiet")
    
    # Scenario 3: yfinance outlier protection
    # Bad avg_volume of 100, real volume 1M
    rv = calculate_rel_vol(1_000_000, 100)
    # Would be 10,000 without cap → should cap at 100
    t.assert_equal(rv, 100.0, "scenario_yfinance_outlier_protected")


# ═══════════════════════════════════════════════════════════════════════
# Main Test Runner
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("🧪 RidingHigh Pro - Formula Unit Tests")
    print("=" * 60)
    
    t = TestResult()
    
    # Run all test groups
    test_mxv(t)
    test_runup(t)
    test_atrx(t)
    test_validate_atrx(t)
    test_gap(t)
    test_vwap_dist(t)
    test_rel_vol(t)
    test_float_pct(t)
    test_real_world_scenarios(t)
    
    # Final summary
    success = t.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
