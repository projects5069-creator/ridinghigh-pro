"""TASK-46 — §10 dedup: dashboard _simulate_short_trades first-touch loop
delegates to utils.classify_trade with two opt-in params. These tests pin the
EXACT equivalence between the OLD dashboard inline verdict and
classify_trade(whipsaw_as_loss=True, resolve_on_available=True), so the
dashboard's pessimistic win-rate (whipsaws-as-losses, early-resolution) is
preserved to the digit.

Pin fixtures = the settled April/May post_analysis research CSVs (deterministic,
local, no live Sheets). The literal live win-rate (~55.8%) is data-dependent;
what these tests lock is the per-row classification equivalence that guarantees
it on any data.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TP_THRESHOLD_FRAC as TP, SL_THRESHOLD_FRAC as SL
from utils import classify_trade

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(_REPO, "docs", "research", "INVESTIGATION_2026-06-10")
APR = os.path.join(FIX, "post_analysis_2026-04.csv")
MAY = os.path.join(FIX, "post_analysis_2026-05.csv")


# ── reference: the OLD dashboard _simulate_short_trades inline verdict ──────
# Mirrors dashboard.py:_simulate_short_trades settled loop EXACTLY:
#   SL-before-TP, same-day both-touch -> SL (loss), first-touch early break.
def _old_dashboard_verdict(entry, row):
    if pd.isna(entry) or entry <= 0:
        return None  # excluded (Pending/No-Data) — not in win-rate
    tp10 = round(entry * (1 - TP), 4)
    sl_p = round(entry * (1 + SL), 4)
    for d in range(1, 6):
        hi = pd.to_numeric(row.get(f"D{d}_High"), errors="coerce")
        lo = pd.to_numeric(row.get(f"D{d}_Low"), errors="coerce")
        if pd.isna(hi) or pd.isna(lo):
            break
        sl_hit = hi >= sl_p
        tp_hit = lo <= tp10
        if sl_hit and tp_hit:
            return "SL"
        if sl_hit:
            return "SL"
        if tp_hit:
            return "TP10"
    return "OPEN"  # 5 days, never resolved — excluded from win-rate


def _ohlc_of(row):
    o = {}
    for d in range(1, 6):
        hi = pd.to_numeric(row.get(f"D{d}_High"), errors="coerce")
        lo = pd.to_numeric(row.get(f"D{d}_Low"), errors="coerce")
        o[f"D{d}_High"] = None if pd.isna(hi) else float(hi)
        o[f"D{d}_Low"] = None if pd.isna(lo) else float(lo)
    return o


# map classify_trade verdict -> dashboard win-rate category
_CAT = {"WIN": "TP10", "LOSS": "SL", "NO_TOUCH": "OPEN", "PENDING": None, "WHIPSAW": "WHIPSAW"}


def _ssot_verdict(entry, row):
    scan = pd.to_numeric(row.get("ScanPrice"), errors="coerce")
    scan = None if pd.isna(scan) else float(scan)
    e = None if (pd.isna(entry) or entry <= 0) else float(entry)
    cls, _day = classify_trade(scan, _ohlc_of(row), entry_price=e,
                               whipsaw_as_loss=True, resolve_on_available=True)
    return _CAT[cls]


def _wr(verdicts):
    wins = verdicts.count("TP10")
    losses = verdicts.count("SL")
    tot = wins + losses
    return wins, losses, (wins / tot * 100 if tot else 0.0)


# pinned from the OLD logic over the fixtures (captured 2026-06-22):
PIN = {
    (APR, "ScanPrice"): (76, 77),
    (APR, "D1_Open"):   (62, 90),
    (MAY, "ScanPrice"): (39, 38),
    (MAY, "D1_Open"):   (29, 47),
}


def _parity_for(path, basis):
    df = pd.read_csv(path)
    ref, ssot = [], []
    for _, row in df.iterrows():
        entry = pd.to_numeric(row.get(basis), errors="coerce")
        ref.append(_old_dashboard_verdict(entry, row))
        ssot.append(_ssot_verdict(entry, row))
    return df, ref, ssot


# ── #1 per-row parity + pinned win-rate over real fixtures ─────────────────
def test_fixture_parity_and_pinned_winrate():
    for path in (APR, MAY):
        for basis in ("ScanPrice", "D1_Open"):
            _df, ref, ssot = _parity_for(path, basis)
            # per-row equivalence on the win-rate-relevant verdicts (TP10/SL).
            # Non-closed rows (OPEN vs PENDING for partial/NO_DATA rows) are both
            # excluded from the win-rate and handled by the dashboard wrapper, so
            # normalize them to a single EXCLUDED token before comparing.
            norm = lambda v: v if v in ("TP10", "SL") else "EXCL"
            assert [norm(x) for x in ref] == [norm(x) for x in ssot], \
                f"closed-verdict mismatch {os.path.basename(path)} {basis}"
            # win-rate identical AND equal to the pinned reference digit
            rw, rl, rwr = _wr([c for c in ref if c in ("TP10", "SL")])
            sw, sl_, swr = _wr([c for c in ssot if c in ("TP10", "SL")])
            assert (rw, rl) == (sw, sl_)
            assert (sw, sl_) == PIN[(path, basis)], f"pin drift {os.path.basename(path)} {basis}"
            assert abs(swr - rwr) < 1e-9


# ── #2 resolve_on_available — partial-day cases (fixtures don't cover) ──────
def test_resolve_on_available_partial():
    entry = 10.0
    tp = 10.0 * (1 - TP)   # short TP = price drops
    sl = 10.0 * (1 + SL)   # short SL = price rises
    # (a) SL on D2, D3-5 absent -> LOSS@2 even though window incomplete
    ohlc = {"D1_High": 10.1, "D1_Low": 9.9, "D2_High": sl + 0.1, "D2_Low": 9.8}
    assert classify_trade(10.0, ohlc, resolve_on_available=True) == ("LOSS", 2)
    # (b) D1-D2 present, no touch -> PENDING (not enough to resolve, <5 present)
    ohlc_b = {"D1_High": 10.1, "D1_Low": 9.9, "D2_High": 10.2, "D2_Low": 9.8}
    assert classify_trade(10.0, ohlc_b, resolve_on_available=True) == ("PENDING", None)
    # (c) all 5 present, no touch -> NO_TOUCH
    ohlc_c = {f"D{d}_High": 10.2 for d in range(1, 6)}
    ohlc_c.update({f"D{d}_Low": 9.8 for d in range(1, 6)})
    assert classify_trade(10.0, ohlc_c, resolve_on_available=True) == ("NO_TOUCH", 5)


# ── #3 whipsaw mapping under the flag ──────────────────────────────────────
def test_whipsaw_flag():
    # D1 hits BOTH tp (low) and sl (high) -> whipsaw
    ohlc = {"D1_High": 10.0 * (1 + SL) + 0.1, "D1_Low": 10.0 * (1 - TP) - 0.1}
    for d in range(2, 6):
        ohlc[f"D{d}_High"] = 10.0
        ohlc[f"D{d}_Low"] = 10.0
    assert classify_trade(10.0, ohlc)[0] == "WHIPSAW"                         # canonical
    assert classify_trade(10.0, ohlc, whipsaw_as_loss=True)[0] == "LOSS"      # dashboard


# ── #4 canonical unchanged (defaults == current contract) ──────────────────
GAP_OHLC = {  # mirror tests/test_task142_wr_d1open_v1.py shape
    "D1_High": 10.0, "D1_Low": 8.9,  # low hits TP (10% drop) -> WIN@1 at entry 10
    "D2_High": 10.0, "D2_Low": 10.0, "D3_High": 10.0, "D3_Low": 10.0,
    "D4_High": 10.0, "D4_Low": 10.0, "D5_High": 10.0, "D5_Low": 10.0,
}


def test_canonical_defaults_unchanged():
    assert classify_trade(10.0, GAP_OHLC) == ("WIN", 1)
    # missing a day -> PENDING under canonical (require all 5)
    partial = {"D1_High": 10.0, "D1_Low": 9.9}
    assert classify_trade(10.0, partial) == ("PENDING", None)
