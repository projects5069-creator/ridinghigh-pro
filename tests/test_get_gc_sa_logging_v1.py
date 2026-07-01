"""Diagnostic: sheets_manager._get_gc must print the client_email of the SA it
selected, so live GitHub Actions logs reveal WHICH service account each process
actually authenticates as.

Motivation (2026-07-01): agent_minute on the dedicated _AM secret still hit 429
on project 591299446687 while auto_scan on _AS stayed clean on the SAME project
— proving the quota is per-SA, not per-project. That means the credential
agent_minute actually authenticates with is still NOT the separate SA. The logs
do not print client_email, so we can't tell which SA is in the _AM secret. This
one-line diagnostic exposes it. client_email is an identifier, not a secret
(the private_key is the secret and is never printed).

We monkeypatch the cred factory + gspread.authorize so no real auth happens.
"""
import json
import gspread
from google.oauth2 import service_account

import sheets_manager as sm


def _patch_auth(monkeypatch):
    monkeypatch.setattr(service_account.Credentials,
                        "from_service_account_info", lambda info, scopes=None: "FAKE_CREDS")
    monkeypatch.setattr(gspread, "authorize", lambda creds: "FAKE_CLIENT")


def test_get_gc_prints_am_client_email(monkeypatch, capsys):
    """When agent_minute's _AM secret is used, _get_gc must print its client_email."""
    _patch_auth(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AS", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_AM", json.dumps(
        {"client_email": "ridinghigh-agent-minute@ridinghigh-pro-v2.iam.gserviceaccount.com"}))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)

    sm._get_gc()

    out = capsys.readouterr().out
    assert "ridinghigh-agent-minute@ridinghigh-pro-v2.iam.gserviceaccount.com" in out, \
        "_get_gc must print the client_email of the _AM SA it authenticates with"


def test_get_gc_prints_shared_client_email_on_fallthrough(monkeypatch, capsys):
    """No _AM/_AS: _get_gc uses the shared SA and must print ITS client_email —
    so a fallthrough (empty/absent _AM) is visible in the logs too."""
    _patch_auth(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AS", raising=False)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_AM", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps(
        {"client_email": "ridinghigh-sheets-v2@ridinghigh-pro-v2.iam.gserviceaccount.com"}))

    sm._get_gc()

    out = capsys.readouterr().out
    assert "ridinghigh-sheets-v2@ridinghigh-pro-v2.iam.gserviceaccount.com" in out, \
        "_get_gc must print the client_email of the shared SA on fallthrough"
