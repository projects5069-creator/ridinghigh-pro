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


# Canonical 25-col header (matches create_agent_sheets.py:81-88 + order_manager).
CANONICAL_HEADER = [
    "PositionID", "Ticker", "EntryDate", "EntryTime", "EntryPrice", "Quantity",
    "PositionSizeUSD", "Side", "EntryOrderID", "TPOrderID", "SLOrderID",
    "TPPrice", "SLPrice", "CurrentPrice", "UnrealizedPnL", "UnrealizedPnLPct",
    "Status", "ExitPrice", "ExitDate", "ExitTime", "ExitReason",
    "RealizedPnL", "RealizedPnLPct", "LastUpdated", "DataQuality",
]


def _is_data_row(row):
    return bool(row) and any(str(c).strip() for c in row)


def main(argv=None):
    """Migrate a drifted paper_portfolio month tab to the canonical header and
    mark its corrupted rows MANUAL_CLEANUP. DRY-RUN by default (no writes);
    --apply is required to write, --force to proceed when recovered-open rows
    exist. Sheets access is lazy-imported so the pure functions stay import-clean.
    """
    import argparse
    import json
    import os
    from datetime import datetime

    import re
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="e.g. 2026-07 (required unless --restore)")
    ap.add_argument("--apply", action="store_true", help="write (default: dry-run)")
    ap.add_argument("--force", action="store_true", help="proceed despite recovered-open rows")
    ap.add_argument("--restore", help="rollback: path to a backup JSON to write back verbatim")
    ap.add_argument("--dry-run", action="store_true", help="with --restore: preview, no write")
    args = ap.parse_args(argv)

    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import sheets_manager

    # ── Rollback path ────────────────────────────────────────────────────
    if args.restore:
        with open(args.restore) as f:
            bak = json.load(f)
        bvalues = bak["values"] if isinstance(bak, dict) else bak
        month = args.month or re.search(r"paper_portfolio_(\d{4}-\d{2})_backup",
                                        os.path.basename(args.restore)).group(1)
        print(f"[restore] {args.restore}: {len(bvalues)} rows -> paper_portfolio {month}")
        print(f"[restore] header: {bvalues[0][:6]}... ({len(bvalues[0])} cols)")
        if args.dry_run or not args.apply:
            print("[restore] DRY-RUN — no writes. Would overwrite A1 with the backup verbatim. "
                  "Re-run with --apply to actually restore.")
            return
        ws = sheets_manager.get_worksheet("paper_portfolio", month=month)
        ws.update("A1", bvalues)
        after = ws.get_all_values()
        ok = after[:len(bvalues)] == bvalues
        print(f"[restore] APPLIED verbatim. round-trip match={ok}")
        return

    if not args.month:
        ap.error("--month is required (unless --restore)")

    ws = sheets_manager.get_worksheet("paper_portfolio", month=args.month)
    values = ws.get_all_values()
    header = values[0] if values else []
    data = [(i, r) for i, r in enumerate(values[1:], start=2) if _is_data_row(r)]
    print(f"[repair] paper_portfolio {args.month}: {len(header)} header cols, {len(data)} data rows")

    if header == CANONICAL_HEADER:
        print("[repair] header already canonical — nothing to migrate.")
        return

    # Backup (verbatim) BEFORE anything — abort if it fails.
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    research_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research")
    bpath = os.path.join(research_dir, f"paper_portfolio_{args.month}_backup_{ts}.json")
    with open(bpath, "w") as f:
        json.dump({"header": header, "values": values}, f)
    print(f"[repair] backup -> {bpath}")

    # Compute remapped rows.
    si = CANONICAL_HEADER.index("Status")
    remapped = []
    recovered_open = 0
    print("\n[repair] BEFORE -> AFTER (per data row):")
    for rownum, r in data:
        rec = remap_row(header, r, CANONICAL_HEADER)
        if str(rec[si]).upper() in ("OPEN", "DRY_RUN_OPEN"):
            recovered_open += 1
        final = mark_manual_cleanup(rec, CANONICAL_HEADER)
        remapped.append((rownum, final))
        d = dict(zip(CANONICAL_HEADER, final))
        print(f"  row{rownum} {d['Ticker']:6} recovered_status={rec[si]!r:>14} "
              f"-> {d['Status']:14} | Entry={d['EntryPrice']!r} Current(blanked)={d['CurrentPrice']!r}")

    print(f"\n[repair] header: {len(header)} cols -> {len(CANONICAL_HEADER)} canonical")
    print(f"[repair] recovered-open rows: {recovered_open}")

    if not args.apply:
        print("[repair] DRY-RUN — no writes. Re-run with --apply (and --force if recovered-open>0) to write.")
        return

    if recovered_open and not args.force:
        print(f"[repair] ABORT: {recovered_open} recovered-open rows; re-run with --force to proceed.")
        return

    # --- APPLY (guarded) ---
    ncols = len(CANONICAL_HEADER)
    ws.update("A1", [CANONICAL_HEADER])
    ws.batch_update([{"range": f"A{rn}", "values": [row]} for rn, row in remapped])
    if ws.col_count > ncols:
        ws.resize(rows=ws.row_count, cols=ncols)
    print(f"[repair] APPLIED: header + {len(remapped)} rows rewritten; cols trimmed to {ncols}.")


if __name__ == "__main__":
    main()
