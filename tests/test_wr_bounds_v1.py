"""TASK-147 WR dual reporting (policy layer): the headline WR excludes WHIPSAW
(optimistic); the pessimistic bound counts WHIPSAW as losses in the denominator.
Pure helper — core classify_trade mapping is untouched."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics_bounds import wr_bounds


def test_optimistic_excludes_whipsaw():
    b = wr_bounds(n_win=50, n_loss=40, n_whip=10)
    assert round(b["optimistic"], 4) == round(50 / 90 * 100, 4)


def test_pessimistic_counts_whipsaw_as_loss():
    b = wr_bounds(n_win=50, n_loss=40, n_whip=10)
    assert round(b["pessimistic"], 4) == round(50 / 100 * 100, 4)


def test_zero_decided_is_zero_not_crash():
    b = wr_bounds(0, 0, 0)
    assert b == {"optimistic": 0.0, "pessimistic": 0.0}


def test_pessimistic_never_above_optimistic():
    b = wr_bounds(7, 3, 5)
    assert b["pessimistic"] <= b["optimistic"]


def test_no_whipsaw_bounds_are_equal():
    b = wr_bounds(7, 3, 0)
    assert b["optimistic"] == b["pessimistic"]
