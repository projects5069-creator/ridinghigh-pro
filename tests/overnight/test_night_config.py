"""Shape/validity tests for the committable config artifacts:
classify_task.md (layer-2 prompt), com.rh.overnight.plist (launchd), and
overnight_report_email.yml (decoupled email). The guardrail files
(settings.night.json, execute_task.md, block_secrets.sh, rh-overnight.sh) are
tested separately and held for explicit approval.
"""
import os
import subprocess

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
    r = subprocess.run(["plutil", "-lint", path], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    body = _read("scripts/overnight/com.rh.overnight.plist")
    assert "StartCalendarInterval" in body
    assert "<integer>2</integer>" in body                 # 02:00
    assert "caffeinate" in body and "rh-overnight.sh" in body
    assert "<false/>" in body                              # RunAtLoad false


def test_email_workflow_shape():
    y = _read(".github/workflows/overnight_report_email.yml")
    assert "overnight-reports" in y                        # branch trigger
    assert "docs/overnight" in y                           # path filter
    assert "secrets.SMTP_HOST" in y and "secrets.EMAIL_TO" in y
    assert "email_sender" in y                             # reuse existing sender
    assert "ANTHROPIC_API_KEY" not in y                    # email job needs no model
