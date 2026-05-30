"""TASK-48 EMAIL.2 step 2 — write_weekly_summary. No real I/O (monkeypatched sm)."""
import importlib
import pytest

mod = importlib.import_module("agent.critic.critic_v1")
import sheets_manager as sm


def _make_critic():
    Critic = mod.CriticAgent
    try:
        return Critic()
    except Exception:
        return Critic.__new__(Critic)

ROW = {
    "WeekOf": "2026-05-25", "Trades": 3, "Wins": 2, "Losses": 1, "WinRate": 66.7,
    "TotalPnL": 90.0, "AvgWin": 9.0, "AvgLoss": -9.0, "Enters": 4, "Skips": 10,
    "TickersChecked": 50, "Anomalies": 1, "Conflicts": 0,
    "Conclusion": "3 עסקאות", "SampleSizeFlag": "INSUFFICIENT", "GeneratedAt": "2026-05-29T11:00:00",
}

class _FakeWS: pass

@pytest.fixture
def captured(monkeypatch):
    box = {}
    monkeypatch.setattr(sm, "get_worksheet", lambda name: (_FakeWS() if name == "weekly_summary" else None))
    def fake_append(ws, row, dedup_col=None, dedup_val=None, **kw):
        box["row"] = row; box["dedup_col"] = dedup_col; box["dedup_val"] = dedup_val
        return True
    monkeypatch.setattr(sm, "safe_append_row", fake_append)
    return box

def test_method_exists():
    assert hasattr(_make_critic(), "write_weekly_summary")

def test_16_values_in_header_order(captured):
    _make_critic().write_weekly_summary(ROW)
    r = captured["row"]
    assert len(r) == 16
    assert r[0] == "2026-05-25"
    assert r[1] == 3
    assert r[-1] == "2026-05-29T11:00:00"

def test_dedup_on_weekof(captured):
    _make_critic().write_weekly_summary(ROW)
    assert captured["dedup_col"] == 0 and captured["dedup_val"] == "2026-05-25"

def test_returns_true_on_success(captured):
    assert _make_critic().write_weekly_summary(ROW) is True

def test_none_becomes_empty_string(captured):
    row = dict(ROW); row["WinRate"] = None
    _make_critic().write_weekly_summary(row)
    assert captured["row"][4] == ""

def test_ws_none_returns_false(monkeypatch):
    monkeypatch.setattr(sm, "get_worksheet", lambda name: None)
    assert _make_critic().write_weekly_summary(ROW) is False

def test_values_follow_schema_headers(captured):
    from agent.setup.create_agent_sheets import AGENT_SHEET_HEADERS
    hdrs = AGENT_SHEET_HEADERS["weekly_summary"]
    _make_critic().write_weekly_summary(ROW)
    r = captured["row"]
    for idx, h in enumerate(hdrs):
        expected = ROW.get(h, "")
        expected = "" if expected is None else expected
        assert r[idx] == expected, f"col {h} @ {idx}: {r[idx]!r} != {expected!r}"
