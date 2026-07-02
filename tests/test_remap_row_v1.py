"""TASK-217 Task2: recover the 8 misaligned 2026-07 rows to canonical order and
mark them MANUAL_CLEANUP.

Decision (עמיחי 2026-07-01): honest record > fabricated P&L. So the repair:
- keeps identity fields [0..10] (PositionID..SLOrderID) verbatim,
- recovers Status / LastUpdated / DataQuality from where the shift left them,
- BLANKS the unreliable middle (TPPrice/SLPrice were overwritten by the update
  and are unrecoverable; CurrentPrice/UnrealizedPnL are scrambled — not trusted),
- does NOT reconstruct any exit/RealizedPnL,
- sets Status=MANUAL_CLEANUP with a note explaining the orphaning.

remap_row/mark_manual_cleanup are pure (no Sheets) — the live migration (Task3)
consumes them.
"""
import pytest

from scripts.repair_paper_portfolio_misalign_v1 import remap_row, mark_manual_cleanup

CANON = [
    "PositionID", "Ticker", "EntryDate", "EntryTime", "EntryPrice", "Quantity",
    "PositionSizeUSD", "Side", "EntryOrderID", "TPOrderID", "SLOrderID",
    "TPPrice", "SLPrice", "CurrentPrice", "UnrealizedPnL", "UnrealizedPnLPct",
    "Status", "ExitPrice", "ExitDate", "ExitTime", "ExitReason",
    "RealizedPnL", "RealizedPnLPct", "LastUpdated", "DataQuality",
]
# Live stale 2026-07 header (missing TPPrice/SLPrice; 2 phantom trailing blanks).
STALE = ["PositionID", "Ticker", "EntryDate", "EntryTime", "EntryPrice", "Quantity",
    "PositionSizeUSD", "Side", "EntryOrderID", "TPOrderID", "SLOrderID",
    "CurrentPrice", "UnrealizedPnL", "UnrealizedPnLPct", "Status", "ExitPrice",
    "ExitDate", "ExitTime", "ExitReason", "RealizedPnL", "RealizedPnLPct",
    "LastUpdated", "DataQuality", "", ""]
# Observed corrupted row (CANF), exactly as get_all_values returned it.
STALE_ROW = ["DEC-1", "CANF", "2026-07-01", "08:45:49", "4.77", "190", "999.4",
    "short", "SIM-x", "SIM-x-tp", "SIM-x-sl", "4.293", "5.247", "", "", "",
    "DRY_RUN_OPEN", "", "", "", "", "", "", "2026-07-01T08:45:49", "CLEAN"]


def _canon(row):
    return dict(zip(CANON, row))


def test_identity_fields_kept():
    out = _canon(remap_row(STALE, STALE_ROW, CANON))
    assert out["PositionID"] == "DEC-1"
    assert out["Ticker"] == "CANF"
    assert out["EntryPrice"] == "4.77"
    assert out["SLOrderID"] == "SIM-x-sl"


def test_status_recovered_from_shift():
    out = _canon(remap_row(STALE, STALE_ROW, CANON))
    assert out["Status"] == "DRY_RUN_OPEN"   # recovered before MANUAL_CLEANUP override


def test_lastupdated_and_dataquality_recovered():
    out = _canon(remap_row(STALE, STALE_ROW, CANON))
    assert out["LastUpdated"] == "2026-07-01T08:45:49"
    assert out["DataQuality"] == "CLEAN"


def test_tpsl_blank_not_fatal():
    out = _canon(remap_row(STALE, STALE_ROW, CANON))
    assert out["TPPrice"] == ""    # overwritten on the stale tab -> unrecoverable
    assert out["SLPrice"] == ""


def test_no_fabricated_exit():
    out = _canon(remap_row(STALE, STALE_ROW, CANON))
    assert out["ExitPrice"] == "" and out["RealizedPnL"] == "" and out["RealizedPnLPct"] == ""


def test_mark_manual_cleanup():
    row = remap_row(STALE, STALE_ROW, CANON)
    out = _canon(mark_manual_cleanup(row, CANON))
    assert out["Status"] == "MANUAL_CLEANUP"
    assert "orphaned" in out["DataQuality"].lower()   # note preserved


def test_length_is_canonical():
    assert len(remap_row(STALE, STALE_ROW, CANON)) == len(CANON)
