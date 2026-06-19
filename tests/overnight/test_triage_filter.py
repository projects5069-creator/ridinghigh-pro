"""Task 2 — deterministic layer-1 triage filter over backlog frontmatter.

A task is a candidate iff status=="To Do", every dependency is Done, and it carries
no needs-human/blocked label. Dependency-free frontmatter parsing (no PyYAML).
"""
import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "overnight",
    ),
)

import triage_filter  # noqa: E402

_FM = "---\nid: TASK-{id}\ntitle: t{id}\nstatus: {status}\nlabels: {labels}\ndependencies: {deps}\npriority: high\n---\nbody\n"


def _write(tmp, tid, status, labels="[]", deps="[]"):
    (tmp / f"task-{tid}.md").write_text(
        _FM.format(id=tid, status=status, labels=labels, deps=deps), encoding="utf-8"
    )


def test_only_clean_todo_is_candidate(tmp_path):
    _write(tmp_path, 1, "To Do", labels="[bug]")
    _write(tmp_path, 2, "In Progress")
    _write(tmp_path, 3, "To Do", labels="[needs-human]")
    _write(tmp_path, 4, "To Do", deps="[TASK-99]")
    assert triage_filter.find_candidates(str(tmp_path), done_ids=set()) == ["TASK-1"]


def test_met_dependency_included(tmp_path):
    _write(tmp_path, 5, "To Do", deps="[TASK-1]")
    assert triage_filter.find_candidates(str(tmp_path), done_ids={"TASK-1"}) == ["TASK-5"]


def test_blocked_label_excluded(tmp_path):
    _write(tmp_path, 6, "To Do", labels="[blocked]")
    assert triage_filter.find_candidates(str(tmp_path), done_ids=set()) == []


def test_block_style_labels_parsed(tmp_path):
    (tmp_path / "task-7.md").write_text(
        "---\nid: TASK-7\nstatus: To Do\nlabels:\n  - needs-human\n  - infra\ndependencies: []\n---\n",
        encoding="utf-8",
    )
    assert triage_filter.find_candidates(str(tmp_path), done_ids=set()) == []


def test_numeric_ordering(tmp_path):
    for n in (2, 10, 1):
        _write(tmp_path, n, "To Do")
    assert triage_filter.find_candidates(str(tmp_path), done_ids=set()) == ["TASK-1", "TASK-2", "TASK-10"]
