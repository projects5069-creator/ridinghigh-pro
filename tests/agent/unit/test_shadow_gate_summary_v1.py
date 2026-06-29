"""TASK-128 Step 3 — shadow_gate_events persistence (one summary row per run).

Mirrors the TASK-125 skip_summary pattern (per-run aggregation → ONE batched write),
so the explicit-gate shadow divergence survives for the 2+ week forward comparison
instead of evaporating in Actions logs. The row answers: of the signals the live logic
SKIPped on Score, how many would the explicit-only gate have ALLOWED (= divergences).

Pure/deterministic: DecisionLogger("fake") is network-free; tests hit only the
in-memory aggregation + row builder, never a live Sheet.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import agent.logging.decision_logger as dl
from agent.logging.decision_logger import DecisionLogger
from agent.trader.decision_logic import Decision


def _logger():
    return DecisionLogger(sheet_id="fake")


def _score_skip(ticker, diverges):
    d = Decision()
    d.ticker = ticker
    d.action = "SKIP"
    d.skip_reason = "SCORE_TOO_LOW: 30.00 < 50"
    d.shadow_explicit_divergence = diverges
    return d


def test_accumulate_counts_score_skips_and_collects_divergences():
    lg = _logger()
    lg._accumulate_shadow_gate(_score_skip("AAA", True))
    lg._accumulate_shadow_gate(_score_skip("BBB", False))
    lg._accumulate_shadow_gate(_score_skip("CCC", True))
    assert lg._shadow_acc["score_skips"] == 3
    assert lg._shadow_acc["would_allow"] == ["AAA", "CCC"]


def test_accumulate_ignores_non_score_skips():
    lg = _logger()
    d = Decision()
    d.ticker = "X"
    d.action = "SKIP"
    d.skip_reason = "VOLUME_TOO_LOW: 50 < 100000"
    d.shadow_explicit_divergence = False
    lg._accumulate_shadow_gate(d)
    assert lg._shadow_acc["score_skips"] == 0
    assert lg._shadow_acc["would_allow"] == []


def test_build_row_shape_and_values(monkeypatch):
    monkeypatch.setattr(dl._config, "EXPLICIT_GATE_MODE", "shadow")  # TASK-194: pin mode (global default now "active")
    lg = _logger()
    lg._accumulate_shadow_gate(_score_skip("AAA", True))
    lg._accumulate_shadow_gate(_score_skip("BBB", False))
    row = lg._build_shadow_gate_row()
    # [run_start, run_id, mode, score_skips, would_allow_count, divergence_tickers]
    assert row[1] == lg.run_id
    assert row[2] == "shadow"      # EXPLICIT_GATE_MODE default
    assert row[3] == 2             # score_skips total
    assert row[4] == 1             # would_allow (divergence) count
    assert row[5] == "AAA"         # divergence tickers


def test_build_row_none_when_no_score_skips():
    lg = _logger()
    assert lg._build_shadow_gate_row() is None


def test_build_row_none_when_mode_off(monkeypatch):
    monkeypatch.setattr(dl._config, "EXPLICIT_GATE_MODE", "off")
    lg = _logger()
    lg._accumulate_shadow_gate(_score_skip("AAA", True))
    assert lg._build_shadow_gate_row() is None


def test_ticker_cap_applied():
    lg = _logger()
    for i in range(30):
        lg._accumulate_shadow_gate(_score_skip(f"T{i}", True))
    row = lg._build_shadow_gate_row()
    assert "+5 more" in row[5]     # 30 divergences − 25 cap = 5 more
