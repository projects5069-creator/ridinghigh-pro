"""TASK-48 monthly — monthly_brief.py
Standalone weekly Critic email template (SEPARATE from the daily brief, by design).
Renders one week's summary row (from build_monthly_row) as HTML, reusing the daily
brief's visual DNA (cards, win/loss colors, bullets) for cross-email consistency.

Scheduling note: sent by orchestrator_critic_monthly.py via agent_critic_monthly.yml
on 1st of month 01:00 Peru (cron '0 6 1 * *') — summarizes the PREVIOUS month; runs 1st of month 01:00 Peru.
"""
import html as _html
from datetime import datetime

import pytz

PERU_TZ = pytz.timezone("America/Lima")

_WIN_COLOR = "#10b981"
_LOSS_COLOR = "#ef4444"
_NEUTRAL = "#6b7280"


def _fmt(v, suffix="", dash="—"):
    """Format a possibly-None numeric value gracefully."""
    if v is None or v == "":
        return dash
    return f"{v}{suffix}"


def render_monthly_email(row):
    """Render the standalone weekly summary email.

    Args:
        row: dict from CriticAgent.build_monthly_row() (16 keys).
    Returns:
        (subject, html) tuple — same shape as render_critic_email.
    """
    row = row or {}
    week_of = row.get("MonthOf", "?")
    trades = row.get("Trades", 0)
    wins = row.get("Wins", 0)
    losses = row.get("Losses", 0)
    win_rate = row.get("WinRate")
    total_pnl = row.get("TotalPnL", 0)
    avg_win = row.get("AvgWin")
    avg_loss = row.get("AvgLoss")
    flag = row.get("SampleSizeFlag", "")
    conclusion = row.get("Conclusion", "")

    try:
        pnl_num = float(total_pnl)
    except (TypeError, ValueError):
        pnl_num = 0.0
    pnl_color = _WIN_COLOR if pnl_num >= 0 else _LOSS_COLOR

    subject = f"📊 סיכום חודשי — חודש {week_of} · {trades} עסקאות · WinRate {_fmt(win_rate, '%')}"

    def _kpi(label, value, color=_NEUTRAL):
        return (
            f'<div style="display:inline-block;background:#f8f9fa;border-radius:6px;'
            f'padding:10px 16px;margin:4px;min-width:90px;text-align:center;">'
            f'<div style="font-size:12px;color:{_NEUTRAL};">{_html.escape(str(label))}</div>'
            f'<div style="font-size:20px;font-weight:bold;color:{color};">{value}</div></div>'
        )

    flag_note = ""
    if flag == "INSUFFICIENT":
        flag_note = (
            '<div style="background:#fef3c7;border-right:4px solid #f59e0b;'
            'padding:10px;margin:12px 0;border-radius:4px;color:#92400e;">'
            '⚠️ מדגם קטן (פחות מ-10 עסקאות) — אין להסיק מסקנות סטטיסטיות מהשבוע הזה.</div>'
        )

    html_body = f"""<div dir="rtl" style="font-family:Arial,sans-serif;max-width:680px;
margin:0 auto;color:#111827;">
  <h2 style="border-bottom:2px solid #e5e7eb;padding-bottom:8px;">
    📊 סיכום חודשי — חודש {_html.escape(str(week_of))}</h2>

  <div style="margin:16px 0;">
    {_kpi("עסקאות", trades)}
    {_kpi("WinRate", _fmt(win_rate, "%"))}
    {_kpi("נצחונות", wins, _WIN_COLOR)}
    {_kpi("הפסדים", losses, _LOSS_COLOR)}
    {_kpi("P&L נטו", f"${total_pnl}", pnl_color)}
  </div>

  <div style="margin:12px 0;">
    {_kpi("ממוצע נצחון", _fmt(avg_win, "%"), _WIN_COLOR)}
    {_kpi("ממוצע הפסד", _fmt(avg_loss, "%"), _LOSS_COLOR)}
  </div>

  {flag_note}

  <div style="background:#f8f9fa;padding:14px;border-radius:6px;margin-top:16px;
border-right:4px solid {pnl_color};">
    <strong>מסקנת החודש:</strong><br>{_html.escape(str(conclusion))}
  </div>

  <p style="color:{_NEUTRAL};font-size:12px;margin-top:24px;">
    RidingHigh Pro · The Critic · סיכום חודשי · נוצר {datetime.now(PERU_TZ).strftime('%Y-%m-%d %H:%M')} Peru
  </p>
</div>"""

    return subject, html_body
