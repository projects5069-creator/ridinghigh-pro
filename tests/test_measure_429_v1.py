"""TASK-213 / TASK-176 AC#2: pure 429-counting over agent_minute run logs.

Traps this must survive (learned live 2026-07-01):
- GitHub masks ']' -> '***', so a real error reads `APIError: [429***: Quota...`
  (never rely on the closing bracket).
- Timestamps like `15:08:09.0651429Z` contain "429" inside the fractional
  seconds — must NOT be counted (they have no '[' before the 429).
- Per-component attribution (news_detective / sentinel / sheets_manager /
  orchestrator) so the news-disable (176) and sentinel-cache effects are visible.

count_429() counts 429 *log lines* (retry lines included) — a consistent metric
for cross-run comparison, not a distinct-operation count.
"""
import importlib.util
import os

_SPEC = importlib.util.spec_from_file_location(
    "measure_429",
    os.path.join(os.path.dirname(__file__), "..", "scripts", "measure_429_by_workflow_v1.py"),
)
measure_429 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(measure_429)


REAL_NEWS = ("2026-07-01T18:30:59.1832348Z 2026-07-01 18:30:59 [WARNING*** "
             "agent.news_detective: Failed to write news findings for AMCI: "
             "APIError: [429***: Quota exceeded for quota metric 'Read requests'")
REAL_SENT = ("2026-07-01T18:31:02.5987849Z 2026-07-01 18:31:02 [WARNING*** "
             "agent.sentinel: Failed to log sentinel event to sentinel_events: "
             "APIError: [429***: Quota exceeded for quota metric 'Read requests'")
REAL_SM = ("2026-07-01T15:35:51.8577100Z [sheets_manager*** all 3 retries "
           "exhausted: APIError: [429***: Quota exceeded for quota metric 'Read requests'")
TS_ONLY = ("2026-07-01T15:08:09.0651429Z 2026-07-01 15:08:09 [INFO*** "
           "agent.orchestrator: Latest scan: 68 signals at 13:25")


def test_counts_real_429_not_timestamp():
    log = "\n".join([REAL_NEWS, TS_ONLY])
    assert measure_429.count_429(log)["total"] == 1  # only the real one


def test_masked_bracket_is_counted():
    assert measure_429.count_429(REAL_NEWS)["total"] == 1


def test_timestamp_429_never_counted():
    assert measure_429.count_429(TS_ONLY)["total"] == 0


def test_component_breakdown():
    log = "\n".join([REAL_NEWS, REAL_SENT, REAL_SENT, REAL_SM])
    res = measure_429.count_429(log)
    assert res["total"] == 4
    assert res["by_component"]["agent.news_detective"] == 1
    assert res["by_component"]["agent.sentinel"] == 2
    assert res["by_component"]["sheets_manager"] == 1


def test_empty_log():
    assert measure_429.count_429("")["total"] == 0
