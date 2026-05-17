"""HTML template for daily Critic brief email (19:00 Peru)."""

from datetime import datetime
from typing import Any, Dict, List
import pytz

PERU_TZ = pytz.timezone("America/Lima")


def render_critic_email(facts: Dict[str, Any], positions: Dict[str, Any]) -> tuple:
    """
    Args:
        facts: output of CriticAgent.daily_facts()
        positions: output of CriticAgent.unified_positions()
    Returns:
        (subject: str, html: str)
    """
    now = datetime.now(PERU_TZ)
    date_str = facts.get("date", now.strftime("%Y-%m-%d"))

    trader = facts.get("trader", {})
    sentinel = facts.get("sentinel", {})
    mc = facts.get("market_context", {})
    nd = facts.get("news_detective", {})
    anomalies = facts.get("anomalies", [])
    conflicts = positions.get("conflicts", [])

    enters = trader.get("enters", 0)
    skips = trader.get("skips")
    skip_str = str(skips) if skips is not None else "לא תועד"
    regime = mc.get("regime") or "לא זמין"
    blocks = sentinel.get("blocks", 0)
    warns = sentinel.get("warns", 0)
    tickers_checked = nd.get("tickers_checked", 0)
    material_count = nd.get("material_news_count", 0)

    has_activity = enters > 0 or blocks > 0 or warns > 0 or tickers_checked > 0

    subject = f"🏆 RidingHigh — סיכום סוכנים יומי {date_str}"

    # ── No-activity shortcut ────────────────────────────────────────
    if not has_activity and not anomalies and not conflicts:
        html = f"""
        <html><body dir="rtl" style="font-family: -apple-system, sans-serif; max-width: 600px; direction: rtl;">
          <h2 style="color: #2563eb;">🏆 סיכום סוכנים יומי</h2>
          <p style="color: #666;">{date_str}</p>
          <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 16px; margin: 16px 0;">
            <strong style="color: #10b981;">יום מסחר ללא פעילות מתועדת.</strong>
          </div>
          <p style="color: #999; font-size: 12px;">RidingHigh Pro · Critic Agent</p>
        </body></html>
        """
        return subject, html

    # ── Build full email ────────────────────────────────────────────

    # 1. Agent activity summary
    unique_tickers = trader.get("entered_tickers_unique", {})
    unique_str = ", ".join(f"{t}×{n}" for t, n in unique_tickers.items()) if unique_tickers else "—"

    activity_html = f"""
    <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin: 16px 0;">
      <h3 style="margin-top: 0; color: #374151;">📋 פעילות סוכנים</h3>
      <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <tr>
          <td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;"><strong>💼 The Trader</strong></td>
          <td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;">{enters} כניסות · {skip_str} דילוגים · {unique_str}</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;"><strong>🛡️ Data Sentinel</strong></td>
          <td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;">{blocks} חסימות · {warns} אזהרות</td>
        </tr>
        <tr>
          <td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;"><strong>🌍 Market Context</strong></td>
          <td style="padding: 6px 0; border-bottom: 1px solid #e5e7eb;">Regime: {regime}</td>
        </tr>
        <tr>
          <td style="padding: 6px 0;"><strong>📰 News Detective</strong></td>
          <td style="padding: 6px 0;">{tickers_checked} מניות נבדקו · {material_count} חדשות מהותיות</td>
        </tr>
      </table>
    </div>
    """

    # 2. Anomalies
    if anomalies:
        anom_rows = ""
        for a in anomalies:
            sev = a.get("severity", "?")
            color = "#dc2626" if sev == "HIGH" else "#f59e0b"
            bg = "#fef2f2" if sev == "HIGH" else "#fffbeb"
            anom_rows += f"""
            <tr style="background: {bg};">
              <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">
                <span style="color: {color}; font-weight: bold;">{sev}</span>
              </td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">{a.get('agent', '?')}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e5e7eb;">{a.get('description', '')}</td>
            </tr>
            """
        anomalies_html = f"""
        <div style="margin: 16px 0;">
          <h3 style="color: #374151;">🚨 חריגות ({len(anomalies)})</h3>
          <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
            <tr style="background: #f3f4f6;">
              <th style="padding: 6px 8px; text-align: right;">חומרה</th>
              <th style="padding: 6px 8px; text-align: right;">סוכן</th>
              <th style="padding: 6px 8px; text-align: right;">תיאור</th>
            </tr>
            {anom_rows}
          </table>
        </div>
        """
    else:
        anomalies_html = """
        <div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 12px; margin: 16px 0;">
          <strong style="color: #10b981;">✅ לא זוהו חריגות היום.</strong>
        </div>
        """

    # 3. Conflicts
    if conflicts:
        conflict_list = ", ".join(conflicts)
        conflicts_html = f"""
        <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 12px; margin: 16px 0;">
          <strong style="color: #dc2626;">⚠️ קונפליקטים:</strong> כניסה למניות עם חדשות מהותיות: {conflict_list}
        </div>
        """
    else:
        conflicts_html = """
        <div style="margin: 16px 0;">
          <span style="color: #10b981;">✅ לא זוהו קונפליקטים.</span>
        </div>
        """

    html = f"""
    <html><body dir="rtl" style="font-family: -apple-system, sans-serif; max-width: 600px; direction: rtl;">
      <h2 style="color: #2563eb;">🏆 סיכום סוכנים יומי</h2>
      <p style="color: #666;">{date_str}</p>
      {activity_html}
      {anomalies_html}
      {conflicts_html}
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
      <p style="color: #999; font-size: 12px;">RidingHigh Pro · Critic Agent · דף מלא בדשבורד: 🏆 דירוג סוכנים</p>
    </body></html>
    """

    return subject, html
