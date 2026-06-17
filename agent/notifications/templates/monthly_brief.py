"""TASK-48 monthly — monthly_brief.py
Standalone MONTHLY Critic email template (SEPARATE from the daily brief, by design).
Renders one month (build_monthly_row + build_monthly_detail) as a rich human-Hebrew
report: bottom line, visual key numbers + win-rate bar, top movers table, per-metric
quality table (the heart), and what-to-check. Every number once; every term explained.

Scheduling: sent by orchestrator_critic_monthly.py via agent_critic_monthly.yml on
the 1st of the month at 01:00 Peru (cron '0 6 1 * *') — summarizes the PREVIOUS month.
"""
import html as _html
from datetime import datetime

import pytz

from formulas import fmt_rate_ci

PERU_TZ = pytz.timezone("America/Lima")

_WIN_COLOR = "#10b981"
_LOSS_COLOR = "#ef4444"
_NEUTRAL = "#6b7280"
_MED_COLOR = "#f59e0b"


def _fmt(v, suffix="", dash="—"):
    """Format a possibly-None numeric value gracefully."""
    if v is None or v == "":
        return dash
    return f"{v}{suffix}"


def _verdict_line(row):
    """Block 1 — one big bottom-line sentence: good/bad + why (magnitude vs frequency)."""
    aw, al = row.get("AvgWin"), row.get("AvgLoss")
    flag = row.get("SampleSizeFlag", "")
    try:
        pnl = float(row.get("TotalPnL") or 0)
    except (TypeError, ValueError):
        pnl = 0.0
    if pnl > 0:
        verdict, emoji, color = "חודש מרוויח", "📈", _WIN_COLOR
    elif pnl < 0:
        verdict, emoji, color = ("חודש מפסיד קל" if pnl > -200 else "חודש מפסיד"), "📉", _LOSS_COLOR
    else:
        verdict, emoji, color = "חודש מאוזן", "➖", _NEUTRAL
    why = ""
    if aw is not None and al is not None:
        if abs(al) > aw:
            why = (f" הסיבה: ההפסד הממוצע ({_fmt(al, '%')}) גדול מהרווח הממוצע "
                   f"({_fmt(aw, '%')}) — לא ריבוי הפסדים.")
        elif aw > abs(al):
            why = (f" החוזק: הרווח הממוצע ({_fmt(aw, '%')}) גדול מההפסד הממוצע "
                   f"({_fmt(al, '%')}).")
    small = " (מדגם קטן — בזהירות)" if flag == "INSUFFICIENT" else ""
    return (f'<div style="background:#f8f9fa;border-right:5px solid {color};padding:14px 16px;'
            f'border-radius:6px;margin:18px 0;font-size:16px;line-height:1.5;">'
            f'<b>{emoji} {verdict}: ${row.get("TotalPnL", "—")}.</b>{why}{small}</div>')


def _key_numbers(row):
    """Block 2 — 4 big number cards + a visual win-rate bar (row-only; works without detail)."""
    pnl = row.get("TotalPnL", 0)
    wr = row.get("WinRate")
    try:
        pnl_n = float(pnl or 0)
    except (TypeError, ValueError):
        pnl_n = 0.0
    pnl_color = _WIN_COLOR if pnl_n >= 0 else _LOSS_COLOR

    def _card(label, value, color):
        return (f'<div style="display:inline-block;text-align:center;margin:6px 14px;vertical-align:top;">'
                f'<div style="font-size:13px;color:{_NEUTRAL};">{label}</div>'
                f'<div style="font-size:28px;font-weight:bold;color:{color};">{value}</div></div>')
    cards = (_card("עסקאות", row.get("Trades", 0), "#111827")
             + _card("ברווח", row.get("Wins", 0), _WIN_COLOR)
             + _card("בהפסד", row.get("Losses", 0), _LOSS_COLOR)
             + _card("נטו", f"${pnl}", pnl_color))
    try:
        wpct = max(0.0, min(100.0, float(wr))) if wr is not None else 0.0
    except (TypeError, ValueError):
        wpct = 0.0
    bar = (f'<div style="max-width:420px;margin:6px auto 0;">'
           f'<div style="font-size:12px;color:{_NEUTRAL};margin-bottom:3px;">אחוז הצלחה: <span dir="ltr" style="unicode-bidi:isolate">{fmt_rate_ci(row.get("Wins", 0), row.get("Trades", 0))}</span></div>'
           f'<div style="background:{_LOSS_COLOR};border-radius:6px;overflow:hidden;height:20px;">'
           f'<div style="background:{_WIN_COLOR};height:20px;width:{wpct}%;"></div></div></div>')
    return f'<div style="text-align:center;margin:16px 0;">{cards}</div>{bar}'


