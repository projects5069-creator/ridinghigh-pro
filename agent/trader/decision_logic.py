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
    AGENT_VOLUME_MIN, AGENT_MIN_SCANPRICE_USD, CHRONIC_DROPPER_BLACKLIST, AGENT_MARKET_CAP_MIN, AGENT_MARKET_CAP_MAX,
    AGENT_TP_PCT, AGENT_SL_PCT, AGENT_POSITION_SIZE_USD,
    AGENT_COLD_START_ENABLED, AGENT_COLD_START_MAX_CONCURRENT,
    AGENT_COLD_START_MAX_DAILY, AGENT_MAX_REENTRIES_PER_TICKER,
    AGENT_ROCKET_GUARD_RUNUP, AGENT_ROCKET_GUARD_PTH,
)
from agent.trader.score_calculator import calculate_agent_score
from agent.perception.data_quality import validate as validate_quality
from agent.perception.tradability import check_tradability
import config as _config  # TASK-128: read EXPLICIT_GATE_MODE at call time (test-monkeypatchable)
import logging

logger = logging.getLogger("agent.trader.decision_logic")

PERU_TZ = pytz.timezone("America/Lima")


# ── Decision dataclass — 43 fields (42 mapped to decision_log Sheet) ────────────────

@dataclass
class Decision:
    """Single decision record. 42 of its 43 fields map to decision_log Sheet (42 cols)."""

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
    price_vs_sma20: Optional[float] = None  # % distance from 20-day SMA. None if unavailable.
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
    # TASK-105: True until a paper_portfolio write fails. Set False by
    # OrderManager.execute() when the entry-write is not persisted, so the
    # orchestrator can surface/count the failure instead of swallowing it.
    portfolio_written: bool = True

    # TASK-128 shadow observer (runtime-only; NOT a decision_log column): what the
    # explicit-only gate (Score decoupled) would decide, set by _observe_explicit_gate.
    shadow_explicit_skip_reason: Optional[str] = None  # None = explicit gate would ALLOW
    shadow_explicit_divergence: bool = False  # True only when live SKIPs on Score but explicit allows
    # TASK-128 T-B shadow observer (runtime-only): would the MxV<=-100 AND price>=$3
    # entry-to-tracking gate enter? Set by _observe_mxv_price_gate; never affects d.action.
    shadow_mxv_price_enter: bool = False


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


def _observe_explicit_gate(d: Decision, signal: Dict[str, Any], quality: Dict[str, Any],
                           live_skip_reason: Optional[str]) -> None:
    """Shadow observer (TASK-128): record what the explicit-only gate would decide.

    Mirrors Sentinel shadow mode. Reads config.EXPLICIT_GATE_MODE at call time:
      - "off" → full no-op (no computation, fields stay at their defaults).
      - otherwise (shadow / active) → compute the explicit-only verdict via the
        Step-1 seam (`include_score_gate=False`, no duplicate chain, §10) and attach it.
    Divergence = the live logic SKIPs on Score but the explicit gate would ALLOW —
    the only behaviour change Score-decoupling can produce. **Never sets d.action.**
    active mode is RESERVED (the future Stage-2 live flip): it still only observes here.
    """
    mode = getattr(_config, "EXPLICIT_GATE_MODE", "shadow")
    if mode == "off":
        return
    d.shadow_explicit_skip_reason = _check_filters(d, signal, quality, include_score_gate=False)
    if (live_skip_reason and live_skip_reason.startswith("SCORE_TOO_LOW")
            and d.shadow_explicit_skip_reason is None):
        d.shadow_explicit_divergence = True
        logger.info(
            "[EXPLICIT-GATE SHADOW] %s would ALLOW — live SKIP (%s)",
            d.ticker, live_skip_reason,
        )


def mxv_price_would_enter(mxv, price) -> bool:
    """TASK-128 T-B: the ONLY entry-to-tracking condition עמיחי approved —
    MxV <= AGENT_MXV_MAX (-100) AND price >= AGENT_MIN_SCANPRICE_USD ($3). Pure predicate,
    no side effects. Used by the SEPARATE shadow observer below; NEVER part of
    _check_filters (the live gate), so it cannot change live behaviour."""
    if mxv is None or price is None:
        return False
    try:
        return float(mxv) <= AGENT_MXV_MAX and float(price) >= AGENT_MIN_SCANPRICE_USD
    except (TypeError, ValueError):
        return False


