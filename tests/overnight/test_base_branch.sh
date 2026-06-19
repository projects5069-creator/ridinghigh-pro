#!/usr/bin/env bash
# BASE_BRANCH pre-flight — replaces the old "cwd branch == main" assert so the runner can
# execute from an isolated worktree (cwd != main) while still basing work on main. Two checks:
# clean working tree AND BASE_BRANCH resolves to a real ref. Tested in a throwaway git repo.
WRAP="$(cd "$(dirname "$0")/../.." && pwd)/scripts/overnight/rh-overnight.sh"
# shellcheck source=/dev/null
source "$WRAP"
fail=0

# default: with no RH_BASE_BRANCH, BASE_BRANCH must be 'main'
[ "${BASE_BRANCH}" = "main" ] && echo "  ✓ BASE_BRANCH defaults to main" || { echo "  ✗ BASE_BRANCH default ($BASE_BRANCH)"; fail=1; }

tmp="$(mktemp -d)"; ( cd "$tmp"
  git init -q -b main 2>/dev/null || { git init -q && git symbolic-ref HEAD refs/heads/main; }
  git config user.email t@t; git config user.name t
  echo a > f; git add f; git commit -qm init
  git branch feature

  rc=0
  BASE_BRANCH=main guard_base_ready >/dev/null 2>&1 || rc=1
  [ "$rc" -eq 0 ] && echo "  ✓ clean tree + main ref → ready" || { echo "  ✗ default should pass"; fail=1; }

  rc=0; BASE_BRANCH=feature guard_base_ready >/dev/null 2>&1 || rc=1
  [ "$rc" -eq 0 ] && echo "  ✓ RH_BASE_BRANCH override (feature) accepted" || { echo "  ✗ override should pass"; fail=1; }

  rc=0; BASE_BRANCH=nope guard_base_ready >/dev/null 2>&1 || rc=1
  [ "$rc" -ne 0 ] && echo "  ✓ nonexistent BASE_BRANCH aborts" || { echo "  ✗ nonexistent base should abort"; fail=1; }

  echo dirty >> f   # unstaged modification
  rc=0; BASE_BRANCH=main guard_base_ready >/dev/null 2>&1 || rc=1
  [ "$rc" -ne 0 ] && echo "  ✓ dirty tree aborts" || { echo "  ✗ dirty tree should abort"; fail=1; }
  exit $fail
)
fail=$(( fail + $? ))
rm -rf "$tmp"
[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit "$fail"
