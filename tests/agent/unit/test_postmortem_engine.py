"""Unit tests for postmortem_engine.py — all mocked."""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.analytics.postmortem_engine import (
    PostmortemEngine,
    STATUS_DRY_RUN_CLOSED,
    AGENT_MODE_DRY_RUN,
    AGENT_MODE_LIVE,
)


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════

def _closed_position(**overrides):
    """Create a CLOSED position dict (paper_portfolio row)."""
    defaults = {
        "PositionID": "DEC-2026-05-03-00001",
        "Ticker": "AAPL",
        "EntryDate": "2026-05-03",
        "EntryTime": "10:30:00",
        "EntryPrice": "150.0",
        "Quantity": "7",
        "PositionSizeUSD": "1050.0",
        "Side": "short",
        "Status": "CLOSED",
        "ExitPrice": "135.0",
        "ExitDate": "2026-05-03",
        "ExitTime": "13:30:00",
        "ExitReason": "TP_HIT",
        "RealizedPnL": "105.0",
        "RealizedPnLPct": "10.0",
    }
    defaults.update(overrides)
    return defaults


def _decision_record(**overrides):
    """Create a decision_log row dict."""
    defaults = {
        "DecisionID": "DEC-2026-05-03-00001",
        "Score": "75.5",
        "MxV": "-300",
        "RunUp": "45.0",
        "ATRX": "2.5",
        "RSI": "78",
        "REL_VOL": "8.0",
        "ScanChange": "25.0",
        "ConfidenceScore": "1.0",
    }
    defaults.update(overrides)
    return defaults


@pytest.fixture
def written_rows():
    return []


@pytest.fixture
def engine(written_rows):
    """PostmortemEngine with mock decision reader and writer (no data_provider)."""
    return PostmortemEngine(
        data_provider=None,  # no MFE/MAE
        decision_reader=lambda pid: _decision_record() if pid else None,
        sheet_writer=lambda row: written_rows.append(row),
    )


# ════════════════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════════════════

class TestBasicGeneration:
    def test_generate_returns_dict_with_postmortem_id(self, engine):
        """generate() returns dict with PM- prefixed PostmortemID."""
        pos = _closed_position()
        pm = engine.generate(pos)
        assert pm["PostmortemID"].startswith("PM-")
        assert len(pm["PostmortemID"]) > 3

    def test_writes_17_column_row(self, engine, written_rows):
        """Row written to sheet has exactly 17 columns."""
        pos = _closed_position()
        engine.generate(pos)
        assert len(written_rows) == 1
        assert len(written_rows[0]) == 17

    def test_position_id_propagated(self, engine):
        """PositionID equals decision_id from input."""
        pos = _closed_position(PositionID="DEC-CUSTOM-001")
        pm = engine.generate(pos)
        assert pm["PositionID"] == "DEC-CUSTOM-001"


class TestDuration:
    def test_3_hour_hold_computes_correctly(self, engine):
        """Entry 10:30, Exit 13:30 → 3.0 hours."""
        pos = _closed_position(EntryTime="10:30:00", ExitTime="13:30:00")
        pm = engine.generate(pos)
        assert pm["DurationHours"] == 3.0

    def test_invalid_dates_returns_zero(self, engine):
        """Bad date format → 0.0, no crash."""
        pos = _closed_position(EntryDate="bad-date")
        pm = engine.generate(pos)
        assert pm["DurationHours"] == 0.0


class TestDecisionContext:
    def test_score_loaded_from_decision_reader(self, engine):
        """ScoreAtEntry comes from decision_reader."""
        pos = _closed_position()
        pm = engine.generate(pos)
        assert pm["ScoreAtEntry"] == 75.5

    def test_metrics_serialized_as_json(self, engine):
        """MetricsAtEntry is JSON-encoded dict with 7 keys."""
        pos = _closed_position()
        pm = engine.generate(pos)
        metrics = json.loads(pm["MetricsAtEntry"])
        assert "MxV" in metrics
        assert "RunUp" in metrics
        assert "ATRX" in metrics
        assert metrics["ATRX"] == 2.5

    def test_no_decision_reader_returns_zero_score(self):
        """Without decision_reader, Score=0 and metrics={}."""
        engine = PostmortemEngine(decision_reader=None, sheet_writer=lambda r: None)
        pos = _closed_position()
        pm = engine.generate(pos)
        assert pm["ScoreAtEntry"] == 0.0


class TestAutoLessons:
    # NOTE: AutoLessons is now Hebrew forensic prose (commit cce6c12), so the 7 rule
    # strings no longer land in pm["AutoLessons"]. The rule LOGIC still runs in
    # _generate_lessons (verified), so these tests exercise it directly. (The rule
    # output is currently computed-then-discarded in generate() — tracked separately.)
    def test_loss_with_high_atrx_triggers_rule1(self, engine):
        """LOSS + ATRX>3 → 'High ATRX' rule fires (via _generate_lessons)."""
        pos = _closed_position(RealizedPnLPct="-7.0", ExitReason="SL_HIT")
        lessons = engine._generate_lessons(
            position=pos, decision_context={"metrics": {"ATRX": 4.5}},
            mfe=None, mae=None, duration=2.0, agent_mode=AGENT_MODE_LIVE)
        assert any("High ATRX" in l for l in lessons)

    def test_loss_with_high_rsi_triggers_rule2(self, engine):
        """LOSS + RSI>90 → 'RSI 90+' rule fires (via _generate_lessons)."""
        pos = _closed_position(RealizedPnLPct="-7.0", ExitReason="SL_HIT")
        lessons = engine._generate_lessons(
            position=pos, decision_context={"metrics": {"RSI": 92}},
            mfe=None, mae=None, duration=2.0, agent_mode=AGENT_MODE_LIVE)
        assert any("RSI 90+" in l for l in lessons)

    def test_dry_run_skips_fast_outcome_rule(self, engine):
        """Rule 3 (fast outcome) does NOT trigger outside LIVE mode (via _generate_lessons)."""
        pos = _closed_position(Status=STATUS_DRY_RUN_CLOSED)
        lessons = engine._generate_lessons(
            position=pos, decision_context={"metrics": {}},
            mfe=None, mae=None, duration=0.016, agent_mode=AGENT_MODE_DRY_RUN)
        assert not any("Very fast outcome" in l for l in lessons)

    def test_eod_close_with_profit_triggers_rule6(self, engine):
        """EOD_CLOSE + profit → 'extending hold' rule fires (via _generate_lessons)."""
        pos = _closed_position(ExitReason="EOD_CLOSE", RealizedPnLPct="3.0")
        lessons = engine._generate_lessons(
            position=pos, decision_context={"metrics": {}},
            mfe=None, mae=None, duration=2.0, agent_mode=AGENT_MODE_LIVE)
        assert any("extending hold" in l for l in lessons)


class TestSchemaIntegrity:
    def test_score_version_from_config(self, engine):
        """ScoreVersion comes from config.AGENT_SCORE_VERSION."""
        from config import AGENT_SCORE_VERSION
        pos = _closed_position()
        pm = engine.generate(pos)
        assert pm["ScoreVersion"] == AGENT_SCORE_VERSION
