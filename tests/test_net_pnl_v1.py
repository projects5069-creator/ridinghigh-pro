"""Unit tests for formulas.calculate_net_pnl — TASK-140 net-PnL cost model.

Written test-first (RED) before the function exists. Pure-function tests only:
calculate_net_pnl(scan_price, classification, resolution_day, borrow_annual_rate, slip)
returns a net PnL FRACTION (short-side), per the phase6 cost model:

    fill  = scan * (1 - slip)                                  # short entry, adverse
    exit  = scan * (1 - TP_FRAC) if WIN else scan * (1 + SL_FRAC)
    cover = exit * (1 + slip)                                  # cover, adverse
    gross = (fill - cover) / fill
    bcost = borrow_annual_rate * resolution_day / 365.0
    net   = gross - bcost

Expected values below are hand-derived with slip=0.01, TP_FRAC=SL_FRAC=0.10.
(Aggregate reproduction of phase6 seed=42 expectancy +1.21% / +1.06/+0.59/-0.34%
 is an INTEGRATION test over the full dataset — out of this pure-fn unit scope.)
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formulas import calculate_net_pnl

SLIP = 0.01


# ───────────────────────── WIN — slip only (borrow=0) ─────────────────────────

def test_win_slip_only_matches_model():
    """WIN, slip 1%/side, no borrow → (0.99 - 0.909)/0.99 = +0.0818182 fraction."""
    net = calculate_net_pnl(100.0, "WIN", resolution_day=2, borrow_annual_rate=0.0, slip=SLIP)
    assert net == pytest.approx(0.0818182, rel=1e-4)


def test_net_is_fraction_independent_of_scan_price():
    """Net PnL is a ratio — same for any scan_price."""
    a = calculate_net_pnl(10.0, "WIN", resolution_day=2, borrow_annual_rate=0.0, slip=SLIP)
    b = calculate_net_pnl(250.0, "WIN", resolution_day=2, borrow_annual_rate=0.0, slip=SLIP)
    assert a == pytest.approx(b, rel=1e-9)


# ───────────────────────── LOSS ─────────────────────────

def test_loss_slip_only_is_negative():
    """LOSS, slip 1%/side, no borrow → (0.99 - 1.111)/0.99 = -0.122222 fraction."""
    net = calculate_net_pnl(100.0, "LOSS", resolution_day=2, borrow_annual_rate=0.0, slip=SLIP)
    assert net == pytest.approx(-0.122222, rel=1e-4)
    assert net < 0


# ───────────────────────── WIN + borrow scenarios (days=2) ─────────────────────────

@pytest.mark.parametrize("rate,expected", [
    (0.50, 0.0818182 - 0.50 * 2 / 365.0),   # +0.0790785
    (2.00, 0.0818182 - 2.00 * 2 / 365.0),   # +0.0708593
    (5.00, 0.0818182 - 5.00 * 2 / 365.0),   # +0.0544209
])
def test_win_borrow_scenarios(rate, expected):
    """net = gross - borrow_annual_rate * days/365 (pro-rata)."""
    net = calculate_net_pnl(100.0, "WIN", resolution_day=2, borrow_annual_rate=rate, slip=SLIP)
    assert net == pytest.approx(expected, rel=1e-4)


def test_borrow_cost_scales_with_days():
    """Holding longer costs more borrow → lower net (same rate)."""
    short = calculate_net_pnl(100.0, "WIN", resolution_day=1, borrow_annual_rate=5.0, slip=SLIP)
    long_ = calculate_net_pnl(100.0, "WIN", resolution_day=5, borrow_annual_rate=5.0, slip=SLIP)
    assert long_ < short
    # exact gap = 5.0 * (5-1)/365
    assert (short - long_) == pytest.approx(5.0 * 4 / 365.0, rel=1e-6)


# ───────────────────────── non-WIN/LOSS → NULL ─────────────────────────

@pytest.mark.parametrize("cls", ["WHIPSAW", "NO_TOUCH", "PENDING"])
def test_non_winloss_returns_none(cls):
    """Only WIN/LOSS are computable; everything else → None (NULL cell)."""
    net = calculate_net_pnl(100.0, cls, resolution_day=2, borrow_annual_rate=0.50, slip=SLIP)
    assert net is None
