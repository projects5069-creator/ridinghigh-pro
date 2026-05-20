"""
agent/sentinel/checks/position_sync.py
───────────────────────────────────────
SYSTEM-level check: paper_portfolio integrity.

Runs ONCE per orchestrator run (not per signal).
Compares paper_portfolio open positions vs decision_log ENTERs of today.

If decision_log shows N ENTERs today but paper_portfolio has 0 open positions,
this strongly suggests paper_portfolio failed to load (e.g. 429 quota error).

Returns HALT (system-wide stop) if mismatch detected.
"""
from typing import Dict, Any, List
import logging
from agent.sentinel.data_sentinel import SentinelResult

logger = logging.getLogger("agent.sentinel.position_sync")


def check_position_sync(account_state: Dict[str, Any],
                         today_enters: int = 0) -> SentinelResult:
    """
    System-level check. NOT called per-signal.

    Args:
        account_state: dict with 'existing_positions' set
        today_enters: count of today's ENTER decisions from decision_log

    Returns:
        SentinelResult — BLOCK means HALT entire run
    """
    # FIX: open_count must be real OPEN rows from paper_portfolio,
    # not len(existing_positions) — that set also holds today's ENTER
    # tickers, which would mask a genuine sync failure.
    open_count = account_state.get("open_position_count", 0)

    # 2026-05-20 FIX: if paper_portfolio fetch failed (e.g. 429), we cannot
    # judge sync state. Return WARN instead of BLOCK — a fetch failure is a
    # quota/network issue, not real position drift. BLOCK in active mode
    # would HALT the entire run, which is wrong when the real problem is
    # just a transient API hiccup. The next minute the cache will be warm.
    if account_state.get("paper_portfolio_fetch_failed", False):
        return SentinelResult(
            decision="WARN",
            reason="POSITION_SYNC_DEFERRED",
            details={
                "today_enters": today_enters,
                "open_positions": open_count,
                "hint": "paper_portfolio fetch failed — likely 429, retry next minute",
            },
        )

    # If no ENTERs today, no way to detect mismatch
    if today_enters == 0:
        return SentinelResult(
            decision="ALLOW",
            reason="NO_ENTERS_TODAY",
            details={"open_positions": open_count},
        )

    # Suspicious: ENTERs happened but no open positions visible
    # (and fetch did NOT fail — so this is a real drift, not a quota issue)
    if today_enters > 0 and open_count == 0:
        return SentinelResult(
            decision="BLOCK",
            reason="POSITION_SYNC_FAILED",
            details={
                "today_enters": today_enters,
                "open_positions": open_count,
                "hint": "paper_portfolio loaded OK but shows 0 OPEN despite ENTERs today — real drift",
            },
        )

    # Discrepancy too large (e.g. 5 ENTERs but only 1 open)
    # Note: some may have closed legitimately, so allow some gap
    if today_enters >= 3 and open_count < today_enters // 3:
        return SentinelResult(
            decision="WARN",
            reason="POSITION_SYNC_PARTIAL",
            details={
                "today_enters": today_enters,
                "open_positions": open_count,
            },
        )

    return SentinelResult(
        decision="ALLOW",
        reason="OK",
        details={"today_enters": today_enters, "open_positions": open_count},
    )
