"""
Generates unique decision IDs in format: DEC-YYYY-MM-DD-NNNNN

Strategy:
- Read current count from decision_log Sheet on init
- Increment in-memory for each generate() call
- Counter resets at midnight (Peru TZ)
- Fallback to timestamp-based ID if Sheet unreachable

Usage:
    from agent.logging.decision_id_generator import DecisionIDGenerator

    gen = DecisionIDGenerator(sheet_id="...")
    id1 = gen.generate()  # -> "DEC-2026-05-03-00001"
    id2 = gen.generate()  # -> "DEC-2026-05-03-00002"

Used by: decision_logger.py (M4)
"""

import re
import sys
import os
from datetime import datetime
from typing import Optional

import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import sheets_manager

PERU_TZ = pytz.timezone("America/Lima")

# Format constants
ID_PATTERN = re.compile(r"^DEC-(\d{4}-\d{2}-\d{2})-(\d{5})$")
ID_PREFIX = "DEC"
COUNTER_FORMAT = "{:05d}"  # 5 digits, zero-padded
MAX_COUNTER = 99999


class DecisionIDGenerator:
    """
    Generates sequential decision IDs scoped to current Peru date.

    Stateful: keeps in-memory counter. Reads initial value from Sheet on init.
    """

    def __init__(self, sheet_id: str):
        """
        Args:
            sheet_id: Google Sheet ID for decision_log
        """
        self.sheet_id = sheet_id
        self._current_date: Optional[str] = None
        self._counter: int = 0
        self._initialize()

    def _today_peru(self) -> str:
        """Today's date in Peru timezone, format YYYY-MM-DD."""
        return datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    def _initialize(self):
        """Read last decision_id from Sheet, set counter accordingly."""
        today = self._today_peru()
        self._current_date = today

        try:
            gc = sheets_manager._get_gc()
            ws = gc.open_by_key(self.sheet_id).sheet1

            # Get DecisionID column (col A)
            ids = ws.col_values(1)  # includes header at index 0

            # Find latest ID for today
            today_max = 0
            for row_id in reversed(ids[1:]):  # skip header
                m = ID_PATTERN.match(row_id)
                if m and m.group(1) == today:
                    today_max = max(today_max, int(m.group(2)))
                    break  # IDs are appended in order, first match from end is highest

            self._counter = today_max
        except Exception as e:
            print(f"[DecisionIDGenerator] Could not read Sheet: {e}", file=sys.stderr)
            print(f"[DecisionIDGenerator] Falling back to counter=0", file=sys.stderr)
            self._counter = 0

    def generate(self) -> str:
        """
        Generate next decision_id.

        Returns:
            str like "DEC-2026-05-03-00001"

        Raises:
            RuntimeError: if counter exceeds MAX_COUNTER (99999/day).
        """
        today = self._today_peru()

        # Date rolled over since last call?
        if today != self._current_date:
            self._current_date = today
            self._counter = 0

        self._counter += 1

        if self._counter > MAX_COUNTER:
            raise RuntimeError(
                f"Counter exceeded {MAX_COUNTER} for {today}. "
                f"Use timestamp fallback or investigate."
            )

        return f"{ID_PREFIX}-{today}-{COUNTER_FORMAT.format(self._counter)}"

    def fallback_timestamp_id(self) -> str:
        """
        Emergency fallback: timestamp-based ID.
        Use only if Sheet write fails and ID must be unique.
        Format: DEC-YYYY-MM-DD-THHMMSS
        """
        now = datetime.now(PERU_TZ)
        return f"{ID_PREFIX}-{now.strftime('%Y-%m-%d')}-T{now.strftime('%H%M%S')}"
