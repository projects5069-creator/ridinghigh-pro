"""test_cross_month_loaders_v1.py — TASK-180 step 2b
Unit tests for the non-destructive inter-day artifact exclusion helpers in
cross_month_loaders.py. Pandas-based, standalone (no pytest required):

    uv run --with pandas python3 test_cross_month_loaders_v1.py

Exit 0 if all pass, 1 otherwise.
"""
import sys
import pandas as pd

from cross_month_loaders import _coerce_bool, exclude_interday_artifacts


def test_coerce_bool_truthy():
    s = pd.Series(["True", "true", "1", "yes", " TRUE "])
    assert _coerce_bool(s).tolist() == [True, True, True, True, True]


def test_coerce_bool_falsy_gotcha():
    # CRITICAL: "False" must be False, not True (bool('False')==True trap)
    s = pd.Series(["False", "false", "", "no", "0", "nan"])
    assert _coerce_bool(s).tolist() == [False] * 6


def test_coerce_bool_numeric_float_strings():
    # TASK-182 §0: gspread returns '1.0'/'0.0' when a bool col was up-cast to float
    import numpy as np
    s = pd.Series(["1.0", "0.0", "2.0", " 1.0 ", "0", "", "-1.0", np.nan])
    assert _coerce_bool(s).tolist() == [True, False, True, True, False, False, True, False]


def test_coerce_bool_real_floats():
    # actual float dtype (not strings) — incl. real NaN (the 128-NaN majority in live data)
    import numpy as np
    s = pd.Series([1.0, 0.0, 1.0, np.nan])
    assert _coerce_bool(s).tolist() == [True, False, True, False]


def test_exclude_two_of_ten():
    df = pd.DataFrame({"Ticker": list("ABCDEFGHIJ"),
                       "InterdayArtifact": ["True", "False", "False", "True", "False",
                                            "False", "False", "False", "False", "False"]})
    clean, pct, n = exclude_interday_artifacts(df)
    assert (n, pct, len(clean)) == (2, 20.0, 8)


def test_exclude_missing_col():
    df = pd.DataFrame({"Ticker": ["A", "B"]})
    clean, pct, n = exclude_interday_artifacts(df)
    assert (pct, n, len(clean)) == (0.0, 0, 2)


def test_exclude_empty_df():
    clean, pct, n = exclude_interday_artifacts(pd.DataFrame())
    assert (pct, n, clean.empty) == (0.0, 0, True)


def test_exclude_all_clean():
    df = pd.DataFrame({"InterdayArtifact": ["False", "False", "False"]})
    clean, pct, n = exclude_interday_artifacts(df)
    assert (n, pct, len(clean)) == (0, 0.0, 3)


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
