"""TASK-162 — pure expectancy dual-bound helper. Mean net-PnL FRACTION per trade:
optimistic excludes WHIPSAW; pessimistic folds WHIPSAW in as losses. Policy-layer
only (mirrors metrics_bounds.wr_bounds) — no I/O, no Streamlit."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics_bounds import expectancy_bounds


def test_optimistic_is_mean_of_decided():
    b = expectancy_bounds([0.08, -0.12, 0.08], [-0.12, -0.12])
    assert round(b["optimistic"], 6) == round((0.08 - 0.12 + 0.08) / 3, 6)


def test_pessimistic_folds_whipsaw_as_loss():
    b = expectancy_bounds([0.08, -0.12], [-0.12, -0.12])
    assert round(b["pessimistic"], 6) == round((0.08 - 0.12 - 0.12 - 0.12) / 4, 6)


def test_pessimistic_le_optimistic():
    b = expectancy_bounds([0.08, 0.06], [-0.12])
    assert b["pessimistic"] <= b["optimistic"]


def test_none_filtered():
    b = expectancy_bounds([0.08, None, -0.12], [None, -0.12])
    assert round(b["optimistic"], 6) == round((0.08 - 0.12) / 2, 6)
    assert round(b["pessimistic"], 6) == round((0.08 - 0.12 - 0.12) / 3, 6)


def test_empty_is_zero():
    assert expectancy_bounds([], []) == {"optimistic": 0.0, "pessimistic": 0.0}


def test_no_whipsaw_bounds_equal():
    b = expectancy_bounds([0.08, -0.12], [])
    assert b["optimistic"] == b["pessimistic"]
