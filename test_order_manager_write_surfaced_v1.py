"""
test_order_manager_write_surfaced_v1.py
────────────────────────────────────────
TASK-105: a failed paper_portfolio entry-write must be SURFACED, not
swallowed silently.

Proves:
1. order_manager.execute() on an ENTER whose paper_portfolio write fails
   (simulated 429 — sheet_writer raises) sets decision.portfolio_written = False
   instead of silently swallowing.
2. order_manager.execute() on a successful write sets portfolio_written = True.
3. orchestrator._record_entry_outcome counts a failed write as an error and
   does NOT count it as a successful ENTER (mirrors decision_log handling).

Mocking is minimal and repo-scoped: a fake broker returns a SimulatedOrder,
and the sheet-write boundary is a stub. No real Sheets, no network.

Run: python3 test_order_manager_write_surfaced_v1.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.execution.alpaca_broker import SimulatedOrder
from agent.execution.order_manager import OrderManager
from agent.trader.decision_logic import Decision

RESULTS = []


def _record(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")


class _FakeBroker:
    """Returns a filled SimulatedOrder for any bracket submission."""
    def submit_bracket_order(self, ticker, qty, limit_price, tp_price, sl_price):
        return SimulatedOrder(id="SIM-test-0001", status="filled",
                              filled_avg_price=limit_price, qty=str(qty),
                              symbol=ticker, legs=[])


def _enter_decision():
    return Decision(
        decision_id="DEC-test-XOS",
        ticker="XOS",
        action="ENTER",
        price=6.94,
        execution_price=6.94,
        quantity=144,
        position_size_usd=1000.0,
        tp_price=6.25,
        sl_price=7.63,
    )


def test_write_failure_surfaced():
    def raising_writer(row):
        raise RuntimeError("simulated 429 — quota exceeded (retries exhausted)")

    om = OrderManager(_FakeBroker(), sheet_writer=raising_writer, data_provider=None)
    decision = om.execute(_enter_decision())
    ok = getattr(decision, "portfolio_written", True) is False
    _record("write_failure_surfaced", ok,
            f"portfolio_written={getattr(decision, 'portfolio_written', '<MISSING>')}")


def test_write_success_marked():
    captured = []

    def good_writer(row):
        captured.append(row)

    om = OrderManager(_FakeBroker(), sheet_writer=good_writer, data_provider=None)
    decision = om.execute(_enter_decision())
    ok = getattr(decision, "portfolio_written", None) is True and len(captured) == 1
    _record("write_success_marked", ok,
            f"portfolio_written={getattr(decision, 'portfolio_written', '<MISSING>')}, rows={len(captured)}")


def test_orchestrator_counts_failed_write():
    from agent.orchestrator import _record_entry_outcome

    # failed write -> errors++, NOT counted as a successful ENTER
    summary_fail = {"enters": 0, "errors": 0}
    d_fail = _enter_decision()
    d_fail.portfolio_written = False
    _record_entry_outcome(d_fail, summary_fail)
    ok_fail = summary_fail["errors"] == 1 and summary_fail["enters"] == 0

    # successful write -> enters++, no error
    summary_ok = {"enters": 0, "errors": 0}
    d_ok = _enter_decision()
    d_ok.portfolio_written = True
    _record_entry_outcome(d_ok, summary_ok)
    ok_ok = summary_ok["enters"] == 1 and summary_ok["errors"] == 0

    _record("orchestrator_counts_failed_write", ok_fail and ok_ok,
            f"fail={summary_fail}, ok={summary_ok}")


def run():
    print("=== test_order_manager_write_surfaced_v1 ===")
    test_write_failure_surfaced()
    test_write_success_marked()
    test_orchestrator_counts_failed_write()
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print(f"\nResults: {passed}/{total} passed")
    if passed == total:
        print("✅ All write-surfaced tests passed!")
        return 0
    print("❌ Some tests failed.")
    return 1


if __name__ == "__main__":
    sys.exit(run())
