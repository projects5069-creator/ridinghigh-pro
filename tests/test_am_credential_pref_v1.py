"""agent_minute dedicated SA: sheets_manager._get_gc prefers a dedicated
agent_minute SA (GOOGLE_CREDENTIALS_JSON_AM) over the shared trading SA
(GOOGLE_CREDENTIALS_JSON), with safe fallback.

Mirror of TASK-215 (_AS for auto_scan) / TASK-58 (_HA for health_audit). Root
cause (live A/B, 2026-07-01): on the shared SA, agent_minute runs suffered
37-61x "429 Read requests per minute per user" while auto_scan on its dedicated
_AS SA stayed clean on the exact same minutes. The only difference is the SA —
so agent_minute gets its own read-quota bucket via _get_gc, gated by which
workflow injects the secret: ONLY agent_minute.yml injects
GOOGLE_CREDENTIALS_JSON_AM, so only the agent_minute process picks it up. Every
other process (auto_scan, health_audit, dashboard, collectors) has no _AM in its
env and keeps its own SA — NO-OP until the _AM secret is provisioned + injected.

We don't want real Google auth, so we monkeypatch the credential factory and
gspread.authorize to capture WHICH env var's JSON was selected.
"""
import json
import gspread
from google.oauth2 import service_account

import sheets_manager as sm


def _capture(monkeypatch):
    """Patch the cred factory + authorize; return a dict that records the info dict."""
    captured = {}

    def fake_from_info(info, scopes=None):
        captured["info"] = info
        return "FAKE_CREDS"

    monkeypatch.setattr(service_account.Credentials,
                        "from_service_account_info", fake_from_info)
    monkeypatch.setattr(gspread, "authorize", lambda creds: ("FAKE_CLIENT", creds))
    return captured


def test_am_preferred_when_am_and_shared_set(monkeypatch):
    """agent_minute process: _AM + shared present → the dedicated _AM SA must win."""
    captured = _capture(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AS", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AM", json.dumps({"marker": "AM"}))
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    sm._get_gc()

    assert captured["info"]["marker"] == "AM", \
        "_get_gc must prefer the dedicated agent_minute _AM SA when present"


def test_fallback_to_shared_when_am_absent(monkeypatch):
    """No-op safety: other processes (no _AM) keep using the shared trading SA."""
    captured = _capture(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AS", raising=False)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AM", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    sm._get_gc()

    assert captured["info"]["marker"] == "TRADING"


def test_am_only(monkeypatch):
    captured = _capture(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AS", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AM", json.dumps({"marker": "AM"}))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)

    sm._get_gc()

    assert captured["info"]["marker"] == "AM"


def test_empty_am_falls_back_to_shared(monkeypatch):
    """GitHub Actions sets an unset secret to "" (present-but-empty). The guard
    must treat empty as absent and fall back to the shared SA — not json.loads("")
    and crash. This is the no-op safety before the _AM secret is provisioned."""
    captured = _capture(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AS", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AM", "")  # empty = unset secret in CI
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    sm._get_gc()

    assert captured["info"]["marker"] == "TRADING"


def test_as_still_preferred_no_regression(monkeypatch):
    """Regression guard for TASK-215: with _AS present and no _AM, the auto_scan
    _AS SA must still win — the new _AM branch must not disturb the _AS path."""
    captured = _capture(monkeypatch)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AS", json.dumps({"marker": "AS"}))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AM", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    sm._get_gc()

    assert captured["info"]["marker"] == "AS"
