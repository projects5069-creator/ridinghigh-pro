"""Regression tests for FIELD_MAPPING — guards the row-length assert in
DecisionLogger against schema drift.

History: commit 5b20cbf (TD.2, 2026-05-26) grew the decision_log schema
41 -> 42 (added PriceVsSMA20), but the runtime assert in
DecisionLogger._decision_to_row stayed `== 41`. Every row then failed the
assert, was caught, and returned None — silently breaking ALL decision_log
writes from 2026-05-26 until the fix on 2026-05-27. No test guarded the
field count, so it slipped. These tests close that gap.
"""
from agent.logging.decision_logger import FIELD_MAPPING, DecisionLogger
from agent.trader.decision_logic import Decision


def test_field_mapping_has_42_entries():
    """The decision_log sheet has 42 columns. FIELD_MAPPING must match.

    If the schema changes, update the decision_log Sheet headers AND this
    test together — that coupling is the whole point of the test.
    """
    assert len(FIELD_MAPPING) == 42, (
        f"FIELD_MAPPING has {len(FIELD_MAPPING)} entries, expected 42. "
        f"If the schema changed, update decision_log Sheet headers + this test together."
    )


def test_decision_to_row_produces_field_mapping_length():
    """The row built by _decision_to_row must always match FIELD_MAPPING length.

    This is the exact invariant the production assert checks — but at runtime
    a mismatch only logged to stderr and returned None. This test catches the
    same drift loudly at unit-test time.
    """
    dec = Decision(
        decision_id="TEST-FIELD-MAPPING-LENGTH",
        timestamp="2026-01-01T00:00:00-05:00",
        ticker="TEST",
        action="SKIP",
        score=50.0,
        skip_reason="UNIT_TEST",
    )
    # Build the logger without __init__ so no Sheets/network calls happen —
    # _decision_to_row uses only FIELD_MAPPING + the decision, never self state.
    logger = DecisionLogger.__new__(DecisionLogger)
    row = logger._decision_to_row(dec)
    assert len(row) == len(FIELD_MAPPING), (
        f"Row has {len(row)} values, FIELD_MAPPING has {len(FIELD_MAPPING)} — schema drift."
    )
