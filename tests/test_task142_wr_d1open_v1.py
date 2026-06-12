"""TASK-142: official WR rebased on D1_Open entry. Core WIN/LOSS/WHIPSAW mapping
unchanged — only the entry BASIS is parametrized. Default path = byte-for-byte
backward compatible."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import classify_trade, classify_trade_row

# 5 settled days, gap-DOWN overnight — the executable entry is WORSE (the inflation
# TASK-142 corrects). scan=10 -> TP=9.0/SL=11.0: D1 low 8.9<=9.0 hits TP, D1 high
# 9.5<11.0 misses SL -> WIN(scan). D1_Open=8.5 -> TP=7.65/SL=9.35: D1 low 8.9>7.65
# misses TP, D1 high 9.5>=9.35 hits SL -> LOSS(D1_Open). Same row flips WIN->LOSS.
GAP_OHLC = {
    "D1_Open": 8.5, "D1_High": 9.5, "D1_Low": 8.9,
    "D2_High": 9.0, "D2_Low": 8.0, "D3_High": 9.0, "D3_Low": 8.0,
    "D4_High": 9.0, "D4_Low": 8.0, "D5_High": 9.0, "D5_Low": 8.0,
}


def test_default_entry_is_scanprice_backward_compatible():
    assert classify_trade(10.0, GAP_OHLC) == ("WIN", 1)


def test_entry_price_override_changes_outcome():
    assert classify_trade(10.0, GAP_OHLC, entry_price=8.5) == ("LOSS", 1)


def test_entry_price_none_equals_scanprice():
    assert classify_trade(10.0, GAP_OHLC, entry_price=None) == classify_trade(10.0, GAP_OHLC)


def test_invalid_entry_price_is_pending():
    assert classify_trade(10.0, GAP_OHLC, entry_price=0) == ("PENDING", None)
    assert classify_trade(10.0, GAP_OHLC, entry_price=-1) == ("PENDING", None)
