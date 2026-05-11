"""
agent/sentinel/checks/completeness.py
──────────────────────────────────────
Check 1: required fields completeness.

Validates that signal has all 7 required metrics:
ticker, score, price, mxv, run_up, atrx, rsi

Missing or None → BLOCK with reason MISSING_METRICS.
"""
from typing import Dict, Any
from agent.sentinel.data_sentinel import SentinelResult

REQUIRED_FIELDS = ["ticker", "score", "price", "mxv", "run_up", "atrx", "rsi"]


def check_completeness(signal: Dict[str, Any],
                       market_state: Dict[str, Any]) -> SentinelResult:
    """Verify all 7 required metrics are present and not None."""
    missing = []
    for field in REQUIRED_FIELDS:
        val = signal.get(field)
        if val is None or val == "" or (isinstance(val, str) and val.lower() in ("nan", "none", "null")):
            missing.append(field)

    if missing:
        return SentinelResult(
            decision="BLOCK",
            reason="MISSING_METRICS",
            details={
                "ticker": signal.get("ticker", "?"),
                "missing_fields": missing,
                "count": len(missing),
            },
        )

    return SentinelResult(
        decision="ALLOW",
        reason="OK",
        details={"ticker": signal.get("ticker", "?")},
    )
