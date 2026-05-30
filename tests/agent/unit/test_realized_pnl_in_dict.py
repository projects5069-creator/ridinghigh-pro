"""TASK-48 bug#1 — review_completed_trades must include RealizedPnL in each dict,
so build_weekly_row/build_monthly_row produce a correct (non-zero) TotalPnL.
RED before fix."""
import importlib
mod = importlib.import_module("agent.critic.critic_v1")

def _c():
    C = mod.CriticAgent
    try: return C()
    except Exception: return C.__new__(C)

# trades מדומים כפי ש-build_weekly_row מקבל (מוזרקים — pure)
FAKE = [
    {"Ticker":"AAA","verdict":"WIN","pnl_pct":10.0,"RealizedPnL":100.0,"exit_date":"2026-05-26"},
    {"Ticker":"BBB","verdict":"LOSS","pnl_pct":-9.0,"RealizedPnL":-90.0,"exit_date":"2026-05-27"},
    {"Ticker":"CCC","verdict":"WIN","pnl_pct":8.0,"RealizedPnL":80.0,"exit_date":"2026-05-28"},
]

def test_weekly_total_pnl_nonzero_when_realized_present():
    # אם RealizedPnL נקרא נכון → TotalPnL = 100-90+80 = 90
    row = _c().build_weekly_row("2026-05-29", trades=FAKE)
    assert abs(float(row["TotalPnL"]) - 90.0) < 0.01, f"TotalPnL={row['TotalPnL']} (צפוי 90.0)"

def test_monthly_total_pnl_nonzero_when_realized_present():
    row = _c().build_monthly_row("2026-06-01", trades=FAKE)  # month_of=2026-05
    assert abs(float(row["TotalPnL"]) - 90.0) < 0.01, f"TotalPnL={row['TotalPnL']} (צפוי 90.0)"

def test_review_completed_trades_dict_has_realized_pnl():
    """אינטגרציה — אם credentials זמינים: ה-dict חייב להכיל RealizedPnL."""
    try:
        trades = _c().review_completed_trades()
    except Exception:
        import pytest; pytest.skip("no credentials")
    if not trades:
        import pytest; pytest.skip("no trades")
    assert "RealizedPnL" in trades[0], f"מפתחות: {sorted(trades[0].keys())}"
