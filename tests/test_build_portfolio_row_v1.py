"""TASK-217 Task 1: entry-write builds the paper_portfolio row BY HEADER NAME.

Root cause of the 2026-07 corruption: order_manager appended a fixed positional
25-elem list to a tab whose live header had drifted (missing TPPrice/SLPrice),
shifting every value +2. build_portfolio_row() orders values by the LIVE header
so a header drift can never silently misplace data — and raises on an unknown
column so drift surfaces loudly instead.
"""
import pytest

from agent.execution.order_manager import build_portfolio_row

CANON = [
    "PositionID", "Ticker", "EntryDate", "EntryTime", "EntryPrice", "Quantity",
    "PositionSizeUSD", "Side", "EntryOrderID", "TPOrderID", "SLOrderID",
    "TPPrice", "SLPrice", "CurrentPrice", "UnrealizedPnL", "UnrealizedPnLPct",
    "Status", "ExitPrice", "ExitDate", "ExitTime", "ExitReason",
    "RealizedPnL", "RealizedPnLPct", "LastUpdated", "DataQuality",
]


def test_ordered_by_header():
    vals = {"PositionID": "P1", "Ticker": "ABC", "Status": "DRY_RUN_OPEN",
            "TPPrice": 9.0, "SLPrice": 11.0, "DataQuality": "CLEAN"}
    row = build_portfolio_row(vals, CANON)
    assert len(row) == len(CANON)
    assert row[CANON.index("Status")] == "DRY_RUN_OPEN"
    assert row[CANON.index("TPPrice")] == 9.0
    assert row[CANON.index("SLPrice")] == 11.0
    assert row[CANON.index("DataQuality")] == "CLEAN"


def test_missing_col_blank():
    row = build_portfolio_row({"Ticker": "ABC"}, CANON)
    assert row[CANON.index("ExitPrice")] == ""      # absent -> blank
    assert row[CANON.index("Ticker")] == "ABC"


def test_unknown_key_raises():
    with pytest.raises(KeyError):
        build_portfolio_row({"NotAColumn": 1}, CANON)


def test_equivalence_healthy():
    """On the canonical (healthy 05/06) header, output must equal the exact
    positional row order_manager used to build — regression guard."""
    vals = {
        "PositionID": "DEC-1", "Ticker": "ABC", "EntryDate": "2026-07-01",
        "EntryTime": "08:45:49", "EntryPrice": 4.77, "Quantity": 190,
        "PositionSizeUSD": 999.4, "Side": "short", "EntryOrderID": "SIM-x",
        "TPOrderID": "SIM-x-tp", "SLOrderID": "SIM-x-sl", "TPPrice": 4.29,
        "SLPrice": 5.25, "CurrentPrice": "", "UnrealizedPnL": "",
        "UnrealizedPnLPct": "", "Status": "DRY_RUN_OPEN", "ExitPrice": "",
        "ExitDate": "", "ExitTime": "", "ExitReason": "", "RealizedPnL": "",
        "RealizedPnLPct": "", "LastUpdated": "2026-07-01T08:45:49", "DataQuality": "CLEAN",
    }
    expected = [
        "DEC-1", "ABC", "2026-07-01", "08:45:49", 4.77, 190, 999.4, "short",
        "SIM-x", "SIM-x-tp", "SIM-x-sl", 4.29, 5.25, "", "", "", "DRY_RUN_OPEN",
        "", "", "", "", "", "", "2026-07-01T08:45:49", "CLEAN",
    ]
    assert build_portfolio_row(vals, CANON) == expected
