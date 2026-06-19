"""Guardrail-file tests (HELD with their impls until explicit approval):
settings.night.json + execute_task.md. The secret hook and wrapper guards have
their own bash tests.
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_settings():
    with open(os.path.join(REPO, ".claude/settings.night.json"), encoding="utf-8") as fh:
        return json.load(fh)


def test_settings_deny_secrets():
    deny = _load_settings()["permissions"]["deny"]
    for rule in ["Read(./.env)", "Read(**/google_credentials.json)",
                 "Read(**/oauth_credentials.json)"]:
        assert rule in deny, rule


def test_settings_registers_secret_hook_not_skillgate():
    cfg = _load_settings()
    cmds = " ".join(
        h["command"] for grp in cfg["hooks"]["PreToolUse"] for h in grp["hooks"]
    )
    assert "block_secrets.sh" in cmds
    assert "pretooluse_skill_gate" not in cmds          # interactive gate disabled at night


def test_settings_allow_is_minimal():
    allow = _load_settings()["permissions"]["allow"]
    assert "Bash(*)" not in allow and "Bash" not in allow   # no blanket shell
    assert "Read" in allow
    assert any(a.startswith("Bash(git ") for a in allow)
    assert any(a.startswith("Bash(gh pr") for a in allow)


def test_execute_prompt_shape():
    with open(os.path.join(REPO, "scripts/overnight/execute_task.md"), encoding="utf-8") as fh:
        t = fh.read().lower()
    for skill in ["using-git-worktrees", "systematic-debugging",
                  "test-driven-development", "verification-before-completion",
                  "finishing-a-development-branch"]:
        assert skill in t, skill
    assert "--draft" in t and "--base main" in t
    assert "never" in t and "main" in t and "push" in t        # main never pushed
    assert "not instructions" in t                              # injection guard
    assert "rule #4" in t or "backup" in t                      # dated .bak
    for key in ["task", "status", "branch", "pr_url", "tokens"]:
        assert key in t                                          # result JSON contract
