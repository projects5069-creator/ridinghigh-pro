"""
test_account_state_v1.py
─────────────────────────
Producer-side integration test for agent.orchestrator.build_account_state.

Proves that pf_total_rows and pf_status_recognized_count are computed
correctly from raw paper_portfolio records, and that the resulting
account_state drives check_position_sync to the right decision end-to-end
(raw records -> producer -> consumer).

Mocking is minimal and repo-scoped: only the sheet-read boundary
(sheets_manager.get_worksheet / get_sheet_records) is stubbed. No real
Sheets I/O, no network, no config mutation.

Run: python3 test_account_state_v1.py
"""
import sys, os
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sheets_manager
from agent.orchestrator import build_account_state
from agent.sentinel.checks.position_sync import check_position_sync

TODAY = datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d")
RESULTS = []


def _enter(ticker):
    """A decision_log ENTER row for today."""
    return {"Timestamp": f"{TODAY}T08:48:03", "Action": "ENTER", "Ticker": ticker}


def _stub_reads(pf_records, dec_records):
    """Patch only the sheet-read boundary; return a restore() callable."""
    orig_ws = sheets_manager.get_worksheet
    orig_recs = sheets_manager.get_sheet_records

    def fake_ws(tab, *a, **k):
        return True  # truthy worksheet handle

    def fake_recs(tab, *a, **k):
        if tab == "paper_portfolio":
            return list(pf_records)
        if tab == "decision_log":
            return list(dec_records)
        return []

    sheets_manager.get_worksheet = fake_ws
    sheets_manager.get_sheet_records = fake_recs

    def restore():
        sheets_manager.get_worksheet = orig_ws
        sheets_manager.get_sheet_records = orig_recs

    return restore


def _case(name, pf_records, dec_records, exp_total, exp_recognized, exp_open,
          exp_decision, exp_reason):
    restore = _stub_reads(pf_records, dec_records)
    try:
        state = build_account_state(broker=None)
    finally:
        restore()

    te = state.get("cold_start_daily_used", 0)
    res = check_position_sync(state, today_enters=te)

    checks = {
        "pf_total_rows": (state.get("pf_total_rows"), exp_total),
        "pf_status_recognized_count": (state.get("pf_status_recognized_count"), exp_recognized),
        "open_position_count": (state.get("open_position_count"), exp_open),
        "decision": (res.decision, exp_decision),
        "reason": (res.reason, exp_reason),
    }
    ok = all(got == exp for got, exp in checks.values())
    RESULTS.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    for field, (got, exp) in checks.items():
        flag = "" if got == exp else "  <-- MISMATCH"
        print(f"        {field}: got={got} exp={exp}{flag}")
    return ok


def run():
    print("=== test_account_state_v1 (producer: build_account_state) ===")

    # a. Misaligned: rows present, all Status empty/unrecognized.
    #    End-to-end proof: raw records -> producer -> consumer -> WARN-not-BLOCK.
    misaligned = [
        {"Ticker": "ANY", "Status": "", "EntryDate": "2026-06-01", "ExitDate": ""},
        {"Ticker": "SPCE", "Status": "", "EntryDate": "2026-06-01", "ExitDate": ""},
        {"Ticker": "DXST", "Status": "", "EntryDate": "2026-06-02", "ExitDate": ""},
    ]
    _case("misaligned_rows_warn_not_block",
          misaligned, [_enter("XOS")],
          exp_total=3, exp_recognized=0, exp_open=0,
          exp_decision="WARN", exp_reason="POSITION_SYNC_DATA_QUALITY")

    # b. Healthy: rows with recognized Status, some OPEN.
    healthy = [
        {"Ticker": "ABC", "Status": "DRY_RUN_OPEN", "EntryDate": TODAY, "ExitDate": ""},
        {"Ticker": "DEF", "Status": "DRY_RUN_OPEN", "EntryDate": TODAY, "ExitDate": ""},
    ]
    _case("healthy_rows_allow",
          healthy, [_enter("ABC"), _enter("DEF")],
          exp_total=2, exp_recognized=2, exp_open=2,
          exp_decision="ALLOW", exp_reason="OK")

    # c. Empty tab: 0 rows -> BLOCK path intact (XOS scenario).
    _case("empty_tab_block",
          [], [_enter("XOS")],
          exp_total=0, exp_recognized=0, exp_open=0,
          exp_decision="BLOCK", exp_reason="POSITION_SYNC_FAILED")

    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print(f"\nResults: {passed}/{total} passed")
    if passed == total:
        print("✅ All build_account_state producer tests passed!")
        return 0
    print("❌ Some tests failed.")
    return 1


if __name__ == "__main__":
    sys.exit(run())