def _movers_table(detail):
    """Block 4 — Top 5 winners / Top 5 losers as an aligned table + cumulative dominance."""
    d = detail or {}
    esc = _html.escape

    def _rows(rows, color):
        out = "".join(
            f'<tr><td style="padding:3px 10px;">{esc(str(r.get("ticker", "?")))} '
            f'<span style="color:#6b7280;">({r.get("entries", 0)})</span></td>'
            f'<td style="padding:3px 10px;text-align:left;color:{color};">${r.get("pnl_usd")}</td>'
            f'<td style="padding:3px 10px;text-align:left;color:{color};">{_fmt(r.get("avg_pct"), "%")}</td></tr>'
            for r in (rows or [])
        )
        return out or '<tr><td colspan="3" style="padding:3px 10px;color:#6b7280;">—</td></tr>'
    dp = d.get("dominant_pos", {}) or {}
    dn = d.get("dominant_neg", {}) or {}
    return (
        '<h3 style="margin-top:22px;">🏆 מי זז הכי הרבה</h3>'
        '<p style="font-size:12px;color:#6b7280;margin:2px 0 6px;">'
        'מאוחד לפי מניה: סך הרווח/הפסד בדולרים על כל הכניסות החודש, ומספר הכניסות בסוגריים.</p>'
        '<table style="border-collapse:collapse;font-size:13px;width:100%;max-width:480px;">'
        '<tr style="color:#6b7280;font-size:12px;"><td style="padding:3px 10px;">מניה (כניסות)</td>'
        '<td style="padding:3px 10px;text-align:left;">סך רווח/הפסד $</td>'
        '<td style="padding:3px 10px;text-align:left;">תשואה ממוצעת %</td></tr>'
        f'<tr style="background:#f0fdf4;"><td colspan="3" style="padding:5px 10px;font-weight:bold;color:{_WIN_COLOR};">Top 5 מנצחות</td></tr>'
        f'{_rows(d.get("top5"), _WIN_COLOR)}'
        f'<tr style="background:#fef2f2;"><td colspan="3" style="padding:5px 10px;font-weight:bold;color:{_LOSS_COLOR};">Top 5 מפסידות</td></tr>'
        f'{_rows(d.get("bottom5"), _LOSS_COLOR)}'
        '</table>'
        f'<p style="font-size:13px;margin:8px 0;color:#374151;">במצטבר החודש: '
        f'<b>{esc(str(dp.get("ticker", "—")))}</b> תרם הכי הרבה (+${dp.get("pnl_usd", "—")}), '
        f'<b>{esc(str(dn.get("ticker", "—")))}</b> הזיק הכי הרבה (${dn.get("pnl_usd", "—")}).</p>'
    )