def _observe_mxv_price_gate(d: Decision, signal: Dict[str, Any]) -> None:
    """Shadow observer (TASK-128 T-B): record whether the MxV+price entry-to-tracking gate
    would enter. Mirrors _observe_explicit_gate — runtime-only, reads
    config.MXV_PRICE_GATE_MODE at call time, **never sets d.action**, separate from
    _check_filters. "off" -> no-op. Promotion to active is TASK-194, not here."""
    mode = getattr(_config, "MXV_PRICE_GATE_MODE", "shadow")
    if mode == "off":
        return
    d.shadow_mxv_price_enter = mxv_price_would_enter(d.mxv, d.price)


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
        price_vs_sma20=signal.get("price_vs_sma20"),
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
        # TASK-194 Stage-1: Score gate (Filter 1) is honored UNLESS EXPLICIT_GATE_MODE=="active"
        # (the Score-decouple flip). shadow/off/any-other -> Score still gates (safe default).
        # Reversible: flip/revert = the EXPLICIT_GATE_MODE config value alone, no code change.
        _score_gate_on = getattr(_config, "EXPLICIT_GATE_MODE", "shadow") != "active"
        skip_reason = _check_filters(d, signal, quality, include_score_gate=_score_gate_on)

        # TASK-128 shadow observer — measure what the explicit-only gate (Score
        # decoupled) would decide. Observe-only: never alters the live action below.
        _observe_explicit_gate(d, signal, quality, skip_reason)
        # TASK-128 T-B: separate shadow observer for the MxV+price entry-to-tracking gate.
        # Observe-only; never alters the live action below.
        _observe_mxv_price_gate(d, signal)

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


def _check_filters(d: Decision, signal: Dict[str, Any], quality: Dict[str, Any],
                   include_score_gate: bool = True) -> Optional[str]:
    """
    Run all entry filters. Returns skip_reason string if any fails, else None.
    Order: most likely failures first for efficiency.

    include_score_gate: when True (default, byte-identical to prior behavior) the
        Score gate (Filter 1) is enforced. When False, ONLY Filter 1 is skipped —
        filters 2-11 (the explicit proven gates) still run. This is the Option-B
        explicit-only gate used by the shadow observer (TASK-128) to measure, forward,
        what would change if Score were decoupled from entry (resolves 141+174).
    """
    # Filter 1: Score
    if include_score_gate and d.score < AGENT_MIN_SCORE:
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

    # Filter 4b (L6 — Layers paradigm, 2026-05-25): ScanPrice minimum
    # Sub-$3 stocks have wide spreads, halt risk, and questionable borrow availability.
    # Backtest: blocking <$3 contributed +129pp improvement (winners median $7.26 vs toxic $3.61).
    # Treats price=None/0 as PRICE_TOO_LOW (safer than DATA_ERROR for missing price).
    if d.price is None or d.price < AGENT_MIN_SCANPRICE_USD:
        _price_str = f"${d.price:.2f}" if d.price is not None else "None"
        return f"PRICE_TOO_LOW: {_price_str} < ${AGENT_MIN_SCANPRICE_USD}"

    # Filter 4c (Stage 2 — Layers, 2026-05-26): chronic dropper blacklist
    # Tickers identified via DropsLab cross-reference as 3+ drops in 30d.
    # AEHL + TDIC together account for ~$120 of DRY_RUN losses in Apr+May.
    if d.ticker in CHRONIC_DROPPER_BLACKLIST:
        return f"BLACKLISTED_TICKER: {d.ticker} in chronic dropper list"

    # Filter 4d (L3 — Layers paradigm, 2026-05-26): Toxic Profile
    # AND condition (both must be true to block):
    #   - RSI > 88  (extreme overbought, toxic median was 92.61)
    #   - Price/SMA20 > 250  (price 250%+ above 20-day mean, toxic median 305%)
    # Winners typically have RSI 80-86 AND Price/SMA20 150-220 — both fail this AND.
    # If price_vs_sma20 is None (data unavailable), filter is SKIPPED — defaults to
    # "trust the other filters" rather than block-on-missing-data.
    if d.rsi is not None and d.rsi > 88:
        if d.price_vs_sma20 is not None and d.price_vs_sma20 > 250:
            return f"TOXIC_PROFILE: RSI={d.rsi:.1f}>88 AND Price/SMA20={d.price_vs_sma20:.0f}%>250"

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

    # Filter 11: ROCKET_GUARD — block shorting a stock still climbing vertically.
    # A stock with high RunUp AND price still near its intraday high is a
    # rocket mid-ascent, not a faded pump. Shorting it fights the trend.
    # Both conditions required (AND): high RunUp alone or near-high alone
    # is not enough. PriceToHigh is read straight off the signal dict.
    _pth = signal.get("price_to_high", 0.0)
    try:
        _pth = float(_pth)
    except (TypeError, ValueError):
        _pth = 0.0
    if d.run_up >= AGENT_ROCKET_GUARD_RUNUP and _pth >= AGENT_ROCKET_GUARD_PTH:
        return (f"ROCKET_GUARD: {d.ticker} still climbing — "
                f"RunUp={d.run_up:.1f}% >= {AGENT_ROCKET_GUARD_RUNUP}% AND "
                f"PriceToHigh={_pth:.1f}% >= {AGENT_ROCKET_GUARD_PTH}%")

    return None  # all filters passed
