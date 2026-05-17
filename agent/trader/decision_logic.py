"""
Decision tree for the agent. Takes a raw signal + account state
and returns a Decision dataclass with full reasoning.

Decision flow (in order):
  1. Pre-filter — basic data sanity (price, volume, ticker valid)
  2. Score check — meets AGENT_MIN_SCORE?
  3. Entry criteria — MxV, RunUp, market cap, volume thresholds
  4. Data quality — quality_score >= 0.5?
  5. Tradability — is_shortable? borrow_available?
  6. Safety — no existing position, sufficient buying power
  7. Cold start — within concurrent + daily limits
  8. Position calculation — size, qty, TP/SL prices

Result: Decision with action="ENTER" or "SKIP" + specific reason.

Used by: trader.py (M3), decision_logger.py (M4)
"""

import time
import sys
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import (
    AGENT_MIN_SCORE, AGENT_MXV_MAX, AGENT_RUNUP_MIN,
    AGENT_VOLUME_MIN, AGENT_MARKET_CAP_MIN, AGENT_MARKET_CAP_MAX,
    AGENT_TP_PCT, AGENT_SL_PCT, AGENT_POSITION_SIZE_USD,
    AGENT_COLD_START_ENABLED, AGENT_COLD_START_MAX_CONCURRENT,
    AGENT_COLD_START_MAX_DAILY, AGENT_MAX_REENTRIES_PER_TICKER,
)
from agent.trader.score_calculator import calculate_agent_score
from agent.perception.data_quality import validate as validate_quality
from agent.perception.tradability import check_tradability

PERU_TZ = pytz.timezone("America/Lima")


# ── Decision dataclass — 41 fields matching decision_log Sheet ────────────────

@dataclass
class Decision:
    """Single decision record. Maps 1:1 to decision_log Sheet (41 cols)."""

    # Identity (5)
    decision_id: Optional[str] = None  # filled by M4 logger
    timestamp: str = ""
    ticker: str = ""
    signal_source: str = "timeline_live"
    agent_mode: str = "DRY_RUN"

    # Action (3)
    action: str = ""              # "ENTER" or "SKIP"
    reason: str = ""              # human-readable
    skip_reason: Optional[str] = None  # specific filter that failed

    # Signal data (7)
    price: float = 0.0
    volume: int = 0
    market_cap: float = 0.0
    float_shares: Optional[float] = None
    open_price: float = 0.0
    high: float = 0.0
    low: float = 0.0

    # Metrics (9)
    score: float = 0.0
    mxv: float = 0.0
    run_up: float = 0.0
    atrx: float = 0.0
    rsi: float = 0.0
    typical_price_dist: float = 0.0
    rel_vol: float = 0.0
    scan_change: float = 0.0       # stored as "change" in metrics dict
    float_pct: Optional[float] = None

    # Decision timing (1)
    decision_time_ms: int = 0

    # Quality (1)
    confidence_score: float = 1.0  # from data_quality.validate

    # Tradability (4)
    is_shortable: bool = True
    borrow_fee: Optional[float] = None
    borrow_available: bool = True
    locate_status: str = "MOCK"

    # Position calc (4) — None if SKIP
    position_size_usd: Optional[float] = None
    quantity: Optional[int] = None
    tp_price: Optional[float] = None
    sl_price: Optional[float] = None

    # Safety (5)
    existing_position: bool = False
    buying_power: Optional[float] = None
    cold_start_concurrent_remaining: Optional[int] = None
    cold_start_daily_remaining: Optional[int] = None
    reentries_used_today: Optional[int] = None  # Bug #5: same-ticker entries today

    # Execution (3) — filled by M5
    order_id: Optional[str] = None
    order_status: Optional[str] = None
    execution_price: Optional[float] = None


# ── Helper functions ──────────────────────────────────────────────────────────

def _now_peru_iso() -> str:
    """ISO timestamp in Peru timezone."""
    return datetime.now(PERU_TZ).isoformat()


