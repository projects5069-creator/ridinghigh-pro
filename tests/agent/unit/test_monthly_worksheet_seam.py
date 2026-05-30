"""TASK-48 2b-ii — _get_monthly_worksheet seam. Monkeypatched, no real I/O. RED before impl."""
import importlib
import pytest

mod = importlib.import_module("agent.critic.critic_v1")

class _FakeWS:
    title = "monthly_summary"

class _FakeSS:
    def __init__(self): self._tabs = {"monthly_summary": _FakeWS()}
    def worksheet(self, name):
        if name in self._tabs: return self._tabs[name]
        raise Exception("WorksheetNotFound")
    def add_worksheet(self, title, rows, cols):
        ws = _FakeWS(); ws.title = title; self._tabs[title] = ws; return ws

class _FakeGC:
    def open_by_key(self, sid): return _FakeSS()

def test_returns_none_when_dotfile_missing(monkeypatch, tmp_path):
    # אם אין dotfile → None (מדגרד בחן, לא קורס)
    monkeypatch.setattr(mod, "_SUMMARIES_DOTFILE", tmp_path / "nope", raising=False)
    assert mod._get_monthly_worksheet() is None

def test_opens_existing_tab(monkeypatch, tmp_path):
    df = tmp_path / ".rh_summaries_sheet_id"; df.write_text("FAKE_ID")
    monkeypatch.setattr(mod, "_SUMMARIES_DOTFILE", df, raising=False)
    import sheets_manager as sm
    monkeypatch.setattr(sm, "_get_gc", lambda: _FakeGC())
    ws = mod._get_monthly_worksheet()
    assert ws is not None and ws.title == "monthly_summary"

def test_creates_tab_if_missing(monkeypatch, tmp_path):
    df = tmp_path / ".rh_summaries_sheet_id"; df.write_text("FAKE_ID")
    monkeypatch.setattr(mod, "_SUMMARIES_DOTFILE", df, raising=False)
    import sheets_manager as sm
    class _EmptySS(_FakeSS):
        def __init__(self): self._tabs = {}
    class _GC2:
        def open_by_key(self, sid): return _EmptySS()
    monkeypatch.setattr(sm, "_get_gc", lambda: _GC2())
    ws = mod._get_monthly_worksheet()
    assert ws is not None and ws.title == "monthly_summary"

def test_returns_none_on_open_error(monkeypatch, tmp_path):
    df = tmp_path / ".rh_summaries_sheet_id"; df.write_text("BAD")
    monkeypatch.setattr(mod, "_SUMMARIES_DOTFILE", df, raising=False)
    import sheets_manager as sm
    class _GCErr:
        def open_by_key(self, sid): raise Exception("open failed")
    monkeypatch.setattr(sm, "_get_gc", lambda: _GCErr())
    assert mod._get_monthly_worksheet() is None
