"""test_health_audit_actions_v1.py — TASK-96
Unit tests for health_audit._github_actions_result (pure, no network).

check_06 robustness: when Actions success_rate<80% (would-be CRITICAL), downgrade
to WARNING ONLY when the failure is transient — SAMPLE-SIZE (completed<10) or
RECOVERING (latest run per failing workflow is green). A PERSISTENT failure MUST
stay CRITICAL (no-masking, the hard task constraint).

The pure function is time-window-free: it operates on the already-24h-filtered
run list, and RECOVERING uses only the relative ordering of run_started_at within
that list — so no as_of injection is needed (deterministic from input alone).

    uv run --with-requirements requirements.txt python3 tests/test_health_audit_actions_v1.py
Exit 0 if all pass, 1 otherwise.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root

from health_audit import _github_actions_result, CRITICAL, WARNING, PASSED, INFO


def _run(name, conclusion, started, status="completed"):
    """Build a minimal GitHub workflow_run dict."""
    return {"name": name, "status": status, "conclusion": conclusion,
            "run_started_at": started}


# ── 1. no-masking guard (THE critical case) ──────────────────────────────────

def test_persistent_failure_stays_critical():
    # 10 completed, 70% success, and workflow "deploy" is STILL failing at its
    # latest run -> not recovered, not tiny -> CRITICAL must be preserved.
    runs = [
        _run("deploy", "failure", "2026-06-19T08:00:00Z"),
        _run("deploy", "failure", "2026-06-19T09:00:00Z"),
        _run("deploy", "failure", "2026-06-19T10:00:00Z"),  # latest = failure
    ] + [_run("scan", "success", f"2026-06-19T1{i}:00:00Z") for i in range(7)]
    r = _github_actions_result(runs)
    assert r.status == CRITICAL, f"expected CRITICAL, got {r.status}"


# ── 2 + 3. downgrade paths ───────────────────────────────────────────────────

def test_clustered_recovered_is_warning():
    # rate<80 (8/11=72.7%) but every failing workflow's LATEST run is green.
    runs = [
        _run("deploy", "failure", "2026-06-19T08:00:00Z"),
        _run("deploy", "failure", "2026-06-19T09:00:00Z"),
        _run("deploy", "success", "2026-06-19T10:00:00Z"),  # deploy recovered
        _run("audit", "failure", "2026-06-19T08:30:00Z"),
        _run("audit", "success", "2026-06-19T11:00:00Z"),   # audit recovered
    ] + [_run("scan", "success", f"2026-06-19T1{i}:30:00Z") for i in range(6)]
    r = _github_actions_result(runs)
    assert r.status == WARNING, f"expected WARNING, got {r.status}"


def test_tiny_sample_is_warning():
    # only 3 completed, 33% success, and the failing wf did NOT recover —
    # sample-size alone must downgrade (isolates the sample gate from recovering).
    runs = [
        _run("deploy", "failure", "2026-06-19T08:00:00Z"),
        _run("deploy", "failure", "2026-06-19T10:00:00Z"),  # latest = failure
        _run("scan", "success", "2026-06-19T09:00:00Z"),
    ]
    r = _github_actions_result(runs)
    assert r.status == WARNING, f"expected WARNING, got {r.status}"


# ── 4 + 5. existing-behavior regression guards ───────────────────────────────

def test_high_success_passed():
    runs = [_run("scan", "success", f"2026-06-19T{i:02d}:00:00Z") for i in range(20)]
    assert _github_actions_result(runs).status == PASSED


def test_mid_success_warning():
    # 17/20 = 85% -> WARNING band (>=80, <95), unchanged behavior.
    runs = ([_run("scan", "success", f"2026-06-19T{i:02d}:00:00Z") for i in range(17)]
            + [_run("deploy", "failure", f"2026-06-19T{i:02d}:30:00Z") for i in range(3)])
    assert _github_actions_result(runs).status == WARNING


# ── 6. edge paths ────────────────────────────────────────────────────────────

def test_no_runs_warning():
    assert _github_actions_result([]).status == WARNING


def test_none_completed_info():
    runs = [_run("scan", None, "2026-06-19T08:00:00Z", status="in_progress")]
    assert _github_actions_result(runs).status == INFO


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {type(e).__name__} - {e}")
            failed += 1
    print("=" * 60)
    print(f"Results: {passed}/{passed + failed} passed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
