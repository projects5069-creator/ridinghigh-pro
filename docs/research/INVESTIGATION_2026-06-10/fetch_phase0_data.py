#!/usr/bin/env python3
"""INVESTIGATION 2026-06-10 — Phase 0 data fetch (READ-ONLY).
Reads post_analysis 2026-04 + 2026-05 and skip_summary 2026-06.
Throttled: sleep 3 between Sheets API calls. Writes CSVs into the
investigation directory only. Zero writes to any Sheet.
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager  # noqa: E402

OUT = os.path.expanduser(
    "~/RidingHighPro/docs/research/INVESTIGATION_2026-06-10")

gc = sheets_manager._get_gc()
if gc is None:
    print("FATAL: no gc")
    sys.exit(1)

import json
cfg = json.load(open(os.path.expanduser("~/RidingHighPro/sheets_config.json")))

def dump(sheet_id, label):
    sh = gc.open_by_key(sheet_id)
    time.sleep(3)
    ws = sh.sheet1
    vals = ws.get_all_values()
    time.sleep(3)
    path = os.path.join(OUT, f"{label}.csv")
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(vals)
    print(f"{label}: {len(vals)-1} data rows, {len(vals[0]) if vals else 0} cols -> {path}")
    return vals

dump(cfg["2026-04"]["post_analysis"], "post_analysis_2026-04")
dump(cfg["2026-05"]["post_analysis"], "post_analysis_2026-05")
vals = dump(cfg["2026-06"]["skip_summary"], "skip_summary_2026-06")
# show last rows for freshness check
for row in vals[-5:]:
    print("TAIL:", row[:4])
