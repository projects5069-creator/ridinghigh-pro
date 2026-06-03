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


def _record(name, ok, detail=""):
    RESULTS.append((name, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")


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


def _counting_build(pf_records, dec_records):
    """Run build_account_state with per-tab read counting. Returns (state, counts)."""
    counts = {}
    orig_ws = sheets_manager.get_worksheet
    orig_recs = sheets_manager.get_sheet_records

    def counting_recs(tab, *a, **k):
        counts[tab] = counts.get(tab, 0) + 1
        if tab == "paper_portfolio":
            return list(pf_records)
        if tab == "decision_log":
            return list(dec_records)
        return []

    sheets_manager.get_worksheet = lambda tab, *a, **k: True
    sheets_manager.get_sheet_records = counting_recs
    try:
        state = build_account_state(broker=None)
    finally:
        sheets_manager.get_worksheet = orig_ws
        sheets_manager.get_sheet_records = orig_recs
    return state, counts


def test_reads_paper_portfolio_once():
    # TASK-58 R1: build_account_state must read each tab ONCE per run.
    pf = [{"Ticker": "ANY", "Status": "DRY_RUN_OPEN", "EntryDate": TODAY, "ExitDate": ""}]
    state, counts = _counting_build(pf, [_enter("ANY")])
    ok = counts.get("paper_portfolio") == 1 and counts.get("decision_log") == 1
    _record("reads_paper_portfolio_once", ok, f"counts={counts}")


def test_exited_today_from_single_read():
    # A ticker entered AND closed today: derived from the single pp read,
    # it must NOT be in existing_positions (re-entry allowed), but still
    # counted in cold_start_daily_used + entries_today_by_ticker.
    pf = [{"Ticker": "XOS", "Status": "DRY_RUN_CLOSED", "EntryDate": TODAY,
           "ExitDate": TODAY}]
    state, counts = _counting_build(pf, [_enter("XOS")])
    ok = ("XOS" not in state["existing_positions"]
          and state["cold_start_daily_used"] == 1
          and state["entries_today_by_ticker"].get("XOS") == 1
          and state["open_position_count"] == 0
          and state["pf_total_rows"] == 1
          and state["pf_status_recognized_count"] == 1
          and counts.get("paper_portfolio") == 1)
    _record("exited_today_from_single_read", ok,
            f"existing={state['existing_positions']}, daily={state['cold_start_daily_used']}, counts={counts}")


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

    # TASK-58 R1: read-once + exited_today from the single read
    test_reads_paper_portfolio_once()
    test_exited_today_from_single_read()

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
