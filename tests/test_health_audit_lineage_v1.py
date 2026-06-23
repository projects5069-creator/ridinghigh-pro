"""test_health_audit_lineage_v1.py — TASK-166 (lineage sentinel)
Unit tests for the PURE lineage-drift logic in health_audit:
  _field_drift, _row_is_settled, _build_ohlc, _lineage_compare_result.
All deterministic — no Sheets, no randomness (row selection + I/O live in the
gc wrapper check_30_lineage_sentinel, which is exercised only live, matching
the established health_audit test pattern).

  uv run --with-requirements requirements.txt python3 tests/test_health_audit_lineage_v1.py
Exit 0 if all pass, 1 otherwise.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

from health_audit import (
    _field_drift,
    _row_is_settled,
    _build_ohlc,
    _lineage_compare_result,
    _LINEAGE_FIELDS,
    WARNING,
    PASSED,
)
from utils import calculate_stats

# A settled 5-day OHLC (full D1-D5) + scan price. min_low=87 (D5) => ~13% drop => a WIN
# with non-None NetPnL_* fields, so blank-vs-value drift is exercisable.
_SCAN_PRICE = 100.0
_OHLC = {
    "D1_Open": 98.0, "D1_High": 101.0, "D1_Low": 95.0, "D1_Close": 96.0,
    "D2_Open": 96.0, "D2_High": 99.0,  "D2_Low": 90.0, "D2_Close": 92.0,
    "D3_Open": 92.0, "D3_High": 94.0,  "D3_Low": 88.0, "D3_Close": 90.0,
    "D4_Open": 90.0, "D4_High": 92.0,  "D4_Low": 89.0, "D4_Close": 91.0,
    "D5_Open": 91.0, "D5_High": 93.0,  "D5_Low": 87.0, "D5_Close": 88.0,
}


def _good_stored():
    """The canonical stored dict == fresh SSoT recompute, restricted to compared fields."""
    fresh = calculate_stats(_SCAN_PRICE, _OHLC)
    return {f: fresh[f] for f in _LINEAGE_FIELDS}


# ---- _field_drift -----------------------------------------------------------

def test_field_drift_none_vs_none_false():
    assert _field_drift(None, None) is False


def test_field_drift_nan_vs_none_false():
    assert _field_drift(float("nan"), None) is False


def test_field_drift_within_tolerance_false():
    assert _field_drift(1.0, 1.005) is False


def test_field_drift_over_tolerance_true():
    assert _field_drift(1.0, 1.02) is True


def test_field_drift_blank_vs_value_true():
    assert _field_drift("", 5.0) is True


# ---- _row_is_settled --------------------------------------------------------

def test_row_settled_full_true():
    assert _row_is_settled(dict(_OHLC)) is True


def test_row_settled_missing_one_low_false():
    row = dict(_OHLC)
    del row["D3_Low"]
    assert _row_is_settled(row) is False


def test_row_settled_empty_false():
    assert _row_is_settled({}) is False


# ---- _build_ohlc ------------------------------------------------------------

def test_build_ohlc_only_d1_d5_keys():
    row = dict(_OHLC)
    row["D6_Close"] = 80.0  # forward-only — must be ignored
    row["D25_Low"] = 70.0
    ohlc = _build_ohlc(row)
    assert len(ohlc) == 20
    assert "D6_Close" not in ohlc and "D25_Low" not in ohlc
    assert ohlc["D1_Open"] == 98.0


# ---- _lineage_compare_result ------------------------------------------------

def test_exact_match_passed():
    r = _lineage_compare_result("AAPL", "2026-06-10", _SCAN_PRICE, _OHLC, _good_stored())
    assert r.status == PASSED


def test_single_field_drift_warning():
    stored = _good_stored()
    stored["MaxDrop%"] = stored["MaxDrop%"] + 5
    r = _lineage_compare_result("AAPL", "2026-06-10", _SCAN_PRICE, _OHLC, stored)
    assert r.status == WARNING
    assert "MaxDrop%" in r.message


def test_multi_field_drift_warning():
    stored = _good_stored()
    stored["TP10_Hit"] = 0 if stored["TP10_Hit"] else 1
    stored["NetPnL_Borrow200"] = stored["NetPnL_Borrow200"] + 1.0
    r = _lineage_compare_result("AAPL", "2026-06-10", _SCAN_PRICE, _OHLC, stored)
    assert r.status == WARNING
    assert "TP10_Hit" in r.message and "NetPnL_Borrow200" in r.message
    assert "2 field" in r.message


def test_within_tolerance_passed():
    stored = _good_stored()
    stored["MaxDrop%"] = stored["MaxDrop%"] + 0.004
    r = _lineage_compare_result("AAPL", "2026-06-10", _SCAN_PRICE, _OHLC, stored)
    assert r.status == PASSED


def test_just_over_tolerance_warning():
    stored = _good_stored()
    stored["MaxDrop%"] = stored["MaxDrop%"] + 0.02
    r = _lineage_compare_result("AAPL", "2026-06-10", _SCAN_PRICE, _OHLC, stored)
    assert r.status == WARNING


def test_blank_vs_value_warning():
    stored = _good_stored()
    assert not _is_blank_marker(stored["NetPnL_Borrow50"])  # fixture sanity: fresh has a value
    stored["NetPnL_Borrow50"] = ""  # corrupt stored to blank
    r = _lineage_compare_result("AAPL", "2026-06-10", _SCAN_PRICE, _OHLC, stored)
    assert r.status == WARNING
    assert "NetPnL_Borrow50" in r.message


def test_none_vs_none_field_not_flagged():
    # D1_Open falsy => fresh D1_Gap% is None; stored blank => must NOT count as drift.
    ohlc = dict(_OHLC)
    ohlc["D1_Open"] = 0
    fresh = calculate_stats(_SCAN_PRICE, ohlc)
    assert fresh["D1_Gap%"] is None  # precondition
    stored = {f: fresh[f] for f in _LINEAGE_FIELDS}
    stored["D1_Gap%"] = ""  # blank on the stored side too
    r = _lineage_compare_result("AAPL", "2026-06-10", _SCAN_PRICE, ohlc, stored)
    assert r.status == PASSED


def test_message_contains_ticker_and_date():
    stored = _good_stored()
    stored["MaxDrop%"] = stored["MaxDrop%"] + 5
    r = _lineage_compare_result("TSLA", "2026-05-21", _SCAN_PRICE, _OHLC, stored)
    assert "TSLA" in r.message and "2026-05-21" in r.message


def _is_blank_marker(v):
    """Local helper for fixture sanity only (mirrors the no-value notion)."""
    if v is None:
        return True
    try:
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return str(v).strip() == ""


def main():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {type(e).__name__} - {e}")
            failed += 1
    print("=" * 60)
    print(f"Results: {passed}/{passed + failed} passed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
