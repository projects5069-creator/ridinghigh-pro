"""
Integration test: write a real decision to decision_log Sheet.

This test writes to a real Google Sheet. It uses a unique ticker
"TEST_INTEGRATION_M4" so the test row is easy to identify and
(optionally) clean up.

Run: python3 -m pytest tests/agent/integration/test_decision_logger_writes.py -v -s
"""

import sys
import os
import json
import re
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

import sheets_manager
from agent.logging.decision_logger import DecisionLogger, FIELD_MAPPING
from agent.trader.decision_logic import Decision


def _get_decision_log_sheet_id() -> str:
    """Get current month's decision_log sheet ID."""
    with open("sheets_config.json") as f:
        config = json.load(f)

    # Use most recent month with decision_log
    for month in sorted(config.keys(), reverse=True):
        if "decision_log" in config[month]:
            return config[month]["decision_log"]

    raise RuntimeError("No decision_log sheet found in any month")


def test_write_real_decision_to_sheet():
    """
    CRITICAL integration test: write a real Decision and verify the
    row is written correctly with 41 values.
    """
    sheet_id = _get_decision_log_sheet_id()
    print(f"\n[TEST] Writing to decision_log sheet: {sheet_id}")

    # Create a realistic SKIP decision (safer than ENTER for test data)
    test_decision = Decision(
        ticker="TEST_INTEGRATION_M4",
        signal_source="integration_test",
        agent_mode="DRY_RUN",
        action="SKIP",
        reason="Integration test — synthetic decision",
        skip_reason="TEST_DATA",
        price=5.42,
        volume=1_500_000,
        market_cap=50_000_000,
        open_price=5.0,
        high=5.5,
        low=4.9,
        score=72.5,
        mxv=-250.0,
        run_up=35.5,
        atrx=2.1,
        rsi=78.0,
        typical_price_dist=0.05,
        rel_vol=8.2,
        scan_change=18.5,
        decision_time_ms=15,
        confidence_score=1.0,
        is_shortable=True,
        borrow_fee=12.5,
        borrow_available=True,
        locate_status="MOCK",
        existing_position=False,
        buying_power=100000.0,
        cold_start_concurrent_remaining=4,
        cold_start_daily_remaining=9,
    )

    # Write
    logger = DecisionLogger(sheet_id=sheet_id)
    decision_id = logger.log(test_decision)

    # Verify ID was returned
    assert decision_id is not None, "Logger returned None — write failed"
    assert decision_id.startswith("DEC-"), f"ID format wrong: {decision_id}"
    print(f"[TEST] Decision logged successfully: {decision_id}")

    # Read back and verify
    gc = sheets_manager._get_gc()
    ws = gc.open_by_key(sheet_id).sheet1

    # Find the row we just wrote (last row with our test ticker)
    all_records = ws.get_all_records()
    our_rows = [r for r in all_records if r.get("Ticker") == "TEST_INTEGRATION_M4"]
    assert len(our_rows) > 0, "Test row not found in sheet"

    # Check the most recent one (last in list)
    written_row = our_rows[-1]
    print(f"[TEST] Found row: DecisionID={written_row.get('DecisionID')}")

    # Verify key fields
    assert written_row["DecisionID"] == decision_id
    assert written_row["Ticker"] == "TEST_INTEGRATION_M4"
    assert written_row["Action"] == "SKIP"
    assert written_row["SkipReason"] == "TEST_DATA"
    assert str(written_row["Score"]) == "72.5"

    # Verify None handling — these fields are None in SKIP decision
    # Sheet returns "" for empty cells (or the cell is missing from dict)
    position_size = written_row.get("PositionSizeUSD", "")
    assert position_size == "" or position_size is None, (
        f"Expected empty PositionSizeUSD, got: {position_size!r}"
    )

    # Verify bool conversion
    is_shortable = written_row.get("IsShortable")
    assert is_shortable in ("True", "TRUE", True), (
        f"Expected 'True' for IsShortable, got: {is_shortable!r}"
    )

    print(f"[TEST] All assertions passed for row {decision_id}")


def test_decision_id_format_in_sheet():
    """Verify the ID matches DEC-YYYY-MM-DD-TICKER-HHMMSS-ff (current timestamp
    format, Bug#3 fix) — or the T-fallback / legacy 5-digit forms."""
    sheet_id = _get_decision_log_sheet_id()

    decision = Decision(
        ticker="TEST_INTEGRATION_M4_2",
        action="SKIP",
        reason="Format test",
        skip_reason="TEST",
    )

    logger = DecisionLogger(sheet_id=sheet_id)
    decision_id = logger.log(decision)

    assert decision_id is not None
    pattern = r"^DEC-\d{4}-\d{2}-\d{2}-(?:[A-Z0-9]+-\d{6}-\d{2}|T\d{6}|\d{5})$"
    assert re.match(pattern, decision_id), f"ID format wrong: {decision_id}"
