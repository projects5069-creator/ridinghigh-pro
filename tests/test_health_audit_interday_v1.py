"""test_health_audit_interday_v1.py — TASK-180 step 2c
Unit tests for health_audit._interday_artifact_result (pure, no Sheets).
    uv run --with-requirements requirements.txt python3 test_health_audit_interday_v1.py
Exit 0 if all pass, 1 otherwise.
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root (relocated to tests/)

from health_audit import _interday_artifact_result, WARNING, PASSED

_TWO = ["True", "False", "False", "True", "False",
        "False", "False", "False", "False", "False"]


def test_two_artifacts_warning():
    df = pd.DataFrame({"Ticker": list("ABCDEFGHIJ"), "InterdayArtifact": _TWO})
    r = _interday_artifact_result(df)
    assert r.status == WARNING
    assert "2" in r.message and "contamination" in r.message


def test_all_clean_passed():
    df = pd.DataFrame({"Ticker": ["A", "B"], "InterdayArtifact": ["False", "False"]})
    assert _interday_artifact_result(df).status == PASSED


def test_empty_df_passed():
    assert _interday_artifact_result(pd.DataFrame()).status == PASSED


def test_missing_col_passed():
    # backward-compat: old sheets pre-detector have no InterdayArtifact column
    df = pd.DataFrame({"Ticker": ["A", "B"]})
    assert _interday_artifact_result(df).status == PASSED


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
