"""TASK-48 EMAIL.3 — LEAN weekly_summary schema (weekly only).
monthly_summary deferred to the monthly sub-task with a per-YEAR global model
(monthly_summary_2026: one row per month), NOT month-rotation. Lean = sourced-today fields only."""
import importlib
cs = importlib.import_module("agent.setup.create_agent_sheets")

EXPECTED_WEEKLY = [
    "WeekOf", "Trades", "Wins", "Losses", "WinRate", "TotalPnL", "AvgWin", "AvgLoss",
    "Enters", "Skips", "TickersChecked", "Anomalies", "Conflicts",
    "Conclusion", "SampleSizeFlag", "GeneratedAt",
]

def test_weekly_in_names():
    assert "weekly_summary" in cs.AGENT_SHEET_NAMES

def test_weekly_headers_lean():
    assert cs.AGENT_SHEET_HEADERS.get("weekly_summary") == EXPECTED_WEEKLY

def test_monthly_not_yet_in_rotation():
    # monthly_summary לא נכנס לרוטציה החודשית — ייווצר per-year בתת-החלק החודשי
    assert "monthly_summary" not in cs.AGENT_SHEET_NAMES

def test_every_name_has_headers():
    for n in cs.AGENT_SHEET_NAMES:
        assert n in cs.AGENT_SHEET_HEADERS, f"{n} missing headers"


# TASK-125 — skip_summary (per-run aggregated SKIP counts by reason)

EXPECTED_SKIP_SUMMARY = [
    "Timestamp", "RunID",
    "SkipReason", "Count", "Tickers", "ScoreMin", "ScoreMax",
]

def test_skip_summary_in_names():
    assert "skip_summary" in cs.AGENT_SHEET_NAMES

def test_skip_summary_headers():
    assert cs.AGENT_SHEET_HEADERS.get("skip_summary") == EXPECTED_SKIP_SUMMARY
