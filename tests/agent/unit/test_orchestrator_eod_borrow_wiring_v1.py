"""Unit tests for the TASK-139 borrow-collection wiring into orchestrator_eod.

Written test-first (RED) before the wiring exists. All-mocked (MagicMock +
patch), zero real API/Sheets — same style as test_orchestrator.py.

Pins the contract of a new best-effort helper:

    orchestrator_eod.collect_borrow_snapshot(summary) -> None

  - ticker source = build_account_state()["existing_positions"]  (the SSoT
    union of paper_portfolio OPEN positions + today's decision_log ENTERs,
    already deduped) -> passed sorted/unique to collect_borrow_data.
  - a DEDICATED AlpacaBroker(dry_run=False) read-only broker (NOT the
    Reconciler's), so real shortability is read even under AGENT_DRY_RUN.
  - SAFETY: only get_asset_info is ever touched — never submit_order /
    submit_bracket_order or any trade call.
  - non-fatal like _system_events_alert: any failure logs a warning and
    does NOT increment summary["errors"]; run() keeps going.
  - run() calls it AFTER the Reconciler block, without disturbing it.
"""

import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent import orchestrator_eod as eod

# patch targets (sources — fetched at call time by the helper's in-function imports)
P_ACCOUNT = "agent.orchestrator.build_account_state"
P_BROKER = "agent.execution.alpaca_broker.AlpacaBroker"
P_COLLECT = "agent.perception.borrow_collector.collect_borrow_data"


def _state(tickers):
    """A build_account_state() return value exposing the unified ticker set."""
    return {"existing_positions": set(tickers)}


# ─────────────── 1. ticker source: open positions + today ENTERs, deduped ───────────────

def test_collects_unified_deduped_tickers_and_passes_to_collector():
    summary = {"errors": 0}
    with patch(P_ACCOUNT, return_value=_state(["BBB", "AAA", "CCC"])), \
         patch(P_BROKER) as Broker, \
         patch(P_COLLECT) as collect:
        eod.collect_borrow_snapshot(summary)
    collect.assert_called_once()
    passed_tickers = collect.call_args.args[0]
    assert passed_tickers == ["AAA", "BBB", "CCC"]                 # sorted + unique
    assert collect.call_args.args[1] is Broker.return_value         # the dedicated broker


# ─────────────── 2. dedicated read-only broker with dry_run=False ───────────────

def test_creates_dedicated_broker_with_dry_run_false():
    summary = {"errors": 0}
    with patch(P_ACCOUNT, return_value=_state(["AAA"])), \
         patch(P_BROKER) as Broker, \
         patch(P_COLLECT):
        eod.collect_borrow_snapshot(summary)
    Broker.assert_called_once_with(dry_run=False)


# ─────────────── 3. SAFETY: only get_asset_info, never any trade call ───────────────

def test_never_calls_any_trade_method_on_broker():
    """Runs the REAL collector against a mock broker; asserts no order/trade call."""
    summary = {"errors": 0}
    broker = MagicMock()
    broker.get_asset_info.return_value = {
        "shortable": True, "easy_to_borrow": True, "tradable": True, "status": "active",
    }
    sm = MagicMock()
    sm.get_worksheet.return_value.get_all_values.return_value = [
        ["Ticker", "CheckDate", "CheckTime", "IsShortable", "IsETB",
         "IsHTB", "BorrowFeePct", "SharesAvailable", "Source"],
    ]
    with patch(P_ACCOUNT, return_value=_state(["AAA", "BBB"])), \
         patch(P_BROKER, return_value=broker), \
         patch("agent.perception.borrow_collector.sheets_manager", sm):
        eod.collect_borrow_snapshot(summary)   # real collect_borrow_data runs
    broker.get_asset_info.assert_called()                     # the only allowed call
    broker.submit_order.assert_not_called()
    broker.submit_bracket_order.assert_not_called()
    broker.submit.assert_not_called()


# ─────────────── 4. broker init failure → non-fatal, errors unchanged ───────────────

def test_broker_init_failure_is_non_fatal():
    summary = {"errors": 0}
    with patch(P_ACCOUNT, return_value=_state(["AAA"])), \
         patch(P_BROKER, side_effect=RuntimeError("no alpaca creds")), \
         patch(P_COLLECT) as collect:
        eod.collect_borrow_snapshot(summary)   # must not raise
    collect.assert_not_called()
    assert summary["errors"] == 0


# ─────────────── 5. collector failure → non-fatal, errors unchanged ───────────────

def test_collect_failure_is_non_fatal():
    summary = {"errors": 0}
    with patch(P_ACCOUNT, return_value=_state(["AAA"])), \
         patch(P_BROKER), \
         patch(P_COLLECT, side_effect=Exception("429 quota")):
        eod.collect_borrow_snapshot(summary)   # must not raise
    assert summary["errors"] == 0


# ─────────────── 6. run() calls it AFTER Reconciler, without disturbing it ───────────────

def test_run_invokes_borrow_after_reconciler_without_disturbing_it():
    with patch("agent.execution.reconciler.Reconciler") as Recon, \
         patch("agent.analytics.score_analytics.ScoreAnalytics"), \
         patch(P_BROKER), \
         patch(P_ACCOUNT, return_value=_state(["AAA"])), \
         patch(P_COLLECT) as collect:
        manager = MagicMock()
        manager.attach_mock(Recon.return_value.reconcile, "reconcile")
        manager.attach_mock(collect, "collect")
        eod.run()
    # Reconciler still runs (not disturbed) AND borrow collection runs
    assert Recon.return_value.reconcile.called
    assert collect.called
    # ordering: reconcile before borrow collection
    names = [c[0] for c in manager.mock_calls]
    assert names.index("reconcile") < names.index("collect")


# ─────────────── 7. no tickers → no collector call, never fails ───────────────

def test_no_tickers_skips_collector_and_does_not_fail():
    summary = {"errors": 0}
    with patch(P_ACCOUNT, return_value=_state([])), \
         patch(P_BROKER) as Broker, \
         patch(P_COLLECT) as collect:
        eod.collect_borrow_snapshot(summary)   # must not raise
    collect.assert_not_called()
    assert summary["errors"] == 0
