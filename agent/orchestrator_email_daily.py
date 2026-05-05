"""
agent/orchestrator_email_daily.py
──────────────────────────────────
Daily brief email. Triggered at 16:30 Peru daily after EOD orchestrator.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
PERU_TZ = pytz.timezone("America/Lima")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent.email_daily")


def gather_daily_stats() -> Dict[str, Any]:
    """Aggregate today's activity from Sheets."""
    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    stats = {
        "decisions_total": 0,
        "decisions_enter": 0,
        "decisions_skip": 0,
        "positions_opened": 0,
        "positions_closed": 0,
        "tp_hits": 0,
        "sl_hits": 0,
        "eod_closes": 0,
        "realized_pnl": 0.0,
        "open_at_eod": 0,
        "errors_today": 0,
        "top_decisions": [],
    }

    try:
        import sheets_manager

        # Decisions
        ws = sheets_manager.get_worksheet("decision_log")
        if ws:
            records = ws.get_all_records()
            today_decisions = [r for r in records if str(r.get("Timestamp", "")).startswith(today)]
            stats["decisions_total"] = len(today_decisions)
            stats["decisions_enter"] = sum(1 for r in today_decisions if str(r.get("Action", "")).upper() == "ENTER")
            stats["decisions_skip"] = stats["decisions_total"] - stats["decisions_enter"]

            # Top 10 by score
            sorted_decisions = sorted(today_decisions, key=lambda r: float(r.get("Score", 0) or 0), reverse=True)
            stats["top_decisions"] = [
                {
                    "ticker": r.get("Ticker", "?"),
                    "score": float(r.get("Score", 0) or 0),
                    "action": r.get("Action", "?"),
                }
                for r in sorted_decisions[:10]
            ]

        # Portfolio (closed today + open at EOD)
        ws = sheets_manager.get_worksheet("paper_portfolio")
        if ws:
            records = ws.get_all_records()
            for r in records:
                status = str(r.get("Status", "")).upper()
                exit_date = str(r.get("ExitDate", ""))

                if status in ("OPEN", "DRY_RUN_OPEN"):
                    stats["open_at_eod"] += 1
                elif exit_date == today:
                    stats["positions_closed"] += 1
                    if "TP" in status:
                        stats["tp_hits"] += 1
                    elif "SL" in status:
                        stats["sl_hits"] += 1
                    elif "EOD" in status:
                        stats["eod_closes"] += 1

                    try:
                        pnl = float(r.get("RealizedPnL", 0) or 0)
                        stats["realized_pnl"] += pnl
                    except (TypeError, ValueError):
                        pass

                if str(r.get("EntryDate", "")) == today:
                    stats["positions_opened"] += 1

        # Errors (system_events)
        ws = sheets_manager.get_worksheet("system_events")
        if ws:
            records = ws.get_all_records()
            stats["errors_today"] = sum(
                1 for r in records
                if str(r.get("Timestamp", "")).startswith(today)
                and str(r.get("Severity", "")).upper() in ("ERROR", "CRITICAL")
            )
    except Exception as e:
        logger.error("Failed to gather daily stats: %s", e, exc_info=True)

    return stats


def run() -> bool:
    logger.info("Daily email starting at %s Peru", datetime.now(PERU_TZ).strftime("%H:%M"))
    stats = gather_daily_stats()

    from agent.notifications.email_sender import EmailSender
    from agent.notifications.templates.daily_brief import render_daily_email

    subject, html = render_daily_email(stats)
    sender = EmailSender()
    success = sender.send(subject, html)

    if success:
        logger.info("Daily email sent: %d decisions, $%.2f PnL",
                    stats["decisions_total"], stats["realized_pnl"])
    else:
        logger.error("Daily email failed to send")
    return success


if __name__ == "__main__":
    run()
