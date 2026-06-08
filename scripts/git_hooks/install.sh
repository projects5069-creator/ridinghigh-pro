#!/bin/bash
#
# install.sh — install the project's tracked git hooks into .git/hooks/.
#
# Mirrors the git-hook convention (a script copies hooks into .git/hooks/).
# Deliberately does NOT set core.hooksPath, because that would bypass any other
# local .git/hooks/ scripts. This script installs the pre-commit AND post-commit
# git hooks AND deploys the tracked Claude Code hooks (scripts/claude_hooks/) to
# ~/.claude/hooks/ (RULE #11 skill enforcement).
#
# Usage:
#   scripts/git_hooks/install.sh
#
# Re-run after cloning the repo, since .git/hooks/ is not version controlled.

set -eu

repo_root="$(git rev-parse --show-toplevel)"

# -- git hooks (pre-commit + post-commit) ------------------------------------
for hook in pre-commit post-commit; do
    src="$repo_root/scripts/git_hooks/$hook"
    dst="$repo_root/.git/hooks/$hook"
    if [ ! -f "$src" ]; then
        echo "error: source hook not found: $src" >&2
        exit 1
    fi
    cp "$src" "$dst"
    chmod +x "$dst"
    echo "Installed $hook hook -> $dst"
done


# -- Claude Code hooks (RULE #11 skill enforcement) --------------------------
# Canonical mirror scripts/claude_hooks/ deployed to live ~/.claude/hooks/.
claude_src="$repo_root/scripts/claude_hooks"
claude_dst="$HOME/.claude/hooks"
mkdir -p "$claude_dst"
for f in "$claude_src"/*; do
    cp "$f" "$claude_dst/"
done
chmod +x "$claude_dst"/*.sh 2>/dev/null || true
echo "Deployed Claude hooks (skill_enforcement, pretooluse_gate, RECOVERY) -> $claude_dst"
