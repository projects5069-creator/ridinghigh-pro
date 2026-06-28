"""TASK-201 forward-only fix — sanity guard in calculate_float_pct.

Float% is float_shares / shares_outstanding * 100. A float (public float) can
NEVER exceed shares outstanding, so float_shares > shares_outstanding means the
fundamentals provider (yfinance) returned a garbage float_shares (orders of
magnitude too large). Without a guard the function emits an absurd percentage
(e.g. BDRX 2026-05-05: float_shares=275,358,405,220 vs shares_out=648,314 ->
42,472,860%), which propagated into daily_snapshots.Float% and post_analysis.

Forward-only fix (no backfill): when float_shares > shares_outstanding, treat
the input as invalid and return 0.0 — consistent with the function's existing
invalid-input convention (None/0 -> 0.0).

RED (before fix): the BDRX case returns ~42,472,860, so the <=100 / ==0.0
assertions fail. GREEN (after guard): returns 0.0.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (relocated to tests/)

from formulas import calculate_float_pct


def test_invalid_float_exceeds_shares_returns_zero():
    # Real corrupted row from the TASK-199 recon (BDRX 2026-05-05).
    # float can't exceed shares outstanding -> invalid input -> 0.0, never >100.
    result = calculate_float_pct(275_358_405_220, 648_314)
    assert result <= 100, f"Float% must be bounded <=100, got {result}"
    assert result == 0.0, f"invalid float_shares>shares_outstanding must yield 0.0, got {result}"


def test_valid_float_unchanged():
    # Legitimate input (float < shares outstanding) must compute normally.
    # Guard must NOT alter valid calculations.
    assert calculate_float_pct(8_000_000, 10_000_000) == 80.0


def test_boundary_float_equals_shares_returns_100():
    # float == shares outstanding is legitimate (100% float) and must NOT be clamped to 0.
    assert calculate_float_pct(10_000_000, 10_000_000) == 100.0
