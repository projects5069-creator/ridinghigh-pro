"""Unit tests for decision_id_generator.py"""

import sys
import os
import re
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.logging.decision_id_generator import (
    DecisionIDGenerator, ID_PATTERN, MAX_COUNTER
)


def test_id_format_matches_pattern():
    """Generated IDs must match DEC-YYYY-MM-DD-NNNNN format."""
    with patch.object(DecisionIDGenerator, '_initialize'), \
         patch.object(DecisionIDGenerator, '_today_peru', return_value='2026-05-03'):
        gen = DecisionIDGenerator(sheet_id="fake")
        gen._current_date = "2026-05-03"
        gen._counter = 0

        id1 = gen.generate()
        assert ID_PATTERN.match(id1), f"ID {id1} doesn't match pattern"
        assert id1 == "DEC-2026-05-03-00001"


def test_counter_increments():
    """Sequential calls produce sequential IDs."""
    with patch.object(DecisionIDGenerator, '_initialize'), \
         patch.object(DecisionIDGenerator, '_today_peru', return_value='2026-05-03'):
        gen = DecisionIDGenerator(sheet_id="fake")
        gen._current_date = "2026-05-03"
        gen._counter = 0

        id1 = gen.generate()
        id2 = gen.generate()
        id3 = gen.generate()

        assert id1 == "DEC-2026-05-03-00001"
        assert id2 == "DEC-2026-05-03-00002"
        assert id3 == "DEC-2026-05-03-00003"


def test_counter_resets_on_new_date():
    """If date changes between calls, counter resets to 1."""
    with patch.object(DecisionIDGenerator, '_initialize'):
        gen = DecisionIDGenerator(sheet_id="fake")
        gen._current_date = "2026-05-03"
        gen._counter = 50

        # Patch _today_peru to simulate date change
        with patch.object(gen, '_today_peru', return_value="2026-05-04"):
            id_new_day = gen.generate()
            assert id_new_day == "DEC-2026-05-04-00001"
            assert gen._counter == 1


def test_max_counter_raises():
    """Counter > MAX_COUNTER raises RuntimeError."""
    with patch.object(DecisionIDGenerator, '_initialize'), \
         patch.object(DecisionIDGenerator, '_today_peru', return_value='2026-05-03'):
        gen = DecisionIDGenerator(sheet_id="fake")
        gen._current_date = "2026-05-03"
        gen._counter = MAX_COUNTER  # at limit

        with pytest.raises(RuntimeError, match="Counter exceeded"):
            gen.generate()


def test_fallback_timestamp_format():
    """Fallback IDs use T-prefix for time portion."""
    with patch.object(DecisionIDGenerator, '_initialize'):
        gen = DecisionIDGenerator(sheet_id="fake")
        fallback = gen.fallback_timestamp_id()
        assert fallback.startswith("DEC-")
        assert "-T" in fallback  # T separates date from time
        # Pattern: DEC-YYYY-MM-DD-THHMMSS
        assert re.match(r"^DEC-\d{4}-\d{2}-\d{2}-T\d{6}$", fallback)
