"""Unit tests for score_analytics.py — all mocked."""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.analytics.score_analytics import (
    ScoreAnalytics,
    TIER_INSUFFICIENT,
    TIER_EXPLORATORY,
    TIER_RELIABLE,
    TIER_STRONG,
    SUGGESTION_THRESHOLD,
    SUGGESTION_WEIGHT,
    SUGGESTION_OBSERVATION,
    METRICS,
)


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════

def _postmortem(score=75, pnl_pct=10.0, exit_date="2026-05-03",
                mxv=-300, runup=45, atrx=2.5, rsi=78, **overrides):
    """Create a postmortem dict (mock postmortems Sheet row)."""
    base = {
        "PostmortemID": f"PM-{score}",
        "PositionID": f"DEC-{score}",
        "Ticker": "AAPL",
        "EntryDate": exit_date,
        "EntryPrice": 5.00,
        "ScoreAtEntry": str(score),
        "MetricsAtEntry": json.dumps({
            "MxV": mxv, "RunUp": runup, "ATRX": atrx, "RSI": rsi,
            "REL_VOL": 8.0, "ScanChange": 25.0, "ConfidenceScore": 1.0,
        }),
        "ExitDate": exit_date,
        "ExitPrice": 4.50,
        "PnLPct": str(pnl_pct),
        "ExitReason": "TP_HIT" if pnl_pct > 0 else "SL_HIT",
        "DurationHours": 2.5,
        "MaxFavorable": 4.30,
        "MaxAdverse": 5.40,
        "AutoLessons": "[]",
        "GeneratedAt": "2026-05-03T16:30:00",
        "ScoreVersion": "v2.6",
    }
    base.update(overrides)
    return base


def _make_postmortems(n_wins, n_losses, score=75, exit_date="2026-05-03"):
    """Create N winning + M losing postmortems."""
    pms = []
    for i in range(n_wins):
        pms.append(_postmortem(score=score, pnl_pct=10.0, exit_date=exit_date))
    for i in range(n_losses):
        pms.append(_postmortem(score=score, pnl_pct=-7.0, exit_date=exit_date))
    return pms


@pytest.fixture
def analytics_rows():
    return []


@pytest.fixture
def suggestion_rows():
    return []


@pytest.fixture
def engine_with_data(analytics_rows, suggestion_rows):
    """ScoreAnalytics with 50 postmortems (RELIABLE tier), varied scores."""
    pms = []
    # 70-80 tier: 20 wins, 5 losses (80% WR)
    pms.extend(_make_postmortems(20, 5, score=75))
    # 60-70 tier: 3 wins, 7 losses (30% WR) → triggers threshold suggestion
    pms.extend(_make_postmortems(3, 7, score=65))
    # 90+ tier: 1 win, 4 losses (20% WR) → triggers observation suggestion
    pms.extend(_make_postmortems(1, 4, score=92))
    # 80-90 tier: 3 wins, 2 losses
    pms.extend(_make_postmortems(3, 2, score=85))
    # Total: 50 postmortems
    return ScoreAnalytics(
        postmortem_reader=lambda: pms,
        analytics_writer=lambda row: analytics_rows.append(row),
        suggestion_writer=lambda row: suggestion_rows.append(row),
    )


# ════════════════════════════════════════════════════════════════════════
# Tests
# ════════════════════════════════════════════════════════════════════════

class TestSampleClassification:
    def test_under_10_is_insufficient(self):
        engine = ScoreAnalytics()
        tier, conf = engine._classify_sample(5)
        assert tier == TIER_INSUFFICIENT
        assert conf is None

    def test_10_to_29_is_exploratory_low(self):
        engine = ScoreAnalytics()
        tier, conf = engine._classify_sample(15)
        assert tier == TIER_EXPLORATORY
        assert conf == "LOW"

    def test_30_to_99_is_reliable_medium(self):
        engine = ScoreAnalytics()
        tier, conf = engine._classify_sample(50)
        assert tier == TIER_RELIABLE
        assert conf == "MEDIUM"

    def test_100_plus_is_strong_high(self):
        engine = ScoreAnalytics()
        tier, conf = engine._classify_sample(150)
        assert tier == TIER_STRONG
        assert conf == "HIGH"


class TestRunDaily:
    def test_returns_25_column_row(self, engine_with_data, analytics_rows):
        engine_with_data.run_daily(date="2026-05-03")
        assert len(analytics_rows) == 1
        assert len(analytics_rows[0]) == 25

    def test_no_suggestions_for_daily(self, engine_with_data, suggestion_rows):
        engine_with_data.run_daily(date="2026-05-03")
        assert len(suggestion_rows) == 0  # daily never generates suggestions

    def test_daily_with_no_data_writes_insufficient(self, analytics_rows):
        engine = ScoreAnalytics(
            postmortem_reader=lambda: [],
            analytics_writer=lambda row: analytics_rows.append(row),
        )
        result = engine.run_daily(date="2026-05-03")
        assert len(analytics_rows) == 1
        assert "INSUFFICIENT_DATA" in analytics_rows[0][22]  # Recommendation column


class TestRunWeekly:
    def test_returns_25_column_row(self, engine_with_data, analytics_rows):
        engine_with_data.run_weekly(week_end_date="2026-05-03")
        assert len(analytics_rows) == 1
        assert len(analytics_rows[0]) == 25

    def test_generates_suggestions_with_sufficient_data(self, engine_with_data, suggestion_rows):
        engine_with_data.run_weekly(week_end_date="2026-05-03")
        assert len(suggestion_rows) >= 1
        assert len(suggestion_rows[0]) == 14  # 14-column suggestion

    def test_period_format_is_range(self, engine_with_data, analytics_rows):
        engine_with_data.run_weekly(week_end_date="2026-05-03")
        period = analytics_rows[0][2]  # Period column
        assert "_to_" in period
        assert "2026-04-27" in period  # 6 days before


class TestCorrelations:
    def test_correlations_computed_for_metrics(self, engine_with_data):
        result = engine_with_data.run_daily(date="2026-05-03")
        stats = result["stats"]
        assert "correlations" in stats


class TestTierWinrates:
    def test_70_80_tier_calculated_correctly(self, analytics_rows):
        # 7 wins, 3 losses, all score 75 → tier 70-80 should be 70%
        pms = _make_postmortems(7, 3, score=75)
        engine = ScoreAnalytics(
            postmortem_reader=lambda: pms,
            analytics_writer=lambda row: analytics_rows.append(row),
        )
        # n=10 → EXPLORATORY tier (just barely sufficient)
        engine.run_daily(date="2026-05-03")
        wr_70_80 = analytics_rows[0][9]  # WinRate_70_80 column
        assert wr_70_80 == 70.0
