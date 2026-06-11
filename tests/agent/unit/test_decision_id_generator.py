"""Unit tests for decision_id_generator.py"""

import sys
import os
import re
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agent.logging.decision_id_generator import (
    DecisionIDGenerator, ID_PATTERN
)


def test_id_format_matches_new_timestamp_pattern():
    """IDs follow DEC-YYYY-MM-DD-TICKER-HHMMSS-ff (Bug #3 timestamp-based, commit 6bc930c).

    Replaces the old DEC-YYYY-MM-DD-NNNNN counter format — the running counter was
    removed to eliminate the read-increment-write race under concurrent runs."""
    gen = DecisionIDGenerator(sheet_id="fake")
    id1 = gen.generate("TDIC")
    assert ID_PATTERN.match(id1), f"ID {id1} doesn't match DEC-date-... pattern"
    assert re.match(r"^DEC-\d{4}-\d{2}-\d{2}-TDIC-\d{6}-\d{2}$", id1), f"unexpected format: {id1}"


def test_ticker_embedded_and_sanitised():
    """Ticker is embedded, uppercased, non-alphanumerics stripped; empty -> 'X'.

    Replaces the removed sequential-counter test — identity is now ticker+timestamp."""
    gen = DecisionIDGenerator(sheet_id="fake")
    assert "-TDIC-" in gen.generate("tdic")
    assert "-ABC1-" in gen.generate("ab.c1")
    assert "-X-" in gen.generate("")


def test_id_embeds_current_peru_date():
    """The date segment is today's Peru date (date-scoped IDs).

    Replaces the removed counter-reset-on-new-date test (no counter to reset)."""
    import pytz
    from datetime import datetime
    today = datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d")
    gen = DecisionIDGenerator(sheet_id="fake")
    assert gen.generate("AAPL").startswith(f"DEC-{today}-AAPL-")


def test_fallback_timestamp_format():
    """Fallback IDs use T-prefix for time portion."""
    with patch.object(DecisionIDGenerator, '_initialize'):
        gen = DecisionIDGenerator(sheet_id="fake")
        fallback = gen.fallback_timestamp_id()
        assert fallback.startswith("DEC-")
        assert "-T" in fallback  # T separates date from time
        # Pattern: DEC-YYYY-MM-DD-THHMMSS
        assert re.match(r"^DEC-\d{4}-\d{2}-\d{2}-T\d{6}$", fallback)
