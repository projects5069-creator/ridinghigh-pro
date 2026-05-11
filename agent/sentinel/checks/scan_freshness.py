"""
agent/sentinel/checks/scan_freshness.py
────────────────────────────────────────
Check 2: scan age in minutes.

Validates that the scan_time is not too old relative to current time.
Thresholds from config:
  - SENTINEL_SCAN_MAX_AGE_MINUTES (default 3) → WARN
  - SENTINEL_SCAN_MAX_AGE_BLOCK_MINUTES (default 5) → BLOCK
"""
from typing import Dict, Any
from datetime import datetime
import pytz
from agent.sentinel.data_sentinel import SentinelResult

PERU_TZ = pytz.timezone("America/Lima")


def _parse_scan_time(signal: Dict[str, Any]) -> int:
    """Extract scan minute-of-day from signal. Returns -1 if unparseable."""
    scan_time = signal.get("scan_time") or signal.get("ScanTime")
    if not scan_time:
        return -1
    try:
        parts = str(scan_time).strip().split(":")
        if len(parts) < 2:
            return -1
        h, m = int(parts[0]), int(parts[1])
        return h * 60 + m
    except (ValueError, TypeError):
        return -1


def check_scan_freshness(signal: Dict[str, Any],
                          market_state: Dict[str, Any]) -> SentinelResult:
    """Verify scan_time is recent (< 5 min old)."""
    from config import (
        SENTINEL_SCAN_MAX_AGE_MINUTES,
        SENTINEL_SCAN_MAX_AGE_BLOCK_MINUTES,
    )

    scan_minute = _parse_scan_time(signal)
    if scan_minute < 0:
        return SentinelResult(
            decision="WARN",
            reason="UNPARSEABLE_SCAN_TIME",
            details={"ticker": signal.get("ticker", "?"), "scan_time": signal.get("scan_time", "?")},
        )

    now_peru = datetime.now(PERU_TZ)
    now_minute = now_peru.hour * 60 + now_peru.minute
    age_min = now_minute - scan_minute

    # Handle day rollover edge case (negative age = next day, treat as fresh)
    if age_min < 0:
        age_min = abs(age_min)

    if age_min >= SENTINEL_SCAN_MAX_AGE_BLOCK_MINUTES:
        return SentinelResult(
            decision="BLOCK",
            reason="STALE_SCAN",
            details={
                "ticker": signal.get("ticker", "?"),
                "scan_age_min": age_min,
                "block_threshold": SENTINEL_SCAN_MAX_AGE_BLOCK_MINUTES,
            },
        )
    if age_min >= SENTINEL_SCAN_MAX_AGE_MINUTES:
        return SentinelResult(
            decision="WARN",
            reason="AGING_SCAN",
            details={
                "ticker": signal.get("ticker", "?"),
                "scan_age_min": age_min,
                "warn_threshold": SENTINEL_SCAN_MAX_AGE_MINUTES,
            },
        )

    return SentinelResult(
        decision="ALLOW",
        reason="OK",
        details={"ticker": signal.get("ticker", "?"), "scan_age_min": age_min},
    )
