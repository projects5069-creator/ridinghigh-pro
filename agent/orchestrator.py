"""
agent/orchestrator.py
─────────────────────
Main agent run loop. Triggered every minute by GitHub Actions
during market hours (08:00-15:00 Peru, Mon-Fri).

Flow:
  1. Setup + safety checks (market hours, emergency stop)
  2. Build account_state from paper_portfolio + decision_log
  3. Read latest scan from timeline_live (today's most recent ScanTime)
  4. For each signal: Trader.evaluate → DecisionLogger.log → OrderManager.execute
  5. PositionManager.monitor_all (update prices, detect TP/SL)
  6. If 14:55 Peru: PositionManager.eod_close_all
  7. Log summary

DRY_RUN behavior: order_manager writes to paper_portfolio with Status="DRY_RUN_OPEN"
LIVE_PAPER behavior: order_manager submits real bracket orders to Alpaca paper
Current state: DRY_RUN (config.AGENT_DRY_RUN=True)
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytz
PERU_TZ = pytz.timezone("America/Lima")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent.orchestrator")


# ════════════════════════════════════════════════════════════════════
# Helper: timeline_live row → signal dict
# ════════════════════════════════════════════════════════════════════

def _signal_from_timeline_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map timeline_live row (capitalized keys) to Trader signal dict (snake_case)."""
    def _f(key, default=0.0):
        try:
            v = row.get(key, default)
            return float(v) if v not in (None, "") else default
        except (TypeError, ValueError):
            return default

    def _i(key, default=0):
        try:
            v = row.get(key, default)
            return int(float(v)) if v not in (None, "") else default
        except (TypeError, ValueError):
            return default

    return {
        "ticker": str(row.get("Ticker", "")).strip().upper(),
        "price": _f("Price"),
        "volume": _i("Volume"),
        "market_cap": _f("MarketCap"),
        "open_price": _f("Open_price"),
        "high": _f("High_today"),
        "low": _f("Low_today"),
        "score": _f("Score"),
        "mxv": _f("MxV"),
        "run_up": _f("RunUp"),
        "atrx": _f("ATRX"),
        "rsi": _f("RSI"),
        "rel_vol": _f("REL_VOL"),
        "change": _f("Change"),
        "typical_price_dist": _f("TypicalPriceDist"),
        "gap": _f("Gap"),
        "float_pct": _f("Float%"),
        "float_shares": _f("FloatShares"),
        "scan_time": str(row.get("ScanTime", "")),
        "scan_date": str(row.get("Date", "")),
    }


# ════════════════════════════════════════════════════════════════════
# Helper: market hours + EOD detection
# ════════════════════════════════════════════════════════════════════

def is_market_hours(now: Optional[datetime] = None) -> bool:
    """True if current time is within 08:30-15:00 Peru, Mon-Fri."""
    if now is None:
        now = datetime.now(PERU_TZ)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    minutes = now.hour * 60 + now.minute
    return 8 * 60 + 30 <= minutes < 15 * 60


def is_eod_window(now: Optional[datetime] = None) -> bool:
    """True if 14:55-14:59 Peru AND AGENT_FORCE_EOD_CLOSE is enabled."""
    from config import AGENT_FORCE_EOD_CLOSE
    if not AGENT_FORCE_EOD_CLOSE:
        return False
    if now is None:
        now = datetime.now(PERU_TZ)
    return now.hour == 14 and now.minute >= 55


# ════════════════════════════════════════════════════════════════════
# Helper: emergency stop check
# ════════════════════════════════════════════════════════════════════

def check_emergency_stop() -> bool:
    """Check system_events for unresolved EMERGENCY_STOP_REQUESTED. Returns True if active."""
    try:
        import sheets_manager
        ws = sheets_manager.get_worksheet("system_events")
        if ws is None:
            return False
        records = ws.get_all_records()
        if not records:
            return False
        # Check last 50 events for active emergency stop
        for row in reversed(records[-50:]):
            if row.get("EventType") == "EMERGENCY_STOP_REQUESTED":
                action = str(row.get("ActionTaken", "")).upper()
                if "RESOLVED" not in action and "CLEARED" not in action:
                    return True
        return False
    except Exception as e:
        logger.warning("Could not check emergency stop: %s", e)
        return False


