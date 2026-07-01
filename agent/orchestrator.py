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

    signal = {
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
        "price_to_high": _f("PriceToHigh"),
        "gap": _f("Gap"),
        "float_pct": _f("Float%"),
        "float_shares": _f("FloatShares"),
        "scan_time": str(row.get("ScanTime", "")),
        "scan_date": str(row.get("Date", "")),
    }

    # L3 enrichment: Price/SMA20 for Toxic Profile filter (4d)
    try:
        from agent.enrichment.sma20_cache import get_price_vs_sma20
        _ticker = signal.get("ticker")
        _price = signal.get("price")
        if _ticker and _price:
            signal["price_vs_sma20"] = get_price_vs_sma20(_ticker, _price)
        else:
            signal["price_vs_sma20"] = None
    except Exception as e:
        print(f"[SMA_ENRICH_FAIL] {signal.get('ticker', '?')}: {type(e).__name__}: {e}", flush=True)
        signal["price_vs_sma20"] = None

    return signal


# ════════════════════════════════════════════════════════════════════
# Helper: market hours + EOD detection
# ════════════════════════════════════════════════════════════════════

def is_market_hours(now: Optional[datetime] = None) -> bool:
    """True if within 08:30-15:00 Peru on a NASDAQ trading day — weekends AND
    exchange holidays excluded (TASK-135; holiday source = utils.is_trading_day,
    the same SSoT TASK-130 uses)."""
    from utils import is_trading_day  # local import — mirrors parse_hhmm usage, avoids cycle
    if now is None:
        now = datetime.now(PERU_TZ)
    if not is_trading_day(now):  # weekend or exchange holiday
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
    """Check system_events (non-Sentinel tab) for unresolved EMERGENCY_STOP_REQUESTED. Returns True if active.

    2026-05-20: Two improvements over previous version:
    1. Uses sheets_manager.get_sheet_records (60s TTL cache) instead of raw
       ws.get_all_records() — runs every minute. system_events (post-P2.1) holds only non-Sentinel events; grew to
       3,500+ rows since Sentinel went active, was hammering Read quota.
    2. Searches by 24-hour timestamp window instead of last 50 rows. With
       Sentinel writing ~700 events/day, an EMERGENCY written at 09:00
       could fall outside the last 50 rows by 11:00 — silently making the
       check useless. 24h cutoff guarantees we see same-day emergencies.
    """
    try:
        import sheets_manager
        try:
            records = sheets_manager.get_sheet_records("system_events")
        except Exception as e:
            # Don't break the agent on a transient fetch failure — log and
            # assume no emergency. Next minute the cache will be warm.
            logger.warning("check_emergency_stop: fetch failed (%s) — assuming no stop", e)
            return False
        if not records:
            return False

        # 24-hour cutoff — anything older has been there long enough to
        # have been resolved or cleared deliberately.
        from datetime import timedelta
        cutoff_iso = (datetime.now(PERU_TZ) - timedelta(hours=24)).isoformat()

        # records is chronological — iterate from newest backwards, break early
        for row in reversed(records):
            ts = str(row.get("Timestamp", ""))
            if ts and ts < cutoff_iso:
                break  # past the 24h window
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
        # Bug #2/#4 fix: count actual OPEN rows, not unique tickers.
        "open_position_count": 0,
        # TASK-107: count today's CLOSED rows (line-count, incl. duplicates —
        # mirrors today_enters which counts re-entries) so position_sync can
        # tell legitimate open→close-same-day from genuine drift.
        "closed_today_count": 0,
        # 2026-06-03 immunization: signals for position_sync to tell an
        # UNREADABLE portfolio (rows present but no recognized Status, e.g. a
        # column-alignment bug) apart from a genuine drift. Computed in the
        # records loop below — no extra sheet read.
        "pf_total_rows": 0,
        "pf_status_recognized_count": 0,
        # Bug #5 fix: per-ticker entry count for today (re-entry limit).
        # 2026-05-23 Fix D: kept as union of two sources — decision_log
        # (primary SSoT) AND paper_portfolio (backup). Google Sheets
        # eventual-consistency can hide recent writes from decision_log
        # for minutes, causing Filter 9 to leak (PIII×14, HCWB×5). Union
        # via max() ensures whichever sheet has the latest count wins.
        "entries_today_by_ticker": {},
        "entries_today_by_ticker_pf": {},   # 2026-05-23 Fix D: paper_portfolio source
        # 2026-05-20 fix: flag for when paper_portfolio read failed (e.g. 429).
        # position_sync uses this to return WARN instead of BLOCK — a fetch
        # failure is a quota/network issue, not a real position drift.
        "paper_portfolio_fetch_failed": False,
    }

    try:
        import sheets_manager
        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

        # ── paper_portfolio: SINGLE read (TASK-58). Derive open/existing,
        #    pf_total_rows/pf_status_recognized_count, today's per-ticker
        #    entries, AND today's exits — all from one fetch (was 2 reads +
        #    redundant get_worksheet truthiness calls). get_sheet_records
        #    returns [] for a missing sheet, so no truthiness probe needed.
        try:
            pf_records = sheets_manager.get_sheet_records("paper_portfolio")
        except Exception as fetch_err:
            # 2026-05-20: a fetch failure (e.g. 429) is a quota/network issue,
            # not real position drift — flag it so position_sync returns WARN.
            logger.warning("build_account_state: paper_portfolio fetch failed (%s) — "
                           "setting paper_portfolio_fetch_failed=True", fetch_err)
            state["paper_portfolio_fetch_failed"] = True
            pf_records = []

        exited_today = set()
        for row in pf_records:
            status = str(row.get("Status", "")).upper()
            ticker = str(row.get("Ticker", "")).strip().upper()
            # 2026-06-03 immunization: count every row + rows with a recognized
            # Status, so position_sync can tell an unreadable portfolio
            # (rows>0 but recognized==0) apart from a genuine drift.
            state["pf_total_rows"] += 1
            if status in ("OPEN", "DRY_RUN_OPEN", "CLOSED", "DRY_RUN_CLOSED"):
                state["pf_status_recognized_count"] += 1
            if status in ("OPEN", "DRY_RUN_OPEN"):
                if ticker:
                    state["existing_positions"].add(ticker)
                # Count every OPEN row — duplicate tickers count separately.
                state["open_position_count"] += 1
            # 2026-05-23 Fix D: per-ticker entries today from paper_portfolio
            # (any status) — secondary source, unioned with decision_log below.
            entry_date = str(row.get("EntryDate", "")).strip()
            if entry_date == today and ticker:
                state["entries_today_by_ticker_pf"][ticker] = (
                    state["entries_today_by_ticker_pf"].get(ticker, 0) + 1
                )
            # Tickers that exited today (so a re-entry isn't blocked) — derived
            # from the SAME read (TASK-58: previously a second paper_portfolio fetch).
            exit_date = str(row.get("ExitDate", "")).strip()
            if exit_date == today and status not in ("OPEN", "DRY_RUN_OPEN") and ticker:
                exited_today.add(ticker)
            # TASK-107: row-count of today's CLOSED positions (incl. duplicate
            # tickers — re-entries closed same day), so position_sync can treat
            # a fully-accounted same-day open→close as ALLOW, not drift BLOCK.
            if exit_date == today and status in ("CLOSED", "DRY_RUN_CLOSED") and ticker:
                state["closed_today_count"] += 1

        # cold_start cap reflects real concurrent positions, not unique tickers.
        state["cold_start_concurrent_used"] = state["open_position_count"]

        # ── decision_log: SINGLE read. Today's ENTERs feed cold_start_daily_used
        #    + per-ticker counts; add tickers to existing_positions UNLESS they
        #    exited today (race-condition fix for un-propagated pp writes).
        try:
            dl_records = sheets_manager.get_sheet_records("decision_log")
        except Exception as dl_err:
            logger.warning("build_account_state: decision_log fetch failed (%s)", dl_err)
            state["paper_portfolio_fetch_failed"] = True
            dl_records = []
        for row in dl_records:
            ts = str(row.get("Timestamp", ""))
            if ts.startswith(today) and str(row.get("Action", "")).upper() == "ENTER":
                state["cold_start_daily_used"] += 1
                # Bug #5 root-cause fix: count per-ticker entries from
                # decision_log (reliable SSoT), not paper_portfolio.
                _tk = str(row.get("Ticker", "")).strip().upper()
                if _tk:
                    state["entries_today_by_ticker"][_tk] = (
                        state["entries_today_by_ticker"].get(_tk, 0) + 1
                    )
                    if _tk not in exited_today:
                        state["existing_positions"].add(_tk)

        # 2026-05-23 Fix D: union the two counters — for each ticker that
        # appears in either source, take the max. This protects Filter 9
        # from Google Sheets eventual-consistency lag (one sheet may be
        # ahead of the other by minutes during quota pressure).
        all_tickers = set(state["entries_today_by_ticker"].keys()) | \
                      set(state["entries_today_by_ticker_pf"].keys())
        for tk in all_tickers:
            dl_count = state["entries_today_by_ticker"].get(tk, 0)
            pf_count = state["entries_today_by_ticker_pf"].get(tk, 0)
            state["entries_today_by_ticker"][tk] = max(dl_count, pf_count)
    except Exception as e:
        logger.warning("Could not build full account_state: %s", e)
        state["paper_portfolio_fetch_failed"] = True

    # Buying power from broker (if available)
    if broker is not None:
        try:
            account = broker.get_account()
            if account and "buying_power" in account:
                state["buying_power"] = float(account["buying_power"])
        except Exception as e:
            logger.debug("Could not get buying_power from broker: %s", e)

    return state


