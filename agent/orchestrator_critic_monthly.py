"""TASK-48 EMAIL.2 — orchestrator_critic_monthly.py
STANDALONE monthly Critic orchestrator (SEPARATE from the daily orchestrator, by design).

Why separate (locked product decision):
  - Runs 1st of month 01:00 Peru (cron '0 6 1 * *'), summarizes the PREVIOUS month.
  - Isolated failure: a monthly failure never affects the daily email, and vice-versa.
  - Clear separation: three distinct emails (daily / monthly / monthly).

Flow: build_monthly_row(today) -> write_monthly_summary(row) -> render_monthly_email(row)
      -> send_email(subject, html). Sends ONLY if there were trades that month
      (no empty monthly spam).
"""
import logging
import sys
from datetime import datetime

import pytz

PERU_TZ = pytz.timezone("America/Lima")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("critic_monthly")


def run():
    """Build + persist + email the monthly summary. Returns summary dict."""
    summary = {"monthly_written": False, "email_sent": False, "errors": 0}
    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    try:
        from agent.critic.critic_v1 import CriticAgent
        from agent.notifications.templates.monthly_brief import render_monthly_email
        from agent.notifications.email_sender import send_email
    except Exception as e:
        logger.error("monthly orchestrator import failed: %s", e, exc_info=True)
        return {"monthly_written": False, "email_sent": False, "errors": 1}

    try:
        critic = CriticAgent()
    except Exception as e:
        logger.error("CriticAgent init failed: %s", e, exc_info=True)
        summary["errors"] += 1
        return summary

    try:
        from dateutil.relativedelta import relativedelta as _rd
        month_of = (datetime.strptime(today, "%Y-%m-%d").date() - _rd(months=1)).strftime("%Y-%m")
        trades = critic.review_completed_trades(month=month_of)
        row = critic.build_monthly_row(today, trades=trades)
    except Exception as e:
        logger.error("build_monthly_row failed: %s", e, exc_info=True)
        summary["errors"] += 1
        return summary

    # TASK-48: per-stock + cross-sectional detail (email-only; never breaks the email)
    detail = None
    try:
        mt = critic._month_trades(trades, row.get("MonthOf"))
        detail = critic.build_monthly_detail(mt)
    except Exception as e:
        logger.error("build_monthly_detail failed (email sends aggregate-only): %s", e, exc_info=True)

    try:
        if critic.write_monthly_summary(row):
            summary["monthly_written"] = True
            logger.info("monthly_summary row written for %s", row.get("MonthOf"))
    except Exception as e:
        logger.error("write_monthly_summary failed: %s", e, exc_info=True)
        summary["errors"] += 1

    try:
        if int(row.get("Trades", 0) or 0) > 0:
            subject, html = render_monthly_email(row, detail)
            if send_email(subject, html):
                summary["email_sent"] = True
                logger.info("monthly email sent for month %s", row.get("MonthOf"))
        else:
            logger.info("no trades for month %s — skipping monthly email", row.get("MonthOf"))
    except Exception as e:
        logger.error("monthly email failed: %s", e, exc_info=True)
        summary["errors"] += 1

    logger.info("Monthly Critic complete: %s", summary)
    return summary


if __name__ == "__main__":
    result = run()
    sys.exit(1 if result.get("errors", 0) > 0 else 0)
