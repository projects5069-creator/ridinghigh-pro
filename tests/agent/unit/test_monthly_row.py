"""TASK-48 monthly — build_monthly_row (pure fn). Summarizes the PREVIOUS month.
Written before implementation → RED expected."""
import importlib
mod = importlib.import_module("agent.critic.critic_v1")

def _c():
    C = mod.CriticAgent
    try: return C()
    except Exception: return C.__new__(C)

SAMPLE = [
    {"Ticker":"AAA","ExitDate":"2026-05-10","verdict":"WIN","pnl_pct":10.0,"RealizedPnL":100.0},
    {"Ticker":"BBB","ExitDate":"2026-05-20","verdict":"LOSS","pnl_pct":-9.0,"RealizedPnL":-90.0},
    {"Ticker":"CCC","ExitDate":"2026-05-28","verdict":"WIN","pnl_pct":8.0,"RealizedPnL":80.0},
    {"Ticker":"DDD","ExitDate":"2026-06-02","verdict":"WIN","pnl_pct":5.0,"RealizedPnL":50.0},
    {"Ticker":"EEE","ExitDate":"2026-04-30","verdict":"WIN","pnl_pct":7.0,"RealizedPnL":70.0},
]

def test_method_exists():
    assert hasattr(_c(), "build_monthly_row")

def test_summarizes_previous_month():
    row = _c().build_monthly_row("2026-06-01", trades=SAMPLE)
    assert row["MonthOf"] == "2026-05"
    assert row["Trades"] == 3

def test_wins_losses():
    row = _c().build_monthly_row("2026-06-01", trades=SAMPLE)
    assert row["Wins"] == 2 and row["Losses"] == 1

def test_total_pnl_dollars():
    row = _c().build_monthly_row("2026-06-01", trades=SAMPLE)
    assert abs(float(row["TotalPnL"]) - 90.0) < 0.01

def test_has_monthof_not_weekof():
    row = _c().build_monthly_row("2026-06-01", trades=SAMPLE)
    assert "MonthOf" in row and "WeekOf" not in row

def test_16_keys():
    row = _c().build_monthly_row("2026-06-01", trades=SAMPLE)
    expected = {"MonthOf","Trades","Wins","Losses","WinRate","TotalPnL","AvgWin","AvgLoss",
                "Enters","Skips","TickersChecked","Anomalies","Conflicts",
                "Conclusion","SampleSizeFlag","GeneratedAt"}
    assert expected.issubset(set(row.keys()))

def test_empty_graceful():
    row = _c().build_monthly_row("2026-06-01", trades=[])
    assert row["Trades"] == 0 and isinstance(row["Conclusion"], str)

def test_january_rolls_to_prev_december():
    row = _c().build_monthly_row("2026-01-01", trades=[])
    assert row["MonthOf"] == "2025-12"
