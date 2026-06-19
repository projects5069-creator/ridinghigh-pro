"""Layer-1 deterministic triage: backlog frontmatter -> auto-safe candidate ids.

Dependency-free (no PyYAML, which isn't in the env). Parses only the fields the
strict filter needs: id, status, labels, dependencies. The layer-2 classifier
(classify_task.md) and the per-task diff review enforce the CORE_UNSAFE / data /
secret gates on top of this — this layer only does the cheap structural cut.
"""
import os
import re
import sys

EXCLUDE_LABELS = {"needs-human", "blocked"}


def parse_frontmatter(text):
    """Minimal YAML-frontmatter reader. Handles scalars, inline `[]`/`[a, b]`
    lists, and block `- item` lists for the fields we care about."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm = {}
    cur_key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("  - ") and cur_key is not None:
            fm.setdefault(cur_key, [])
            if isinstance(fm[cur_key], list):
                fm[cur_key].append(line.strip()[2:].strip())
            continue
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if val == "":
                fm[key] = []          # block list may follow
                cur_key = key
            elif val == "[]":
                fm[key] = []
                cur_key = None
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                fm[key] = [x.strip() for x in inner.split(",") if x.strip()]
                cur_key = None
            else:
                fm[key] = val.strip("\"'")
                cur_key = None
    return fm


def _num(task_id):
    m = re.search(r"(\d+)", task_id or "")
    return int(m.group(1)) if m else 0


def collect_done_ids(tasks_dir):
    """Ids of tasks whose status is Done (dependency satisfaction)."""
    done = set()
    for name in os.listdir(tasks_dir):
        if not name.endswith(".md"):
            continue
        fm = parse_frontmatter(_read(os.path.join(tasks_dir, name)))
        if fm.get("status") == "Done" and fm.get("id"):
            done.add(fm["id"])
    return done


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def find_candidates(tasks_dir, done_ids=None, max_tasks=None):
    done_ids = set() if done_ids is None else set(done_ids)
    candidates = []
    for name in sorted(os.listdir(tasks_dir)):
        if not name.endswith(".md"):
            continue
        fm = parse_frontmatter(_read(os.path.join(tasks_dir, name)))
        if fm.get("status") != "To Do":
            continue
        labels = fm.get("labels") or []
        if any(lbl in EXCLUDE_LABELS for lbl in labels):
            continue
        deps = fm.get("dependencies") or []
        if any(d not in done_ids for d in deps):
            continue
        tid = fm.get("id")
        if tid:
            candidates.append(tid)
    candidates.sort(key=_num)
    return candidates[:max_tasks] if max_tasks else candidates


if __name__ == "__main__":  # `python3 triage_filter.py <tasks_dir> [max]`
    tasks_dir = sys.argv[1] if len(sys.argv) > 1 else "backlog/tasks"
    max_tasks = int(sys.argv[2]) if len(sys.argv) > 2 else None
    done = collect_done_ids(tasks_dir)
    for tid in find_candidates(tasks_dir, done_ids=done, max_tasks=max_tasks):
        print(tid)