def _calculate_position(price: float) -> Dict[str, Any]:
    """Calculate position size, qty, TP, SL for short."""
    qty = int(AGENT_POSITION_SIZE_USD / price)
    actual_size = qty * price
    tp_price = price * (1 - AGENT_TP_PCT / 100)  # short: TP is lower
    sl_price = price * (1 + AGENT_SL_PCT / 100)  # short: SL is higher
    return {
        "position_size_usd": round(actual_size, 2),
        "quantity": qty,
        "tp_price": round(tp_price, 4),
        "sl_price": round(sl_price, 4),
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def evaluate_signal(
    signal: Dict[str, Any],
    account_state: Optional[Dict[str, Any]] = None,
) -> Decision:
    """
    Evaluate a signal and return a Decision.

    Args:
        signal: dict with raw signal data (price, volume, mxv, etc.).
                Required keys: ticker, price, volume, mxv, run_up, atrx,
                rsi, rel_vol, change, typical_price_dist, market_cap.
        account_state: dict with account state. If None, defaults applied.
                Keys: existing_positions, buying_power, cold_start_concurrent_used,
                cold_start_daily_used.

    Returns:
        Decision dataclass populated with full reasoning.
    """
    start_time = time.perf_counter()

    # Default account state if none provided (DRY_RUN with no real account)
    if account_state is None:
        account_state = {
            "existing_positions": [],
            "buying_power": 100000.0,
            "cold_start_concurrent_used": 0,
            "cold_start_daily_used": 0,
        }

    # Initialize Decision with signal data
    d = Decision(
        timestamp=_now_peru_iso(),
        ticker=signal.get("ticker", ""),
        price=signal.get("price", 0.0),
        volume=signal.get("volume", 0),
        market_cap=signal.get("market_cap", 0.0),
        float_shares=signal.get("float_shares"),
        open_price=signal.get("open", 0.0),
        high=signal.get("high", 0.0),
        low=signal.get("low", 0.0),
        mxv=signal.get("mxv", 0.0),
        run_up=signal.get("run_up", 0.0),
        atrx=signal.get("atrx", 0.0),
        rsi=signal.get("rsi", 0.0),
        typical_price_dist=signal.get("typical_price_dist", 0.0),
        rel_vol=signal.get("rel_vol", 0.0),
        scan_change=signal.get("change", 0.0),
        float_pct=signal.get("float_pct"),
    )

    try:
        # Step 1: Calculate score
        score_metrics = {
            "mxv": signal["mxv"],
            "run_up": signal["run_up"],
            "atrx": signal["atrx"],
            "rsi": signal["rsi"],
            "rel_vol": signal["rel_vol"],
            "change": signal["change"],
            "typical_price_dist": signal["typical_price_dist"],
        }
        d.score = calculate_agent_score(score_metrics)

        # Step 2: Data quality check
        quality = validate_quality({
            "atrx": signal["atrx"],
            "change": signal["change"],
            "rsi": signal["rsi"],
            "price": signal["price"],
            "volume": signal["volume"],
        })
        d.confidence_score = quality["quality_score"]

        # Step 3: Cold start state
        if AGENT_COLD_START_ENABLED:
            d.cold_start_concurrent_remaining = (
                AGENT_COLD_START_MAX_CONCURRENT - account_state["cold_start_concurrent_used"]
            )
            d.cold_start_daily_remaining = (
                AGENT_COLD_START_MAX_DAILY - account_state["cold_start_daily_used"]
            )

        d.buying_power = account_state.get("buying_power")
        d.existing_position = signal.get("ticker", "") in account_state.get("existing_positions", [])

        # Bug #5: how many times this ticker has already been entered today.
        _entries_by_ticker = account_state.get("entries_today_by_ticker", {})
        d.reentries_used_today = _entries_by_ticker.get(signal.get("ticker", ""), 0)

        # ── Decision tree ──
        skip_reason = _check_filters(d, signal, quality)

        if skip_reason:
            d.action = "SKIP"
            d.skip_reason = skip_reason
            d.reason = f"SKIP: {skip_reason}"
        else:
            # All checks passed — ENTER
            tradability = check_tradability(d.ticker)
            d.is_shortable = tradability["is_shortable"]
            d.borrow_fee = tradability["borrow_fee_pct"]
            d.borrow_available = tradability["borrow_available"]
            d.locate_status = tradability["locate_status"]

            position = _calculate_position(d.price)
            d.position_size_usd = position["position_size_usd"]
            d.quantity = position["quantity"]
            d.tp_price = position["tp_price"]
            d.sl_price = position["sl_price"]

            d.action = "ENTER"
            d.reason = (
                f"ENTER: Score={d.score:.2f}, MxV={d.mxv:.0f}, RunUp={d.run_up:.1f}%, "
                f"qty={d.quantity}, TP=${d.tp_price}, SL=${d.sl_price}"
            )

    except (KeyError, ValueError) as e:
        d.action = "SKIP"
        d.skip_reason = f"DATA_ERROR: {type(e).__name__}: {e}"
        d.reason = d.skip_reason

    finally:
        d.decision_time_ms = int((time.perf_counter() - start_time) * 1000)

    return d


def _check_filters(d: Decision, signal: Dict[str, Any], quality: Dict[str, Any]) -> Optional[str]:
    """
    Run all entry filters. Returns skip_reason string if any fails, else None.
    Order: most likely failures first for efficiency.
    """
    # Filter 1: Score
    if d.score < AGENT_MIN_SCORE:
        return f"SCORE_TOO_LOW: {d.score:.2f} < {AGENT_MIN_SCORE}"

    # Filter 2: MxV (must be very negative)
    if d.mxv > AGENT_MXV_MAX:
        return f"MXV_TOO_HIGH: {d.mxv:.0f} > {AGENT_MXV_MAX}"

    # Filter 3: RunUp
    if d.run_up < AGENT_RUNUP_MIN:
        return f"RUNUP_TOO_LOW: {d.run_up:.1f}% < {AGENT_RUNUP_MIN}%"

    # Filter 4: Volume
    if d.volume < AGENT_VOLUME_MIN:
        return f"VOLUME_TOO_LOW: {d.volume} < {AGENT_VOLUME_MIN}"

    # Filter 5: Market cap range
    if d.market_cap < AGENT_MARKET_CAP_MIN:
        return f"MARKET_CAP_TOO_SMALL: ${d.market_cap:,.0f} < ${AGENT_MARKET_CAP_MIN:,}"
    if d.market_cap > AGENT_MARKET_CAP_MAX:
        return f"MARKET_CAP_TOO_LARGE: ${d.market_cap:,.0f} > ${AGENT_MARKET_CAP_MAX:,}"

    # Filter 6: Data quality
    if not quality["is_trustworthy"]:
        return f"QUALITY_TOO_LOW: {quality['quality_score']:.2f} < 0.5; flags={quality['flags']}"

    # Filter 7: Existing position
    if d.existing_position:
        return f"EXISTING_POSITION: already short {d.ticker}"

    # Filter 8: Cold start limits
    if AGENT_COLD_START_ENABLED:
        if d.cold_start_concurrent_remaining is not None and d.cold_start_concurrent_remaining <= 0:
            return f"COLD_START_CONCURRENT_LIMIT: {AGENT_COLD_START_MAX_CONCURRENT} positions already open"
        if d.cold_start_daily_remaining is not None and d.cold_start_daily_remaining <= 0:
            return f"COLD_START_DAILY_LIMIT: {AGENT_COLD_START_MAX_DAILY} trades already today"

    # Filter 9: Re-entry limit per ticker (Bug #5 fix)
    if d.reentries_used_today is not None and d.reentries_used_today >= AGENT_MAX_REENTRIES_PER_TICKER:
        return (f"REENTRY_LIMIT: {d.ticker} already entered {d.reentries_used_today}x today "
                f"(max {AGENT_MAX_REENTRIES_PER_TICKER})")

    # Filter 10: Buying power
    if d.buying_power is not None and d.buying_power < AGENT_POSITION_SIZE_USD:
        return f"INSUFFICIENT_BUYING_POWER: ${d.buying_power:.2f} < ${AGENT_POSITION_SIZE_USD}"

    return None  # all filters passed
