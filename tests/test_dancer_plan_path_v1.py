"""Auto-Dancer plan.md write-path invariant (TASK-234, Fix A).

Root cause (this session): the PLANNER (scripts/overnight/plan_task.md) is told
to write its plan document to `plan.md` at the worktree ROOT, but the night
settings allow ONLY Write(.dancer/**) + Write(tests/**). Under --permission-mode
dontAsk the root write is silently DENIED, so no plan document is ever created;
the EXECUTOR and CRITIC then read a `plan.md` that does not exist -> the whole
RPI execute chain (TASK-186 execute-proof) cannot succeed.

Fix A: the plan document lives at `.dancer/plan.md` (an allowed write path), and
every consumer reads it there. These are config/prompt invariants — read-only,
hermetic, no subprocess.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OVN = ROOT / "scripts" / "overnight"


def _read(name):
    return (OVN / name).read_text(encoding="utf-8")


def _night_write_globs():
    cfg = json.loads((ROOT / ".claude" / "settings.night.json").read_text(encoding="utf-8"))
    return [a for a in cfg["permissions"]["allow"] if a.startswith("Write(")]


def test_night_allows_dancer_but_not_root():
    globs = _night_write_globs()
    assert "Write(.dancer/**)" in globs          # .dancer/plan.md is writable
    assert "Write(plan.md)" not in globs          # root plan.md is NOT writable


def test_planner_declares_dancer_plan_path():
    txt = _read("plan_task.md")
    assert '"plan_path": ".dancer/plan.md"' in txt, \
        "PLANNER output JSON must declare plan_path .dancer/plan.md"
    assert "path `plan.md`" not in txt, \
        "PLANNER must not be told to write plan.md at the worktree root (night-blocked)"


def test_executor_reads_dancer_plan_path():
    assert ".dancer/plan.md" in _read("execute_task.md")


def test_critic_reads_dancer_plan_path():
    assert ".dancer/plan.md" in _read("critique_task.md")
