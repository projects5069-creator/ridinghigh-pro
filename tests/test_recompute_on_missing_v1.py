"""TASK-182 Path 2 — exclude_interday_artifacts must recompute the artifact flag
for rows whose persisted InterdayArtifact is blank/NaN (legacy rows written before
TASK-180 wiring), closing the column-dependent leak into the research aggregates AND
health_audit Check 29.

RED: current code does `is_artifact = _coerce_bool(df[flag_col])`, which maps a blank
flag to False — so a legacy reverse-split row is NOT excluded and leaks. These tests
fail until exclude_interday_artifacts recomputes blanks from the D0-D5 close chain
(via flag_interday_artifact_chain, single source of truth). In-memory only — never
writes back to Sheets.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

from cross_month_loaders import exclude_interday_artifacts

CLOSES = ["D0_Close", "D1_Close", "D2_Close", "D3_Close", "D4_Close", "D5_Close"]
# TDIC 2026-05-12 reverse-split artifact: 2.34 -> 22.82 = +877% (D0->D1)
ART = [2.34, 22.82, 23.0, 22.5, 23.1, 22.9]
BENIGN = [10, 11, 12, 11, 10, 11]


def _row(ticker, flag, closes):
    d = {"Ticker": ticker, "InterdayArtifact": flag}
    d.update(dict(zip(CLOSES, closes)))
    return d


def _df(rows):
    return pd.DataFrame(rows)


def test_blank_flag_artifact_is_excluded():
    """Legacy blank-flag row with reverse-split closes is recomputed -> excluded."""
    df = _df([_row("TDIC", "", ART), _row("AAA", "", BENIGN)])
    clean, pct, n = exclude_interday_artifacts(df)
    assert n == 1
    assert "TDIC" not in clean["Ticker"].tolist()
    assert "AAA" in clean["Ticker"].tolist()


def test_nan_flag_artifact_is_excluded():
    """A real NaN (column absent in legacy month -> reindexed to NaN) is recomputed."""
    df = _df([_row("TDIC", float("nan"), ART)])
    clean, pct, n = exclude_interday_artifacts(df)
    assert n == 1
    assert "TDIC" not in clean["Ticker"].tolist()


def test_present_flag_false_wins_not_recomputed():
    """Explicit persisted False is trusted (collector wrote it) -> not recomputed."""
    df = _df([_row("X", "False", ART)])
    clean, pct, n = exclude_interday_artifacts(df)
    assert n == 0
    assert "X" in clean["Ticker"].tolist()


def test_present_flag_true_wins_not_recomputed():
    """Explicit persisted True is kept even with benign closes."""
    df = _df([_row("Y", "True", BENIGN)])
    clean, pct, n = exclude_interday_artifacts(df)
    assert n == 1
    assert "Y" not in clean["Ticker"].tolist()


def test_fail_closed_missing_closes():
    """Blank flag + missing closes -> cannot compute -> stays False (kept), no crash."""
    df = _df([_row("Z", "", [None, None, None, None, None, None])])
    clean, pct, n = exclude_interday_artifacts(df)
    assert n == 0
    assert "Z" in clean["Ticker"].tolist()


def test_input_df_not_mutated():
    """Recompute is in-memory on a copy — the caller's df (and the sheet) is untouched."""
    df = _df([_row("TDIC", "", ART)])
    before = df["InterdayArtifact"].tolist()
    exclude_interday_artifacts(df)
    assert df["InterdayArtifact"].tolist() == before  # still blank in caller's df


def test_no_close_columns_falls_back_safe():
    """A df without D0-D5 closes must not crash; falls back to column-dependent."""
    df = pd.DataFrame([{"Ticker": "W", "InterdayArtifact": ""}])
    clean, pct, n = exclude_interday_artifacts(df)
    assert n == 0
    assert "W" in clean["Ticker"].tolist()


def test_check29_counts_legacy_artifact():
    """health_audit Check 29 (reuses exclude) must now COUNT the legacy artifact."""
    from health_audit import _interday_artifact_result
    df = _df([_row("TDIC", "", ART), _row("AAA", "", BENIGN)])
    res = _interday_artifact_result(df)
    assert "1 inter-day split/halt artifact" in res.message
