"""
tests/agent/unit/test_sentinel_handle_cache_v1.py
─────────────────────────────────────────────────
TASK-218 · cache the sentinel_events worksheet handle once per run.

_log_sentinel_event calls sm.get_worksheet("sentinel_events") on EVERY event
(agent/sentinel/data_sentinel.py:58). With 60 BLOCK/WARN signals that is 60
worksheet lookups per minute-run, on top of 60 appends.

The failure actually measured on 2026-08-05 was:

    APIError: [429]: Quota exceeded for quota metric 'Read requests' and limit
    'Read requests per minute per user'

READ requests — so it is the get_worksheet lookup that fails, not the append.
55 of 60 events were lost that way in one sampled run. safe_append_row already
carries its own retry (sheets_manager.py:389); the lookup carries none.

Mock-only. No network. No Sheets.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from agent.sentinel import data_sentinel as ds


@pytest.fixture(autouse=True)
def _fresh_cache():
    """Every test starts from a cold cache, and leaves one behind."""
    ds.reset_sentinel_ws_cache()
    yield
    ds.reset_sentinel_ws_cache()


def _emit(n, sm):
    """Emit n events through the real _log_sentinel_event against a mock sheets_manager."""
    for i in range(n):
        ds._log_sentinel_event(
            decision="WARN",
            component="scan_freshness",
            reason="AGING_SCAN",
            details={"ticker": f"TK{i:02d}"},
            action_taken="SHADOW_LOGGED",
        )


# ── 1. one lookup per run, not one per event ──────────────────────────────

def test_sixty_events_look_the_worksheet_up_once():
    sm = MagicMock()
    with patch.dict(sys.modules, {"sheets_manager": sm}):
        _emit(60, sm)

    assert sm.get_worksheet.call_count == 1, (
        f"expected 1 worksheet lookup for 60 events, got {sm.get_worksheet.call_count}"
    )
    assert sm.get_worksheet.call_args.args[0] == "sentinel_events"


# ── 2. the appends themselves are unchanged: still one per event, in order ──

def test_appends_are_still_one_per_event_and_in_order():
    sm = MagicMock()
    with patch.dict(sys.modules, {"sheets_manager": sm}):
        _emit(60, sm)

    assert sm.safe_append_row.call_count == 60
    ws = sm.get_worksheet.return_value
    tickers = []
    for call in sm.safe_append_row.call_args_list:
        assert call.args[0] is ws, "every append must use the SAME cached handle"
        row = call.args[1]
        assert len(row) == 7, "schema is 7 columns"
        assert row[1] == "SENTINEL_WARN"
        assert row[2] == "WARNING"
        assert row[3] == "scan_freshness"
        assert row[4] == "AGING_SCAN"
        assert row[6] == "SHADOW_LOGGED"
        tickers.append(row[5])

    # Details carry the ticker; order must be exactly as emitted.
    assert [f"TK{i:02d}" in t for i, t in enumerate(tickers)] == [True] * 60


# ── 3. a failed lookup is swallowed AND not cached ────────────────────────

def test_failed_lookup_is_swallowed_and_not_cached():
    """The except at data_sentinel.py:60-61 is deliberate — it must stay.

    But a failure must not poison the cache: the next event has to try again,
    otherwise one 429 at the start of a run silently kills every later event.
    """
    sm = MagicMock()
    ws = MagicMock()
    sm.get_worksheet.side_effect = [RuntimeError("429 read quota"), ws, ws]

    with patch.dict(sys.modules, {"sheets_manager": sm}):
        _emit(3, sm)   # must not raise

    assert sm.get_worksheet.call_count == 2, (
        "first call failed, second must retry, third must reuse the cache"
    )
    assert sm.safe_append_row.call_count == 2, "only the 2 events after recovery are written"


def test_worksheet_returning_none_is_not_cached():
    """get_worksheet can return None without raising. That is not a usable handle."""
    sm = MagicMock()
    ws = MagicMock()
    sm.get_worksheet.side_effect = [None, ws]

    with patch.dict(sys.modules, {"sheets_manager": sm}):
        _emit(2, sm)

    assert sm.get_worksheet.call_count == 2
    assert sm.safe_append_row.call_count == 1


# ── 4. the cache must not survive into the next run ───────────────────────

def test_cache_does_not_leak_across_runs():
    """THE CRITICAL ONE.

    A dead handle kept across runs would be worse than today: today every event
    re-looks-up and so self-heals, whereas a stale cached handle would fail for
    the whole of every later run. The module-level singleton pattern already in
    this file (_sentinel_instance, data_sentinel.py:294-302) has per-process
    lifetime, which on a GitHub runner is exactly one run — but the reset must
    exist and work for anything longer-lived, and for the suite itself.
    """
    sm1 = MagicMock()
    with patch.dict(sys.modules, {"sheets_manager": sm1}):
        _emit(5, sm1)
    assert sm1.get_worksheet.call_count == 1

    ds.reset_sentinel_ws_cache()          # a new run begins

    sm2 = MagicMock()
    with patch.dict(sys.modules, {"sheets_manager": sm2}):
        _emit(5, sm2)
    assert sm2.get_worksheet.call_count == 1, "a new run must fetch its own handle"
    assert sm2.get_worksheet.return_value is not sm1.get_worksheet.return_value
