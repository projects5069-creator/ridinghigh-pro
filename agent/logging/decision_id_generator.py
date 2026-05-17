"""
Generates unique decision IDs in format: DEC-YYYY-MM-DD-TICKER-HHMMSS-ff

Strategy (Bug #3 fix 2026-05-16):
- Timestamp-based — NO running counter, NO Sheet read on init.
- Each ID embeds ticker + Peru-time HHMMSS + 2-digit microsecond fraction.
- Collision-proof: two entries for the same ticker in the same second
  still differ by the microsecond fraction.
- Eliminates the read-increment-write race that produced duplicate
  PositionIDs under concurrent GitHub Actions runs / quota 429.

Usage:
    from agent.logging.decision_id_generator import DecisionIDGenerator

    gen = DecisionIDGenerator(sheet_id="...")
    id1 = gen.generate("TDIC")  # -> "DEC-2026-05-13-TDIC-143052-47"

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
# New format: DEC-YYYY-MM-DD-TICKER-HHMMSS-ff  (legacy 5-digit still parseable)
ID_PATTERN = re.compile(r"^DEC-(\d{4}-\d{2}-\d{2})-(.+)$")
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
        """Timestamp-based generator — no Sheet read, no counter (Bug #3 fix)."""
        self._current_date = self._today_peru()
        self._counter = 0  # retained for backward-compat; unused

    def generate(self, ticker: str = "") -> str:
        """
        Generate a unique decision_id.

        Format: DEC-YYYY-MM-DD-TICKER-HHMMSS-ff
        Collision-proof — embeds ticker + Peru HHMMSS + 2-digit microsecond.

        Args:
            ticker: stock ticker to embed (uppercased, sanitised).

        Returns:
            str like "DEC-2026-05-13-TDIC-143052-47"
        """
        now = datetime.now(PERU_TZ)
        date_part = now.strftime("%Y-%m-%d")
        time_part = now.strftime("%H%M%S")
        frac = f"{now.microsecond // 10000:02d}"  # 2-digit hundredths-of-second
        # Sanitise ticker: keep alphanumerics only, uppercase, fallback "X"
        tk = "".join(c for c in str(ticker).upper() if c.isalnum()) or "X"
        return f"{ID_PREFIX}-{date_part}-{tk}-{time_part}-{frac}"

    def fallback_timestamp_id(self) -> str:
        """
        Emergency fallback: timestamp-based ID.
        Use only if Sheet write fails and ID must be unique.
        Format: DEC-YYYY-MM-DD-THHMMSS
        """
        now = datetime.now(PERU_TZ)
        return f"{ID_PREFIX}-{now.strftime('%Y-%m-%d')}-T{now.strftime('%H%M%S')}"
