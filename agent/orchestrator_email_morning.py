"""
agent/orchestrator_email_morning.py
────────────────────────────────────
Morning start email. Triggered at 08:30 Peru daily.
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
)
logger = logging.getLogger("agent.email_morning")


def gather_morning_state() -> Dict[str, Any]:
    """Build state dict for morning email."""
    state = {
        "mode": "DRY_RUN",
        "open_positions_count": 0,
        "buying_power": 100000.0,
        "last_postmortems_count": 0,
        "account_status": "OK",
    }

    try:
        from config import AGENT_LIVE_PAPER
        state["mode"] = "LIVE_PAPER" if AGENT_LIVE_PAPER else "DRY_RUN"
    except Exception:
        pass

    try:
        import sheets_manager
        ws = sheets_manager.get_worksheet("paper_portfolio")
        if ws:
            records = ws.get_all_records()
            state["open_positions_count"] = sum(
                1 for r in records
                if str(r.get("Status", "")).upper() in ("OPEN", "DRY_RUN_OPEN")
            )
    except Exception as e:
        logger.warning("Could not fetch portfolio: %s", e)

    try:
        import sheets_manager
        ws = sheets_manager.get_worksheet("postmortems")
        if ws:
            records = ws.get_all_records()
            # Count last 7 days
            from datetime import timedelta
            cutoff = (datetime.now(PERU_TZ) - timedelta(days=7)).strftime("%Y-%m-%d")
            state["last_postmortems_count"] = sum(
                1 for r in records if str(r.get("ExitDate", "")) >= cutoff
            )
    except Exception as e:
        logger.warning("Could not fetch postmortems: %s", e)

    try:
        from agent.execution.alpaca_broker import AlpacaBroker
        broker = AlpacaBroker()
        account = broker.get_account()
        if account and "buying_power" in account:
            state["buying_power"] = float(account["buying_power"])
    except Exception as e:
        logger.warning("Could not fetch buying_power: %s", e)
        state["account_status"] = f"⚠️ Could not connect to Alpaca: {e}"

    return state


def run() -> bool:
    logger.info("Morning email starting at %s Peru", datetime.now(PERU_TZ).strftime("%H:%M"))
    state = gather_morning_state()

    from agent.notifications.email_sender import EmailSender
    from agent.notifications.templates.morning_brief import render_morning_email

    subject, html = render_morning_email(state)
    sender = EmailSender()
    success = sender.send(subject, html)

    if success:
        logger.info("Morning email sent successfully")
    else:
        logger.error("Morning email failed to send")
    return success


if __name__ == "__main__":
    run()