def _record_entry_outcome(decision, summary) -> bool:
    """TASK-105: account for an executed ENTER based on whether its
    paper_portfolio write actually persisted.

    Mirrors the decision_log failure handling: a successful write counts as a
    real ENTER; a failed write is surfaced as an error (counted + logged), NOT
    silently counted as a successful entry. Returns True if persisted.
    """
    if getattr(decision, "portfolio_written", True):
        summary["enters"] += 1
        return True
    summary["errors"] += 1
    logger.warning(
        "paper_portfolio write FAILED for ENTER %s — surfaced, not counted as a "
        "successful entry (likely 429 quota; decision_log ENTER may now lack a "
        "matching portfolio row)",
        getattr(decision, "ticker", "?"),
    )
    return False


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

        records = sheets_manager.get_sheet_records("timeline_live")
        if not records:
            logger.info("timeline_live is empty")
            return []

        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        today_records = [r for r in records if str(r.get("Date", "")) == today]
        if not today_records:
            logger.info("No scans yet today (%s)", today)
            return []

        # Find latest ScanTime
        from utils import parse_hhmm
        latest_scan_time = max(
            (str(r.get("ScanTime", "")) for r in today_records),
            key=parse_hhmm,
        )
        latest_records = [r for r in today_records if str(r.get("ScanTime", "")) == latest_scan_time]

        signals = [_signal_from_timeline_row(r) for r in latest_records]
        logger.info("Latest scan: %d signals at %s", len(signals), latest_scan_time)
        return signals
    except Exception as e:
        logger.error("Failed to read timeline_live: %s", e)
        return []


