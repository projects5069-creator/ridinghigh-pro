#!/usr/bin/env python3
"""M1 queue reader for The Auto Dancer — parse a human-written QUEUE file into TSV.

stdlib-only (runs under /usr/bin/python3, bypassing the modern-python PATH shim).
The queue file is the task SOURCE for a MANUAL run: Amihay hand-picks and orders
tasks; each line names a backlog task with an optional per-task token budget and
note. The classifier in rh-overnight.sh still vetoes each task fail-closed
(spec §3) — this reader only decides WHICH tasks, in WHAT order.

Line format (file order == execution order):
    - TASK-159 | budget: 120k | note: wire-or-remove only
    - TASK-228
Blank lines and #-comments are skipped. budget/note are optional
(default budget = 150000). A token id that does not match ^TASK-[0-9]+$ is
reported to stderr and SKIPPED — one malformed line never drops the whole file.

Output: one TSV row per valid task:  TASK-id<TAB>budget<TAB>note
"""
import re
import sys

DEFAULT_BUDGET = 150000
_TASK_RE = re.compile(r"^TASK-[0-9]+$")
_KBUDGET_RE = re.compile(r"^([0-9]+)\s*k$")


def _parse_budget(raw):
    """'120k' -> 120000, '80000' -> 80000, '' / bad -> DEFAULT_BUDGET."""
    raw = raw.strip().lower()
    if not raw:
        return DEFAULT_BUDGET
    m = _KBUDGET_RE.match(raw)
    if m:
        return int(m.group(1)) * 1000
    if raw.isdigit():
        return int(raw)
    return DEFAULT_BUDGET


def parse_line(line):
    """One queue line -> (task_id, budget, note) or None (blank/comment).

    Raises ValueError for a malformed task id (caller logs to stderr + skips)."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("- "):        # tolerate a leading markdown bullet
        stripped = stripped[2:].strip()
    parts = [p.strip() for p in stripped.split("|")]
    task_id = parts[0].strip()
    if not _TASK_RE.match(task_id):
        raise ValueError(f"bad task id: {parts[0]!r}")
    budget = DEFAULT_BUDGET
    note = ""
    for field in parts[1:]:
        low = field.lower()
        if low.startswith("budget:"):
            budget = _parse_budget(field.split(":", 1)[1])
        elif low.startswith("note:"):
            note = field.split(":", 1)[1].strip()
    return task_id, budget, note


def read_queue(path):
    """Yield (task_id, budget, note) for each valid line, in file order."""
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            try:
                parsed = parse_line(line)
            except ValueError as exc:
                print(f"read_queue: line {lineno}: {exc} — skipped", file=sys.stderr)
                continue
            if parsed is not None:
                yield parsed


def main(argv):
    if len(argv) < 2:
        print("usage: read_queue.py <QUEUE_file>", file=sys.stderr)
        return 1
    path = argv[1]
    try:
        rows = list(read_queue(path))
    except FileNotFoundError:
        print(f"read_queue: queue file not found: {path}", file=sys.stderr)
        return 1
    for task_id, budget, note in rows:
        # note is single-line (line iteration) and pipe-free (split on '|') by format
        print(f"{task_id}\t{budget}\t{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
