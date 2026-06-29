"""TASK-203 — guard Float% at the collector copy-path.

post_analysis_collector copies Float% as-is from daily_snapshots (metric_fields),
so values computed pre-TASK-201 from garbage float_shares (e.g. BDRX 42,473,000)
propagate into post_analysis. Float% is a percentage and must lie in (0, 100].
A pure helper clamp_float_pct() nulls any out-of-range/invalid value; the collector
applies it ONLY to Float% (other metric_fields untouched).

RED (before): clamp_float_pct does not exist (ImportError).
GREEN (after): out-of-range -> None; valid kept.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

from post_analysis_collector import clamp_float_pct


def test_corrupt_value_becomes_none():
    # Real corrupted row (BDRX 2026-05-05) — must NOT propagate.
    assert clamp_float_pct(42_473_000.0) is None


def test_boundary_100_kept():
    # 100% float is legitimate and must NOT be clamped.
    assert clamp_float_pct(100.0) == 100.0


def test_valid_value_unchanged():
    assert clamp_float_pct(67.8) == 67.8


def test_zero_and_negative_become_none():
    # (0,100]: 0 and negatives are invalid -> None.
    assert clamp_float_pct(0.0) is None
    assert clamp_float_pct(-5.0) is None


def test_none_and_nan_become_none():
    assert clamp_float_pct(None) is None
    assert clamp_float_pct(float("nan")) is None
