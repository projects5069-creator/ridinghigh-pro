"""TDD for Wilson 95% CI in email templates — TASK-169 AC#2 (emails half).

Wires the existing pure fmt_rate_ci (formulas.py) into the WinRate display of
the daily / weekly / monthly briefs. Dual-axis correctness:
  - CI only on inferential proportions (WinRate on trades = edge estimate).
  - NOT on PRE_FIX% (census — known composition of the month, no sampling).
RTL templates (weekly + monthly) wrap the CI token in a dir="ltr"
unicode-bidi:isolate span so the bracketed range does not visually flip;
daily is LTR and needs no wrapper. Subjects stay plain (no CI).

RED phase: no CI is rendered yet, so the CI-presence assertions fail.
"""
from agent.notifications.templates.daily_brief import render_daily_email
from agent.notifications.templates.weekly_brief import render_weekly_email
from agent.notifications.templates.monthly_brief import render_monthly_email, _quality_check
from formulas import fmt_rate_ci

# 14 wins of 26 closed -> 53.8% with Wilson CI; shared across templates.
_K, _N = 14, 26
_CI = fmt_rate_ci(_K, _N)          # "53.8% [35–71%]"
_ISOLATE = "unicode-bidi:isolate"

_DAILY_STATS = {
    "tp_hits": 14, "sl_hits": 10, "eod_closes": 2, "realized_pnl": 50.0,
    "decisions_total": 3, "decisions_enter": 1, "decisions_skip": 2,
    "errors_today": 0, "open_at_eod": 0,
    "top_decisions": [], "closed_trades": [], "open_positions": [],
}
_WEEKLY_ROW = {
    "WeekOf": "2026-W24", "Trades": 26, "Wins": 14, "Losses": 12, "WinRate": 53.8,
    "TotalPnL": 150, "AvgWin": 8.0, "AvgLoss": -5.0, "SampleSizeFlag": "", "Conclusion": "t",
}
_MONTHLY_ROW = {
    "MonthOf": "2026-06", "Trades": 26, "Wins": 14, "Losses": 12, "WinRate": 53.8,
    "TotalPnL": 150, "AvgWin": 8.0, "AvgLoss": -5.0,
}


# ── Daily (LTR — CI present, no isolate wrapper needed) ──────────────────────
def test_daily_winrate_has_ci():
    _subject, html = render_daily_email(_DAILY_STATS)
    assert _CI in html, "daily WIN RATE must render the Wilson CI"


# ── Weekly (RTL — CI present + isolate span) ─────────────────────────────────
def test_weekly_winrate_has_ci_and_isolate():
    _subject, html = render_weekly_email(_WEEKLY_ROW)
    assert _CI in html, "weekly WinRate must render the Wilson CI"
    assert _ISOLATE in html, "RTL CI token must be wrapped in a dir=ltr isolate span"


def test_weekly_subject_has_no_ci():
    subject, _html = render_weekly_email(_WEEKLY_ROW)
    assert "[" not in subject, "subject must stay plain (no CI bracket)"


# ── Monthly (RTL — CI present + isolate span; PRE_FIX gets NO CI) ────────────
def test_monthly_winrate_has_ci_and_isolate():
    _subject, html = render_monthly_email(_MONTHLY_ROW, detail=None)
    assert _CI in html, "monthly WinRate (bar label) must render the Wilson CI"
    assert _ISOLATE in html, "RTL CI token must be wrapped in a dir=ltr isolate span"


def test_monthly_subject_has_no_ci():
    subject, _html = render_monthly_email(_MONTHLY_ROW, detail=None)
    assert "[" not in subject


def test_monthly_prefix_pct_has_no_ci():
    # PRE_FIX% is a census fraction (known composition) — must NOT carry a CI.
    out = _quality_check({"pre_fix": 20, "exit_reason_counts": {"TP_HIT": 14, "SL_HIT": 12},
                          "manual_cleanup": 0}, 26)
    assert "77%" in out, "PRE_FIX line should still render its percentage"
    assert fmt_rate_ci(20, 26) not in out, "PRE_FIX (census) must not get a Wilson CI"