# ════════════════════════════════════════════════════════════════════
# Outage detection (P3.4 Phase 1)
# ════════════════════════════════════════════════════════════════════


def detect_outage(now: datetime) -> Optional[Dict[str, Any]]:
    """
    Detect cron-drift outages by checking gap since last successful scan.

    Uses timeline_live as a proxy for "last successful run" — if scanner
    wrote a row, the workflow ran successfully. Compares to current time.

    Returns:
      Dict with 'gap_min' (float) + 'last_scan_time' (str) if gap > 10 min.
      None otherwise (no history, first scan of day, or invalid data).

    Notes:
      - Uses parse_hhmm for numeric time comparison (same pattern as
        read_latest_signals to avoid lex-compare bugs — see SENT.1).
      - Caller should be inside is_market_hours() — outside market hours,
        gaps are expected, not outages.
      - Graceful: any exception returns None (observability is best-effort).
    """
    try:
        import sheets_manager
        from utils import parse_hhmm

        records = sheets_manager.get_sheet_records("timeline_live")
        if not records:
            return None

        today_str = now.strftime("%Y-%m-%d")
        today_records = [r for r in records if str(r.get("Date", "")) == today_str]
        if not today_records:
            return None

        latest_scan_time_str = max(
            (str(r.get("ScanTime", "")) for r in today_records),
            key=parse_hhmm,
        )
        latest_min_of_day = parse_hhmm(latest_scan_time_str)
        if latest_min_of_day < 0:
            return None

        now_min_of_day = now.hour * 60 + now.minute
        gap_min = now_min_of_day - latest_min_of_day

        if gap_min > 10:
            return {
                "gap_min": float(gap_min),
                "last_scan_time": latest_scan_time_str,
            }
        return None
    except Exception as e:
        logger.error("detect_outage failed: %s", e)
        return None


