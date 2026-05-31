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


def _render_detail(detail):
    """TASK-48: render the 3 detail sections (per-stock / quality / exploratory).
    Returns '' when detail is falsy, so render_monthly_email stays backward compatible.
    Section C is explicitly labeled exploratory/descriptive — NOT a trading trigger."""
    if not detail:
        return ""
    d = detail
    esc = _html.escape

    def _trade_rows(rows, color):
        return "".join(
            f'<tr><td style="padding:3px 8px;">{esc(str(r.get("ticker","?")))}</td>'
            f'<td style="padding:3px 8px;color:{color};">{_fmt(r.get("pnl_pct"),"%")}</td>'
            f'<td style="padding:3px 8px;color:{color};">${r.get("pnl_usd")}</td></tr>'
            for r in (rows or [])
        )

    dp = d.get("dominant_pos", {}) or {}
    dn = d.get("dominant_neg", {}) or {}
    sec_a = (
        '<h3 style="margin-top:20px;">🏆 ביצועים פר-מניה</h3>'
        '<table style="border-collapse:collapse;font-size:13px;width:100%;">'
        f'<tr><td colspan="3" style="font-weight:bold;color:{_WIN_COLOR};padding:4px 8px;">Top 5 מנצחות</td></tr>'
        f'{_trade_rows(d.get("top5"), _WIN_COLOR)}'
        f'<tr><td colspan="3" style="font-weight:bold;color:{_LOSS_COLOR};padding:8px 8px 4px;">Top 5 מפסידות</td></tr>'
        f'{_trade_rows(d.get("bottom5"), _LOSS_COLOR)}'
        '</table>'
        '<p style="font-size:13px;margin:8px 0;">'
        f'💰 דומיננטית לחיוב: <b>{esc(str(dp.get("ticker","—")))}</b> (${dp.get("pnl_usd","—")}) · '
        f'🔻 דומיננטית לשלילה: <b>{esc(str(dn.get("ticker","—")))}</b> (${dn.get("pnl_usd","—")})</p>'
    )

    er = d.get("exit_reason_counts", {}) or {}
    er_str = " · ".join(f"{esc(str(k))}: {v}" for k, v in er.items()) or "—"
    sec_b = (
        '<h3 style="margin-top:20px;">🔧 איכות והתנהגות</h3>'
        '<p style="font-size:13px;margin:6px 0;">'
        f'סיבות יציאה: {er_str}<br>'
        f'ניקויים ידניים (MANUAL_CLEANUP): <b>{d.get("manual_cleanup",0)}</b> · '
        f'דאטה PRE_FIX: <b>{d.get("pre_fix",0)}</b></p>'
    )

    w = d.get("entry_metrics_win", {}) or {}
    l = d.get("entry_metrics_loss", {}) or {}
    labels = [("score_at_entry", "Score"), ("run_up", "RunUp"), ("atrx", "ATRX"), ("float_pct", "Float%")]
    rows_c = "".join(
        f'<tr><td style="padding:3px 8px;">{lbl}</td>'
        f'<td style="padding:3px 8px;color:{_WIN_COLOR};">{_fmt(w.get(k))}</td>'
        f'<td style="padding:3px 8px;color:{_LOSS_COLOR};">{_fmt(l.get(k))}</td></tr>'
        for k, lbl in labels
    )
    sec_c = (
        '<div style="background:#eef2ff;border-right:4px solid #6366f1;padding:10px;margin-top:20px;border-radius:4px;">'
        '<b>🔬 חקרני — תיאורי, לא טריגר מסחר</b>'
        '<table style="border-collapse:collapse;font-size:13px;width:100%;margin-top:6px;">'
        f'<tr><td style="padding:3px 8px;">מדד כניסה</td>'
        f'<td style="padding:3px 8px;color:{_WIN_COLOR};">ממוצע מנצחות</td>'
        f'<td style="padding:3px 8px;color:{_LOSS_COLOR};">ממוצע מפסידות</td></tr>'
        f'{rows_c}</table>'
        f'<div style="font-size:12px;color:{_NEUTRAL};margin-top:4px;">חוזרים סדרתיים (≥2 הופעות): {d.get("serial_count",0)}</div>'
        '</div>'
    )
    return sec_a + sec_b + sec_c


def render_monthly_email(row, detail=None):
    """Render the standalone monthly summary email.

    Args:
        row: dict from CriticAgent.build_monthly_row() (16 keys).
        detail: optional dict from CriticAgent.build_monthly_detail(). When None,
            output is identical to the pre-detail aggregate email (backward compatible).
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
  {_render_detail(detail)}

  <div style="background:#f8f9fa;padding:14px;border-radius:6px;margin-top:16px;
border-right:4px solid {pnl_color};">
    <strong>מסקנת החודש:</strong><br>{_html.escape(str(conclusion))}
  </div>

  <p style="color:{_NEUTRAL};font-size:12px;margin-top:24px;">
    RidingHigh Pro · The Critic · סיכום חודשי · נוצר {datetime.now(PERU_TZ).strftime('%Y-%m-%d %H:%M')} Peru
  </p>
</div>"""

    return subject, html_body
