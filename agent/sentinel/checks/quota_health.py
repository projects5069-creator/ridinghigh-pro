"""
agent/sentinel/checks/quota_health.py
──────────────────────────────────────
SYSTEM-level check: Google Sheets quota health.

Tracks writes/min via a rolling counter. Operates in 3 modes:
  - NORMAL: writes < SENTINEL_QUOTA_DEFENSIVE_THRESHOLD
  - DEFENSIVE: 50+ writes/min — skip non-essential writes
  - HALT: 60+ writes/min — block all new ENTERs

Caller increments counter via record_write() after each Sheets write.
Sentinel calls check_quota_health() at start of orchestrator run.
"""
from typing import Dict, Any
import time
import logging
from collections import deque
from agent.sentinel.data_sentinel import SentinelResult

logger = logging.getLogger("agent.sentinel.quota_health")

# Rolling window of write timestamps (last 60 seconds)
_write_timestamps: deque = deque()
_WINDOW_SEC = 60


def record_write():
    """Call this after every Sheets write to track quota usage."""
    now = time.time()
    _write_timestamps.append(now)
    # Trim old entries
    cutoff = now - _WINDOW_SEC
    while _write_timestamps and _write_timestamps[0] < cutoff:
        _write_timestamps.popleft()


def get_current_writes_per_min() -> int:
    """Return current writes in last 60 seconds."""
    now = time.time()
    cutoff = now - _WINDOW_SEC
    while _write_timestamps and _write_timestamps[0] < cutoff:
        _write_timestamps.popleft()
    return len(_write_timestamps)


def check_quota_health() -> SentinelResult:
    """System-level check. Returns BLOCK if quota saturated."""
    from config import (
        SENTINEL_QUOTA_DEFENSIVE_THRESHOLD,
        SENTINEL_QUOTA_HALT_THRESHOLD,
    )

    writes_per_min = get_current_writes_per_min()

    if writes_per_min >= SENTINEL_QUOTA_HALT_THRESHOLD:
        return SentinelResult(
            decision="BLOCK", reason="QUOTA_SATURATED",
            details={
                "writes_per_min": writes_per_min,
                "halt_threshold": SENTINEL_QUOTA_HALT_THRESHOLD,
            },
        )

    if writes_per_min >= SENTINEL_QUOTA_DEFENSIVE_THRESHOLD:
        return SentinelResult(
            decision="WARN", reason="QUOTA_HIGH",
            details={
                "writes_per_min": writes_per_min,
                "defensive_threshold": SENTINEL_QUOTA_DEFENSIVE_THRESHOLD,
            },
        )

    return SentinelResult(
        decision="ALLOW", reason="OK",
        details={"writes_per_min": writes_per_min},
    )


def reset():
    """For testing."""
    _write_timestamps.clear()
