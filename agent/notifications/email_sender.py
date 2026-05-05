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


def send_alert(error_summary: str, details: str = "") -> bool:
    """Send urgent alert email immediately."""
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
    return send_email(subject, html)
