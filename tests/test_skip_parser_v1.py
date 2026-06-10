"""TASK-126 — parser tests for historical [SKIP] extraction from Actions logs.

Real-log facts (verified 10/6 against run 27024752264, 2026-06-05):
- gh log export masks ']' (and '{','}') as '***', so a SKIP line arrives as:
    2026-06-05T15:45:48.4818156Z [SKIP*** DEC-2026-06-05-STAK-104548-48 STAK Score=20.0 -> SCORE_TOO_LOW: 20.00 < 50
  The parser must key on "[SKIP" and NOT rely on the closing bracket.
- Observed edge cases: ticker "NA", decimal scores (14.94), reasons containing
  ':' and '<'.
- Each run ends with a verification line:
    ... [INFO*** agent.orchestrator: Run complete: signals=24, decisions=24 (ENTER=0, SKIP=24), errors=0, sentinel_blocks=0
"""
import importlib.util
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPT = os.path.join(_REPO, "research", "extract_historical_skips.py")

# research/ is gitignored — on CI the script is absent; skip instead of erroring.
if not os.path.exists(_SCRIPT):
    pytest.skip("research/ gitignored — TASK-126 wip", allow_module_level=True)

_spec = importlib.util.spec_from_file_location("extract_historical_skips", _SCRIPT)
ehs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ehs)


# ── parse_skip_line ──────────────────────────────────────────────────────────

REAL_STAK = ("2026-06-05T15:45:48.4818156Z [SKIP*** DEC-2026-06-05-STAK-104548-48 "
             "STAK Score=20.0 -> SCORE_TOO_LOW: 20.00 < 50")
REAL_NA = ("2026-06-05T15:46:01.6115729Z [SKIP*** DEC-2026-06-05-NA-104601-61 "
           "NA Score=7.72 -> SCORE_TOO_LOW: 7.72 < 50")
REAL_DECIMAL = ("2026-06-05T15:45:50.3999599Z [SKIP*** DEC-2026-06-05-FOXX-104550-39 "
                "FOXX Score=14.94 -> SCORE_TOO_LOW: 14.94 < 50")
REAL_COLON_LT = ("2026-06-10T17:10:10.5943319Z [SKIP*** DEC-2026-06-10-BATL-121010-59 "
                 "BATL Score=76.62 -> PRICE_TOO_LOW: $2.19 < $3.0")
UNMASKED = ("2026-06-05T15:45:48.4818156Z [SKIP] DEC-2026-06-05-STAK-104548-48 "
            "STAK Score=20.0 -> SCORE_TOO_LOW: 20.00 < 50")


def test_parses_real_masked_line():
    d = ehs.parse_skip_line(REAL_STAK)
    assert d == {
        "run_date": "2026-06-05",
        "scan_time": "10:45:48",
        "decision_id": "DEC-2026-06-05-STAK-104548-48",
        "ticker": "STAK",
        "score": 20.0,
        "reason": "SCORE_TOO_LOW: 20.00 < 50",
    }


def test_parses_na_ticker():
    d = ehs.parse_skip_line(REAL_NA)
    assert d["ticker"] == "NA"
    assert d["decision_id"] == "DEC-2026-06-05-NA-104601-61"
    assert d["scan_time"] == "10:46:01"


def test_parses_decimal_score():
    d = ehs.parse_skip_line(REAL_DECIMAL)
    assert d["score"] == 14.94


def test_reason_keeps_colon_and_lt():
    d = ehs.parse_skip_line(REAL_COLON_LT)
    assert d["reason"] == "PRICE_TOO_LOW: $2.19 < $3.0"
    assert d["ticker"] == "BATL"


def test_unmasked_bracket_also_parses():
    d = ehs.parse_skip_line(UNMASKED)
    assert d is not None
    assert d["ticker"] == "STAK"


def test_non_skip_line_returns_none():
    assert ehs.parse_skip_line(
        "2026-06-05T15:45:47.6881422Z 2026-06-05 15:45:47 [INFO*** "
        "agent.news_detective: Fetched news for STAK: 0 filings, 7 articles"
    ) is None
    assert ehs.parse_skip_line("") is None


# ── parse_run_summary ────────────────────────────────────────────────────────

REAL_SUMMARY = ("2026-06-05T15:46:07.2960968Z 2026-06-05 15:46:07 [INFO*** "
                "agent.orchestrator: Run complete: signals=24, decisions=24 "
                "(ENTER=0, SKIP=24), errors=0, sentinel_blocks=0")


def test_parses_run_summary():
    s = ehs.parse_run_summary(REAL_SUMMARY)
    assert s == {"signals": 24, "decisions": 24, "enter": 0, "skip": 24,
                 "errors": 0, "sentinel_blocks": 0}


def test_non_summary_returns_none():
    assert ehs.parse_run_summary(REAL_STAK) is None
