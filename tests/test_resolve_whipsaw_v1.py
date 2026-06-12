"""TASK-155 Phase 2 — pure WHIPSAW resolver.

A daily WHIPSAW proves BOTH TP and SL were hit that day. The minute bars resolve
it ONLY if they capture BOTH in separate bars (earlier one decides). One side only
(other extreme not on the IEX feed), same-bar both, or neither -> UNRESOLVED — never
a guessed verdict. Same SSoT thresholds as classify_trade. entry=10 -> tp=9, sl=11.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import resolve_whipsaw


def _bars(rows):
    """rows: list of (low, high) in time order."""
    idx = pd.to_datetime([f"2026-05-13 13:{30 + i:02d}:00" for i in range(len(rows))], utc=True)
    return pd.DataFrame(
        {"low": [r[0] for r in rows], "high": [r[1] for r in rows],
         "open": [r[0] for r in rows], "close": [r[0] for r in rows],
         "volume": [1.0] * len(rows)},
        index=idx,
    )


def test_tp_before_sl_is_win():
    # bar1 TP-only (13:31), bar2 SL (13:32) -> TP first -> WIN
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (8.9, 10.5), (9.5, 11.2)])) == "WIN"


def test_sl_before_tp_is_loss():
    # bar1 SL-only (13:31), bar2 TP (13:32) -> SL first -> LOSS
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (9.5, 11.2), (8.9, 10.0)])) == "LOSS"


def test_same_bar_both_unresolved():
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (8.9, 11.1)])) == "UNRESOLVED"


def test_only_tp_visible_unresolved():
    # daily said both touched, but minutes show only TP -> SL hidden -> UNRESOLVED
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (8.9, 10.4), (8.5, 10.2)])) == "UNRESOLVED"


def test_only_sl_visible_unresolved():
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (9.4, 11.2), (9.6, 11.5)])) == "UNRESOLVED"


def test_neither_unresolved():
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (9.6, 10.4)])) == "UNRESOLVED"


def test_empty_unresolved():
    assert resolve_whipsaw(10.0, pd.DataFrame(columns=["low", "high"])) == "UNRESOLVED"


def test_invalid_entry_unresolved():
    assert resolve_whipsaw(0, _bars([(8.0, 12.0)])) == "UNRESOLVED"
    assert resolve_whipsaw(None, _bars([(8.0, 12.0)])) == "UNRESOLVED"


def test_out_of_order_bars_sorted_by_time():
    # SL bar (13:31) chronologically precedes TP bar (13:32); rows arrive shuffled.
    df = _bars([(9.5, 10.5), (9.5, 11.2), (8.5, 10.0)])      # 13:30 none, 13:31 SL, 13:32 TP
    shuffled = df.iloc[[2, 0, 1]]
    assert resolve_whipsaw(10.0, shuffled) == "LOSS"
