"""TASK-155 Phase 2 — pure WHIPSAW resolver. Walks minute bars in time order:
first bar to touch TP (without same-bar SL) -> WIN; first to touch SL -> LOSS;
a single bar touching BOTH -> UNRESOLVED (sub-minute, IEX floor); never touching,
or empty/invalid -> UNRESOLVED. Same SSoT thresholds as classify_trade."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import resolve_whipsaw

# entry=10 -> tp=9.0, sl=11.0


def _bars(rows):
    """rows: list of (low, high) in time order."""
    idx = pd.to_datetime([f"2026-05-13 13:{30 + i:02d}:00" for i in range(len(rows))], utc=True)
    return pd.DataFrame(
        {"low": [r[0] for r in rows], "high": [r[1] for r in rows],
         "open": [r[0] for r in rows], "close": [r[0] for r in rows],
         "volume": [1.0] * len(rows)},
        index=idx,
    )


def test_tp_first_is_win():
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (8.9, 10.2), (8.0, 10.0)])) == "WIN"


def test_sl_first_is_loss():
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (9.2, 11.1), (8.0, 12.0)])) == "LOSS"


def test_same_bar_both_unresolved():
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (8.9, 11.1)])) == "UNRESOLVED"


def test_neither_unresolved():
    assert resolve_whipsaw(10.0, _bars([(9.5, 10.5), (9.6, 10.4)])) == "UNRESOLVED"


def test_empty_unresolved():
    assert resolve_whipsaw(10.0, pd.DataFrame(columns=["low", "high"])) == "UNRESOLVED"


def test_invalid_entry_unresolved():
    assert resolve_whipsaw(0, _bars([(1.0, 2.0)])) == "UNRESOLVED"
    assert resolve_whipsaw(None, _bars([(1.0, 2.0)])) == "UNRESOLVED"


def test_out_of_order_bars_sorted_by_time():
    # SL bar (13:31) is chronologically before the TP bar (13:32) -> LOSS even if
    # the rows arrive out of order.
    df = _bars([(9.5, 10.5), (9.5, 11.2), (8.5, 10.0)])      # bar1 13:30, bar2 13:31 SL-only, bar3 13:32 TP-only
    shuffled = df.iloc[[2, 0, 1]]                            # rows out of time order
    assert resolve_whipsaw(10.0, shuffled) == "LOSS"