# ════════════════════════════════════════════════════════════════════
# Main run
# ════════════════════════════════════════════════════════════════════

def make_portfolio_batch_writer(ws, hdr, pid_col):
    """TASK-192 (C4): buffer per-position paper_portfolio cell updates, flush as ONE
    batch_update. Returns (writer, flush).

    writer(pos, updates) appends row-specific cells to a buffer — each cell targets
    pos['_row_number'] (Bug #2 fix; PositionID fallback if absent), so a position's
    value can never land in another's row. flush() issues a single
    safe_batch_update(USER_ENTERED) for all buffered cells and clears the buffer,
    so N monitored positions cost 1 API write instead of N. Returns the cell count
    written (0 on empty/error). Never raises — observability/writes must not break the run.
    """
    from gspread.utils import rowcol_to_a1
    buffer = []

    def writer(pos, updates):
        if not ws or not hdr:
            logger.error("paper_portfolio not available for update")
            return
        target_row = pos.get("_row_number")
        if not target_row:
            # Fallback: match by PositionID (legacy path; logs a warning)
            pos_id = pos.get("PositionID", "")
            if not pos_id:
                logger.warning("No _row_number and no PositionID in pos dict")
                return
            logger.warning("pos %s has no _row_number — falling back to PositionID match", pos_id)
            try:
                col_values = ws.col_values(pid_col + 1)
                for row_idx, val in enumerate(col_values[1:], start=2):
                    if val == pos_id:
                        target_row = row_idx
                        break
            except Exception as e:
                logger.error("Fallback row lookup failed for %s: %s", pos_id, e)
                return
            if not target_row:
                logger.warning("PositionID %s not in sheet", pos_id)
                return
        for col_name, value in updates.items():
            if col_name in hdr:
                col_idx_1 = hdr.index(col_name) + 1
                a1 = rowcol_to_a1(target_row, col_idx_1)
                buffer.append({"range": a1, "values": [[value]]})

    def flush():
        if not buffer:
            return 0
        try:
            import sheets_manager as _sm
            _sm.safe_batch_update(ws, buffer, value_input_option="USER_ENTERED")
            n = len(buffer)
            buffer.clear()
            return n
        except Exception as e:
            logger.error("Failed to flush portfolio batch (%d cells): %s", len(buffer), e)
            buffer.clear()
            return 0

    return writer, flush


