"""TASK-169 AC#1 — Wilson 95% score confidence interval (pure, tested).

A binomial proportion CI that stays valid at small n (unlike normal-approx),
so rates like WR n=26 are never shown as precise. Pure scalar -> lives in
formulas.py (pandas-free). AC#2 (render in dashboard + emails) is separate.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formulas import wilson_ci


def test_50_of_100_known_value():
    # Wilson(50,100) is a textbook value ~ (0.404, 0.596)
    lo, hi = wilson_ci(50, 100)
    assert lo == pytest.approx(0.4038, abs=0.001)
    assert hi == pytest.approx(0.5962, abs=0.001)


def test_small_n_is_wider_than_large_n():
    # same 50% rate, n=26 must give a WIDER band than n=200 (the whole point)
    lo_s, hi_s = wilson_ci(13, 26)
    lo_l, hi_l = wilson_ci(100, 200)
    assert (hi_s - lo_s) > (hi_l - lo_l)


def test_bounds_clamped_to_unit_interval():
    lo0, hi0 = wilson_ci(0, 10)      # all failures
    lo1, hi1 = wilson_ci(10, 10)     # all successes
    assert lo0 == 0.0 and hi0 > 0.0          # low clamped at 0
    assert hi1 == 1.0 and lo1 < 1.0          # high clamped at 1
    assert 0.0 <= lo0 <= hi0 <= 1.0
    assert 0.0 <= lo1 <= hi1 <= 1.0


def test_center_brackets_point_estimate():
    lo, hi = wilson_ci(30, 50)       # p = 0.60
    assert lo < 0.60 < hi


def test_zero_n_returns_full_uncertainty():
    assert wilson_ci(0, 0) == (0.0, 1.0)
    assert wilson_ci(5, 0) == (0.0, 1.0)     # defensive: n<=0
