"""
test_reconciler_missing_portfolio_v1.py
────────────────────────────────────────
TASK-106 (flag-only): the Reconciler must detect a decision_log ENTER that
has NO matching paper_portfolio row (the XOS pattern), and flag it — without
auto-repair, without live Sheets.

Match key: paper_portfolio.PositionID == decision_log.DecisionID, across ALL
statuses (so a same-day close is NOT a false positive), for today's ENTERs.

Mocking is minimal and repo-scoped: decision_log + paper_portfolio readers
and the alert_writer are injected. No real Sheets, no Alpaca, no network.

Run: python3 test_reconciler_missing_portfolio_v1.py
"""
import sys, os
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.execution.reconciler import Reconciler

TODAY = datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d")
RESULTS = []


def _record(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")


def _enter(decision_id, ticker="XOS"):
    return {"DecisionID": decision_id, "Timestamp": f"{TODAY}T08:48:03",
            "Ticker": ticker, "Action": "ENTER"}


def _pf(position_id, status="DRY_RUN_OPEN", ticker="XOS"):
    return {"PositionID": position_id, "Ticker": ticker, "Status": status}


def _build(dl_rows, pf_rows):
    alerts = []
    rec = Reconciler(
        broker=None,
        decision_log_reader=lambda: list(dl_rows),
        portfolio_all_reader=lambda: list(pf_rows),
        alert_writer=lambda ev: alerts.append(ev),
    )
    return rec, alerts


def test_gap_detected():
    rec, alerts = _build([_enter("DEC-X")], [])
    summary = {}
    report = rec.reconcile_decision_log_vs_portfolio(summary)
    ok = (report["missing_portfolio_row"] == 1
          and len(alerts) == 1
          and alerts[0].get("decision_id") == "DEC-X"
          and alerts[0].get("action_taken") == "flag"
          and summary.get("reconcile_missing_portfolio") == 1)
    _record("gap_detected", ok, f"missing={report['missing_portfolio_row']}, alerts={len(alerts)}")


def test_same_day_close_no_false_positive():
    rec, alerts = _build([_enter("DEC-X")], [_pf("DEC-X", status="DRY_RUN_CLOSED")])
    report = rec.reconcile_decision_log_vs_portfolio({})
    ok = report["missing_portfolio_row"] == 0 and len(alerts) == 0
    _record("same_day_close_no_false_positive", ok, f"missing={report['missing_portfolio_row']}")


def test_healthy_open_no_gap():
    rec, alerts = _build([_enter("DEC-X")], [_pf("DEC-X", status="DRY_RUN_OPEN")])
    report = rec.reconcile_decision_log_vs_portfolio({})
    ok = report["missing_portfolio_row"] == 0 and len(alerts) == 0
    _record("healthy_open_no_gap", ok, f"missing={report['missing_portfolio_row']}")


def test_reentry_detects_only_missing():
    rec, alerts = _build(
        [_enter("DEC-X1"), _enter("DEC-X2")],
        [_pf("DEC-X1", status="DRY_RUN_OPEN")],
    )
    report = rec.reconcile_decision_log_vs_portfolio({})
    missing_ids = [a.get("decision_id") for a in alerts]
    ok = (report["missing_portfolio_row"] == 1 and missing_ids == ["DEC-X2"])
    _record("reentry_detects_only_missing", ok, f"missing_ids={missing_ids}")


def run():
    print("=== test_reconciler_missing_portfolio_v1 ===")
    test_gap_detected()
    test_same_day_close_no_false_positive()
    test_healthy_open_no_gap()
    test_reentry_detects_only_missing()
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print(f"\nResults: {passed}/{total} passed")
    if passed == total:
        print("✅ All reconciler missing-portfolio tests passed!")
        return 0
    print("❌ Some tests failed.")
    return 1


if __name__ == "__main__":
    sys.exit(run())
