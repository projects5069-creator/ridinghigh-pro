"""TASK-48 EMAIL.2 — orchestrator_critic_weekly.py
STANDALONE weekly Critic orchestrator (SEPARATE from the daily orchestrator, by design).

Why separate (locked product decision):
  - Runs Fridays 18:00 Peru (cron '0 23 * * 5') — one hour AFTER the daily run (17:00),
    so all 5 trading days are processed before the weekly aggregation.
  - Isolated failure: a weekly failure never affects the daily email, and vice-versa.
  - Clear separation: three distinct emails (daily / weekly / monthly).

Flow: build_weekly_row(today) -> write_weekly_summary(row) -> render_weekly_email(row)
      -> send_email(subject, html). Sends ONLY if there were trades that week
      (no empty weekly spam).
"""
import logging
import sys
from datetime import datetime

import pytz

PERU_TZ = pytz.timezone("America/Lima")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("critic_weekly")


def run():
    """Build + persist + email the weekly summary. Returns summary dict."""
    summary = {"weekly_written": False, "email_sent": False, "errors": 0}
    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    try:
        from agent.critic.critic_v1 import CriticAgent
        from agent.notifications.templates.weekly_brief import render_weekly_email
        from agent.notifications.email_sender import send_email
    except Exception as e:
        logger.error("weekly orchestrator import failed: %s", e, exc_info=True)
        return {"weekly_written": False, "email_sent": False, "errors": 1}

    try:
        critic = CriticAgent()
    except Exception as e:
        logger.error("CriticAgent init failed: %s", e, exc_info=True)
        summary["errors"] += 1
        return summary

    try:
        row = critic.build_weekly_row(today)
    except Exception as e:
        logger.error("build_weekly_row failed: %s", e, exc_info=True)
        summary["errors"] += 1
        return summary

    try:
        if critic.write_weekly_summary(row):
            summary["weekly_written"] = True
            logger.info("weekly_summary row written for %s", row.get("WeekOf"))
    except Exception as e:
        logger.error("write_weekly_summary failed: %s", e, exc_info=True)
        summary["errors"] += 1

    try:
        if int(row.get("Trades", 0) or 0) > 0:
            subject, html = render_weekly_email(row)
            if send_email(subject, html):
                summary["email_sent"] = True
                logger.info("weekly email sent for week %s", row.get("WeekOf"))
        else:
            logger.info("no trades for week %s — skipping weekly email", row.get("WeekOf"))
    except Exception as e:
        logger.error("weekly email failed: %s", e, exc_info=True)
        summary["errors"] += 1

    logger.info("Weekly Critic complete: %s", summary)
    return summary


if __name__ == "__main__":
    result = run()
    sys.exit(1 if result.get("errors", 0) > 0 else 0)
