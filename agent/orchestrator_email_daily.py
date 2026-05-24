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


def _days_between(date_str: str, today_str: str) -> int:
    """Return calendar days between EntryDate and today."""
    try:
        from datetime import date
        y1, m1, d1 = [int(x) for x in str(date_str).strip().split("-")]
        y2, m2, d2 = [int(x) for x in str(today_str).strip().split("-")]
        return (date(y2, m2, d2) - date(y1, m1, d1)).days
    except Exception:
        return 0


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
        "closed_trades": [],   # NEW: per-trade detail for closes today
        "open_positions": [],  # NEW: per-trade detail for still-open positions
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
                exit_date = str(r.get("ExitDate", "")).strip()
                exit_reason = str(r.get("ExitReason", "")).upper()

                if status in ("OPEN", "DRY_RUN_OPEN"):
                    stats["open_at_eod"] += 1
                    # NEW: collect per-position detail
                    entry_date = str(r.get("EntryDate", "")).strip()
                    try:
                        unreal = float(r.get("UnrealizedPnL", 0) or 0)
                    except (TypeError, ValueError):
                        unreal = 0.0
                    try:
                        unreal_pct = float(r.get("UnrealizedPnLPct", 0) or 0)
                    except (TypeError, ValueError):
                        unreal_pct = 0.0
                    try:
                        entry_price = float(r.get("EntryPrice", 0) or 0)
                    except (TypeError, ValueError):
                        entry_price = 0.0
                    try:
                        current_price = float(r.get("CurrentPrice", 0) or 0)
                    except (TypeError, ValueError):
                        current_price = 0.0
                    stats["open_positions"].append({
                        "ticker": r.get("Ticker", "?"),
                        "entry_date": entry_date,
                        "days_open": _days_between(entry_date, today),
                        "entry_price": entry_price,
                        "current_price": current_price,
                        "unrealized_pnl": unreal,
                        "unrealized_pnl_pct": unreal_pct,
                    })
                elif exit_date == today:
                    stats["positions_closed"] += 1
                    # FIX: classify by ExitReason, not Status (Status=DRY_RUN_CLOSED for all)
                    if "TP" in exit_reason:
                        stats["tp_hits"] += 1
                    elif "SL" in exit_reason:
                        stats["sl_hits"] += 1
                    elif "EOD" in exit_reason:
                        stats["eod_closes"] += 1

                    try:
                        pnl = float(r.get("RealizedPnL", 0) or 0)
                        stats["realized_pnl"] += pnl
                    except (TypeError, ValueError):
                        pnl = 0.0

                    # NEW: collect per-trade detail
                    try:
                        pnl_pct = float(r.get("RealizedPnLPct", 0) or 0)
                    except (TypeError, ValueError):
                        pnl_pct = 0.0
                    entry_date = str(r.get("EntryDate", "")).strip()
                    stats["closed_trades"].append({
                        "ticker": r.get("Ticker", "?"),
                        "entry_date": entry_date,
                        "exit_time": str(r.get("ExitTime", "")).strip(),
                        "exit_reason": exit_reason or "?",
                        "realized_pnl": pnl,
                        "realized_pnl_pct": pnl_pct,
                        "days_held": _days_between(entry_date, today),
                    })

                if str(r.get("EntryDate", "")).strip() == today:
                    stats["positions_opened"] += 1

        # Sort closed_trades by exit_time (descending — newest first)
        stats["closed_trades"].sort(key=lambda x: x.get("exit_time", ""), reverse=True)
        # Sort open_positions by entry_date (descending — newest first)
        stats["open_positions"].sort(key=lambda x: x.get("entry_date", ""), reverse=True)

        # Errors (sentinel_events + system_events, P2.1)
        ws = sheets_manager.get_worksheet("sentinel_events") or sheets_manager.get_worksheet("system_events")
        if ws:
            records = ws.get_all_records()
            stats["errors_today"] = sum(
                1 for r in records
                if str(r.get("Timestamp", "")).startswith(today)
                and str(r.get("Severity", "")).upper() in ("ERROR", "CRITICAL")
                and not str(r.get("EventType", "")).upper().startswith("SENTINEL_")
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
