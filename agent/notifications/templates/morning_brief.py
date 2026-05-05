"""HTML template for morning start email (08:30 Peru)."""

from datetime import datetime
from typing import Dict, Any
import pytz

PERU_TZ = pytz.timezone("America/Lima")


def render_morning_email(state: Dict[str, Any]) -> tuple:
    """
    Args:
        state: dict with keys:
            - mode (str): "DRY_RUN" or "LIVE_PAPER"
            - open_positions_count (int)
            - buying_power (float)
            - last_postmortems_count (int)
            - account_status (str): "OK" or warning text
    Returns:
        (subject: str, html: str)
    """
    now = datetime.now(PERU_TZ)
    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%H:%M Peru")

    mode_color = "#10b981" if state.get("mode") == "DRY_RUN" else "#f59e0b"

    subject = f"🌅 RidingHigh Agent — Starting {date_str}"

    html = f"""
    <html><body style="font-family: -apple-system, sans-serif; max-width: 600px;">
      <h2 style="color: #2563eb;">🌅 Good Morning</h2>
      <p style="color: #666;">{date_str} · {time_str}</p>

      <div style="background: #f0f9ff; border-left: 4px solid #2563eb; padding: 12px; margin: 16px 0;">
        <strong>Agent is starting for the day.</strong><br>
        Mode: <span style="color: {mode_color}; font-weight: bold;">{state.get("mode", "DRY_RUN")}</span>
      </div>

      <h3>📊 Status</h3>
      <table style="border-collapse: collapse; width: 100%;">
        <tr><td style="padding: 6px; border-bottom: 1px solid #e5e7eb;"><strong>Open positions:</strong></td>
            <td style="padding: 6px; border-bottom: 1px solid #e5e7eb;">{state.get("open_positions_count", 0)}</td></tr>
        <tr><td style="padding: 6px; border-bottom: 1px solid #e5e7eb;"><strong>Buying power:</strong></td>
            <td style="padding: 6px; border-bottom: 1px solid #e5e7eb;">${state.get("buying_power", 0):,.2f}</td></tr>
        <tr><td style="padding: 6px; border-bottom: 1px solid #e5e7eb;"><strong>Recent postmortems:</strong></td>
            <td style="padding: 6px; border-bottom: 1px solid #e5e7eb;">{state.get("last_postmortems_count", 0)}</td></tr>
        <tr><td style="padding: 6px;"><strong>Account status:</strong></td>
            <td style="padding: 6px;">{state.get("account_status", "OK")}</td></tr>
      </table>

      <p style="color: #888; font-size: 12px; margin-top: 24px;">
        Market opens at 08:30 Peru. Agent will start evaluating signals every minute.<br>
        Dashboard: <a href="https://ridinghigh-pro-v2.streamlit.app">ridinghigh-pro-v2.streamlit.app</a>
      </p>
    </body></html>
    """
    return subject, html
