"""TASK-48 monthly רכיב 2a — write_monthly_summary. No real I/O (monkeypatched)."""
import importlib
import pytest

mod = importlib.import_module("agent.critic.critic_v1")
import sheets_manager as sm

def _c():
    C = mod.CriticAgent
    try: return C()
    except Exception: return C.__new__(C)

ROW = {
    "MonthOf":"2026-05","Trades":12,"Wins":7,"Losses":5,"WinRate":58.3,"TotalPnL":340.0,
    "AvgWin":9.5,"AvgLoss":-8.2,"Enters":20,"Skips":40,"TickersChecked":200,
    "Anomalies":3,"Conflicts":1,"Conclusion":"12 עסקאות","SampleSizeFlag":"OK",
    "GeneratedAt":"2026-06-01T01:00:00",
}

class _FakeWS: pass

@pytest.fixture
def captured(monkeypatch):
    box = {}
    monkeypatch.setattr(mod, "_get_monthly_worksheet", lambda: _FakeWS(), raising=False)
    def fake_append(ws, row, dedup_col=None, dedup_val=None, **kw):
        box["row"]=row; box["dedup_col"]=dedup_col; box["dedup_val"]=dedup_val; return True
    monkeypatch.setattr(sm, "safe_append_row", fake_append)
    return box

def test_method_exists():
    assert hasattr(_c(), "write_monthly_summary")

def test_16_values_header_order(captured):
    _c().write_monthly_summary(ROW)
    r = captured["row"]
    assert len(r)==16 and r[0]=="2026-05" and r[-1]=="2026-06-01T01:00:00"

def test_dedup_on_monthof(captured):
    _c().write_monthly_summary(ROW)
    assert captured["dedup_col"]==0 and captured["dedup_val"]=="2026-05"

def test_returns_true(captured):
    assert _c().write_monthly_summary(ROW) is True

def test_none_to_empty(captured):
    row=dict(ROW); row["WinRate"]=None
    _c().write_monthly_summary(row)
    assert captured["row"][4]==""

def test_follows_schema_headers(captured):
    from agent.setup.create_agent_sheets import AGENT_SHEET_HEADERS
    hdrs=AGENT_SHEET_HEADERS["monthly_summary"]
    _c().write_monthly_summary(ROW)
    r=captured["row"]
    for i,h in enumerate(hdrs):
        exp=ROW.get(h,""); exp="" if exp is None else exp
        assert r[i]==exp, f"col {h}@{i}: {r[i]!r}!={exp!r}"
