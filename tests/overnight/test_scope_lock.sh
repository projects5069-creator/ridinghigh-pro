#!/usr/bin/env bash
# M2b-3c-iv-2 — check_scope_lock(): proves a task's git diff touched ONLY the plan's
# allowed_files and no CORE_UNSAFE file. Hermetic: builds a throwaway git repo as the
# worktree, mutates files, and drives plan_result.json variants. No API.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
ok()  { echo "  ✓ $1"; }
bad() { echo "  ✗ $1"; fail=1; }

source "$REPO/scripts/overnight/rh-overnight.sh"   # main() does NOT run when sourced

# --- throwaway git repo as the task worktree ---
wt="$TMP/wt"; mkdir -p "$wt"
git -C "$wt" init -q
git -C "$wt" config user.email t@t; git -C "$wt" config user.name t
printf 'x=1\n' > "$wt/allowed.py"
printf 'y=1\n' > "$wt/other.py"
printf 'z=1\n' > "$wt/formulas.py"
printf '.dancer/\n' > "$wt/.gitignore"
git -C "$wt" add -A; git -C "$wt" commit -qm base
git -C "$wt" tag base
BASE_BRANCH=base          # override the global for this hermetic repo

adir="$wt/.dancer"; mkdir -p "$adir"
mkplan() { printf '%s' "$1" > "$adir/plan_result.json"; }

# 1) only an allowed file touched → pass (0)
mkplan '{"allowed_files":["allowed.py"]}'
printf 'x=2\n' > "$wt/allowed.py"
if check_scope_lock "$wt" "$adir" 2>/dev/null; then ok "in-scope edit → pass"; else bad "in-scope wrongly rejected"; fi
git -C "$wt" checkout -q -- allowed.py

# 2) an out-of-scope file touched → reject (nonzero) + SCOPE VIOLATION on stderr
mkplan '{"allowed_files":["allowed.py"]}'
printf 'y=2\n' > "$wt/other.py"
err="$(check_scope_lock "$wt" "$adir" 2>&1 1>/dev/null)"; rc=$?
[ "$rc" -ne 0 ] && ok "out-of-scope → reject" || bad "out-of-scope wrongly passed"
printf '%s' "$err" | grep -q "SCOPE VIOLATION" && ok "emits SCOPE VIOLATION" || bad "no SCOPE VIOLATION msg"
git -C "$wt" checkout -q -- other.py

# 3) plan without allowed_files → fail-closed (1)
mkplan '{"task":"TASK-1"}'
printf 'x=3\n' > "$wt/allowed.py"
if check_scope_lock "$wt" "$adir" 2>/dev/null; then bad "missing allowed_files wrongly passed"; else ok "no allowed_files → fail-closed"; fi
git -C "$wt" checkout -q -- allowed.py

# 4) a CORE_UNSAFE file, even if listed in allowed_files → reject (1)
mkplan '{"allowed_files":["formulas.py"]}'
printf 'z=2\n' > "$wt/formulas.py"
if check_scope_lock "$wt" "$adir" 2>/dev/null; then bad "CORE_UNSAFE wrongly passed"; else ok "CORE_UNSAFE (formulas.py) → reject even if allowed"; fi
git -C "$wt" checkout -q -- formulas.py

if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
