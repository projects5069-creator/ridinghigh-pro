#!/usr/bin/env python3
"""
Warm OAuth Token — keep refresh token alive.

Google revokes refresh tokens for apps in 'testing' status after 7 days
of inactivity. This script does a refresh every 3 days to reset the clock.

If refresh fails → email alert with renewal instructions.

Runs from GitHub Actions cron every 3 days. Also runnable locally for testing.
"""
import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText

import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


PERU_TZ = pytz.timezone("America/Lima")


def send_alert(reason: str) -> None:
    """Send email alert when token refresh fails."""
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_pass = os.environ.get("GMAIL_APP_PASS")
    report_to = os.environ.get("REPORT_TO")

    if not all([gmail_user, gmail_pass, report_to]):
        print("⚠️  Email credentials missing — skipping alert", file=sys.stderr)
        return

    now_peru = datetime.now(PERU_TZ).strftime("%Y-%m-%d %H:%M %Z")
    subject = "🔴 RidingHigh: OAuth Token EXPIRED — Manual Renewal Required"
    body = f"""OAuth Token Refresh Failed
============================

Time: {now_peru}
Reason: {reason}

ACTION REQUIRED — manual renewal needed:

1. On your Mac, open terminal:
   cd ~/RidingHighPro
   python3 get_oauth_token.py

2. Browser will open — sign in and approve.

3. Copy the new oauth_token.json contents:
   python3 -c "import json; print(json.dumps(json.load(open('oauth_token.json'))))"

4. Update GitHub Secret GOOGLE_OAUTH_TOKEN_JSON:
   https://github.com/projects5069-creator/ridinghigh-pro/settings/secrets/actions

5. Test by running prepare_next_month workflow manually.

Why this happens:
Google revokes refresh tokens for OAuth apps in 'Testing' status after 7
days of inactivity. The Token Warmer normally prevents this by refreshing
every 3 days, but something broke this cycle.

Token Warmer code: warm_oauth_token.py
Workflow: .github/workflows/warm_oauth_token.yml
"""

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = report_to

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, [report_to], msg.as_string())
        print(f"📧 Alert sent to {report_to}")
    except Exception as e:
        print(f"❌ Failed to send alert: {e}", file=sys.stderr)


def main() -> int:
    now_peru = datetime.now(PERU_TZ).strftime("%Y-%m-%d %H:%M %Z")
    print(f"🔥 Token Warmer — {now_peru}")
    print("=" * 60)

    token_json = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
    if not token_json:
        print("❌ GOOGLE_OAUTH_TOKEN_JSON env var not set", file=sys.stderr)
        return 1

    try:
        data = json.loads(token_json)
    except json.JSONDecodeError as e:
        reason = f"Token JSON malformed: {e}"
        print(f"❌ {reason}", file=sys.stderr)
        send_alert(reason)
        return 1

    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )

    try:
        creds.refresh(Request())
        print("✅ Token refresh succeeded — token is alive")
        print(f"   New access token expiry: {creds.expiry}")
        return 0
    except Exception as e:
        reason = f"Refresh failed: {type(e).__name__}: {e}"
        print(f"❌ {reason}", file=sys.stderr)
        send_alert(reason)
        return 1


if __name__ == "__main__":
    sys.exit(main())
