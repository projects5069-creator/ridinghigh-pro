"""HTML template for end-of-day brief email (16:30 Peru)."""

from datetime import datetime
from typing import Dict, Any, List
import pytz

PERU_TZ = pytz.timezone("America/Lima")


def _exit_emoji(reason: str) -> str:
    """Map exit reason to emoji."""
    r = (reason or "").upper()
    if "TP" in r:
        return "🟢"
    if "SL" in r:
        return "🔴"
    if "EOD" in r:
        return "⚪"
    return "•"


def _build_closed_trades_section(trades: List[Dict[str, Any]]) -> str:
    """Render Closed Trades table."""
    if not trades:
        return ""
    rows = ""
    for t in trades:
        pnl = t.get("realized_pnl", 0.0)
        pnl_color = "#10b981" if pnl >= 0 else "#dc2626"
        pnl_sign = "+" if pnl >= 0 else ""
        pnl_pct = t.get("realized_pnl_pct", 0.0)
        emoji = _exit_emoji(t.get("exit_reason", ""))
        days = t.get("days_held", 0)
        days_label = f"same day" if days == 0 else (f"{days}d" if days < 7 else f"{days}d")
        rows += f"""
        <tr>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;"><b>{t.get("ticker", "?")}</b></td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; color: #666;">{t.get("entry_date", "?")} → {days_label}</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">{t.get("exit_time", "?")}</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">{emoji} {t.get("exit_reason", "?")}</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; text-align: right; color: {pnl_color}; font-weight: bold;">{pnl_sign}${pnl:.2f}</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; text-align: right; color: {pnl_color};">{pnl_sign}{pnl_pct:.2f}%</td>
        </tr>"""
    return f"""
      <h3>✅ Closed Trades ({len(trades)})</h3>
      <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
        <thead>
          <tr style="background: #f3f4f6;">
            <th style="padding: 8px; text-align: left;">Ticker</th>
            <th style="padding: 8px; text-align: left;">Entry → Held</th>
            <th style="padding: 8px; text-align: left;">Exit Time</th>
            <th style="padding: 8px; text-align: left;">Reason</th>
            <th style="padding: 8px; text-align: right;">P&L $</th>
            <th style="padding: 8px; text-align: right;">P&L %</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>"""


def _build_open_positions_section(positions: List[Dict[str, Any]]) -> str:
    """Render Open Positions table."""
    if not positions:
        return ""
    rows = ""
    for p_pos in positions:
        unreal = p_pos.get("unrealized_pnl", 0.0)
        unreal_color = "#10b981" if unreal >= 0 else "#dc2626"
        unreal_sign = "+" if unreal >= 0 else ""
        unreal_pct = p_pos.get("unrealized_pnl_pct", 0.0)
        days = p_pos.get("days_open", 0)
        days_label = f"today" if days == 0 else (f"{days} day" if days == 1 else f"{days} days")
        rows += f"""
        <tr>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;"><b>{p_pos.get("ticker", "?")}</b></td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; color: #666;">{p_pos.get("entry_date", "?")} ({days_label})</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">${p_pos.get("entry_price", 0):.2f}</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">${p_pos.get("current_price", 0):.2f}</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; text-align: right; color: {unreal_color}; font-weight: bold;">{unreal_sign}${unreal:.2f}</td>
          <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb; text-align: right; color: {unreal_color};">{unreal_sign}{unreal_pct:.2f}%</td>
        </tr>"""
    return f"""
      <h3>⏳ Open Positions ({len(positions)})</h3>
      <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
        <thead>
          <tr style="background: #f3f4f6;">
            <th style="padding: 8px; text-align: left;">Ticker</th>
            <th style="padding: 8px; text-align: left;">Entry (Held)</th>
            <th style="padding: 8px; text-align: right;">Entry $</th>
            <th style="padding: 8px; text-align: right;">Current $</th>
            <th style="padding: 8px; text-align: right;">Unrealized $</th>
            <th style="padding: 8px; text-align: right;">Unrealized %</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>"""