# ════════════════════════════════════════════════════════════════════
# Helper: build account_state
# ════════════════════════════════════════════════════════════════════

def build_account_state(broker=None) -> Dict[str, Any]:
    """Build account_state dict from paper_portfolio + decision_log + broker."""
    state = {
        "existing_positions": set(),
        "buying_power": 100000.0,  # default for DRY_RUN
        "cold_start_concurrent_used": 0,
        "cold_start_daily_used": 0,
    }

    try:
        import sheets_manager
        # Open positions from paper_portfolio
        ws_pf = sheets_manager.get_worksheet("paper_portfolio")
        if ws_pf:
            records = ws_pf.get_all_records()
            for row in records:
                status = str(row.get("Status", "")).upper()
                if status in ("OPEN", "DRY_RUN_OPEN"):
                    ticker = str(row.get("Ticker", "")).strip().upper()
                    if ticker:
                        state["existing_positions"].add(ticker)

        state["cold_start_concurrent_used"] = len(state["existing_positions"])

        # Today's ENTER decisions from decision_log
        # ALSO add tickers to existing_positions to prevent duplicate ENTER
        # when paper_portfolio sheet write hasn't propagated yet (race condition fix)
        ws_dl = sheets_manager.get_worksheet("decision_log")
        if ws_dl:
            records = ws_dl.get_all_records()
            today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
            # Build set of tickers that exited today (so we can re-enter them)
            exited_today = set()
            ws_pf2 = sheets_manager.get_worksheet("paper_portfolio")
            if ws_pf2:
                pf_records = ws_pf2.get_all_records()
                for pf_row in pf_records:
                    exit_date = str(pf_row.get("ExitDate", "")).strip()
                    status = str(pf_row.get("Status", "")).upper()
                    if exit_date == today and status not in ("OPEN", "DRY_RUN_OPEN"):
                        ticker = str(pf_row.get("Ticker", "")).strip().upper()
                        if ticker:
                            exited_today.add(ticker)
            # Add today's ENTER tickers to existing_positions UNLESS they exited today
            for row in records:
                ts = str(row.get("Timestamp", ""))
                if ts.startswith(today) and str(row.get("Action", "")).upper() == "ENTER":
                    state["cold_start_daily_used"] += 1
                    ticker = str(row.get("Ticker", "")).strip().upper()
                    if ticker and ticker not in exited_today:
                        state["existing_positions"].add(ticker)
    except Exception as e:
        logger.warning("Could not build full account_state: %s", e)

    # Buying power from broker (if available)
    if broker is not None:
        try:
            account = broker.get_account()
            if account and "buying_power" in account:
                state["buying_power"] = float(account["buying_power"])
        except Exception as e:
            logger.debug("Could not get buying_power from broker: %s", e)

    return state


# ════════════════════════════════════════════════════════════════════
# Helper: read latest signals from timeline_live
# ════════════════════════════════════════════════════════════════════

def read_latest_signals() -> List[Dict[str, Any]]:
    """Read today's latest scan from timeline_live. Returns list of signal dicts."""
    try:
        import sheets_manager
        ws = sheets_manager.get_worksheet("timeline_live")
        if ws is None:
            logger.warning("timeline_live worksheet unavailable")
            return []

        records = ws.get_all_records()
        if not records:
            logger.info("timeline_live is empty")
            return []

        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        today_records = [r for r in records if str(r.get("Date", "")) == today]
        if not today_records:
            logger.info("No scans yet today (%s)", today)
            return []

        # Find latest ScanTime
        latest_scan_time = max(str(r.get("ScanTime", "")) for r in today_records)
        latest_records = [r for r in today_records if str(r.get("ScanTime", "")) == latest_scan_time]

        signals = [_signal_from_timeline_row(r) for r in latest_records]
        logger.info("Latest scan: %d signals at %s", len(signals), latest_scan_time)
        return signals
    except Exception as e:
        logger.error("Failed to read timeline_live: %s", e)
        return []


