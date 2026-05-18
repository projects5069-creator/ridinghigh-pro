"""
agent/orchestrator_critic.py
─────────────────────────────
Daily Critic orchestrator. Triggered by GitHub Actions at 19:00 Peru (00:00 UTC+1).

Flow:
  1. CriticAgent.write_scorecard() — persist daily facts + anomalies for all agents
  2. CriticAgent.unified_positions() — build cross-agent stance table, log conflicts
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
PERU_TZ = pytz.timezone("America/Lima")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent.orchestrator_critic")


def run() -> Dict[str, Any]:
    """Run daily Critic tasks. Returns summary dict."""
    now = datetime.now(PERU_TZ)
    today = now.strftime("%Y-%m-%d")

    summary: Dict[str, Any] = {
        "timestamp": now.isoformat(),
        "date": today,
        "scorecard_ok": False,
        "total_tickers": 0,
        "conflict_count": 0,
        "email_sent": False,
        "errors": 0,
    }

    logger.info("=" * 60)
    logger.info("Critic orchestrator started at %s Peru", now.strftime("%Y-%m-%d %H:%M:%S"))

    from agent.critic import CriticAgent
    critic = CriticAgent()

    # 1. Write scorecard (daily facts + anomalies → agent_scorecard sheet)
    try:
        ok = critic.write_scorecard(today)
        summary["scorecard_ok"] = ok
        logger.info("write_scorecard: %s", "OK" if ok else "FAILED")
    except Exception as e:
        summary["errors"] += 1
        logger.error("write_scorecard failed: %s", e, exc_info=True)

    # 2. Unified positions (cross-agent stance table)
    positions = {}
    try:
        positions = critic.unified_positions(today)
        summary["total_tickers"] = positions.get("summary", {}).get("total_tickers", 0)
        summary["conflict_count"] = positions.get("summary", {}).get("conflict_count", 0)
        if summary["conflict_count"] > 0:
            logger.warning("Conflicts detected: %s", positions.get("conflicts", []))
        logger.info(
            "unified_positions: %d tickers, %d conflicts",
            summary["total_tickers"], summary["conflict_count"],
        )
    except Exception as e:
        summary["errors"] += 1
        logger.error("unified_positions failed: %s", e, exc_info=True)

    # 3. Send daily Critic email (with weekly summary on Fridays)
    weekly_data = None
    summary["weekly_included"] = False
    if now.weekday() == 4:  # Friday
        try:
            weekly_data = critic.weekly_summary(today)
            summary["weekly_included"] = True
            logger.info("Weekly summary computed: %s", weekly_data.get("totals", {}))
        except Exception as e:
            logger.error("weekly_summary failed (sending daily-only): %s", e, exc_info=True)

    try:
        facts = critic.daily_facts(today)
        from agent.notifications.templates.critic_brief import render_critic_email
        from agent.notifications.email_sender import send_email
        subject, html = render_critic_email(facts, positions, weekly=weekly_data)
        sent = send_email(subject, html)
        summary["email_sent"] = sent
        logger.info("Critic email: %s%s",
                     "sent" if sent else "not sent (SMTP not configured?)",
                     " (with weekly)" if weekly_data else "")
    except Exception as e:
        summary["errors"] += 1
        logger.error("Critic email failed: %s", e, exc_info=True)

    logger.info("Critic complete: errors=%d", summary["errors"])
    return summary


if __name__ == "__main__":
    result = run()
    print(f"OK: scorecard={'OK' if result['scorecard_ok'] else 'FAIL'}, "
          f"tickers={result['total_tickers']}, conflicts={result['conflict_count']}, "
          f"errors={result['errors']}")
    sys.exit(1 if result["errors"] > 0 else 0)
