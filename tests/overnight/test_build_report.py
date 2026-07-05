"""Task 7 — morning report assembler. Renders per-task results into the §3 layout
with Hebrew section headers, draft-PR links, NEEDS-HUMAN CORE_UNSAFE triggers, and a
token (not dollar) budget line."""
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

import build_report  # noqa: E402


def _sample():
    results = [
        {"task": "TASK-9", "status": "done", "title": "fix off-by-one",
         "branch": "rh-night/TASK-9", "pr_url": "https://github.com/x/y/pull/12",
         "tests": "125/125", "files": ["foo.py", "tests/test_foo.py"], "tokens": 138000},
        {"task": "TASK-150", "status": "needs_human",
         "reason": "touches config.py (weights/score)"},
        {"task": "TASK-201", "status": "skipped", "reason": "dependency TASK-199 not Done"},
        {"task": "TASK-177", "status": "red", "branch": "rh-night/TASK-177",
         "reason": "tests red after fix", "tail": "E   assert 1 == 2"},
        {"task": "TASK-160", "status": "uncertain",
         "reason": "REL_VOL cap is a trading judgment"},
    ]
    budget = {"tasks_run": 3, "max_tasks": 3, "tokens": 512000, "token_ceiling": 600000,
              "ceiling_hit": False, "per_task": {"TASK-9": 138000}}
    return results, budget


def test_all_sections_present():
    md = build_report.render_report(*_sample(), date="2026-06-18", base_sha="abc1234")
    for marker in ["📊", "✅", "⏭️", "🚧", "❌", "⚠️", "💰"]:
        assert marker in md, marker


def test_pr_link_and_core_trigger_and_tokens():
    md = build_report.render_report(*_sample(), date="2026-06-18", base_sha="abc1234")
    assert "pull/12" in md                 # draft PR link
    assert "config.py" in md               # NEEDS-HUMAN CORE_UNSAFE trigger
    assert "512" in md and "600" in md     # tokens X / 600k (not dollars)
    assert "$" not in md                   # subscription run: no dollar figures


def test_red_task_shows_branch_for_inspection():
    md = build_report.render_report(*_sample(), date="2026-06-18", base_sha="abc1234")
    assert "rh-night/TASK-177" in md
    assert "TASK-160" in md                # uncertainty flag listed


def _sample_dancer():
    results = [
        {"task": "TASK-9", "status": "ready", "rounds": 2, "tokens": 140000},
        {"task": "TASK-50", "status": "parked", "stage": "rejected", "rounds": 5,
         "question": "the fix needs a config threshold change — is that in scope?",
         "evidence_paths": [".dancer/verify.json"]},
        {"task": "TASK-60", "status": "scope_violation",
         "reason": "diff touched files outside plan allowed_files"},
        {"task": "TASK-70", "status": "empty_diff", "reason": "ready but the diff is empty"},
    ]
    budget = {"tasks_run": 4, "max_tasks": 4, "tokens": 300000, "token_ceiling": 600000,
              "ceiling_hit": False, "per_task": {}}
    return results, budget


def test_ready_shows_local_branch_no_pr():
    md = build_report.render_report(*_sample_dancer(), date="2026-07-05", base_sha="def5678")
    assert "auto-dancer/TASK-9" in md          # local branch, not a PR
    assert "rounds 2" in md
    assert "pr_url" not in md                   # the key never leaks into output
    assert "draft PR" not in md                 # no PR language anywhere in the report


def test_parked_shows_written_question():
    md = build_report.render_report(*_sample_dancer(), date="2026-07-05", base_sha="def5678")
    assert "⏸" in md
    assert "is that in scope?" in md            # the concrete written question surfaces


def test_scope_and_empty_diff_grouped():
    md = build_report.render_report(*_sample_dancer(), date="2026-07-05", base_sha="def5678")
    assert "SCOPE VIOLATION" in md and "TASK-60" in md
    assert "EMPTY-DIFF" in md and "TASK-70" in md
