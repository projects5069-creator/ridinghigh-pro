"""TASK-200 — post_analysis collection universe = MxV<=AGENT_MXV_MAX, NOT Score>=60.

In the scoreless era (SCORE_WRITE_FROZEN), daily_snapshots.Score is blank, so the
old Score>=60 filter (post_analysis_collector:429) collects ~nothing. עמיחי trades
on MxV<=-100, so the collection universe must be metric-based on MxV.

CRITICAL (feeds TASK-128): selection is MxV-only. The supporting metrics
TPD / REL_VOL / Float% are kept as columns but MUST NOT filter here — filtering
would bias 128's validation set. A deep-MxV row with weak supporting metrics is
still selected.

RED (before): select_candidates does not exist (ImportError).
GREEN (after): MxV-based pure selector.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

import pandas as pd
from config import AGENT_MXV_MAX
from post_analysis_collector import select_candidates


def _df():
    # MxV as strings to mimic raw Sheets reads (selector must coerce numerically).
    return pd.DataFrame([
        {"Ticker": "A", "MxV": "-150", "Score": "",   "TypicalPriceDist": "8",  "REL_VOL": "20", "Float%": "70"},
        {"Ticker": "B", "MxV": "-200", "Score": "75",  "TypicalPriceDist": "6",  "REL_VOL": "18", "Float%": "65"},
        {"Ticker": "C", "MxV": "-50",  "Score": "",    "TypicalPriceDist": "9",  "REL_VOL": "30", "Float%": "80"},
        {"Ticker": "D", "MxV": "-300", "Score": "",    "TypicalPriceDist": "0",  "REL_VOL": "1",  "Float%": "5"},
        {"Ticker": "E", "MxV": "-30",  "Score": "90",  "TypicalPriceDist": "7",  "REL_VOL": "25", "Float%": "60"},
    ])


def test_selects_deep_mxv_with_blank_score():
    # Core transition: deep MxV + blank Score (frozen era) — excluded by Score>=60, now selected.
    out = select_candidates(_df())
    assert "A" in set(out["Ticker"])


def test_selects_deep_mxv_regardless_of_score_presence():
    # MxV<=-100 selected whether Score is numeric (B) or blank (A).
    out = set(select_candidates(_df())["Ticker"])
    assert {"A", "B"}.issubset(out)


def test_rejects_shallow_mxv():
    # MxV>-100 is outside the universe even with blank Score (C).
    out = set(select_candidates(_df())["Ticker"])
    assert "C" not in out


def test_high_score_shallow_mxv_not_selected():
    # Proves Score no longer drives selection: E has Score=90 but MxV=-30 -> excluded.
    out = set(select_candidates(_df())["Ticker"])
    assert "E" not in out


def test_weak_supporting_metrics_still_selected():
    # PRESERVATION (feeds 128): deep MxV with weak TPD/REL_VOL/Float% (D) is STILL selected.
    out = set(select_candidates(_df())["Ticker"])
    assert "D" in out


def test_exact_universe():
    out = set(select_candidates(_df())["Ticker"])
    assert out == {"A", "B", "D"}


def test_boundary_uses_config_constant():
    # Boundary at AGENT_MXV_MAX (-100): exactly -100 is in (<=), -99.99 is out.
    df = pd.DataFrame([
        {"Ticker": "AT", "MxV": str(AGENT_MXV_MAX),       "Score": ""},
        {"Ticker": "JUST_OUT", "MxV": str(AGENT_MXV_MAX + 0.01), "Score": ""},
    ])
    out = set(select_candidates(df)["Ticker"])
    assert "AT" in out and "JUST_OUT" not in out
