#!/bin/bash
#
# install.sh — install the project's tracked git hooks into .git/hooks/.
#
# Mirrors the existing post-commit convention (a script installs hooks into
# .git/hooks/). Deliberately does NOT set core.hooksPath, because that would
# disable the existing local .git/hooks/post-commit hook. This script installs
# the pre-commit git hook AND deploys the tracked Claude Code hooks
# (scripts/claude_hooks/) to ~/.claude/hooks/ (RULE #11 skill enforcement).
#
# Usage:
#   scripts/git_hooks/install.sh
#
# Re-run after cloning the repo, since .git/hooks/ is not version controlled.

set -eu

repo_root="$(git rev-parse --show-toplevel)"
src="$repo_root/scripts/git_hooks/pre-commit"
dst="$repo_root/.git/hooks/pre-commit"

if [ ! -f "$src" ]; then
    echo "error: source hook not found: $src" >&2
    exit 1
fi

cp "$src" "$dst"
chmod +x "$dst"
echo "Installed pre-commit hook -> $dst"


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
