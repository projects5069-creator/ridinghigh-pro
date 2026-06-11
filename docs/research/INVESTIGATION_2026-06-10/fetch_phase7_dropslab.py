#!/usr/bin/env python3
"""Phase 7 — fetch DropsLab drops_raw + drops_post. READ-ONLY, throttled."""
import csv, os, sys, time
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

OUT = os.path.expanduser("~/RidingHighPro/docs/research/INVESTIGATION_2026-06-10")
gc = sheets_manager._get_gc()
sh = gc.open_by_key("1XM-qId7HAwEu-8-1GGHcy3RoyyAnsYshjZfDrKFnTMI")
time.sleep(3)
for tab in ("drops_raw", "drops_post"):
    ws = sh.worksheet(tab)
    time.sleep(3)
    vals = ws.get_all_values()
    time.sleep(3)
    with open(os.path.join(OUT, f"dropslab_{tab}.csv"), "w", newline="") as f:
        csv.writer(f).writerows(vals)
    print(f"{tab}: {len(vals)-1} data rows, {len(vals[0]) if vals else 0} cols")
