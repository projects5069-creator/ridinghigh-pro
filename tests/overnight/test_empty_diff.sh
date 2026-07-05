#!/usr/bin/env bash
# M4-3 — finalize_ready() git-diff-verify: on a VERIFIED `ready`, an EMPTY diff (VERIFIER said
# ready but no file changed) must NOT commit — it writes status=empty_diff instead. A real diff
# commits locally. Hermetic: throwaway git repo as the worktree, no API.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
ok()  { echo "  ✓ $1"; }
bad() { echo "  ✗ $1"; fail=1; }

source "$REPO/scripts/overnight/rh-overnight.sh"   # main() does NOT run when sourced

# throwaway git repo as the task worktree
wt="$TMP/wt"; mkdir -p "$wt"
git -C "$wt" init -q
git -C "$wt" config user.email t@t; git -C "$wt" config user.name t
printf 'x=1\n' > "$wt/allowed.py"
printf '.dancer/\n' > "$wt/.gitignore"
git -C "$wt" add -A; git -C "$wt" commit -qm base
git -C "$wt" tag base
BASE_BRANCH=base

adir="$wt/.dancer"; mkdir -p "$adir"
printf '%s' '{"allowed_files":["allowed.py"],"done_sentence":"make x=2"}' > "$adir/plan_result.json"
RAW="$TMP/raw"; mkdir -p "$RAW"

# 1) EMPTY diff → no commit, status=empty_diff
before="$(git -C "$wt" rev-list --count HEAD)"
finalize_ready TASK-1 "$wt" "$adir" "$RAW" >/dev/null 2>&1
after="$(git -C "$wt" rev-list --count HEAD)"
[ "$after" = "$before" ] && ok "empty diff -> NO commit" || bad "empty diff wrongly committed ($before to $after)"
[ "$(jq -r .status "$RAW/TASK-1.json" 2>/dev/null)" = "empty_diff" ] && ok "empty diff → status=empty_diff" || bad "empty_diff status not written"

# 2) REAL diff → local commit made
printf 'x=2\n' > "$wt/allowed.py"
before="$(git -C "$wt" rev-list --count HEAD)"
finalize_ready TASK-2 "$wt" "$adir" "$RAW" >/dev/null 2>&1
after="$(git -C "$wt" rev-list --count HEAD)"
[ "$after" = "$((before + 1))" ] && ok "real diff -> local commit made" || bad "real diff not committed ($before to $after)"
git -C "$wt" log -1 --pretty=%s | grep -q 'auto-dancer(TASK-2)' && ok "commit message = auto-dancer(TASK-2)" || bad "commit message wrong"

# 3) scope violation still short-circuits before the diff check
printf '%s' '{"allowed_files":["allowed.py"],"done_sentence":"x"}' > "$adir/plan_result.json"
printf 'z=1\n' > "$wt/other.py"       # a file NOT in allowed_files
before="$(git -C "$wt" rev-list --count HEAD)"
finalize_ready TASK-3 "$wt" "$adir" "$RAW" >/dev/null 2>&1
after="$(git -C "$wt" rev-list --count HEAD)"
[ "$after" = "$before" ] && ok "scope violation → NO commit" || bad "scope violation wrongly committed"
[ "$(jq -r .status "$RAW/TASK-3.json" 2>/dev/null)" = "scope_violation" ] && ok "scope violation → status=scope_violation" || bad "scope_violation status not written"

if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