# ════════════════════════════════════════════════════════════════════
# Main run
# ════════════════════════════════════════════════════════════════════

def run() -> Dict[str, Any]:
    """
    Main orchestrator run. Called once per minute by GitHub Actions.
    Returns summary dict for logging/testing.
    """
    summary = {
        "timestamp": datetime.now(PERU_TZ).isoformat(),
        "halted": False,
        "halt_reason": None,
        "signals": 0,
        "decisions": 0,
        "enters": 0,
        "skips": 0,
        "errors": 0,
        "monitored": 0,
        "eod_closed": 0,
    }

    now = datetime.now(PERU_TZ)
    logger.info("=" * 60)
    logger.info("Agent run started at %s Peru", now.strftime("%Y-%m-%d %H:%M:%S"))

    # Safety check 1: market hours
    if not is_market_hours(now):
        logger.info("Outside market hours, skipping run")
        summary["halted"] = True
        summary["halt_reason"] = "OUTSIDE_MARKET_HOURS"
        return summary

    # Safety check 2: emergency stop
    if check_emergency_stop():
        logger.warning("EMERGENCY STOP ACTIVE — agent halted")
        summary["halted"] = True
        summary["halt_reason"] = "EMERGENCY_STOP"
        return summary

    # Initialize components
    try:
        from agent.trader.trader import Trader
        from agent.logging.decision_logger import DecisionLogger
        from agent.execution.alpaca_broker import AlpacaBroker
        from agent.execution.order_manager import OrderManager
        from agent.execution.position_manager import PositionManager
        from agent.analytics.postmortem_engine import PostmortemEngine
        from data_provider import get_data_provider
        import sheets_manager

        trader = Trader()
        broker = AlpacaBroker()
        decision_logger = DecisionLogger(
            sheet_id=sheets_manager.get_sheet_id("decision_log"),
        )
        data_provider = get_data_provider()
        order_manager = OrderManager(broker, data_provider=data_provider)
        postmortem_engine = PostmortemEngine(data_provider=data_provider)

        # ── Sheet writer for position_manager ──────────────────────
        # Wires position updates (CurrentPrice, UnrealizedPnL, TP/SL closes)
        # back into the paper_portfolio sheet. Cache header at init to
        # minimise quota usage. Uses gspread A1 helper for >26 cols safety.
        from gspread.utils import rowcol_to_a1 as _rowcol_to_a1
        _portfolio_ws = sheets_manager.get_worksheet("paper_portfolio")
        _portfolio_hdr = _portfolio_ws.row_values(1) if _portfolio_ws else []
        _portfolio_pid_col = (
            _portfolio_hdr.index("PositionID") if "PositionID" in _portfolio_hdr else 0
        )

        def _portfolio_sheet_writer(pos: dict, updates: dict):
            """Write position updates to paper_portfolio. Header is cached."""
            if not _portfolio_ws or not _portfolio_hdr:
                logger.error("paper_portfolio not available for update")
                return
            pos_id = pos.get("PositionID", "")
            if not pos_id:
                logger.warning("No PositionID in pos dict")
                return
            try:
                # Locate the target row (single API read)
                col_values = _portfolio_ws.col_values(_portfolio_pid_col + 1)
                target_row = None
                for row_idx, val in enumerate(col_values[1:], start=2):
                    if val == pos_id:
                        target_row = row_idx
                        break
                if target_row is None:
                    logger.warning("PositionID %s not in sheet", pos_id)
                    return

                # Build batch update
                cells = []
                for col_name, value in updates.items():
                    if col_name in _portfolio_hdr:
                        col_idx_1 = _portfolio_hdr.index(col_name) + 1
                        a1 = _rowcol_to_a1(target_row, col_idx_1)
                        cells.append({"range": a1, "values": [[value]]})
                if cells:
                    _portfolio_ws.batch_update(
                        cells, value_input_option="USER_ENTERED"
                    )
            except Exception as e:
                logger.error(
                    "Failed to update position %s: %s", pos.get("Ticker"), e
                )

        position_manager = PositionManager(
            broker=broker,
            data_provider=data_provider,
            sheet_writer=_portfolio_sheet_writer,
            postmortem_engine=postmortem_engine,
        )
    except Exception as e:
        logger.error("Failed to initialize components: %s", e)
        summary["halted"] = True
        summary["halt_reason"] = f"INIT_FAILED: {e}"
        return summary

    # Build account state
    account_state = build_account_state(broker)
    logger.info(
        "Account state: %d open positions, %d ENTER today, $%.0f buying_power",
        account_state["cold_start_concurrent_used"],
        account_state["cold_start_daily_used"],
        account_state["buying_power"],
    )

    # Read latest signals
    signals = read_latest_signals()
    summary["signals"] = len(signals)

    if not signals:
        logger.info("No signals to process this minute")
    else:
        # Process each signal
        for signal in signals:
            ticker = signal.get("ticker", "?")
            try:
                decision = trader.evaluate(signal, account_state)
                log_result = decision_logger.log(decision)
                if log_result is None:
                    # Sheet write failed (likely 429 quota) — count as error for visibility
                    summary["errors"] += 1
                    logger.warning(
                        "Decision log failed for %s %s (likely quota 429)",
                        getattr(decision, "action", "?"),
                        getattr(decision, "ticker", "?"),
                    )
                summary["decisions"] += 1

                if decision.action == "ENTER":
                    enriched = order_manager.execute(decision)
                    summary["enters"] += 1
                    # Update local state for next signal in batch
                    account_state["existing_positions"].add(ticker)
                    account_state["cold_start_concurrent_used"] += 1
                    account_state["cold_start_daily_used"] += 1
                    logger.info("ENTER %s: score=%.2f, order=%s",
                                ticker, decision.score, enriched.order_id or "n/a")
                else:
                    summary["skips"] += 1
                    logger.debug("SKIP %s: %s", ticker, decision.skip_reason or decision.reason)
            except Exception as e:
                summary["errors"] += 1
                logger.error("Failed signal %s: %s", ticker, e, exc_info=True)
                continue

    # Monitor positions
    try:
        monitor_stats = position_manager.monitor_all()
        summary["monitored"] = sum(monitor_stats.values()) if isinstance(monitor_stats, dict) else 0
        logger.info("Position monitor: %s", monitor_stats)
    except Exception as e:
        logger.error("Position monitor failed: %s", e, exc_info=True)
        summary["errors"] += 1

    # EOD close
    if is_eod_window(now):
        try:
            eod_stats = position_manager.eod_close_all()
            summary["eod_closed"] = sum(eod_stats.values()) if isinstance(eod_stats, dict) else 0
            logger.info("EOD close: %s", eod_stats)
        except Exception as e:
            logger.error("EOD close failed: %s", e, exc_info=True)
            summary["errors"] += 1

    # Send urgent alert if any errors occurred this run
    if summary["errors"] > 0:
        try:
            from agent.notifications.email_sender import send_alert
            send_alert(
                f"{summary['errors']} error(s) in agent run",
                f"Run at {summary['timestamp']}\n"
                f"Signals: {summary['signals']}\n"
                f"Decisions: {summary['decisions']} (ENTER={summary['enters']}, SKIP={summary['skips']})\n"
                f"Errors: {summary['errors']}\n"
                f"Check GitHub Actions logs for details."
            )
        except Exception as e:
            logger.error("Failed to send alert: %s", e)

    # Summary
    logger.info(
        "Run complete: signals=%d, decisions=%d (ENTER=%d, SKIP=%d), errors=%d",
        summary["signals"], summary["decisions"],
        summary["enters"], summary["skips"], summary["errors"],
    )
    return summary


if __name__ == "__main__":
    run()
