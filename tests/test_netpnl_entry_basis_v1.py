"""TASK-147/162 plumbing note (TASK-142 context): calculate_net_pnl's PnL FRACTION
is scale-invariant to the entry price.

    gross = (fill - cover) / fill = 1 - (1∓frac)(1+slip)/(1-slip)

TP/SL are defined as fractions of the entry, so the entry cancels — the per-trade
net fraction is identical whether entry = ScanPrice or D1_Open. The D1_Open-vs-
ScanPrice EXPECTANCY difference is carried ENTIRELY by the (classification,
resolution_day) that classify_trade(entry_price=...) produces, NOT by this function.

These tests LOCK that invariance so no one adds a misleading `entry_price` param to
calculate_net_pnl later (it would look meaningful but change nothing). TASK-162 gets
the D1_Open expectancy by feeding D1_Open-based (cls, day) into this unchanged fn."""
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formulas import calculate_net_pnl


def test_fraction_invariant_to_entry_scale_win():
    # invariant up to floating-point: the entry cancels analytically, but the
    # intermediate products differ in magnitude so bit-exact == can round differently.
    assert calculate_net_pnl(10.0, "WIN", 1, 0.50) == pytest.approx(
        calculate_net_pnl(8.5, "WIN", 1, 0.50))


def test_fraction_invariant_to_entry_scale_loss():
    assert calculate_net_pnl(10.0, "LOSS", 3, 2.00) == pytest.approx(
        calculate_net_pnl(8.5, "LOSS", 3, 2.00))


def test_whipsaw_notouch_pending_return_none():
    for cls in ("WHIPSAW", "NO_TOUCH", "PENDING"):
        assert calculate_net_pnl(10.0, cls, 1, 0.50) is None
