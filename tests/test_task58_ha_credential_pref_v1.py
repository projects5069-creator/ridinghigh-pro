"""TASK-58: health_audit prefers a dedicated SA (GOOGLE_CREDENTIALS_JSON_HA)
over the shared trading SA (GOOGLE_CREDENTIALS_JSON), with safe fallback.

The fix must be a no-op until the _HA secret exists: when only the trading
env var is set, get_gspread_client must keep using it (so nothing breaks
before the 2nd SA is provisioned).

We don't want real Google auth, so we monkeypatch the credential factory and
gspread.authorize to capture WHICH env var's JSON was selected.
"""
import json
import gspread
from google.oauth2 import service_account

import health_audit as ha


def _capture(monkeypatch):
    """Patch the cred factory + authorize; return a dict that records the info dict."""
    captured = {}

    def fake_from_info(info, scopes=None):
        captured["info"] = info
        return "FAKE_CREDS"

    # from_service_account_info is accessed on the class inside get_gspread_client;
    # replacing the class attribute with a plain function works for the class-level call.
    monkeypatch.setattr(service_account.Credentials,
                        "from_service_account_info", fake_from_info)
    monkeypatch.setattr(gspread, "authorize", lambda creds: ("FAKE_CLIENT", creds))
    return captured


def test_ha_preferred_when_both_env_set(monkeypatch):
    captured = _capture(monkeypatch)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_HA", json.dumps({"marker": "HA"}))
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    client, err = ha.get_gspread_client(local=False)

    assert err is None
    assert captured["info"]["marker"] == "HA", \
        "health_audit must prefer the dedicated _HA SA when present"


def test_fallback_to_trading_when_ha_absent(monkeypatch):
    """No-op safety: until the _HA secret exists, the trading SA is still used."""
    captured = _capture(monkeypatch)
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON_HA", raising=False)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    client, err = ha.get_gspread_client(local=False)

    assert err is None
    assert captured["info"]["marker"] == "TRADING"


def test_ha_only(monkeypatch):
    captured = _capture(monkeypatch)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_HA", json.dumps({"marker": "HA"}))
    monkeypatch.delenv("GOOGLE_CREDENTIALS_JSON", raising=False)

    client, err = ha.get_gspread_client(local=False)

    assert err is None
    assert captured["info"]["marker"] == "HA"


def test_empty_ha_falls_back_to_trading(monkeypatch):
    """GitHub Actions sets an unset secret to "" (present-but-empty). The guard
    must treat empty as absent and fall back to the trading SA — not json.loads("")
    and crash. This is the no-op safety before the _HA secret is provisioned."""
    captured = _capture(monkeypatch)
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON_HA", "")  # empty = unset secret in CI
    monkeypatch.setenv("GOOGLE_CREDENTIALS_JSON", json.dumps({"marker": "TRADING"}))

    client, err = ha.get_gspread_client(local=False)

    assert err is None, f"empty _HA must not crash; got err={err}"
    assert captured["info"]["marker"] == "TRADING"
