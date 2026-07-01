#!/usr/bin/env python3
"""TASK-213 / TASK-176 AC#2 — measure Sheets 429 per run, per workflow, per day.

Verifies the SA-separation + read-reduction program (TASK-58 health_audit _HA,
TASK-215 auto_scan _AS, TASK-176 news_detective disable, sentinel-cache) actually
cut market-hours 429. Pulls each run's log via `gh run view --log` and counts
429 lines, broken down by component.

Log facts (live recon 2026-07-01):
- GitHub masks ']' -> '***', so a real error reads `APIError: [429***: Quota...`.
  Match on `[429` (never the closing bracket) or the "Quota exceeded" text.
- Timestamps like `15:08:09.0651429Z` embed "429" in the fractional seconds —
  they are NOT preceded by '[', so `\[429` never matches them.
- count_429 counts 429 *log lines* (retry lines included) — a consistent metric
  for cross-run comparison, not a distinct-operation count.

MARKET-SAFE: gh (read-only) + local CSV in research/ (gitignored). Zero Sheets,
zero quota, zero production-code changes.

Usage:
    python3 research/measure_429_by_workflow_v1.py --since 2026-06-30 --max-runs 40
    python3 research/measure_429_by_workflow_v1.py --since 2026-06-30 --workflows agent_minute.yml
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import time

REPO = "projects5069-creator/ridinghigh-pro"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
# Output to research/ (gitignored) so measurement CSVs stay local, never committed.
OUT_DIR = os.path.join(REPO_ROOT, "research")
CSV_PATH = os.path.join(OUT_DIR, "measure_429_by_workflow.csv")
THROTTLE_SECONDS = 0.4
PROGRESS_EVERY = 20

DEFAULT_WORKFLOWS = ["agent_minute.yml", "auto_scan.yml", "health_audit.yml"]

# A real Sheets 429: `APIError: [429***` (']' masked) or the quota-metric text.
# `\[429` cannot match a timestamp's "...429Z" (no '[' precedes it).
_ERR_RE = re.compile(r"\[429|Quota exceeded for quota metric")
# Attribute the line to its logger/component.
_COMP_RE = re.compile(r"agent\.(?:news_detective|sentinel|orchestrator)|sheets_manager")

CSV_FIELDS = ["run_date", "workflow", "run_id", "started_at", "total_429",
              "news_detective", "sentinel", "sheets_manager", "orchestrator", "other"]


def count_429(log_text):
    """Pure: count 429 log lines in `log_text`, broken down by component.

    Returns {"total": int, "by_component": {component: int}}. Retry lines are
    included (consistent across runs). Timestamps ending in ...429Z are ignored.
    """
    total = 0
    by_component = {}
    for line in log_text.splitlines():
        if not _ERR_RE.search(line):
            continue
        total += 1
        m = _COMP_RE.search(line)
        comp = m.group(0) if m else "other"
        by_component[comp] = by_component.get(comp, 0) + 1
    return {"total": total, "by_component": by_component}


def _gh(args):
    """Run a gh command, return stdout (str). Raises on non-zero."""
    return subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=True, cwd=REPO_ROOT
    ).stdout


def _list_runs(workflow, since, max_runs):
    """Return [(run_id, started_at), ...] completed runs for a workflow since date."""
    import json as _json
    out = _gh(["run", "list", "--repo", REPO, "--workflow", workflow,
               "--status", "completed", "--limit", str(max_runs),
               "--created", f">={since}",
               "--json", "databaseId,startedAt"])
    return [(str(r["databaseId"]), r["startedAt"]) for r in _json.loads(out)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="YYYY-MM-DD lower bound (run created)")
    ap.add_argument("--workflows", nargs="+", default=DEFAULT_WORKFLOWS)
    ap.add_argument("--max-runs", type=int, default=60, help="per workflow")
    ap.add_argument("--out", default=CSV_PATH)
    args = ap.parse_args(argv)

    rows = []
    for wf in args.workflows:
        runs = _list_runs(wf, args.since, args.max_runs)
        print(f"[measure_429] {wf}: {len(runs)} completed runs since {args.since}")
        for i, (rid, started) in enumerate(runs, 1):
            try:
                log = _gh(["run", "view", rid, "--repo", REPO, "--log"])
            except subprocess.CalledProcessError as e:
                print(f"  ! run {rid}: log fetch failed ({e}) — skipping", file=sys.stderr)
                continue
            c = count_429(log)
            bc = c["by_component"]
            rows.append({
                "run_date": started[:10], "workflow": wf, "run_id": rid,
                "started_at": started, "total_429": c["total"],
                "news_detective": bc.get("agent.news_detective", 0),
                "sentinel": bc.get("agent.sentinel", 0),
                "sheets_manager": bc.get("sheets_manager", 0),
                "orchestrator": bc.get("agent.orchestrator", 0),
                "other": bc.get("other", 0),
            })
            if i % PROGRESS_EVERY == 0:
                print(f"  ... {i}/{len(runs)}")
            time.sleep(THROTTLE_SECONDS)

    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"[measure_429] wrote {len(rows)} rows -> {args.out}")
    # Quick per-workflow-per-day mean, so the trend is visible without opening the CSV.
    agg = {}
    for r in rows:
        k = (r["run_date"], r["workflow"])
        agg.setdefault(k, []).append(r["total_429"])
    for (d, wf), vals in sorted(agg.items()):
        print(f"  {d} {wf:20s} runs={len(vals):3d} mean429={sum(vals)/len(vals):6.1f} max={max(vals)}")


if __name__ == "__main__":
    main()
