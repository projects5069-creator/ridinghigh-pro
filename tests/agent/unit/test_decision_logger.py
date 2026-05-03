"""Unit tests for decision_logger.py"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.logging.decision_logger import DecisionLogger, FIELD_MAPPING, _format_value
from agent.trader.decision_logic import Decision


def test_field_mapping_has_41_entries():
    """Critical: Decision schema (41) must match Sheet (41 cols)."""
    assert len(FIELD_MAPPING) == 41, f"FIELD_MAPPING has {len(FIELD_MAPPING)}, expected 41"


def test_field_mapping_field_names_exist_in_decision():
    """Every field name in mapping must exist in Decision dataclass."""
    from dataclasses import fields
    decision_fields = {f.name for f in fields(Decision)}
    for field_name, _ in FIELD_MAPPING:
        assert field_name in decision_fields, f"Field {field_name} not in Decision"


def test_format_value_none_to_empty_string():
    assert _format_value(None) == ""


def test_format_value_bool_to_string():
    assert _format_value(True) == "True"
    assert _format_value(False) == "False"


def test_format_value_passes_through_others():
    assert _format_value(42) == 42
    assert _format_value(3.14) == 3.14
    assert _format_value("hello") == "hello"


def test_decision_to_row_has_41_values():
    """Critical: row built from Decision must have exactly 41 values."""
    with patch.object(DecisionLogger, '__init__', lambda self, sheet_id: None):
        logger = DecisionLogger(sheet_id="fake")
        decision = Decision(
            ticker="TEST", action="ENTER", reason="test",
            price=5.0, volume=1000000, score=75.5,
        )
        row = logger._decision_to_row(decision)
        assert len(row) == 41, f"Row has {len(row)} values, expected 41"


def test_decision_to_row_handles_none_values():
    """SKIP decisions have None for position_size, quantity, etc -- should become ''."""
    with patch.object(DecisionLogger, '__init__', lambda self, sheet_id: None):
        logger = DecisionLogger(sheet_id="fake")
        # SKIP decision: many fields are None
        decision = Decision(
            ticker="TEST", action="SKIP", skip_reason="LOW_SCORE",
            position_size_usd=None, quantity=None, tp_price=None,
        )
        row = logger._decision_to_row(decision)
        assert "" in row, "Expected empty strings for None values"
        # Check specific positions: position_size at index 31, quantity at 32, tp_price at 33
        assert row[31] == ""  # position_size_usd
        assert row[32] == ""  # quantity
        assert row[33] == ""  # tp_price
