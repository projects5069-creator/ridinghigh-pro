#!/bin/bash
#
# install.sh — install the project's tracked git hooks into .git/hooks/.
#
# Mirrors the existing post-commit convention (a script installs hooks into
# .git/hooks/). Deliberately does NOT set core.hooksPath, because that would
# disable the existing local .git/hooks/post-commit hook. This script only
# touches the pre-commit hook and leaves every other hook untouched.
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
