#!/usr/bin/env python3
"""detect_duplicate_entries_v1.py — daily net for duplicate ENTERs.

WHY THIS EXISTS
On 2026-08-10, day 1 of the measurement window, JWEL and DKI were each entered
twice, one second apart, by two agent_minute runs whose jobs started in the same
second (13:31:13Z). Filter 9 is correct and AGENT_MAX_REENTRIES_PER_TICKER=1
already permits exactly one entry per ticker per day — it was not breached by
configuration, it was bypassed by concurrency: build_account_state snapshots
once at the start of a run, so the second run could not see the first run's
write. The code itself records why a re-read cannot close this
(agent/orchestrator.py:200-203: Sheets writes can stay invisible "for minutes").

Prevention needs the runs serialised. Until that is deployed, this is the net:
it does not prevent the duplicate, it makes the duplicate impossible to miss,
so the 2026-09-07 sample can be cleaned instead of silently polluted.

THE CLASSIFICATION IS THE POINT
  identical Score  -> ENFORCEMENT duplicate. Score is derived from the signal
                      row, so two identical scores mean both runs decided on the
                      SAME signal snapshot. Not a new decision — a copy.
  different Score  -> REAL re-entry. Two distinct decisions on two distinct
                      observations. A policy question, not an enforcement bug.
That distinction decides whether HYPOTHESES.md §F:261 ("another breach of the
reentry cap") is even engaged. Do not collapse the two.

ZERO Sheets access — GitHub Actions logs only.

USAGE
  detect_duplicate_entries_v1.py --date 2026-08-10
  detect_duplicate_entries_v1.py --from-file fixture.tsv --date 2026-08-10
  detect_duplicate_entries_v1.py --date 2026-08-10 --full-starts

EXIT  0 = clean · 1 = duplicates found · 2 = usage/fetch error
"""
import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict

REPO = os.environ.get("RH_REPO", "projects5069-creator/ridinghigh-pro")
WORKFLOW = "agent_minute.yml"
OUT_DIR = os.path.expanduser(
    os.environ.get("RH_DUP_OUT", "~/ClaudeWork/RidingHighPro/audit/duplicates")
)
NEAR_START_SECONDS = 15  # the metric that actually predicts a duplicate

ENTER_RE = re.compile(r"ENTER ([A-Z][A-Z0-9.\-]*): score=(-?[0-9.]+)")
TS_RE = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")


def gh(args):
    try:
        r = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=120)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def run_ids(date):
    # ⚠️ --limit truncates from the NEWEST side. Measured 2026-08-10 evening:
    # with --limit 400 the day had grown to 431+ runs (the cron keeps creating
    # post-close runs until 21:59Z), the MORNING fell off the list, and the
    # detector reported CLEAN on the very day it was built to flag — 4 ENTERs
    # instead of 9, both duplicate pairs gone. A minute-cron weekday tops out
    # at ~540 runs; 1000 covers it with margin, and the cap is asserted below.
    out = gh(["run", "list", "--repo", REPO, "--workflow", WORKFLOW,
              "--created", date, "--limit", "1000",
              "--json", "databaseId,conclusion",
              "--jq", '.[]|select(.conclusion=="success")|.databaseId'])
    ids = [x for x in out.splitlines() if x.strip()]
    if len(ids) >= 950:
        print(f"⚠️ run list near the 1000 cap ({len(ids)}) — coverage no longer "
              f"guaranteed; refusing to report CLEAN from a truncated list.",
              file=sys.stderr)
        sys.exit(2)
    return ids


def enters_from_gh(date):
    """-> list of (run_id, iso_ts, ticker, score). One log fetch per run."""
    ids = run_ids(date)
    rows = []
    for rid in ids:
        log = gh(["run", "view", rid, "--repo", REPO, "--log"])
        if not log:                       # transient fetch failure — retry once
            log = gh(["run", "view", rid, "--repo", REPO, "--log"])
        for line in log.splitlines():
            m = ENTER_RE.search(line)
            if not m:
                continue
            t = TS_RE.search(line)
            rows.append((rid, t.group(1) if t else "", m.group(1), m.group(2)))
    return rows, len(ids)


def enters_from_file(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) >= 4:
                rows.append((p[0], p[1], p[2], p[3]))
    return rows, len({r[0] for r in rows})


def job_start(rid):
    return gh(["api", f"repos/{REPO}/actions/runs/{rid}/jobs",
               "--jq", ".jobs[0].started_at"]).strip()