def _metric_table(detail):
    """Block 5 (the heart) — per-metric quality: how well each entry metric separated
    winners from losers this month, sorted strong->weak. DESCRIPTIVE, not a trigger."""
    d = detail or {}
    mq = d.get("metric_quality") or []
    if not mq:
        return ""
    rating_he = {"strong": "חזק", "medium": "בינוני", "weak": "חלש"}
    rating_color = {"strong": _WIN_COLOR, "medium": _MED_COLOR, "weak": _NEUTRAL}
    rows = "".join(
        f'<tr><td style="padding:4px 10px;">{_html.escape(str(m.get("label", "?")))}</td>'
        f'<td style="padding:4px 10px;text-align:center;color:{_WIN_COLOR};">{_fmt(m.get("win"))}</td>'
        f'<td style="padding:4px 10px;text-align:center;color:{_LOSS_COLOR};">{_fmt(m.get("loss"))}</td>'
        f'<td style="padding:4px 10px;text-align:center;">{m.get("gap", 0):+}</td>'
        f'<td style="padding:4px 10px;text-align:center;"><span style="background:'
        f'{rating_color.get(m.get("rating"), _NEUTRAL)};color:#fff;border-radius:4px;'
        f'padding:1px 8px;font-size:12px;">{rating_he.get(m.get("rating"), "?")}</span></td></tr>'
        for m in mq
    )
    weak_n = sum(1 for m in mq if m.get("rating") == "weak")
    footnote = ""
    if weak_n >= len(mq) / 2:
        footnote = ('<div style="font-size:12px;color:#6b7280;margin-top:4px;">'
                    'רוב המדדים לא הבדילו החודש — זו תמונת-אמת, לא חולשת-דיווח.</div>')
    return (
        '<h3 style="margin-top:22px;">🔬 ביצועי המדדים '
        '<span style="font-size:12px;color:#6b7280;font-weight:normal;">'
        '— כמה כל מדד הבדיל בין מנצחות למפסידות (תיאורי, לא טריגר מסחר)</span></h3>'
        '<p style="font-size:12px;color:#6b7280;margin:2px 0 6px;">'
        'לכל מדד: הערך הממוצע במנצחות מול מפסידות. "פער" = כמה המדד הבדיל ביניהן '
        '— פער גדול = עזר לחזות, פער קטן = לא עזר.</p>'
        '<table style="border-collapse:collapse;font-size:13px;width:100%;max-width:520px;">'
        '<tr style="background:#f8f9fa;">'
        '<td style="padding:4px 10px;">מדד</td>'
        f'<td style="padding:4px 10px;text-align:center;color:{_WIN_COLOR};">מנצחות</td>'
        f'<td style="padding:4px 10px;text-align:center;color:{_LOSS_COLOR};">מפסידות</td>'
        '<td style="padding:4px 10px;text-align:center;">פער</td>'
        '<td style="padding:4px 10px;text-align:center;">איכות</td></tr>'
        f'{rows}'
        '</table>'
        '<div style="font-size:11px;color:#6b7280;margin-top:4px;">'
        'Score = ציון 0-100 · RunUp = % עלייה ביום-הכניסה · Float% = % סחירות חופשית · ATRX = תנודתיות (ATR)</div>'
        f'{footnote}'
    )


def _quality_check(detail, trades):
    """Block 6 — what to check: PRE_FIX reliability warning (red if >50%) + human exit mix."""
    d = detail or {}
    pre = int(d.get("pre_fix", 0) or 0)
    n = int(trades or 0)
    pct = round(pre / n * 100) if n else 0
    er = d.get("exit_reason_counts", {}) or {}
    tp = sum(v for k, v in er.items() if str(k).startswith("TP_HIT"))
    sl = sum(v for k, v in er.items() if str(k).startswith("SL_HIT"))
    man = d.get("manual_cleanup", 0)
    out = '<h3 style="margin-top:22px;">⚠️ מה לבדוק</h3>'
    if pct > 50:
        out += (f'<p style="color:{_LOSS_COLOR};font-weight:bold;font-size:14px;margin:4px 0;">'
                f'{pct}% מהחודש בדאטה לא-אמין (PRE_FIX) — קח את המספרים בערבון מוגבל.</p>')
    out += (f'<p style="font-size:13px;margin:4px 0;color:#374151;">'
            f'איך נסגרו: {tp} ביעד-רווח, {sl} בסטופ-הפסד, {man} ידנית.</p>')
    return out


def render_monthly_email(row, detail=None):
    """Render the rich monthly summary email.

    Args:
        row: dict from CriticAgent.build_monthly_row() (16 keys).
        detail: optional dict from CriticAgent.build_monthly_detail(). When None,
            a safe fallback renders the verdict + key numbers only — never breaks.
    Returns:
        (subject, html) tuple — same shape as render_critic_email.
    """
    row = row or {}
    month_of = row.get("MonthOf", "?")
    trades = row.get("Trades", 0)
    win_rate = row.get("WinRate")
    subject = f"📊 סיכום חודשי {month_of} · {trades} עסקאות · {_fmt(win_rate, '%')} הצלחה"

    blocks = [_verdict_line(row), _key_numbers(row)]
    if detail:
        blocks += [
            "<!-- equity curve: commit ב' -->",
            _movers_table(detail),
            _metric_table(detail),
            _quality_check(detail, trades),
        ]
    body = "\n  ".join(blocks)

    html_body = f"""<div dir="rtl" style="font-family:Arial,sans-serif;max-width:680px;
margin:0 auto;color:#111827;">
  <h2 style="border-bottom:2px solid #e5e7eb;padding-bottom:8px;">
    📊 סיכום חודשי — {_html.escape(str(month_of))}</h2>
  {body}
  <p style="color:{_NEUTRAL};font-size:12px;margin-top:24px;">
    RidingHigh Pro · The Critic · סיכום חודשי · נוצר {datetime.now(PERU_TZ).strftime('%Y-%m-%d %H:%M')} Peru
  </p>
</div>"""
    return subject, html_body
