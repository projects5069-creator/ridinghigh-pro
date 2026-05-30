"""TASK-48 EMAIL.2 step 1 — build_weekly_row (pure function, no I/O).
Written before implementation → AttributeError expected (method missing)."""
import importlib
import pytest

mod = importlib.import_module("agent.critic.critic_v1")


def _make_critic():
    Critic = getattr(mod, "CriticAgent", None)
    assert Critic is not None, "CriticAgent not found"
    try:
        return Critic()
    except Exception:
        return Critic.__new__(Critic)


SAMPLE = [
    {"Ticker": "AAA", "ExitDate": "2026-05-25", "verdict": "WIN",  "pnl_pct": 10.0, "RealizedPnL": 100.0},
    {"Ticker": "BBB", "ExitDate": "2026-05-26", "verdict": "LOSS", "pnl_pct": -9.0, "RealizedPnL": -90.0},
    {"Ticker": "CCC", "ExitDate": "2026-05-27", "verdict": "WIN",  "pnl_pct": 8.0,  "RealizedPnL": 80.0},
    {"Ticker": "DDD", "ExitDate": "2026-06-02", "verdict": "WIN",  "pnl_pct": 5.0,  "RealizedPnL": 50.0},
]


def test_method_exists():
    c = _make_critic()
    assert hasattr(c, "build_weekly_row")

def test_filters_to_week_only():
    c = _make_critic()
    row = c.build_weekly_row("2026-05-29", trades=SAMPLE)
    assert row["Trades"] == 3

def test_wins_losses_winrate():
    c = _make_critic()
    row = c.build_weekly_row("2026-05-29", trades=SAMPLE)
    assert row["Wins"] == 2 and row["Losses"] == 1
    assert abs(float(row["WinRate"]) - 66.7) < 1.0

def test_total_pnl_dollars():
    c = _make_critic()
    row = c.build_weekly_row("2026-05-29", trades=SAMPLE)
    assert abs(float(row["TotalPnL"]) - 90.0) < 0.01

def test_sample_size_flag_insufficient():
    c = _make_critic()
    row = c.build_weekly_row("2026-05-29", trades=SAMPLE)
    assert row["SampleSizeFlag"] == "INSUFFICIENT"

def test_conclusion_is_string_with_counts():
    c = _make_critic()
    row = c.build_weekly_row("2026-05-29", trades=SAMPLE)
    assert isinstance(row["Conclusion"], str) and "3" in row["Conclusion"]

def test_has_all_16_keys():
    c = _make_critic()
    row = c.build_weekly_row("2026-05-29", trades=SAMPLE)
    expected = {"WeekOf","Trades","Wins","Losses","WinRate","TotalPnL","AvgWin","AvgLoss",
                "Enters","Skips","TickersChecked","Anomalies","Conflicts",
                "Conclusion","SampleSizeFlag","GeneratedAt"}
    assert expected.issubset(set(row.keys()))

def test_empty_week_graceful():
    c = _make_critic()
    row = c.build_weekly_row("2026-05-29", trades=[])
    assert row["Trades"] == 0 and row["SampleSizeFlag"] == "INSUFFICIENT"
    assert isinstance(row["Conclusion"], str)