def secs(iso):
    try:
        return (int(iso[11:13]) * 3600 + int(iso[14:16]) * 60 + int(iso[17:19]))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--from-file", dest="from_file")
    ap.add_argument("--full-starts", action="store_true",
                    help="fetch job start times for EVERY run (slow); default is ENTER runs only")
    ap.add_argument("--out-dir", default=OUT_DIR)
    a = ap.parse_args()

    if a.from_file:
        rows, n_runs = enters_from_file(a.from_file)
        source = f"fixture {a.from_file}"
    else:
        rows, n_runs = enters_from_gh(a.date)
        source = f"gh logs · {REPO} · {WORKFLOW}"

    by_ticker = defaultdict(list)
    for rid, ts, tk, sc in rows:
        by_ticker[tk].append((ts, rid, sc))
    for tk in by_ticker:
        by_ticker[tk].sort()

    dups = {tk: v for tk, v in by_ticker.items() if len(v) > 1}
    enforcement, reentry = [], []
    for tk, v in dups.items():
        same_score = len({s for _, _, s in v}) == 1
        same_run = len({r for _, r, _ in v}) == 1
        (enforcement if same_score else reentry).append((tk, v, same_run))

    # near-simultaneous job starts — the predictor, not "overlap %"
    starts, pairs = {}, []
    if not a.from_file:
        ids = sorted({r[0] for r in rows}) if not a.full_starts else run_ids(a.date)
        for rid in ids:
            s = job_start(rid)
            if s:
                starts[rid] = s
        items = sorted(starts.items(), key=lambda kv: kv[1])
        for i in range(len(items) - 1):
            for j in range(i + 1, len(items)):
                d = (secs(items[j][1]) or 0) - (secs(items[i][1]) or 0)
                if d < 0:
                    continue
                if d <= NEAR_START_SECONDS:
                    pairs.append((items[i][0], items[j][0], items[i][1], d))
                else:
                    break

    L = []
    L.append(f"# גלאי-כפילויות · {a.date}")
    L.append("")
    L.append(f"מקור: {source} · ריצות שנסרקו: {n_runs} · שורות ENTER: {len(rows)}")
    L.append(f"טיקרים שנכנסו: {len(by_ticker)} · טיקרים עם 2+ כניסות: {len(dups)}")
    L.append("")
    if enforcement:
        L.append("## ❌ כפילות-אכיפה (ציון זהה = אותה שורת-סיגנל, לא החלטה חדשה)")
        for tk, v, same_run in enforcement:
            L.append(f"- **{tk}** ×{len(v)} · ציון {v[0][2]} בכולן"
                     f"{' · **מאותה ריצה** (באג אחר!)' if same_run else ' · מריצות שונות'}")
            for ts, rid, sc in v:
                L.append(f"    - {ts}  run {rid}  score={sc}")
        L.append("")
    if reentry:
        L.append("## ⚠️ כניסה-חוזרת אמיתית (ציון שונה = החלטה נפרדת)")
        for tk, v, _ in reentry:
            L.append(f"- **{tk}** ×{len(v)} · ציונים: {', '.join(s for _, _, s in v)}")
            for ts, rid, sc in v:
                L.append(f"    - {ts}  run {rid}  score={sc}")
        L.append("")
    if not dups:
        L.append("## ✅ אין כפילויות")
        L.append("")
    L.append(f"## התחלות-צמודות (הפרש ≤ {NEAR_START_SECONDS}ש)")
    if a.from_file:
        L.append("- לא נמדד (מצב fixture)")
    elif pairs:
        for r1, r2, t, d in pairs:
            L.append(f"- run {r1} ו-run {r2} התחילו ב-{t} · הפרש {d}ש")
    else:
        scope = "כל הריצות" if a.full_starts else "ריצות שהניבו ENTER בלבד"
        L.append(f"- אין ({scope})")
    L.append("")
    L.append("⚠️ 'חפיפה%' אינה המדד. ריצות במרווח 60ש אינן מכפילות — ה-snapshot")
    L.append("   של השנייה נבנה אחרי הכתיבות של הראשונה. רק התחלה-צמודה מכפילה.")

    report = "\n".join(L)
    print(report)

    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, f"{a.date}.md"), "w") as f:
        f.write(report + "\n")
    with open(os.path.join(a.out_dir, f"{a.date}.summary"), "w") as f:
        f.write(f"STATUS={'DUPLICATES' if dups else 'CLEAN'} DUPES={len(dups)} "
                f"ENFORCEMENT={len(enforcement)} REENTRY={len(reentry)} "
                f"ENTERS={len(rows)} RUNS={n_runs} PAIRS{NEAR_START_SECONDS}S={len(pairs)}\n")

    return 1 if dups else 0


if __name__ == "__main__":
    sys.exit(main())
