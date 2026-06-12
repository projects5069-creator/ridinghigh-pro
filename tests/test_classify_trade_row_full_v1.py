"""TASK-162 — classify_trade_row_full returns (cls, resolution_day) so the
expectancy surface can get the day. classify_trade_row keeps its string contract
(delegates to _full). Same gap-down fixture as the 142 suite: WIN on ScanPrice,
LOSS on D1_Open."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import classify_trade_row, classify_trade_row_full


def _row(**over):
    base = {
        "ScanPrice": 10.0, "D1_Open": 8.5,
        "D1_High": 9.5, "D1_Low": 8.9,
        "D2_High": 9.0, "D2_Low": 8.0, "D3_High": 9.0, "D3_Low": 8.0,
        "D4_High": 9.0, "D4_Low": 8.0, "D5_High": 9.0, "D5_Low": 8.0,
    }
    base.update(over)
    return base


def test_full_scanprice_returns_cls_and_day():
    assert classify_trade_row_full(_row()) == ("WIN", 1)


def test_full_d1open_returns_cls_and_day():
    assert classify_trade_row_full(_row(), entry_basis="D1_Open") == ("LOSS", 1)


def test_full_missing_d1open_is_pending_tuple():
    assert classify_trade_row_full(_row(D1_Open=None), entry_basis="D1_Open") == ("PENDING", None)
    assert classify_trade_row_full(_row(D1_Open=0), entry_basis="D1_Open") == ("PENDING", None)


def test_row_string_contract_preserved():
    # classify_trade_row still returns the bare cls string (dashboard callers unbroken)
    assert classify_trade_row(_row()) == "WIN"
    assert classify_trade_row(_row(), entry_basis="D1_Open") == "LOSS"
    assert classify_trade_row(_row(D1_Open=None), entry_basis="D1_Open") == "PENDING"
