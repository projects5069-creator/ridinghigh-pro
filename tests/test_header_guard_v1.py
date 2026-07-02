"""TASK-217 Task4: provisioning must FAIL LOUD when an existing agent tab's
header has drifted from the canonical schema — instead of silently skipping it
(_already_done), which is exactly how the 2026-07 paper_portfolio tab kept a
stale 23-col header and corrupted 8 rows.

header_matches_canonical is a pure list comparison (no Sheets); assert_header_canonical
raises on drift so the rotation surfaces it instead of writing into a bad tab.
"""
import pytest

from agent.setup.create_agent_sheets import (
    header_matches_canonical,
    assert_header_canonical,
)

CANON = [
    "PositionID", "Ticker", "EntryDate", "EntryTime", "EntryPrice", "Quantity",
    "PositionSizeUSD", "Side", "EntryOrderID", "TPOrderID", "SLOrderID",
    "TPPrice", "SLPrice", "CurrentPrice", "UnrealizedPnL", "UnrealizedPnLPct",
    "Status", "ExitPrice", "ExitDate", "ExitTime", "ExitReason",
    "RealizedPnL", "RealizedPnLPct", "LastUpdated", "DataQuality",
]
# The real 2026-07 drift: TPPrice/SLPrice missing, 2 phantom trailing blanks.
STALE = [c for c in CANON if c not in ("TPPrice", "SLPrice")] + ["", ""]


def test_canonical_passes():
    assert header_matches_canonical(CANON, CANON) is True


def test_drift_missing_cols_detected():
    missing = [c for c in CANON if c not in ("TPPrice", "SLPrice")]
    assert header_matches_canonical(missing, CANON) is False


def test_phantom_trailing_detected():
    assert header_matches_canonical(STALE, CANON) is False


def test_assert_raises_on_drift():
    with pytest.raises(ValueError):
        assert_header_canonical(STALE, CANON, "paper_portfolio")


def test_assert_passes_on_canonical():
    # must not raise
    assert_header_canonical(CANON, CANON, "paper_portfolio")
