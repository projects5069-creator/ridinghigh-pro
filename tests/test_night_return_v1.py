"""TASK-204 — night_return as the trader-convention sign-flip of D1_Gap%.

D1_Gap% = (D1_Open - ScanPrice)/ScanPrice*100 (calculate_d1_gap, formulas.py).
night_return = (ScanPrice - D1_Open)/ScanPrice*100 = the overnight DROP, where a
favorable short move (gap down) is POSITIVE. It is exactly -D1_Gap%.

SSoT (§10): night_return is DERIVED from the single existing calculator
(calculate_d1_gap) via a sign flip — NOT a second formula. The collector passes
the already-computed D1_Gap% (None when D1 not yet available) to night_return_from_gap.

CRITICAL: None (no D1 yet) must stay None — distinct from a real 0 move.

RED (before): night_return_from_gap does not exist (ImportError).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

from formulas import night_return_from_gap


def test_gap_down_is_positive_night_return():
    # Favorable overnight drop for a short: D1_Gap% -19 -> night_return +19.
    assert night_return_from_gap(-19.0) == 19.0


def test_gap_up_is_negative_night_return():
    assert night_return_from_gap(5.0) == -5.0


def test_missing_d1_stays_none():
    # No D1 yet -> None (NOT 0). Distinguishes "unknown" from "zero move".
    assert night_return_from_gap(None) is None


def test_nan_becomes_none():
    assert night_return_from_gap(float("nan")) is None


def test_real_zero_move_is_zero_not_none():
    # A genuine 0% overnight move must be 0.0, NOT None.
    assert night_return_from_gap(0.0) == 0.0
    assert night_return_from_gap(0.0) is not None
