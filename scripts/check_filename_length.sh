#!/bin/bash
#
# check_filename_length.sh — SSoT filename-length guard (TASK-85 / TASK-133).
#
# Fails (exit 1) if any inspected path's BASENAME is >= LIMIT bytes.
#
# Why: Linux ext4 caps a single filename component at 255 BYTES, and Hebrew is
# 2 bytes per character. The backlog CLI embeds the full task title into the
# filename, so a long Hebrew title silently produces an over-long basename. On
# 2026-06-09 a 333-byte task-122 filename made actions/checkout fail on EVERY
# GitHub Actions workflow, taking CI down ~16h (rename: 307c0e5).
#
# Single source of truth: both the pre-commit hook (scripts/git_hooks/pre-commit)
# and the CI guard (.github/workflows/filename_guard.yml) call THIS script — the
# byte-measuring logic lives in exactly one place (§10).
#
# Modes:
#   check_filename_length.sh <path> [<path> ...]   # check the given paths
#   check_filename_length.sh                       # no args -> all tracked files (git ls-files)
#
# Limit (bytes), via env FILENAME_BYTE_LIMIT (default 200):
#   - pre-commit calls it at 200 on STAGED files only  -> early margin for NEW names
#   - CI calls it at 250 over the WHOLE tree (repo-wide) -> hard-cap guard (255
#     ext4 limit, 5 B margin) that stays green on grandfathered 204-219 B files
#     yet still blocks anything that would actually break checkout.
#
# Override a single LOCAL commit (never CI): git commit --no-verify

set -eu

LIMIT="${FILENAME_BYTE_LIMIT:-200}"
violations=""

check_one() {
    base=$(basename -- "$1")
    bytes=$(printf '%s' "$base" | wc -c | tr -d ' ')
    if [ "$bytes" -ge "$LIMIT" ]; then
        violations="${violations}  ${bytes} bytes: ${base}\n"
    fi
}

if [ "$#" -gt 0 ]; then
    for p in "$@"; do
        [ -n "$p" ] && check_one "$p"
    done
else
    # -z = NUL-delimited, UNQUOTED. Plain `git ls-files` C-quotes non-ASCII paths
    # (octal \NNN per byte + surrounding quotes), which inflates the measured
    # basename length far past its true byte count. -z gives the real bytes.
    while IFS= read -r -d '' p; do
        [ -n "$p" ] && check_one "$p"
    done < <(git ls-files -z)
fi

if [ -n "$violations" ]; then
    printf '\n❌ filename-length guard (TASK-85/133): basename(s) >= %s bytes:\n' "$LIMIT" >&2
    printf '%b' "$violations" >&2
    printf '\nLinux ext4 caps a filename at 255 bytes (Hebrew = 2 B/char); over-long\n' >&2
    printf 'names break actions/checkout on every workflow. Shorten the name — for a\n' >&2
    printf 'backlog task that means a shorter TITLE (the CLI embeds it in the filename).\n' >&2
    printf 'Override a single LOCAL commit (not CI): git commit --no-verify\n\n' >&2
    exit 1
fi

exit 0
