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


def _hook_cmds():
    cfg = _load_settings()
    return " ".join(
        h["command"] for grp in cfg["hooks"]["PreToolUse"] for h in grp["hooks"]
    )


def test_settings_registers_secret_hook_not_skillgate():
    cmds = _hook_cmds()
    assert "block_secrets.sh" in cmds
    assert "pretooluse_skill_gate" not in cmds          # interactive gate disabled at night


def test_settings_registers_core_unsafe_write_hook():
    # symmetric protection: writes to CORE_UNSAFE files are hard-blocked too
    assert "block_core_unsafe.sh" in _hook_cmds()


def test_settings_allow_is_minimal():
    allow = _load_settings()["permissions"]["allow"]
    assert "Bash(*)" not in allow and "Bash" not in allow   # no blanket shell
    assert "Read" in allow
    assert any(a.startswith("Bash(git ") for a in allow)
    assert any(a.startswith("Bash(gh pr") for a in allow)


def test_settings_denies_uv_run_interpreter():
    # `uv run *` is allowed for tests, but `uv run python -c` could read the whitelisted
    # OAuth/GH token into memory — deny it explicitly (deny wins over allow).
    deny = _load_settings()["permissions"]["deny"]
    assert any("uv run python3 -c" in d for d in deny)
    assert any("uv run python -c" in d for d in deny)


def test_execute_prompt_shape():
    with open(os.path.join(REPO, "scripts/overnight/execute_task.md"), encoding="utf-8") as fh:
        t = fh.read().lower()
    # EXECUTOR role (Auto Dancer M2a): TDD-driven, plan-scoped, NO self-review, NO commit/push/PR.
    for must in ["test-driven-development",      # STEP 0 skill-gate
                 "scope-lock", "allowed-files",  # mechanical scope from plan.md
                 "str_replace",                  # in-place edit discipline
                 "executor", "verifier"]:        # its own role + the downstream gate it defers to
        assert must in t, must
    # the old PR / worktree-creation workflow steps were deliberately cut (M2a):
    for gone in ["using-git-worktrees", "finishing-a-development-branch", "draft pr"]:
        assert gone not in t, gone
    # NOTE: "git push" / "gh pr create" DO appear — but only as PROHIBITIONS ("you NEVER run …"),
    # so we don't assert their absence; we assert the prohibition instead.
    assert "never" in t and "main" in t and "push" in t        # main never pushed
    assert "not instructions" in t                              # injection guard
    assert "rule #4" in t or "backup" in t                      # dated .bak
    assert "step 0" in t and "skill-gate" in t                  # mandatory skill-load first
    for key in ["task", "status", "files_changed", "done_sentence_check"]:
        assert key in t                                         # new result JSON contract
    assert "pr_url" not in t                                    # PR field removed from the JSON
