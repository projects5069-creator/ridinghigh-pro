"""
Score Calculator — Agent wrapper around formulas.calculate_score().

This module is intentionally a thin wrapper with NO additional logic.
The agent MUST produce identical scores to the scanner — any divergence
is a critical bug caught by test_scanner_agent_match.py.

Why a wrapper exists at all:
- Provides a single import point for all agent modules
- Validates input keys before calling formulas (fail-fast)
- Will serve as the integration point for Score Analytics (M7)

Used by: decision_logic.py (M3), score_analytics.py (M7)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from formulas import calculate_score


REQUIRED_METRICS = {"mxv", "run_up", "atrx", "rsi", "rel_vol", "change", "typical_price_dist"}


def calculate_agent_score(metrics: dict) -> float:
    """
    Calculate score for a signal using the scanner's formula.

    Args:
        metrics: dict with keys: mxv, run_up, atrx, rsi, rel_vol,
                 change, typical_price_dist. Values must be numeric.
                 Note: key 'change' (not 'scan_change'); ScanChange is the Sheet column display name.

    Returns:
        float: Score 0-100 (rounded to 2 decimals by formulas.py).

    Raises:
        ValueError: If any required metric key is missing.
    """
    missing = REQUIRED_METRICS - set(metrics.keys())
    if missing:
        raise ValueError(f"Missing required metrics: {missing}")

    return calculate_score(metrics)
