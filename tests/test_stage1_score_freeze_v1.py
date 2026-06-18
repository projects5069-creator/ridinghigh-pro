"""TDD Stage 1 — freeze Score sheet-writes via SCORE_WRITE_FROZEN (TASK-127.2, ADR-009).

forward-only: auto_scanner keeps computing Score in-memory (sort/>=70/idxmax intact)
but writes "" to the Score COLUMN of the warehouse + output sheets when the flag is on.
RED: the flag + the two write-helpers do not exist yet. Imports are LAZY so a missing
heavy dep / not-yet-added symbol fails only its own test, never the collection.
"""
import types

import pytest


def _ns(**kw):
    return types.SimpleNamespace(**kw)


# ── flag default ─────────────────────────────────────────────────────────────
def test_default_flag_is_frozen_true():
    import config
    assert config.SCORE_WRITE_FROZEN is True


# ── scalar write helper (the 6 dict sites) ──────────────────────────────────
def test_score_write_value_frozen_empty(monkeypatch):
    import auto_scanner as a
    monkeypatch.setattr(a, "SCORE_WRITE_FROZEN", True, raising=False)
    assert a.score_write_value(75.5) == ""


def test_score_write_value_unfrozen_numeric(monkeypatch):
    import auto_scanner as a
    monkeypatch.setattr(a, "SCORE_WRITE_FROZEN", False, raising=False)
    assert a.score_write_value(75.5) == 75.5      # no-op when flag off


# ── daily_snapshots column blank — must NOT mutate the in-memory selection input
def test_snapshot_freeze_blanks_but_keeps_inmemory(monkeypatch):
    import auto_scanner as a
    import pandas as pd
    monkeypatch.setattr(a, "SCORE_WRITE_FROZEN", True, raising=False)
    df = pd.DataFrame({"Score": [80.0, 50.0], "Ticker": ["A", "B"]})
    snap = a.apply_snapshot_score_freeze(df)
    assert (snap["Score"] == "").all(), "frozen snapshot Score column must be ''"
    assert df["Score"].tolist() == [80.0, 50.0], "original results_df (selection input) must stay intact"


def test_snapshot_unfrozen_noop(monkeypatch):
    import auto_scanner as a
    import pandas as pd
    monkeypatch.setattr(a, "SCORE_WRITE_FROZEN", False, raising=False)
    df = pd.DataFrame({"Score": [80.0]})
    snap = a.apply_snapshot_score_freeze(df)
    assert snap["Score"].iloc[0] == 80.0          # no-op when flag off


# ── end-to-end: frozen snapshot Score "" feeds the collector -> v3_scoreless ──
def test_frozen_snapshot_feeds_collector_v3_scoreless(monkeypatch):
    import auto_scanner as a
    import post_analysis_collector as pac
    import pandas as pd
    monkeypatch.setattr(a, "SCORE_WRITE_FROZEN", True, raising=False)
    snap = a.apply_snapshot_score_freeze(pd.DataFrame({"Score": [80.0]}))
    cell, ver = pac.score_cell_and_version(snap["Score"].iloc[0])
    assert cell == "" and ver == "v3_scoreless"
