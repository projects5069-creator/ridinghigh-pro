"""Assemble the morning report from per-task result dicts.

Subscription run => NO dollar figures (total_cost_usd is notional); the budget line
is in tokens against the 600k ceiling. Hebrew section headers per design §3.
"""
import glob
import json
import os
import sys

_STATUS_GROUPS = [
    ("done", "✅ DONE (draft PRs)"),
    ("skipped", "⏭️ SKIPPED"),
    ("needs_human", "🚧 NEEDS-HUMAN (auto-unsafe — NOT attempted)"),
    ("red", "❌ RED / STOPPED (attempted, halted, NO PR)"),
    ("uncertain", "⚠️ UNCERTAINTY FLAGS (agent stopped on a judgment call)"),
]


def _fmt_done(r):
    files = ", ".join(r.get("files", []))
    tok = f"{r.get('tokens', 0) // 1000}k tok"
    return (f"  {r['task']}  {r.get('title', '')}\n"
            f"    branch {r.get('branch', '?')} → {r.get('pr_url', '(no PR)')}\n"
            f"    tests {r.get('tests', '?')} | files: {files} | {tok}")


def _fmt_other(r):
    line = f"  {r['task']}  {r.get('reason', '')}".rstrip()
    if r.get("branch"):
        line += f"\n    branch {r['branch']} left for inspection"
    if r.get("tail"):
        line += f"\n    tail: {r['tail']}"
    return line


def render_report(results, budget, date, base_sha):
    out = [f"📊 RH OVERNIGHT — {date}  | base {base_sha} | claude 2.1.170",
           "─" * 47]
    by_status = {}
    for r in results:
        by_status.setdefault(r.get("status"), []).append(r)
    for key, header in _STATUS_GROUPS:
        rows = by_status.get(key, [])
        out.append("")
        out.append(header)
        if not rows:
            out.append("  (none)")
            continue
        fmt = _fmt_done if key == "done" else _fmt_other
        out.extend(fmt(r) for r in rows)
    # budget — tokens, never dollars
    tok = budget.get("tokens", 0) // 1000
    ceil = budget.get("token_ceiling", 600000) // 1000
    out.append("")
    out.append("💰 BUDGET")
    out.append(f"  tasks run {budget.get('tasks_run', 0)}/{budget.get('max_tasks', 0)} | "
               f"tokens {tok}k / {ceil}k | ceiling hit: "
               f"{'YES' if budget.get('ceiling_hit') else 'NO'}")
    per = budget.get("per_task", {})
    if per:
        out.append("  per-task: " + ", ".join(f"{k} {v // 1000}k" for k, v in per.items()))
    return "\n".join(out) + "\n"


def _load_results(raw_dir):
    results = []
    for path in sorted(glob.glob(os.path.join(raw_dir, "*.json"))):
        if os.path.basename(path).startswith("_"):  # skip _budget.json etc.
            continue
        with open(path, encoding="utf-8") as fh:
            results.append(json.load(fh))
    return results


if __name__ == "__main__":  # `python3 build_report.py <raw_dir> <date> <base_sha> <out.md>`
    raw_dir, date, base_sha, out_path = sys.argv[1:5]
    budget_path = os.path.join(raw_dir, "_budget.json")
    budget = json.load(open(budget_path)) if os.path.exists(budget_path) else {}
    md = render_report(_load_results(raw_dir), budget, date, base_sha)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(out_path)
