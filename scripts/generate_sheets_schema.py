#!/usr/bin/env python3
"""TASK-167 — generate SCHEMA.json, the per-sheet column contract.

SCHEMA.json is a DERIVED artifact: this script builds it from the live code
constants so the code stays the §10 single source of truth. NEVER hand-edit
SCHEMA.json — change the constants and re-run this script.

Sources (Layer-1, all local — no Sheets / no gc):
  - AGENT_SHEET_HEADERS / AGENT_SHEET_NAMES  (agent.setup.create_agent_sheets)  -> 14 sheets, mode=exact
  - TIMELINE_LIVE_COLS                        (sheets_manager)                   -> timeline_live, mode=exact
  - post_analysis: required-subset (authored here — it has no static header
    constant; columns are written dynamically) + D6..COLLECT_DAYS_FORWARD as
    forward_optional, derived from config so the contract tracks config changes.

Usage:
  python3 scripts/generate_sheets_schema.py            # write SCHEMA.json
  python3 scripts/generate_sheets_schema.py --check    # exit 1 if on-disk JSON is stale
"""
import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO)

from agent.setup.create_agent_sheets import AGENT_SHEET_NAMES, AGENT_SHEET_HEADERS
from sheets_manager import TIMELINE_LIVE_COLS
from config import CLASSIFY_DAYS, COLLECT_DAYS_FORWARD

SCHEMA_PATH = os.path.join(_REPO, "SCHEMA.json")
SCHEMA_VERSION = 1

# post_analysis has no static header constant (rows are built dynamically and
# the header grows forward-only). These are the stable columns every row carries.
POST_ANALYSIS_REQUIRED = [
    "Ticker", "ScanDate", "Score", "ScanPrice", "score_version",
]


def _forward_optional_cols():
    """D6..COLLECT_DAYS_FORWARD Close+Low — forward-only growth (TASK-177).

    Derived from config (CLASSIFY_DAYS / COLLECT_DAYS_FORWARD) so the contract
    tracks the collector's horizon instead of hard-coding it. D1..CLASSIFY_DAYS
    are the full-OHLC classification window; D6.. are Close+Low data-only.
    """
    cols = []
    for i in range(CLASSIFY_DAYS + 1, COLLECT_DAYS_FORWARD + 1):
        cols.append(f"D{i}_Close")
        cols.append(f"D{i}_Low")
    return cols


def build_contract():
    """Return the contract dict — pure, deterministic, no I/O, no timestamps."""
    sheets = {}
    for name in AGENT_SHEET_NAMES:
        sheets[name] = {
            "mode": "exact",
            "source": "AGENT_SHEET_HEADERS",
            "columns": list(AGENT_SHEET_HEADERS[name]),
        }
    sheets["timeline_live"] = {
        "mode": "exact",
        "source": "TIMELINE_LIVE_COLS",
        "columns": list(TIMELINE_LIVE_COLS),
    }
    sheets["post_analysis"] = {
        "mode": "required_subset",
        "source": "post_analysis stable-subset (authored) + config forward-window",
        "required": list(POST_ANALYSIS_REQUIRED),
        "forward_optional": _forward_optional_cols(),
    }
    return {
        "_meta": {
            "do_not_edit": True,
            "generated_by": "scripts/generate_sheets_schema.py",
            "schema_version": SCHEMA_VERSION,
            "sources": [
                "create_agent_sheets.AGENT_SHEET_HEADERS",
                "sheets_manager.TIMELINE_LIVE_COLS",
                "post_analysis stable-subset (authored) + config forward-window",
            ],
        },
        "sheets": sheets,
    }


def _serialize(contract):
    """Deterministic JSON text (stable across runs for byte-exact round-trip)."""
    return json.dumps(contract, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def write_schema(path=SCHEMA_PATH):
    text = _serialize(build_contract())
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def check_fresh(path=SCHEMA_PATH):
    """Return (ok, message). ok=False if on-disk JSON != freshly generated."""
    if not os.path.exists(path):
        return False, f"{path} does not exist — run generator"
    with open(path, encoding="utf-8") as fh:
        disk = json.load(fh)
    if disk != build_contract():
        return False, f"{path} is STALE — re-run scripts/generate_sheets_schema.py"
    return True, f"{path} is fresh"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--check" in argv:
        ok, msg = check_fresh()
        print(msg)
        return 0 if ok else 1
    write_schema()
    print(f"wrote {SCHEMA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
