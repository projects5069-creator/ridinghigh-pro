#!/usr/bin/env python3
"""TASK-217 Task2/3 — repair the 8 misaligned 2026-07 paper_portfolio rows.

Pure recovery (Task2, this file's functions) + live migration (Task3, main() —
added separately; keep the pure functions import-clean, no gspread/sheets_manager
at module import time per §10).

Corruption (proven live 2026-07-01): the 2026-07 tab has a STALE 23-col header
(missing TPPrice/SLPrice) + 2 phantom trailing cols. order_manager appended a
canonical-ordered 25-value row positionally, so values landed against the wrong
columns; then the by-name update-writer overwrote stale positions 11-12 with
CurrentPrice/UnrealizedPnL. Net: only identity [0..10], Status, LastUpdated and
DataQuality are reliably recoverable (by re-interpreting the row against the
CANONICAL index); TP/SL are lost (overwritten) and Current/Unrealized/exits are
unreliable -> blanked. No exit is fabricated (עמיחי decision: honest > invented).
"""

# Fields we trust after re-interpreting the row against the canonical header:
# identity block [0..10] + the three that happen to sit at a recoverable index.
_RECOVERABLE_EXTRA = {"Status", "LastUpdated", "DataQuality"}

_CLEANUP_NOTE = "orphaned by misalign 2026-07-01; no valid live exit"


def remap_row(stale_header, stale_row, canonical):
    """Return `stale_row` re-aligned to `canonical` order.

    The entry-writer wrote a canonical-ordered positional list, so a value's
    canonical field == the value at that canonical index. We keep only the
    reliably-recoverable fields (identity[0..10] + Status/LastUpdated/DataQuality)
    and blank everything else (TP/SL overwritten; Current/Unrealized scrambled;
    exits never happened). `stale_header` is accepted for signature symmetry and
    future validation; recovery is index-based because the write was positional.
    """
    padded = list(stale_row) + [""] * (len(canonical) - len(stale_row))
    recoverable = set(canonical[:11]) | _RECOVERABLE_EXTRA
    return [
        (padded[i] if canonical[i] in recoverable else "")
        for i in range(len(canonical))
    ]


def mark_manual_cleanup(row, canonical):
    """Set Status=MANUAL_CLEANUP and write the orphan note into DataQuality.

    Returns a new list; does not mutate `row`."""
    out = list(row)
    out[canonical.index("Status")] = "MANUAL_CLEANUP"
    out[canonical.index("DataQuality")] = _CLEANUP_NOTE
    return out
