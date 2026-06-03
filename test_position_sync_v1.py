"""
test_position_sync_v1.py
─────────────────────────
Unit tests for agent/sentinel/checks/position_sync.check_position_sync.

Covers the data-quality immunization: an UNREADABLE paper_portfolio
(rows present but no recognized Status) must WARN (non-blocking), while a
genuine drift (readable portfolio with 0 open, or zero rows written at
all) must still BLOCK.

Pure unit test — feeds crafted account_state dicts. No Sheets, no network,
no config mutation. Run: python3 test_position_sync_v1.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.sentinel.checks.position_sync import check_position_sync

RESULTS = []


def _check(name, account_state, today_enters, exp_decision, exp_reason):
    res = check_position_sync(account_state, today_enters=today_enters)
    ok = (res.decision == exp_decision and res.reason == exp_reason)
    RESULTS.append((name, ok, exp_decision, exp_reason, res.decision, res.reason))
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: expected {exp_decision}/{exp_reason}, got {res.decision}/{res.reason}")
    return ok


def run():
    print("=== test_position_sync_v1 ===")

    # 1. data-quality (rows exist, no recognized Status) → WARN not BLOCK
    _check("data_quality_warns_not_blocks",
           {"open_position_count": 0, "paper_portfolio_fetch_failed": False,
            "pf_total_rows": 8, "pf_status_recognized_count": 0},
           today_enters=1, exp_decision="WARN", exp_reason="POSITION_SYNC_DATA_QUALITY")

    # 2. real drift, portfolio readable (statuses parse, none open) → BLOCK
    _check("real_drift_readable_blocks",
           {"open_position_count": 0, "paper_portfolio_fetch_failed": False,
            "pf_total_rows": 5, "pf_status_recognized_count": 5},
           today_enters=1, exp_decision="BLOCK", exp_reason="POSITION_SYNC_FAILED")

    # 3. real drift, zero rows written at all (XOS scenario) → BLOCK
    _check("real_drift_zero_rows_blocks",
           {"open_position_count": 0, "paper_portfolio_fetch_failed": False,
            "pf_total_rows": 0, "pf_status_recognized_count": 0},
           today_enters=1, exp_decision="BLOCK", exp_reason="POSITION_SYNC_FAILED")

    # 4. regression: fetch failed (429) → DEFERRED WARN
    _check("fetch_failed_deferred",
           {"open_position_count": 0, "paper_portfolio_fetch_failed": True,
            "pf_total_rows": 0, "pf_status_recognized_count": 0},
           today_enters=1, exp_decision="WARN", exp_reason="POSITION_SYNC_DEFERRED")

    # 5. regression: no enters today → ALLOW
    _check("no_enters_allows",
           {"open_position_count": 0, "paper_portfolio_fetch_failed": False,
            "pf_total_rows": 3, "pf_status_recognized_count": 3},
           today_enters=0, exp_decision="ALLOW", exp_reason="NO_ENTERS_TODAY")

    # 6. regression: healthy (enters and open positions) → ALLOW OK
    _check("healthy_allows_ok",
           {"open_position_count": 2, "paper_portfolio_fetch_failed": False,
            "pf_total_rows": 2, "pf_status_recognized_count": 2},
           today_enters=2, exp_decision="ALLOW", exp_reason="OK")

    # 7. regression: partial (>=3 enters, few open but >0) → PARTIAL WARN
    _check("partial_warns",
           {"open_position_count": 1, "paper_portfolio_fetch_failed": False,
            "pf_total_rows": 6, "pf_status_recognized_count": 6},
           today_enters=6, exp_decision="WARN", exp_reason="POSITION_SYNC_PARTIAL")

    # 8. backward-compat: new signals absent + enters>0 + open==0 → BLOCK (current behavior preserved)
    _check("backward_compat_blocks",
           {"open_position_count": 0, "paper_portfolio_fetch_failed": False},
           today_enters=1, exp_decision="BLOCK", exp_reason="POSITION_SYNC_FAILED")

    passed = sum(1 for r in RESULTS if r[1])
    total = len(RESULTS)
    print(f"\nResults: {passed}/{total} passed")
    if passed == total:
        print("✅ All position_sync tests passed!")
        return 0
    print("❌ Some tests failed.")
    return 1


if __name__ == "__main__":
    sys.exit(run())
