"""TASK-208-B — borrow scanned-universe must select by MxV, not the frozen Score.

RED: in the scoreless era (SCORE_WRITE_FROZEN) daily_snapshots.Score is blank "",
so get_scanned_universe(df, min_score) coerces "" -> NaN -> NaN>=min_score is False
-> empty set. orchestrator_eod.py:58/66 reads daily_snapshots, so the LIVE borrow
universe loses every scanned candidate (only existing positions remain) — a silent
TASK-172 coverage gap. Selection must use MxV (kept in daily_snapshots) <= AGENT_MXV_MAX.

Hermetic: pure function, no I/O.
"""
import importlib

import pandas as pd

bc = importlib.import_module("agent.perception.borrow_collector")


def _scoreless_df():
    """daily_snapshots-shaped frame in the scoreless era: Score blank, MxV numeric."""
    return pd.DataFrame({
        "Ticker": ["AAA", "BBB", "CCC"],
        "Score":  ["",    "",    ""],      # frozen — SCORE_WRITE_FROZEN
        "MxV":    [-150,  -50,   -200],     # AAA/CCC <= -100 ; BBB does not qualify
    })


def test_scanned_universe_selects_by_mxv_not_frozen_score():
    universe = bc.get_scanned_universe(_scoreless_df())
    assert universe == {"AAA", "CCC"}, (
        f"scoreless-era universe must select by MxV<=-100, not blank Score; got {universe}"
    )
