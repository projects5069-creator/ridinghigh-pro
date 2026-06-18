"""TDD Stage 0 — absence-safe Score writers (TASK-127.1, forward-only freeze).

RED: the warehouse writers still masquerade absence-of-Score as 0 / "v2". The
forward-only freeze must write "" + "v3_scoreless", never a 0 that looks like a
real low Score. Imports are LAZY (inside each test) so a missing heavy dep or a
not-yet-added helper fails only its own test, never the whole collection.
"""
import types

import pytest


def _ns(**kw):
    return types.SimpleNamespace(**kw)


# ── 1+2: collector pure helper score_cell_and_version (GREEN adds it) ────────
def test_collector_scoreless_row_tags_v3_and_empty_score():
    import post_analysis_collector as pac
    cell, ver = pac.score_cell_and_version("")        # absent score
    assert cell == "" and ver == "v3_scoreless"


def test_collector_scored_row_unchanged():
    import post_analysis_collector as pac
    cell, ver = pac.score_cell_and_version("75.5")    # present score (no-regression)
    assert cell == 75.5 and ver == "v2"


# ── 3: _get_decision_context returns Score=None on absence (not 0.0) ─────────
def test_get_decision_context_none_on_absence():
    from agent.analytics.postmortem_engine import PostmortemEngine
    eng = PostmortemEngine(decision_reader=None)      # no reader -> absence path
    ctx = eng._get_decision_context("POS123")
    assert ctx["Score"] is None


# ── 4: ScoreAtEntry == "" when the decision context has no Score ─────────────
def test_score_at_entry_empty_when_absent():
    from agent.analytics.postmortem_engine import PostmortemEngine
    # no-op sheet_writer + no data_provider/reader -> fully hermetic (no Sheets/network)
    eng = PostmortemEngine(decision_reader=None, data_provider=None,
                           sheet_writer=lambda row: None)
    position = {"PositionID": "P1", "Ticker": "AAA", "Status": "CLOSED",
                "RealizedPnLPct": 5.0, "PnLPct": 5.0, "ExitReason": "TP_HIT"}
    pm = eng.generate(position)
    assert pm["ScoreAtEntry"] == ""


# ── 5: forensic prose OMITS the Score line when absent; keeps it when present ─
def test_prose_omits_score_line_when_absent():
    from agent.analytics.postmortem_engine import PostmortemEngine
    eng = PostmortemEngine()
    pos = {"Ticker": "AAA", "RealizedPnLPct": 5.0, "PnLPct": 5.0, "ExitReason": "TP_HIT"}
    absent = eng._build_forensic_prose(pos, {"Score": None, "metrics": {}}, 1.0, -1.0, 2.0)
    assert "Score=" not in absent, "absent Score must NOT render a Score line"
    present = eng._build_forensic_prose(pos, {"Score": 75.0, "metrics": {}}, 1.0, -1.0, 2.0)
    assert "Score=" in present, "present Score must still render (no-regression)"


# ── 6: skip_summary ScoreMin/Max not accumulated as 0 when score is absent ──
def test_skip_summary_score_empty_when_absent():
    from agent.logging.decision_logger import DecisionLogger
    logger = DecisionLogger.__new__(DecisionLogger)   # bypass the network __init__
    logger._skip_acc = {}
    logger._accumulate_skip(_ns(score=None, skip_reason="SCORE_TOO_LOW", ticker="T"))
    entry = logger._skip_acc["SCORE_TOO_LOW"]
    assert entry["score_min"] is None and entry["score_max"] is None
