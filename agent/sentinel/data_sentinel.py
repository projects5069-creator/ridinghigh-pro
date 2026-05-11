"""
agent/sentinel/data_sentinel.py
────────────────────────────────
DataSentinel — main gatekeeper class.

Runs all enabled checks on a signal before The Trader evaluates it.
Returns SentinelResult: ALLOW / WARN / BLOCK + reason + details.

Shadow mode: result is logged but orchestrator ignores BLOCK.
Active mode: BLOCK actually prevents trader.evaluate().
"""
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable, Optional, Literal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger("agent.sentinel")


# ────────────────────────────────────────────────────────────────────
# Result types
# ────────────────────────────────────────────────────────────────────

DecisionType = Literal["ALLOW", "WARN", "BLOCK"]


@dataclass
class SentinelResult:
    """Result from running all sentinel checks on a signal."""
    decision: DecisionType
    reason: str  # short code: "STALE_FINVIZ_PRICE", "MISSING_METRICS", etc.
    details: Dict[str, Any] = field(default_factory=dict)
    checks_run: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)

    @property
    def is_block(self) -> bool:
        return self.decision == "BLOCK"

    @property
    def is_warn(self) -> bool:
        return self.decision == "WARN"

    @property
    def is_allow(self) -> bool:
        return self.decision == "ALLOW"

    def to_log_dict(self) -> Dict[str, Any]:
        """Compact dict for decision_log columns."""
        return {
            "sentinel_result": self.decision,
            "sentinel_reason": self.reason,
            "sentinel_details": str(self.details)[:200],
        }


# ────────────────────────────────────────────────────────────────────
# DataSentinel
# ────────────────────────────────────────────────────────────────────

class DataSentinel:
    """
    Main gatekeeper. Runs all enabled checks on a signal.

    Usage:
        sentinel = DataSentinel()
        result = sentinel.check_signal(signal, market_state={})
        if result.is_block:
            decision_logger.log_skip(...)
            continue
    """

    def __init__(self):
        from config import (
            DATA_SENTINEL_ENABLED,
            SENTINEL_MODE,
        )
        self.enabled = DATA_SENTINEL_ENABLED
        self.mode = SENTINEL_MODE  # "shadow" | "active" | "off"
        self._checks: List[Callable] = []
        self._load_checks()
        logger.info("DataSentinel initialized: enabled=%s, mode=%s, checks=%d",
                    self.enabled, self.mode, len(self._checks))

    def _load_checks(self):
        """Load enabled per-signal checks from config."""
        from config import (
            SENTINEL_CHECK_COMPLETENESS,
            SENTINEL_CHECK_SCAN_FRESHNESS,
            SENTINEL_CHECK_PRICE_SANITY,
        )

        if SENTINEL_CHECK_COMPLETENESS:
            from agent.sentinel.checks.completeness import check_completeness
            self._checks.append(("completeness", check_completeness))

        if SENTINEL_CHECK_SCAN_FRESHNESS:
            from agent.sentinel.checks.scan_freshness import check_scan_freshness
            self._checks.append(("scan_freshness", check_scan_freshness))

        if SENTINEL_CHECK_PRICE_SANITY:
            from agent.sentinel.checks.price_sanity import check_price_sanity
            self._checks.append(("price_sanity", check_price_sanity))

        # Phase 3 (next):
        # SENTINEL_CHECK_PRICE_FRESHNESS (Alpaca call)
        # SENTINEL_CHECK_QUOTA (writes/min counter)
        # SENTINEL_CHECK_PROVIDER (heartbeat)

    def check_signal(self, signal: Dict[str, Any],
                     market_state: Optional[Dict[str, Any]] = None) -> SentinelResult:
        """
        Run all enabled checks on a signal.

        Args:
            signal: dict from timeline_live row (ticker, score, price, etc.)
            market_state: optional dict with provider clients, account info

        Returns:
            SentinelResult with overall decision (BLOCK > WARN > ALLOW)
        """
        if not self.enabled or self.mode == "off":
            return SentinelResult(decision="ALLOW", reason="SENTINEL_DISABLED")

        market_state = market_state or {}
        checks_run = []
        checks_failed = []
        worst_decision: DecisionType = "ALLOW"
        worst_reason = "OK"
        worst_details: Dict[str, Any] = {}

        for check_name, check_fn in self._checks:
            try:
                result = check_fn(signal, market_state)
                checks_run.append(check_name)

                if result.decision == "BLOCK":
                    checks_failed.append(check_name)
                    if worst_decision != "BLOCK":
                        worst_decision = "BLOCK"
                        worst_reason = result.reason
                        worst_details = result.details
                elif result.decision == "WARN" and worst_decision == "ALLOW":
                    checks_failed.append(check_name)
                    worst_decision = "WARN"
                    worst_reason = result.reason
                    worst_details = result.details
            except Exception as e:
                logger.error("Sentinel check '%s' raised: %s", check_name, e, exc_info=True)
                checks_failed.append(check_name)
                # On exception: treat as WARN but don't block
                if worst_decision == "ALLOW":
                    worst_decision = "WARN"
                    worst_reason = f"CHECK_ERROR_{check_name}"

        # Shadow mode override: log decision but return ALLOW for actual blocking
        effective_decision = worst_decision
        if self.mode == "shadow" and worst_decision == "BLOCK":
            logger.info("[SHADOW] Would BLOCK %s: %s — but returning ALLOW (shadow mode)",
                        signal.get("ticker", "?"), worst_reason)
            effective_decision = "ALLOW"

        return SentinelResult(
            decision=effective_decision,
            reason=worst_reason,
            details=worst_details,
            checks_run=checks_run,
            checks_failed=checks_failed,
        )

    def check_system(self, account_state: Dict[str, Any],
                     today_enters: int = 0) -> SentinelResult:
        """
        System-level check (runs once per orchestrator run, not per signal).

        Validates global state: paper_portfolio integrity, etc.
        Returns BLOCK if entire run should HALT.
        """
        if not self.enabled or self.mode == "off":
            return SentinelResult(decision="ALLOW", reason="SENTINEL_DISABLED")

        from config import SENTINEL_CHECK_POSITION_SYNC

        if SENTINEL_CHECK_POSITION_SYNC:
            from agent.sentinel.checks.position_sync import check_position_sync
            result = check_position_sync(account_state, today_enters)

            # Shadow mode override
            if self.mode == "shadow" and result.decision == "BLOCK":
                logger.info("[SHADOW] System check would HALT: %s", result.reason)
                return SentinelResult(decision="ALLOW", reason=f"SHADOW_{result.reason}",
                                      details=result.details)
            return result

        return SentinelResult(decision="ALLOW", reason="NO_SYSTEM_CHECKS")


# ────────────────────────────────────────────────────────────────────
# Singleton helper (used by orchestrator)
# ────────────────────────────────────────────────────────────────────

_sentinel_instance: Optional[DataSentinel] = None


def get_sentinel() -> DataSentinel:
    """Get or create the global sentinel instance."""
    global _sentinel_instance
    if _sentinel_instance is None:
        _sentinel_instance = DataSentinel()
    return _sentinel_instance
