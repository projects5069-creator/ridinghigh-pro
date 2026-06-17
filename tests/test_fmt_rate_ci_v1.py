"""TDD for fmt_rate_ci — display formatter for a proportion rate + Wilson 95% CI
(TASK-169 AC#2). Wraps the existing pure wilson_ci (formulas.py) into a single
SSoT display string shared by dashboard + emails.

Format: "<rate>.1f% [<lo>.0f<en-dash><hi>.0f%]"  e.g. "53.8% [35–71%]".
The "95% CI" meaning is conveyed once per surface (legend/caption), not in
every string. n<=0 -> "—" (no rate for an empty sample).

RED phase: fmt_rate_ci does not exist yet.
"""
import pytest

from formulas import wilson_ci, fmt_rate_ci  # RED: fmt_rate_ci does not exist yet

_NDASH = "–"  # en-dash, range separator
_MDASH = "—"  # em-dash, empty-sample sentinel


def _expected(successes, n, decimals=1):
    """Reference rendering built from the canonical wilson_ci."""
    rate = successes / n * 100
    lo, hi = wilson_ci(successes, n)
    return f"{rate:.{decimals}f}% [{lo * 100:.0f}{_NDASH}{hi * 100:.0f}%]"


def test_zero_n_returns_dash():
    assert fmt_rate_ci(0, 0) == _MDASH
    assert fmt_rate_ci(5, 0) == _MDASH
    assert fmt_rate_ci(0, -3) == _MDASH


def test_matches_wilson_format_midcase():
    # 14/26 = 53.8% — the canonical small-n honesty example
    assert fmt_rate_ci(14, 26) == _expected(14, 26)


def test_zero_successes_lower_bound_zero():
    s, n = 0, 20
    out = fmt_rate_ci(s, n)
    assert out.startswith(f"0.0% [0{_NDASH}"), out
    assert out == _expected(s, n)


def test_full_successes_upper_bound_capped_at_100():
    s, n = 20, 20
    out = fmt_rate_ci(s, n)
    assert out.startswith("100.0% ["), out
    assert out.endswith("100%]"), out          # Wilson upper rounds to 100, never exceeds
    assert out == _expected(s, n)


def test_small_n_ci_wider_than_large_n():
    def width(s, n):
        lo, hi = wilson_ci(s, n)
        return hi - lo
    # same 50% point estimate, smaller n -> wider interval
    assert width(5, 10) > width(50, 100)
    assert fmt_rate_ci(5, 10).startswith("50.0%")
    assert fmt_rate_ci(50, 100).startswith("50.0%")


def test_bounds_use_percent_and_endash():
    out = fmt_rate_ci(14, 26)
    assert out.count("%") == 2          # one on the rate, one closing the range
    assert _NDASH in out
    assert out.endswith("%]")


def test_decimals_param_controls_rate_precision():
    assert fmt_rate_ci(14, 26, decimals=0) == _expected(14, 26, decimals=0)
    assert fmt_rate_ci(14, 26, decimals=2) == _expected(14, 26, decimals=2)
