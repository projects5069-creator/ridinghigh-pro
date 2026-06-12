"""TASK-164 — resolved_class maps a TASK-155 intraday verdict to an effective
class for the resolved bound: WIN/LOSS pass through, UNRESOLVED is excluded (None),
and anything missing/unknown falls back to pessimistic (LOSS) — never inflates the
edge as the dataset grows beyond the snapshot."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics_bounds import resolved_class


def test_win_passes_through():
    assert resolved_class("WIN") == "WIN"


def test_loss_passes_through():
    assert resolved_class("LOSS") == "LOSS"


def test_unresolved_is_excluded():
    assert resolved_class("UNRESOLVED") is None


def test_missing_falls_back_to_pessimistic_loss():
    assert resolved_class(None) == "LOSS"
    assert resolved_class("") == "LOSS"
    assert resolved_class("PENDING") == "LOSS"   # unknown -> conservative


def test_fallback_override_but_unresolved_still_excluded():
    assert resolved_class(None, fallback="WIN") == "WIN"
    assert resolved_class("UNRESOLVED", fallback="WIN") is None
