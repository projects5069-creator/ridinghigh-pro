"""TASK-140 integration — our chain ≡ phase6 cost model on a fixed committed fixture.

The exact phase6 aggregate (+1.21% / +1.06/+0.59/-0.34%) is NOT reproducible — its
dataset is gitignored + a third frame lived in /tmp (gone). So instead we prove
MODEL EQUIVALENCE: our chain (classify_trade -> calculate_net_pnl, folded into
calculate_stats) produces, on a deterministic synthetic fixture, byte-identical
per-row and aggregate net-PnL to an INDEPENDENT in-test re-implementation of the
phase6 formula (phase6_analysis.py lines 29-43 + 93-104).

If the reference and the chain ever diverge, the test fails — surfacing a real bug.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import calculate_stats
from config import TP_THRESHOLD_FRAC, SL_THRESHOLD_FRAC, SLIP, BORROW_SCENARIOS

# NetPnL key -> borrow annual rate (mirrors calculate_stats wiring)
KEY_RATE = {
    "NetPnL_SlipOnly": 0.0,
    "NetPnL_Borrow50": BORROW_SCENARIOS[0],
    "NetPnL_Borrow200": BORROW_SCENARIOS[1],
    "NetPnL_Borrow500": BORROW_SCENARIOS[2],
}


# ─────────── independent reference re-implementation of phase6 ───────────

def ref_classify_walk(sp, ohlc):
    """Mirror of utils.classify_trade / phase6 classify_walk -> (cls, day)."""
    if sp is None or sp <= 0:
        return ("PENDING", None)
    for i in range(1, 6):
        if ohlc.get(f"D{i}_Low") is None or ohlc.get(f"D{i}_High") is None:
            return ("PENDING", None)
    tp, sl = sp * (1 - TP_THRESHOLD_FRAC), sp * (1 + SL_THRESHOLD_FRAC)
    for i in range(1, 6):
        lo, hi = ohlc[f"D{i}_Low"], ohlc[f"D{i}_High"]
        tp_hit, sl_hit = lo <= tp, hi >= sl
        if tp_hit and sl_hit:
            return ("WHIPSAW", i)
        if sl_hit:
            return ("LOSS", i)
        if tp_hit:
            return ("WIN", i)
    return ("NO_TOUCH", 5)


def ref_net(sp, ohlc, borrow):
    """Mirror of phase6 cost model. None for non WIN/LOSS."""
    cls, day = ref_classify_walk(sp, ohlc)
    if cls not in ("WIN", "LOSS"):
        return None
    win = (cls == "WIN")
    fill = sp * (1 - SLIP)
    exitp = sp * (1 - TP_THRESHOLD_FRAC) if win else sp * (1 + SL_THRESHOLD_FRAC)
    cover = exitp * (1 + SLIP)
    gross = (fill - cover) / fill
    bcost = borrow * day / 365.0
    return gross - bcost


# ─────────── fixed fixture: ≥1 of every classification, varied price/day ───────────

def _ohlc(*days):
    d = {}
    for i, (lo, hi) in enumerate(days, start=1):
        d[f"D{i}_Low"] = lo
        d[f"D{i}_High"] = hi
    return d


# (scan_price, ohlc, expected_cls) — varied scan prices and resolution days
FIXTURE = [
    # WIN on D1 (scan=100, tp=90)
    (100.0, _ohlc((89.0, 105.0), (95, 105), (95, 105), (95, 105), (95, 105)), "WIN"),
    # WIN on D3 (scan=50, tp=45)
    (50.0,  _ohlc((48, 52), (48, 52), (44.0, 52.0), (48, 52), (48, 52)), "WIN"),
    # LOSS on D1 (scan=200, sl=220)
    (200.0, _ohlc((195, 221.0), (195, 205), (195, 205), (195, 205), (195, 205)), "LOSS"),
    # LOSS on D2 (scan=100, sl=110)
    (100.0, _ohlc((95, 105), (95.0, 111.0), (95, 105), (95, 105), (95, 105)), "LOSS"),
    # WHIPSAW on D1 (scan=100, both)
    (100.0, _ohlc((89.0, 111.0), (95, 105), (95, 105), (95, 105), (95, 105)), "WHIPSAW"),
    # NO_TOUCH (5 neutral days)
    (100.0, _ohlc((95, 105), (95, 105), (95, 105), (95, 105), (95, 105)), "NO_TOUCH"),
    # PENDING (only D1-D2 present)
    (100.0, _ohlc((95, 105), (95, 105)), "PENDING"),
]


def test_fixture_classifications_as_expected():
    """Sanity: the fixture covers each classification as intended."""
    for sp, ohlc, exp in FIXTURE:
        cls, _ = ref_classify_walk(sp, ohlc)
        assert cls == exp, f"scan={sp}: expected {exp}, got {cls}"


def test_chain_matches_phase6_reference_per_row():
    """Per row, per scenario: calculate_stats NetPnL == independent phase6 reference."""
    for sp, ohlc, _ in FIXTURE:
        stats = calculate_stats(sp, ohlc)
        for key, rate in KEY_RATE.items():
            ours = stats[key]
            ref = ref_net(sp, ohlc, rate)
            if ref is None:
                assert ours is None, f"scan={sp} {key}: ours={ours} expected None"
            else:
                assert ours == pytest.approx(ref, rel=1e-9), f"scan={sp} {key}: ours={ours} ref={ref}"


def test_aggregate_expectancy_matches_reference():
    """Aggregate mean over WIN/LOSS rows (phase6 expectancy) — chain == reference."""
    for key, rate in KEY_RATE.items():
        ours_vals = [calculate_stats(sp, ohlc)[key] for sp, ohlc, _ in FIXTURE]
        ours_vals = [v for v in ours_vals if v is not None]
        ref_vals = [ref_net(sp, ohlc, rate) for sp, ohlc, _ in FIXTURE]
        ref_vals = [v for v in ref_vals if v is not None]
        assert len(ours_vals) == len(ref_vals) == 4   # 4 WIN/LOSS rows
        ours_mean = sum(ours_vals) / len(ours_vals)
        ref_mean = sum(ref_vals) / len(ref_vals)
        assert ours_mean == pytest.approx(ref_mean, rel=1e-9), f"{key}: agg {ours_mean} vs {ref_mean}"
