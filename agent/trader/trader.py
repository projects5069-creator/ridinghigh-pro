"""
The Trader — orchestrator for the agent.

Wraps decision_logic.evaluate_signal() and provides:
- Single-signal evaluation
- Batch evaluation
- Mode awareness (DRY_RUN / LIVE_PAPER)

CRITICAL: Trader is STATELESS. State (positions, cold_start counters)
must be passed as account_state in each call. State persistence is
handled by Sheets (M4) and Alpaca (M5), not by this class.

This separation makes:
- Testing trivial (no fixture state)
- Concurrency safe (no shared state)
- M5 transition simple (state moves to Alpaca, no refactor needed)

Used by: orchestrator.py (M10), test suites
"""

import sys
import os
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import AGENT_DRY_RUN, AGENT_LIVE_PAPER
from agent.trader.decision_logic import evaluate_signal, Decision


class Trader:
    """
    Stateless decision orchestrator.

    Usage:
        trader = Trader()  # uses config defaults
        decision = trader.evaluate(signal, account_state)

        # Or batch
        decisions = trader.evaluate_batch(signals, account_state)
    """

    def __init__(self, mode: Optional[str] = None):
        """
        Args:
            mode: "DRY_RUN" or "LIVE_PAPER". If None, uses config.
        """
        if mode is not None:
            if mode not in ("DRY_RUN", "LIVE_PAPER"):
                raise ValueError(f"Invalid mode: {mode}")
            self.mode = mode
        else:
            self.mode = "LIVE_PAPER" if AGENT_LIVE_PAPER else "DRY_RUN"

    def evaluate(
        self,
        signal: Dict[str, Any],
        account_state: Optional[Dict[str, Any]] = None,
    ) -> Decision:
        """
        Evaluate a single signal.

        Args:
            signal: dict with raw signal (price, mxv, score, etc.)
            account_state: optional dict with positions, buying_power,
                          cold_start_concurrent_used, cold_start_daily_used.

        Returns:
            Decision with action="ENTER" or "SKIP" + full reasoning.
        """
        decision = evaluate_signal(signal, account_state)
        decision.agent_mode = self.mode
        return decision

    def evaluate_batch(
        self,
        signals: List[Dict[str, Any]],
        account_state: Optional[Dict[str, Any]] = None,
    ) -> List[Decision]:
        """
        Evaluate multiple signals.

        NOTE: Account state is shared across all signals. If you want
        cold_start_used to accumulate as ENTER decisions are made,
        use evaluate() in a loop with updated state instead.

        Args:
            signals: list of signal dicts
            account_state: optional dict (used for ALL signals)

        Returns:
            list of Decision objects, one per input signal
        """
        return [self.evaluate(sig, account_state) for sig in signals]
