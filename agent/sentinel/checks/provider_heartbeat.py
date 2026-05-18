"""
agent/sentinel/checks/provider_heartbeat.py
────────────────────────────────────────────
SYSTEM-level check: data provider liveness.

Calls get_latest_bar("AAPL") as canary. If 3 consecutive failures
within last 5 minutes → HALT (data_provider is down).

State tracked in module-level variables — persists across calls
within same orchestrator run.
"""
from typing import Dict, Any
import time
import logging
from collections import deque
from agent.sentinel.data_sentinel import SentinelResult

logger = logging.getLogger("agent.sentinel.provider_heartbeat")

# Recent heartbeat results: deque of (timestamp, success_bool)
_heartbeat_results: deque = deque(maxlen=10)
_CANARY_TICKER = "AAPL"
_FAILURE_WINDOW_SEC = 300  # 5 min
_MIN_FAILURES_FOR_HALT = 3


def _perform_heartbeat(market_state: Dict[str, Any]) -> bool:
    """Try to fetch AAPL bar. Returns True if successful."""
    try:
        data_provider = market_state.get("data_provider")
        if data_provider is None:
            from data_provider import get_data_provider
            data_provider = get_data_provider()

        bar = data_provider.get_latest_bar(_CANARY_TICKER)
        if bar and isinstance(bar, dict) and "close" in bar:
            return True
        return False
    except Exception as e:
        logger.warning("Heartbeat failed: %s", e)
        return False


def check_provider_heartbeat(market_state: Dict[str, Any]) -> SentinelResult:
    """System-level check. Returns BLOCK if provider down."""
    now = time.time()
    success = _perform_heartbeat(market_state)
    _heartbeat_results.append((now, success))

    # Count failures in last 5 minutes
    cutoff = now - _FAILURE_WINDOW_SEC
    recent_failures = sum(
        1 for ts, ok in _heartbeat_results
        if ts >= cutoff and not ok
    )

    if recent_failures >= _MIN_FAILURES_FOR_HALT:
        return SentinelResult(
            decision="BLOCK", reason="PROVIDER_DOWN",
            details={
                "canary": _CANARY_TICKER,
                "recent_failures": recent_failures,
                "window_min": _FAILURE_WINDOW_SEC // 60,
            },
        )

    if not success:
        return SentinelResult(
            decision="WARN", reason="HEARTBEAT_FAILED",
            details={"canary": _CANARY_TICKER, "recent_failures": recent_failures},
        )

    return SentinelResult(
        decision="ALLOW", reason="OK",
        details={"canary": _CANARY_TICKER, "alive": True},
    )


def reset():
    """For testing."""
    _heartbeat_results.clear()
