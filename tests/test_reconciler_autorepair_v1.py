"""TASK-108 — reconciler auto-repair (phase-2 of TASK-106). Fully injectable.

Run: python3 tests/test_reconciler_autorepair_v1.py   (self-contained runner)
 or: python3 -m pytest tests/test_reconciler_autorepair_v1.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.execution.reconciler import Reconciler

# A decision_log ENTER row as get_sheet_records would return it (Sheet col names).
ENTER = {
    "DecisionID": "D-XOS-001", "Timestamp": "2026-06-03T08:48:12-05:00",
    "Ticker": "XOS", "Action": "ENTER", "AgentMode": "DRY_RUN",
    "Price": "5.12", "ExecutionPrice": "", "Quantity": "100",
    "PositionSizeUSD": "512.00", "TPPrice": "4.61", "SLPrice": "5.63",
    "OrderID": "", "OrderStatus": "",
}
TODAY = "2026-06-03"


def make_reconciler(dec_rows, pf_rows, appended):
    return Reconciler(
        broker=None,
        decision_log_reader=lambda: dec_rows,
        portfolio_all_reader=lambda: pf_rows,
        portfolio_row_appender=lambda row: (appended.append(row) or True),
    )


def test_flag_off_gap_does_not_write():
    appended = []
    rc = make_reconciler([ENTER], [], appended)
    rep = rc.reconcile_decision_log_vs_portfolio(auto_repair=False, today=TODAY)
    assert rep["missing_portfolio_row"] == 1
    assert appended == []  # flag OFF -> no write


def test_flag_on_gap_writes_correct_25col_row():
    appended = []
    rc = make_reconciler([ENTER], [], appended)
    rep = rc.reconcile_decision_log_vs_portfolio(auto_repair=True, today=TODAY)
    assert rep["missing_portfolio_row"] == 1
    assert len(appended) == 1
    row = appended[0]
    assert len(row) == 25
    assert row[0] == "D-XOS-001"             # PositionID
    assert row[1] == "XOS"                   # Ticker
    assert row[2] == "2026-06-03"            # EntryDate
    assert row[3] == "08:48:12"              # EntryTime
    assert row[4] == "5.12"                  # EntryPrice <- Price (ExecutionPrice empty)
    assert row[7] == "short"                 # Side
    assert row[8] == "" and row[9] == "" and row[10] == ""   # Entry/TP/SL OrderID lossy
    assert row[16] == "DRY_RUN_CLOSED"       # Status <- AgentMode
    assert row[18] == "2026-06-03"           # ExitDate == EntryDate (decision a)
    assert row[19] == "08:48:12"             # ExitTime == EntryTime
    assert row[20] == "RECONCILER_BACKFILL"  # ExitReason
    assert row[17] == "" and row[21] == "" and row[22] == ""  # ExitPrice/RealizedPnL/Pct empty
    assert row[24] == "BACKFILL"             # DataQuality


def test_existing_row_not_flagged_not_written():
    appended = []
    pf = [{"PositionID": "D-XOS-001", "Status": "DRY_RUN_CLOSED"}]
    rc = make_reconciler([ENTER], pf, appended)
    rep = rc.reconcile_decision_log_vs_portfolio(auto_repair=True, today=TODAY)
    assert rep["missing_portfolio_row"] == 0  # already present -> not a gap
    assert appended == []                      # false-positive guard


def test_double_run_idempotent_single_row():
    appended = []
    pf = []

    def appender(row):
        appended.append(row)
        pf.append({"PositionID": row[0], "Status": row[16]})  # simulate persisted row
        return True

    rc = Reconciler(broker=None, decision_log_reader=lambda: [ENTER],
                    portfolio_all_reader=lambda: pf, portfolio_row_appender=appender)
    rc.reconcile_decision_log_vs_portfolio(auto_repair=True, today=TODAY)
    rc.reconcile_decision_log_vs_portfolio(auto_repair=True, today=TODAY)  # second EOD run
    assert len(appended) == 1  # re-detection prevents a duplicate


def test_live_paper_status_mapping():
    appended = []
    live = dict(ENTER, AgentMode="LIVE_PAPER", DecisionID="D-XOS-002")
    rc = make_reconciler([live], [], appended)
    rc.reconcile_decision_log_vs_portfolio(auto_repair=True, today=TODAY)
    assert appended[0][16] == "CLOSED"  # LIVE_PAPER -> CLOSED


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