def _maybe_write_news(news_detective, ticker: str) -> None:
    """TASK-176: gate news_detective off the per-minute path.

    news_detective.write_findings() calls get_worksheet() per-ticker (~46 Sheets
    read-requests/run — the single biggest agent_minute 429 contributor, 46/91).
    Research proved it net-negative (WITH-news WR 60% < WITHOUT 62%, EDGAR r=-0.156),
    so it is disabled per-minute via config.NEWS_DETECTIVE_ENABLED (reversible).
    Log-only, never blocks — a write error is swallowed (matches prior behaviour).
    """
    from config import NEWS_DETECTIVE_ENABLED
    if not NEWS_DETECTIVE_ENABLED:
        return
    try:
        news_detective.write_findings(ticker)
    except Exception as e:
        logger.warning("News Detective failed for %s: %s", ticker, e)


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

    # TASK-58: reset per-tab read counter so the end-of-run summary reflects
    # this run's actual API reads (for measuring read-reduction).
    try:
        import sheets_manager as _sm_rc
        _sm_rc.reset_read_counts()
    except Exception:
        pass

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

    # Safety check 3: cron-drift outage detection (P3.4 Phase 1 — observability only)
    try:
        outage_info = detect_outage(now)
        if outage_info:
            gap_min = outage_info["gap_min"]
            severity = "CRITICAL" if gap_min > 30 else "WARNING"

            from agent.sentinel.data_sentinel import _log_sentinel_event
            _log_sentinel_event(
                decision="OUTAGE",
                component="orchestrator",
                reason="CRON_DRIFT_OUTAGE",
                details={
                    "gap_minutes": round(gap_min, 1),
                    "last_scan_time": outage_info["last_scan_time"],
                    "now": now.strftime("%H:%M:%S"),
                    "severity": severity,
                },
                action_taken=f"OUTAGE_LOGGED gap={gap_min:.1f}min severity={severity}",
            )
            logger.warning(
                "P3.4 Outage detected: %.1f min gap since last scan at %s (severity=%s)",
                gap_min, outage_info["last_scan_time"], severity,
            )

            # Send email alert for severe outages only
            if gap_min > 30:
                try:
                    from agent.notifications.email_sender import send_alert
                    send_alert(
                        f"Cron-drift outage: {gap_min:.0f} min gap",
                        f"Last successful scan: {outage_info['last_scan_time']} Peru\n"
                        f"Current time: {now.strftime('%H:%M:%S')} Peru\n"
                        f"Gap: {gap_min:.1f} minutes\n"
                        f"Severity: CRITICAL (>30 min threshold)\n\n"
                        f"GH Actions may have skipped runs. Phase 1 = observability only.\n"
                        f"Catch-up logic (Phase 2) not yet implemented."
                    )
                    logger.info("Outage alert email sent")
                except Exception as e:
                    logger.error("Failed to send outage alert email: %s", e)
    except Exception as e:
        # Outage detection must never halt the run
        logger.error("Outage detection block failed: %s", e)

    # Initialize components
    try:
        from agent.trader.trader import Trader
        from agent.sentinel.data_sentinel import get_sentinel
        from agent.news_detective import NewsDetectiveAgent
        from agent.logging.decision_logger import DecisionLogger
        from agent.execution.alpaca_broker import AlpacaBroker
        from agent.execution.order_manager import OrderManager
        from agent.execution.position_manager import PositionManager, cached_portfolio_reader
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
        # decision_reader callback: look up decision_log by DecisionID
        # Required by PostmortemEngine to populate MetricsAtEntry
        def _read_decision(decision_id):
            try:
                from sheets_manager import get_worksheet
                ws = get_worksheet("decision_log")
                if ws is None:
                    return {}
                rows = ws.get_all_records()
                for row in rows:
                    if row.get("DecisionID") == decision_id:
                        return row
                return {}
            except Exception as e:
                logger.warning("_read_decision failed for %s: %s", decision_id, e)
                return {}

        postmortem_engine = PostmortemEngine(data_provider=data_provider, decision_reader=_read_decision)
        news_detective = NewsDetectiveAgent()

        # ── Sheet writer for position_manager ──────────────────────
        # Wires position updates (CurrentPrice, UnrealizedPnL, TP/SL closes)
        # back into the paper_portfolio sheet. Cache header at init to
        # minimise quota usage. Uses gspread A1 helper for >26 cols safety.
        _portfolio_ws = sheets_manager.get_worksheet("paper_portfolio")
        _portfolio_hdr = _portfolio_ws.row_values(1) if _portfolio_ws else []
        _portfolio_pid_col = (
            _portfolio_hdr.index("PositionID") if "PositionID" in _portfolio_hdr else 0
        )

        # TASK-192 (C4): buffer per-position writes, flush ONE batch_update per step.
        _portfolio_writer, _portfolio_flush = make_portfolio_batch_writer(
            _portfolio_ws, _portfolio_hdr, _portfolio_pid_col
        )

        position_manager = PositionManager(
            broker=broker,
            data_provider=data_provider,
            sheet_reader=cached_portfolio_reader,  # TASK-136 C1: share the 60s
            # paper_portfolio cache (account-state-builder already read it this
            # run at :222) instead of a duplicate uncached get_all_records.
            sheet_writer=_portfolio_writer,
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

    sentinel = get_sentinel()
    sentinel_blocks = 0

    # System-level check (HALT entire run if fails)
    # FIX: today_enters must be today's ENTER count from decision_log,
    # not the size of the mixed existing_positions set. cold_start_daily_used
    # is incremented once per today's ENTER row in build_account_state.
    today_enters_count = account_state.get("cold_start_daily_used", 0)
    sys_result = sentinel.check_system(
        account_state,
        today_enters=today_enters_count,
        market_state={"data_provider": data_provider} if 'data_provider' in dir() else None,
    )
    if sys_result.is_block:
        logger.error("Sentinel SYSTEM HALT: %s — skipping run. Details: %s",
                     sys_result.reason, sys_result.details)
        summary["errors"] += 1
        try:
            from agent.notifications.email_sender import send_alert
            send_alert(
                f"Sentinel HALT: {sys_result.reason}",
                f"Reason: {sys_result.reason}\nDetails: {sys_result.details}\nRun at {summary['timestamp']}",
            )
        except Exception as e:
            logger.error("Failed to send HALT alert: %s", e)
        return summary

    if not signals:
        logger.info("No signals to process this minute")
    else:
        # Process each signal
        for signal in signals:
            ticker = signal.get("ticker", "?")
            try:
                # Data Sentinel gate (shadow mode by default)
                sentinel_result = sentinel.check_signal(signal, market_state={
                    "account_state": account_state,
                    "data_provider": data_provider if 'data_provider' in dir() else None,
                })
                if sentinel_result.is_block:
                    sentinel_blocks += 1
                    logger.info("Sentinel BLOCK %s: %s", ticker, sentinel_result.reason)
                    summary["skips"] += 1
                    continue
                if sentinel_result.is_warn:
                    logger.warning("Sentinel WARN %s: %s", ticker, sentinel_result.reason)

                # News Detective — log-only, never blocks; gated off per-minute (TASK-176)
                _maybe_write_news(news_detective, ticker)

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
                    # TASK-105: count a real ENTER only if the portfolio write
                    # persisted; a failed write is surfaced as an error, not a
                    # silent success.
                    _record_entry_outcome(enriched, summary)
                    # Update local state for next signal in batch
                    account_state["existing_positions"].add(ticker)
                    account_state["cold_start_concurrent_used"] += 1
                    account_state["cold_start_daily_used"] += 1
                    # Bug #5 fix: keep per-ticker count current within the
                    # batch so Filter 9 sees re-entries from the same run.
                    account_state["entries_today_by_ticker"][ticker] = (
                        account_state["entries_today_by_ticker"].get(ticker, 0) + 1
                    )
                    logger.info("ENTER %s: score=%.2f, order=%s",
                                ticker, decision.score, enriched.order_id or "n/a")
                else:
                    summary["skips"] += 1
                    logger.debug("SKIP %s: %s", ticker, decision.skip_reason or decision.reason)
            except Exception as e:
                summary["errors"] += 1
                logger.error("Failed signal %s: %s", ticker, e, exc_info=True)
                continue

    # TASK-125: one batched skip_summary write per run (never fails the run).
    # Deliberately NOT counted in summary["errors"] — a quota incident would
    # otherwise trigger the alert email every minute.
    try:
        summary["skip_summary_rows"] = decision_logger.flush_skip_summary()
    except Exception as e:
        logger.warning("skip_summary flush failed (non-fatal): %s", e)

    # TASK-128: one shadow-gate summary row per run (explicit-gate vs live Score gate).
    try:
        summary["shadow_gate_rows"] = decision_logger.flush_shadow_gate_summary()
    except Exception as e:
        logger.warning("shadow_gate flush failed (non-fatal): %s", e)

    # Monitor positions
    try:
        monitor_stats = position_manager.monitor_all()
        summary["portfolio_write_cells"] = _portfolio_flush()  # TASK-192: 1 batch_update for all monitored
        summary["monitored"] = sum(monitor_stats.values()) if isinstance(monitor_stats, dict) else 0
        logger.info("Position monitor: %s", monitor_stats)
    except Exception as e:
        logger.error("Position monitor failed: %s", e, exc_info=True)
        summary["errors"] += 1

    # EOD close
    if is_eod_window(now):
        try:
            eod_stats = position_manager.eod_close_all()
            _portfolio_flush()  # TASK-192: 1 batch_update for all EOD closes
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
        "Run complete: signals=%d, decisions=%d (ENTER=%d, SKIP=%d), errors=%d, sentinel_blocks=%d",
        summary["signals"], summary["decisions"],
        summary["enters"], summary["skips"], summary["errors"],
        sentinel_blocks,
    )
    # TASK-58: one-line read summary per run (per-tab API reads, cache misses only).
    try:
        import sheets_manager as _sm_rc
        _rc = _sm_rc.get_read_counts()
        summary["sheet_reads"] = _rc
        logger.info("Sheets API reads this run (cache misses): total=%d %s",
                    sum(_rc.values()), _rc)
    except Exception:
        pass
    return summary


if __name__ == "__main__":
    run()
