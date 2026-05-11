"""
agent/sentinel/checks/dummy_allow.py
─────────────────────────────────────
Phase 1 dummy check — always returns ALLOW.

Used to verify the integration plumbing works end-to-end before
real checks are added in Phase 2.
"""
from typing import Dict, Any
from agent.sentinel.data_sentinel import SentinelResult


def check_dummy_allow(signal: Dict[str, Any],
                      market_state: Dict[str, Any]) -> SentinelResult:
    """Always returns ALLOW. Placeholder until Phase 2."""
    return SentinelResult(
        decision="ALLOW",
        reason="DUMMY_CHECK_OK",
        details={"ticker": signal.get("ticker", "?")},
    )
