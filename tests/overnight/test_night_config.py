"""Shape/validity tests for the committable config artifacts:
classify_task.md (layer-2 prompt), com.rh.overnight.plist (launchd), and
overnight_report_email.yml (decoupled email). settings.night.json is covered
here too (Auto Dancer M2b-3b — .dancer/ artifact write-scope + no security
regression). The remaining guardrail files (execute_task.md, block_secrets.sh,
rh-overnight.sh) are tested separately.
"""
import json
import os
import plistlib

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return fh.read()


def test_classify_prompt_shape():
    t = _read("scripts/overnight/classify_task.md")
    for field in ["auto_safe", "touches_core", "reads_data", "reason"]:
        assert field in t, field
    low = t.lower()
    assert "read-only" in low or "read only" in low
    assert "uncertain" in low and "false" in low          # fail-closed
    assert "edit" not in low.split("never")[-1] or "never edit" in low  # no editing


def test_plist_valid_and_scheduled():
    path = os.path.join(REPO, "scripts/overnight/com.rh.overnight.plist")
    with open(path, "rb") as fh:
        plistlib.load(fh)   # cross-platform validity (replaces macOS-only `plutil`; works on ubuntu CI)
    body = _read("scripts/overnight/com.rh.overnight.plist")
    assert "StartCalendarInterval" in body
    assert "<integer>2</integer>" in body                 # 02:00
    assert "caffeinate" in body and "rh-overnight.sh" in body
    assert "<false/>" in body                              # RunAtLoad false
    assert "MAX_CANDIDATES" in body and "<string>70</string>" in body   # reach TASK-126 in the tail


def test_checkauth_plist_valid():
    # gate 6: a one-shot LaunchAgent that runs --check-auth so we verify the Keychain read
    # from the REAL restricted launchd session (not the convenient shell) BEFORE arming the schedule.
    path = os.path.join(REPO, "scripts/overnight/com.rh.overnight.checkauth.plist")
    with open(path, "rb") as fh:
        plistlib.load(fh)   # cross-platform validity (replaces macOS-only `plutil`)
    body = _read("scripts/overnight/com.rh.overnight.checkauth.plist")
    assert "--check-auth" in body
    assert "com.rh.overnight.checkauth" in body
    assert "<false/>" in body                                 # RunAtLoad false → kickstart only, never scheduled


def test_email_workflow_shape():
    y = _read(".github/workflows/overnight_report_email.yml")
    assert "overnight-reports" in y                        # branch trigger
    assert "docs/overnight" in y                           # path filter
    assert "secrets.SMTP_HOST" in y and "secrets.EMAIL_TO" in y
    assert "email_sender" in y                             # reuse existing sender
    assert "ANTHROPIC_API_KEY" not in y                    # email job needs no model


def _night_settings():
    return json.loads(_read(".claude/settings.night.json"))


def test_night_settings_valid_json():
    _night_settings()   # raises if malformed


def test_dancer_artifact_write_scope():
    # Auto Dancer M2b-3b: RPI roles may write artifacts under .dancer/ (plan.md,
    # critique-*.json, verify.json, ...) — scoped, NOT a blanket Write.
    allow = _night_settings()["permissions"]["allow"]
    assert "Write(.dancer/**)" in allow
    assert "Write(tests/**)" in allow                      # existing scope preserved
    assert "Write" not in allow                            # never a blanket Write


def test_secret_denies_intact():
    # no security regression — every secret Read-deny still present
    deny = _night_settings()["permissions"]["deny"]
    for pat in [
        "Read(**/.env)", "Read(**/.env.*)", "Read(**/google_credentials.json)",
        "Read(**/oauth_credentials.json)", "Read(**/*_sheet_id)", "Read(**/secrets.toml)",
    ]:
        assert pat in deny, pat


def test_hooks_intact():
    # both PreToolUse guard hooks still registered
    hooks = json.dumps(_night_settings()["hooks"])
    assert "block_secrets.sh" in hooks
    assert "block_core_unsafe.sh" in hooks
