"""TASK-176: News Detective demoted — no longer runs per-minute.

Root cause (2026-07-01): news_detective.write_findings() calls get_worksheet()
per-ticker inside the agent_minute loop = ~46 read-requests/run, the largest
single contributor to agent_minute's per-SA 429 flood (46/91). Research proved
it net-negative (WITH-news WR 60% < WITHOUT 62%, EDGAR r=-0.156). So it is gated
off per-minute via config.NEWS_DETECTIVE_ENABLED (default False), reversible.

We test the orchestrator's _maybe_write_news guard directly (no full run()).
"""
from unittest.mock import Mock

import config
import agent.orchestrator as orch


def test_news_disabled_skips_write(monkeypatch):
    """flag False -> write_findings must NOT be called (removes the 46/91 429s)."""
    monkeypatch.setattr(config, "NEWS_DETECTIVE_ENABLED", False)
    spy = Mock()

    orch._maybe_write_news(spy, "ABC")

    spy.write_findings.assert_not_called()


def test_news_enabled_calls_write(monkeypatch):
    """flag True -> preserve the existing per-ticker behaviour (regression guard)."""
    monkeypatch.setattr(config, "NEWS_DETECTIVE_ENABLED", True)
    spy = Mock()

    orch._maybe_write_news(spy, "ABC")

    spy.write_findings.assert_called_once_with("ABC")


def test_news_write_error_is_swallowed(monkeypatch):
    """Even enabled, a write error must NOT propagate (log-only, never blocks)."""
    monkeypatch.setattr(config, "NEWS_DETECTIVE_ENABLED", True)
    spy = Mock()
    spy.write_findings.side_effect = RuntimeError("429 boom")

    orch._maybe_write_news(spy, "ABC")  # must not raise

    spy.write_findings.assert_called_once_with("ABC")
