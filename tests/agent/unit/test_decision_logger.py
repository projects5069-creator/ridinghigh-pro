"""TASK-125 — DecisionLogger skip aggregation unit tests.

Route B keeps per-SKIP stdout lines; these tests pin the NEW in-run
accumulator + flush_skip_summary() (one batched safe_append_rows call
per run to the skip_summary tab). All Sheets I/O is mocked — zero real
writes. DecisionLogger("fake") is network-free (timestamp-based IDs).
"""
import os
from unittest.mock import MagicMock, patch

import pytest

import sheets_manager
from agent.logging.decision_logger import DecisionLogger
from agent.trader.decision_logic import Decision


def _make_logger(run_id="RUN-TEST-1"):
    with patch.dict(os.environ, {"GITHUB_RUN_ID": run_id}):
        return DecisionLogger(sheet_id="fake-sheet-id")


def _skip_decision(ticker="AAAA", score=45.0, skip_reason="SCORE_TOO_LOW: 45.00 < 60"):
    return Decision(
        ticker=ticker,
        action="SKIP",
        score=score,
        skip_reason=skip_reason,
        reason=skip_reason,
    )


# ── accumulation ─────────────────────────────────────────────────────────────

def test_skip_log_accumulates_reason_key(capsys):
    logger = _make_logger()
    logger.log(_skip_decision())
    acc = logger._skip_acc
    assert list(acc.keys()) == ["SCORE_TOO_LOW"]
    entry = acc["SCORE_TOO_LOW"]
    assert entry["count"] == 1
    assert entry["tickers"] == ["AAAA"]
    assert entry["score_min"] == 45.0
    assert entry["score_max"] == 45.0


def test_two_skips_same_reason_increment_count_and_minmax(capsys):
    logger = _make_logger()
    logger.log(_skip_decision(ticker="AAAA", score=45.0))
    logger.log(_skip_decision(ticker="BBBB", score=52.5,
                              skip_reason="SCORE_TOO_LOW: 52.50 < 60"))
    entry = logger._skip_acc["SCORE_TOO_LOW"]
    assert entry["count"] == 2
    assert entry["tickers"] == ["AAAA", "BBBB"]
    assert entry["score_min"] == 45.0
    assert entry["score_max"] == 52.5


def test_enter_does_not_accumulate():
    logger = _make_logger()
    decision = Decision(ticker="CCCC", action="ENTER", score=80.0)
    with patch.object(sheets_manager, "_get_gc") as mock_gc, \
         patch.object(sheets_manager, "safe_append_row") as mock_append, \
         patch.object(sheets_manager, "invalidate_cache"):
        mock_gc.return_value.open_by_key.return_value.sheet1 = MagicMock()
        logger.log(decision)
    assert logger._skip_acc == {}
    assert mock_append.called  # ENTER path unchanged — still writes its row


def test_data_error_reason_normalized(capsys):
    logger = _make_logger()
    logger.log(_skip_decision(skip_reason="DATA_ERROR: TypeError: bad value: x"))
    assert list(logger._skip_acc.keys()) == ["DATA_ERROR"]


def test_missing_skip_reason_falls_back_to_reason_then_unknown(capsys):
    logger = _make_logger()
    d1 = Decision(ticker="DDDD", action="SKIP", score=1.0,
                  skip_reason=None, reason="ROCKET_GUARD: still climbing")
    logger.log(d1)
    assert "ROCKET_GUARD" in logger._skip_acc

    d2 = Decision(ticker="EEEE", action="SKIP", score=1.0,
                  skip_reason=None, reason="")
    logger.log(d2)
    assert "UNKNOWN" in logger._skip_acc


# ── flush ────────────────────────────────────────────────────────────────────

def test_flush_empty_accumulator_no_api_call():
    logger = _make_logger()
    with patch.object(sheets_manager, "get_worksheet") as mock_ws, \
         patch.object(sheets_manager, "safe_append_rows") as mock_append:
        result = logger.flush_skip_summary()
    assert result == 0
    assert not mock_ws.called
    assert not mock_append.called


def test_flush_builds_one_row_per_reason_single_call(capsys):
    logger = _make_logger(run_id="RUN-42")
    logger.log(_skip_decision(ticker="AAAA", score=45.0))
    logger.log(_skip_decision(ticker="BBBB", score=52.5,
                              skip_reason="SCORE_TOO_LOW: 52.50 < 60"))
    logger.log(_skip_decision(ticker="FFFF", score=70.0,
                              skip_reason="MXV_TOO_HIGH: 900 > 500"))
    fake_ws = MagicMock()
    with patch.object(sheets_manager, "get_worksheet", return_value=fake_ws), \
         patch.object(sheets_manager, "safe_append_rows") as mock_append:
        result = logger.flush_skip_summary()
    assert result == 2  # two reason rows
    assert mock_append.call_count == 1  # ONE batched API call
    args, kwargs = mock_append.call_args
    rows = args[1]
    assert len(rows) == 2
    # Schema order: Timestamp | RunID | SkipReason | Count | Tickers | ScoreMin | ScoreMax
    by_reason = {r[2]: r for r in rows}
    score_row = by_reason["SCORE_TOO_LOW"]
    assert score_row[1] == "RUN-42"
    assert score_row[3] == 2
    assert score_row[4] == "AAAA,BBBB"
    assert score_row[5] == 45.0
    assert score_row[6] == 52.5
    mxv_row = by_reason["MXV_TOO_HIGH"]
    assert mxv_row[3] == 1
    assert mxv_row[4] == "FFFF"
    # Idempotent retry: dedup on RunID column (0-based col 1)
    assert kwargs.get("dedup_col") == 1
    assert kwargs.get("dedup_vals") == {"RUN-42"}


def test_flush_clears_accumulator(capsys):
    logger = _make_logger()
    logger.log(_skip_decision())
    fake_ws = MagicMock()
    with patch.object(sheets_manager, "get_worksheet", return_value=fake_ws), \
         patch.object(sheets_manager, "safe_append_rows") as mock_append:
        logger.flush_skip_summary()
        second = logger.flush_skip_summary()
    assert second == 0
    assert mock_append.call_count == 1  # second flush made no call


def test_flush_swallows_exceptions(capsys):
    logger = _make_logger()
    logger.log(_skip_decision())
    fake_ws = MagicMock()
    with patch.object(sheets_manager, "get_worksheet", return_value=fake_ws), \
         patch.object(sheets_manager, "safe_append_rows",
                      side_effect=Exception("429 quota exhausted")):
        result = logger.flush_skip_summary()  # must NOT raise
    assert result == 0


def test_ticker_list_capped_at_25_plus_n_more(capsys):
    logger = _make_logger()
    for i in range(28):
        logger.log(_skip_decision(ticker=f"T{i:03d}", score=10.0 + i))
    fake_ws = MagicMock()
    with patch.object(sheets_manager, "get_worksheet", return_value=fake_ws), \
         patch.object(sheets_manager, "safe_append_rows") as mock_append:
        logger.flush_skip_summary()
    rows = mock_append.call_args[0][1]
    tickers_cell = rows[0][4]
    assert tickers_cell.endswith(" +3 more")
    assert tickers_cell.count(",") == 24  # exactly 25 tickers listed


# ── Route B compatibility (TASK-126 / Actions audit) ─────────────────────────

def test_skip_stdout_print_unchanged(capsys):
    logger = _make_logger()
    decision = _skip_decision(ticker="GGGG", score=33.0)
    result = logger.log(decision)
    captured = capsys.readouterr()
    assert "[SKIP]" in captured.out
    assert "GGGG" in captured.out
    assert result == decision.decision_id
    assert result is not None
