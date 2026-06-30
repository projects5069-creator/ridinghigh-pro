"""TASK-215: sheets_manager._get_gc prefers a dedicated auto_scan SA
(GOOGLE_CREDENTIALS_JSON_AS) over the shared trading SA (GOOGLE_CREDENTIALS_JSON),
with safe fallback.

Goal: move auto_scan off the shared SA's read quota to end market-hours 429
contention (mirror of TASK-58, which did the same for health_audit). Because
auto_scan goes through the SHARED _get_gc (unlike health_audit's isolated
client), the switch lives in _get_gc itself and is gated by which workflow
injects the secret: ONLY auto_scan.yml injects GOOGLE_CREDENTIALS_JSON_AS, so
only the auto_scan process picks it up. Every other process (agents, dashboard)
has no _AS in its env and keeps the shared SA — so this is a NO-OP until the
_AS secret is provisioned and injected.

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


def test_as_preferred_when_both_env_set(monkeypatch):
    """auto_scan process: both vars present → the dedicated _AS SA must win."""
    captured = _capture(monkeypatch)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AS", json.dumps({"marker": "AS"}))
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    sm._get_gc()

    assert captured["info"]["marker"] == "AS", \
        "_get_gc must prefer the dedicated auto_scan _AS SA when present"


def test_fallback_to_shared_when_as_absent(monkeypatch):
    """No-op safety: other processes (no _AS) keep using the shared trading SA."""
    captured = _capture(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AS", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    sm._get_gc()

    assert captured["info"]["marker"] == "TRADING"


def test_as_only(monkeypatch):
    captured = _capture(monkeypatch)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AS", json.dumps({"marker": "AS"}))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)

    sm._get_gc()

    assert captured["info"]["marker"] == "AS"


def test_empty_as_falls_back_to_shared(monkeypatch):
    """GitHub Actions sets an unset secret to "" (present-but-empty). The guard
    must treat empty as absent and fall back to the shared SA — not json.loads("")
    and crash. This is the no-op safety before the _AS secret is provisioned."""
    captured = _capture(monkeypatch)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AS", "")  # empty = unset secret in CI
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    sm._get_gc()

    assert captured["info"]["marker"] == "TRADING"
