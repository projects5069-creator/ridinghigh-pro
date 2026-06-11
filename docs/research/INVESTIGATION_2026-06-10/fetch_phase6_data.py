#!/usr/bin/env python3
"""Phase 6 — fetch borrow_data + market_context (May+June). READ-ONLY, throttled sleep 3."""
import csv, json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/RidingHighPro"))
import sheets_manager

OUT = os.path.expanduser("~/RidingHighPro/docs/research/INVESTIGATION_2026-06-10")
gc = sheets_manager._get_gc()
cfg = json.load(open(os.path.expanduser("~/RidingHighPro/sheets_config.json")))

def dump(sheet_id, label):
    try:
        sh = gc.open_by_key(sheet_id); time.sleep(3)
        vals = sh.sheet1.get_all_values(); time.sleep(3)
        with open(os.path.join(OUT, f"{label}.csv"), "w", newline="") as f:
            csv.writer(f).writerows(vals)
        print(f"{label}: {len(vals)-1 if vals else 0} data rows, cols={vals[0][:8] if vals else []}")
    except Exception as e:
        print(f"{label}: FAILED {e}")

dump(cfg["2026-06"]["borrow_data"], "borrow_data_2026-06")
dump(cfg["2026-05"]["borrow_data"], "borrow_data_2026-05")
dump(cfg["2026-06"]["market_context"], "market_context_2026-06")
dump(cfg["2026-05"]["market_context"], "market_context_2026-05")