def render_daily_email(stats: Dict[str, Any]) -> tuple:
    """
    Args:
        stats: dict with keys:
            - decisions_total, decisions_enter, decisions_skip
            - positions_opened, positions_closed
            - tp_hits, sl_hits, eod_closes
            - realized_pnl (float)
            - open_at_eod (int)
            - errors_today (int)
            - top_decisions (list of dicts with ticker, score, action)
    Returns:
        (subject: str, html: str)
    """
    now = datetime.now(PERU_TZ)
    date_str = now.strftime("%A, %B %d")

    pnl = stats.get("realized_pnl", 0.0)
    pnl_color = "#10b981" if pnl >= 0 else "#dc2626"
    pnl_sign = "+" if pnl >= 0 else ""

    win_count = stats.get("tp_hits", 0)
    loss_count = stats.get("sl_hits", 0)
    eod_count = stats.get("eod_closes", 0)
    closed_total = win_count + loss_count + eod_count

    win_rate_str = "—"
    if closed_total > 0:
        win_rate_str = f"{win_count / closed_total * 100:.1f}%"

    subject = f"📊 RidingHigh Agent — Daily Brief {date_str} ({pnl_sign}${pnl:.2f})"

    # Top decisions table
    top_rows = ""
    for d in stats.get("top_decisions", [])[:10]:
        action_color = "#10b981" if d.get("action") == "ENTER" else "#6b7280"
        top_rows += f"""
        <tr>
          <td style="padding: 4px 8px; border-bottom: 1px solid #e5e7eb;">{d.get("ticker", "?")}</td>
          <td style="padding: 4px 8px; border-bottom: 1px solid #e5e7eb;">{d.get("score", 0):.2f}</td>
          <td style="padding: 4px 8px; border-bottom: 1px solid #e5e7eb;">
            <span style="color: {action_color}; font-weight: bold;">{d.get("action", "?")}</span>
          </td>
        </tr>
        """

    if not top_rows:
        top_rows = '<tr><td colspan="3" style="padding: 12px; color: #888; text-align: center;">No decisions today</td></tr>'

    errors_section = ""
    if stats.get("errors_today", 0) > 0:
        errors_section = f"""
        <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin: 16px 0;">
          <strong style="color: #dc2626;">⚠️ {stats["errors_today"]} error(s) today.</strong>
          Check Actions logs.
        </div>
        """

    closed_section = _build_closed_trades_section(stats.get("closed_trades", []))
    open_section = _build_open_positions_section(stats.get("open_positions", []))

    html = f"""
    <html><body style="font-family: -apple-system, sans-serif; max-width: 600px;">
      <h2 style="color: #2563eb;">📊 Daily Brief</h2>
      <p style="color: #666;">{date_str}</p>

      <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin: 16px 0;">
        <div style="display: flex; gap: 24px; flex-wrap: wrap;">
          <div>
            <div style="color: #888; font-size: 12px;">REALIZED P&L</div>
            <div style="color: {pnl_color}; font-size: 28px; font-weight: bold;">{pnl_sign}${pnl:.2f}</div>
          </div>
          <div>
            <div style="color: #888; font-size: 12px;">DECISIONS</div>
            <div style="font-size: 24px; font-weight: bold;">{stats.get("decisions_total", 0)}</div>
            <div style="color: #888; font-size: 12px;">
              {stats.get("decisions_enter", 0)} ENTER · {stats.get("decisions_skip", 0)} SKIP
            </div>
          </div>
          <div>
            <div style="color: #888; font-size: 12px;">WIN RATE</div>
            <div style="font-size: 24px; font-weight: bold;">{win_rate_str}</div>
            <div style="color: #888; font-size: 12px;">{win_count}W / {loss_count}L / {eod_count}EOD</div>
          </div>
          <div>
            <div style="color: #888; font-size: 12px;">OPEN AT EOD</div>
            <div style="font-size: 24px; font-weight: bold;">{stats.get("open_at_eod", 0)}</div>
          </div>
        </div>
      </div>

      {errors_section}

      {closed_section}

      {open_section}

      <h3>🎯 Today's Top Decisions</h3>
      <table style="border-collapse: collapse; width: 100%; font-size: 14px;">
        <thead>
          <tr style="background: #f3f4f6;">
            <th style="padding: 8px; text-align: left;">Ticker</th>
            <th style="padding: 8px; text-align: left;">Score</th>
            <th style="padding: 8px; text-align: left;">Action</th>
          </tr>
        </thead>
        <tbody>{top_rows}</tbody>
      </table>

      <p style="color: #888; font-size: 12px; margin-top: 24px;">
        Dashboard: <a href="https://ridinghigh-pro-v2.streamlit.app">Live Agent</a> ·
        <a href="https://ridinghigh-pro-v2.streamlit.app">Score Brain</a>
      </p>
    </body></html>
    """
    return subject, html
