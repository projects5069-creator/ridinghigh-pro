"""TASK-140 wiring step 1 — classify_trade returns (classification, resolution_day).

Written test-first (RED) before utils.py is changed. Option C:
  - classify_trade -> (cls, day)   [day = resolution D-day; NO_TOUCH=5; PENDING=None]
  - classify_trade_row -> still a STRING (unwraps [0]) so dashboard callers are unbroken.

scan_price=100 → tp_price=90 (scan*0.90), sl_price=110 (scan*1.10).
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import classify_trade, classify_trade_row


def _ohlc(*days):
    """days = list of (Low, High) for D1..; missing days left absent."""
    d = {}
    for i, (lo, hi) in enumerate(days, start=1):
        d[f"D{i}_Low"] = lo
        d[f"D{i}_High"] = hi
    return d


# 5 "neutral" days that never hit TP(90) or SL(110)
NEUTRAL = (95.0, 105.0)


# ───────────────── classify_trade now returns (cls, day) ─────────────────

def test_win_returns_cls_and_resolution_day():
    """TP hits on D2 (not D1) → ('WIN', 2)."""
    ohlc = _ohlc(NEUTRAL, (89.0, 105.0), NEUTRAL, NEUTRAL, NEUTRAL)
    assert classify_trade(100.0, ohlc) == ("WIN", 2)


def test_loss_returns_cls_and_resolution_day():
    """SL hits on D1 → ('LOSS', 1)."""
    ohlc = _ohlc((95.0, 111.0), NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL)
    assert classify_trade(100.0, ohlc) == ("LOSS", 1)


def test_whipsaw_returns_cls_and_resolution_day():
    """Same day hits BOTH TP and SL on D3 → ('WHIPSAW', 3)."""
    ohlc = _ohlc(NEUTRAL, NEUTRAL, (89.0, 111.0), NEUTRAL, NEUTRAL)
    assert classify_trade(100.0, ohlc) == ("WHIPSAW", 3)


def test_no_touch_returns_day_5():
    """5 days, never resolved → ('NO_TOUCH', 5)."""
    ohlc = _ohlc(NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL)
    assert classify_trade(100.0, ohlc) == ("NO_TOUCH", 5)


def test_pending_missing_ohlc_day_none():
    """Fewer than 5 days of OHLC → ('PENDING', None)."""
    ohlc = _ohlc(NEUTRAL, NEUTRAL)  # only D1-D2 present
    assert classify_trade(100.0, ohlc) == ("PENDING", None)


def test_pending_bad_scan_price_day_none():
    """scan_price <= 0 → ('PENDING', None)."""
    assert classify_trade(0.0, _ohlc(NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL, NEUTRAL)) == ("PENDING", None)


# ───────────────── classify_trade_row stays a STRING (dashboard unbroken) ─────────────────

def test_classify_trade_row_returns_string_not_tuple():
    """Adapter must still return the classification string only (dashboard callers)."""
    row = {"ScanPrice": "100.0",
           "D1_Low": "95", "D1_High": "105",
           "D2_Low": "89", "D2_High": "105",
           "D3_Low": "95", "D3_High": "105",
           "D4_Low": "95", "D4_High": "105",
           "D5_Low": "95", "D5_High": "105"}
    out = classify_trade_row(row)
    assert isinstance(out, str)
    assert out == "WIN"
