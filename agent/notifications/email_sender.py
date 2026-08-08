"""
agent/notifications/email_sender.py
────────────────────────────────────
SMTP wrapper for sending HTML emails via Gmail.

Reads SMTP credentials from environment variables (GitHub Actions secrets):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_TO

Used by:
  - orchestrator_email_morning.py (08:30 Peru)
  - orchestrator_email_daily.py (16:30 Peru)
  - orchestrator (immediate alerts on errors)
"""

import os
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger("agent.notifications.email_sender")


class EmailSender:
    """Send HTML emails via Gmail SMTP."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        recipient: Optional[str] = None,
    ):
        self.host = host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(port or os.getenv("SMTP_PORT", "587"))
        self.user = user or os.getenv("SMTP_USER", "")
        self.password = password or os.getenv("SMTP_PASSWORD", "")
        self.recipient = recipient or os.getenv("EMAIL_TO", "")

        # Strip Gmail App Password whitespace (Gmail UI shows with spaces)
        self.password = self.password.replace(" ", "")

    def is_configured(self) -> bool:
        """Returns True if all required env vars are set."""
        return bool(self.user and self.password and self.recipient)

    def send(self, subject: str, html_body: str, plain_body: Optional[str] = None) -> bool:
        """
        Send HTML email. Returns True on success, False on failure.
        Logs errors but does NOT raise — email failures must not crash orchestrator.
        """
        if not self.is_configured():
            logger.warning("Email not configured (missing SMTP env vars), skipping send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.user
            msg["To"] = self.recipient

            # Plain text fallback (some clients prefer it)
            if plain_body is None:
                plain_body = self._html_to_plain(html_body)
            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)

            logger.info("Email sent: %s → %s", subject, self.recipient)
            return True
        except Exception as e:
            logger.error("Failed to send email '%s': %s", subject, e, exc_info=True)
            return False

    @staticmethod
    def _html_to_plain(html: str) -> str:
        """Crude HTML → plain text fallback."""
        import re
        text = re.sub(r"<br\s*/?>", "\n", html)
        text = re.sub(r"</p>", "\n\n", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


# ════════════════════════════════════════════════════════════════════
# Convenience helpers — used by orchestrators
# ════════════════════════════════════════════════════════════════════

def send_email(subject: str, html_body: str) -> bool:
    """Quick send. Reads creds from env. Returns True on success."""
    sender = EmailSender()
    return sender.send(subject, html_body)


# T-201 leg B: alert throttle — idempotency-key (error_summary) checked
# against system_events inside a window. Without it a persistent failure
# (e.g. a 429-storm keeping errors>0 every minute) mails every minute.
ALERT_THROTTLE_WINDOW_MIN = 30
_ALERT_EVENT_TYPE = "ALERT_EMAIL"


def _default_event_reader():
    # The same cached read the orchestrator already performs each cycle
    # (sheets_manager.get_sheet_records carries a 60s TTL cache).
    import sheets_manager
    return sheets_manager.get_sheet_records("system_events") or []


def _default_event_writer(row):
    import sheets_manager
    ws = sheets_manager.get_worksheet("system_events")
    if ws:
        sheets_manager.safe_append_row(ws, row)


def _recently_alerted(error_summary, records, now) -> bool:
    cutoff = now - timedelta(minutes=ALERT_THROTTLE_WINDOW_MIN)
    for rec in records:
        if rec.get("EventType") != _ALERT_EVENT_TYPE:
            continue
        if rec.get("Message") != error_summary:
            continue
        try:
            ts = datetime.fromisoformat(str(rec.get("Timestamp", "")))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=now.tzinfo)
        if ts >= cutoff:
            return True
    return False


def send_alert(error_summary: str, details: str = "", *,
               sender=None, event_reader=None, event_writer=None,
               now=None) -> bool:
    """Send urgent alert email, throttled per error_summary.

    Identical error_summary already alerted inside the last
    ALERT_THROTTLE_WINDOW_MIN minutes (per system_events) ⇒ no send,
    returns False. Never raises. Fail-CLOSED on a failed system_events
    read: during the exact storm this throttle exists for, the read is
    what fails — sending on read-failure would mail every minute.
    """
    if now is None:
        import pytz
        now = datetime.now(pytz.timezone("America/Lima"))
    # Default (uninjected) throttle state lives in the LIVE system_events
    # tab. Touch it only when SMTP is actually configured: without SMTP no
    # real mail can go out, so there is no storm to throttle — and an
    # uninjected local/test call must never do live Sheets I/O (on
    # 2026-08-07 exactly that wrote a test row into production).
    _configured = EmailSender().is_configured()
    reader = event_reader or (_default_event_reader if _configured else None)
    writer = event_writer or (_default_event_writer if _configured else None)
    if reader is not None:
        try:
            records = reader()
        except Exception as e:
            logger.error(
                "Alert throttle: system_events read failed (%s) — suppressing '%s'",
                e, error_summary,
            )
            return False
        if _recently_alerted(error_summary, records, now):
            logger.info(
                "Alert throttled (<%d min, already alerted): %s",
                ALERT_THROTTLE_WINDOW_MIN, error_summary,
            )
            return False

    subject = f"🚨 RidingHigh Agent — {error_summary}"
    html = f"""
    <html><body style="font-family: -apple-system, sans-serif;">
      <h2 style="color: #d33;">🚨 Agent Alert</h2>
      <p><strong>Error:</strong> {error_summary}</p>
      <pre style="background: #f5f5f5; padding: 12px; border-radius: 6px; overflow: auto;">
{details}
      </pre>
      <p style="color: #888; font-size: 12px;">
        Sent automatically by RidingHigh Agent orchestrator.
      </p>
    </body></html>
    """
    ok = (sender or send_email)(subject, html)
    if ok and writer is not None:
        # Record the send so sibling processes (each minute-run is a new
        # process) see it through system_events. Best-effort, never raises.
        row = [now.isoformat(), _ALERT_EVENT_TYPE, "CRITICAL",
               "email_sender", error_summary, "", "sent"]
        try:
            writer(row)
        except Exception as e:
            logger.warning("Alert throttle: event write failed (non-fatal): %s", e)
    return ok
