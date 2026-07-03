#!/usr/bin/env python3
"""TASK-219 header audit v2 — READ-ONLY, correct tab->worksheet resolution.

Fixes v1's false-NOTAB bug. Structure (verified from sheets_manager +
sheets_config, 2026-07-02):
  - Each (month, agent-tab) is its OWN spreadsheet file "RH-{month}-{tab}"; the
    header lives in that file's sheet1 when no worksheet is named after the tab.
    A few tabs (e.g. sentinel_events+system_events in 2026-05) share one file
    with per-tab worksheets. get_worksheet() handles both: worksheet(tab) else
    sheet1. v1 skipped the sheet1 fallback -> spurious NOTAB.
  - Some agent tabs are ABSENT from sheets_config for older months (they were
    added later, e.g. the 4 May gaps). That is a real SKIP, not a drift.

This v2 replicates get_worksheet's resolution WITHOUT the auto-create path:
sheet_ids come straight from sheets_config.json (never get_sheet_id/_ensure_month).
Reuses one authed client, caches opened spreadsheets by id, backs off 5/10/20s on
429, paces between tabs. Never writes / never creates / never repairs.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.setup.create_agent_sheets import (
    AGENT_SHEET_NAMES,
    AGENT_SHEET_HEADERS,
    header_matches_canonical,
)
import sheets_manager as sm

MONTHS = ["2026-05", "2026-06", "2026-07"]
PACE_SEC = 1.5  # gentle gap between row reads


def _resolve_ws(ss, tab):
    """Return the worksheet for `tab`: the one named `tab`, else sheet1 (matches
    get_worksheet's fallback). Pure client-side on already-fetched metadata."""
    try:
        return ss.worksheet(tab)
    except Exception:
        return ss.sheet1


def _row1(ws, tries=3):
    for i in range(tries):
        try:
            return ws.row_values(1)
        except Exception as e:
            if "429" in str(e) or "uota" in str(e).lower():
                wait = 5 * (2 ** i)  # 5,10,20
                sys.stderr.write(f"    [429] backoff {wait}s\n")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("429 backoff exhausted")


def main():
    cfg = json.load(open("sheets_config.json"))
    gc = sm._get_gc()
    if gc is None:
        print("FATAL: no authenticated Sheets client (creds missing)")
        return 1
    ss_cache = {}

    print(f"{'tab':<20} {'month':<9} {'verdict':<7} detail")
    print("-" * 84)
    drift = 0
    checked = 0
    skipped = 0
    for tab in AGENT_SHEET_NAMES:
        canonical = list(AGENT_SHEET_HEADERS[tab])
        for month in MONTHS:
            sid = cfg.get(month, {}).get(tab)
            if not sid:
                skipped += 1
                print(f"{tab:<20} {month:<9} {'SKIP':<7} tab not in sheets_config[{month}] (added later)")
                continue
            try:
                if sid not in ss_cache:
                    ss_cache[sid] = gc.open_by_key(sid)
                ws = _resolve_ws(ss_cache[sid], tab)
                hdr = _row1(ws)
            except Exception as e:
                print(f"{tab:<20} {month:<9} {'ERROR':<7} {type(e).__name__}: {str(e)[:48]}")
                continue

            checked += 1
            if header_matches_canonical(hdr, canonical):
                print(f"{tab:<20} {month:<9} {'MATCH':<7} {len(hdr)} cols")
            else:
                drift += 1
                missing = [c for c in canonical if c not in hdr]
                extra = [c for c in hdr if c and c not in canonical]
                phantom = sum(1 for c in hdr if c == "")
                print(f"{tab:<20} {month:<9} {'DRIFT':<7} "
                      f"exp={len(canonical)} got={len(hdr)} "
                      f"missing={missing} extra={extra} phantom_blanks={phantom}")
            time.sleep(PACE_SEC)
    print("-" * 84)
    print(f"SUMMARY: checked={checked}  DRIFT={drift}  SKIP(not-in-config)={skipped}  "
          f"(total tab-months={len(AGENT_SHEET_NAMES)*len(MONTHS)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
