"""
agent/orchestrator_eod.py
──────────────────────────
End-of-day orchestrator. Triggered by GitHub Actions at 16:00 Peru daily.

Flow:
  1. Reconciler.reconcile() — detect drift between paper_portfolio and Alpaca
  2. ScoreAnalytics.run_daily() — write daily analytics row
  3. If Saturday: ScoreAnalytics.run_weekly() — write weekly + suggestions
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
logger = logging.getLogger("agent.orchestrator_eod")


def run() -> Dict[str, Any]:
    """Run end-of-day tasks. Returns summary dict."""
    summary = {
        "timestamp": datetime.now(PERU_TZ).isoformat(),
        "reconciler_drift": 0,
        "reconcile_missing_portfolio": 0,   # TASK-106: decision_log ENTERs w/o portfolio row
        "daily_analytics": None,
        "weekly_analytics": None,
        "weekly_suggestions": 0,
        "errors": 0,
    }

    now = datetime.now(PERU_TZ)
    logger.info("=" * 60)
    logger.info("EOD orchestrator started at %s Peru", now.strftime("%Y-%m-%d %H:%M:%S"))

    # 1. Reconciler
    try:
        from agent.execution.alpaca_broker import AlpacaBroker
        from agent.execution.reconciler import Reconciler
        broker = AlpacaBroker()

        # TASK-106: alert_writer flags reconciliation gaps to system_events
        # (non-Sentinel tab; best-effort — never breaks the EOD run).
        def _system_events_alert(event):
            try:
                import json as _json
                import sheets_manager as _sm
                ws = _sm.get_worksheet("system_events")
                if not ws:
                    return
                row = [
                    event.get("timestamp", datetime.now(PERU_TZ).isoformat()),
                    "RECONCILE_" + str(event.get("type", "DRIFT")),
                    "WARNING",
                    "reconciler",
                    str(event.get("type", "")),
                    _json.dumps({"ticker": event.get("ticker"),
                                 "decision_id": event.get("decision_id")}, default=str)[:500],
                    str(event.get("action_taken", "flag")),
                ]
                _sm.safe_append_row(ws, row)
            except Exception as _e:
                logger.warning("system_events alert write failed (non-fatal): %s", _e)

        reconciler = Reconciler(broker=broker, alert_writer=_system_events_alert)
        drift_stats = reconciler.reconcile()
        summary["reconciler_drift"] = drift_stats.get("phantom_open", 0) + drift_stats.get("orphan_position", 0)
        logger.info("Reconciler: %s", drift_stats)

        # TASK-106 (flag-only): decision_log ENTER without a matching
        # paper_portfolio row (the XOS pattern). Works in DRY_RUN.
        missing_stats = reconciler.reconcile_decision_log_vs_portfolio(summary)
        logger.info("Reconcile decision_log↔portfolio: %s missing", missing_stats["missing_portfolio_row"])
    except Exception as e:
        summary["errors"] += 1
        logger.error("Reconciler failed: %s", e, exc_info=True)

    # 2. Daily analytics
    try:
        from agent.analytics.score_analytics import ScoreAnalytics
        analytics = ScoreAnalytics()
        result = analytics.run_daily()
        summary["daily_analytics"] = {
            "tier": result.get("tier"),
            "sample_size": result.get("sample_size"),
        }
        logger.info(
            "Daily analytics: tier=%s, n=%d",
            result.get("tier"), result.get("sample_size", 0),
        )
    except Exception as e:
        summary["errors"] += 1
        logger.error("Daily analytics failed: %s", e, exc_info=True)

    # 3. Weekly (Saturday only — weekday 5)
    if now.weekday() == 5:
        try:
            from agent.analytics.score_analytics import ScoreAnalytics
            analytics = ScoreAnalytics()
            result = analytics.run_weekly()
            summary["weekly_analytics"] = {
                "tier": result.get("tier"),
                "sample_size": result.get("sample_size"),
            }
            summary["weekly_suggestions"] = len(result.get("suggestions", []))
            logger.info(
                "Weekly analytics: tier=%s, n=%d, suggestions=%d",
                result.get("tier"), result.get("sample_size", 0),
                summary["weekly_suggestions"],
            )
        except Exception as e:
            summary["errors"] += 1
            logger.error("Weekly analytics failed: %s", e, exc_info=True)

    # Send urgent alert if any errors occurred
    if summary["errors"] > 0:
        try:
            from agent.notifications.email_sender import send_alert
            send_alert(
                f"{summary['errors']} error(s) in EOD orchestrator",
                f"Run at {summary['timestamp']}\n"
                f"Reconciler drift: {summary['reconciler_drift']}\n"
                f"Missing portfolio rows (decision_log↔pf): {summary['reconcile_missing_portfolio']}\n"
                f"Daily analytics: {summary['daily_analytics']}\n"
                f"Weekly suggestions: {summary['weekly_suggestions']}\n"
                f"Errors: {summary['errors']}"
            )
        except Exception as e:
            logger.error("Failed to send alert: %s", e)

    logger.info("EOD complete: errors=%d", summary["errors"])
    return summary


if __name__ == "__main__":
    run()
