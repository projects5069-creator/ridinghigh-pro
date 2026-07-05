#!/usr/bin/env bash
# M2b-3c-iv-3 — verify main()'s execute loop is wired to the RPI chain. A full headless run
# needs a Keychain token + green base + real worktrees, so this is a structural smoke test:
# the RPI functions are defined, the loop calls run_rpi_task + check_scope_lock, uses the
# auto-dancer branch, commits locally only on `ready`, and never pushes / opens a PR / leaves
# a stray per-task rh-night/ branch.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO/scripts/overnight/rh-overnight.sh"

fail=0
ok()  { echo "  ✓ $1"; }
bad() { echo "  ✗ $1"; fail=1; }

# 1) RPI functions are defined after sourcing (main() does NOT run when sourced)
source "$SCRIPT"
for fn in run_stage run_rpi_chain run_rpi_task check_scope_lock; do
  declare -F "$fn" >/dev/null && ok "function $fn defined" || bad "function $fn MISSING"
done

# 2) execute loop wired to the RPI chain + scope-lock + auto-dancer branch/worktree
grep -qF 'run_rpi_task "$tid" "$wt" "$resolved_settings" "$adir"' "$SCRIPT" && ok "loop calls run_rpi_task" || bad "run_rpi_task not called"
grep -qF 'check_scope_lock "$wt" "$adir"' "$SCRIPT"                        && ok "commit gated on check_scope_lock" || bad "scope-lock not wired"
grep -qF 'auto-dancer/$tid' "$SCRIPT"                                      && ok "branch = auto-dancer/<tid>" || bad "auto-dancer branch missing"
grep -qF 'rh-dancer-${tid}' "$SCRIPT"                                      && ok "worktree = rh-dancer-<tid>" || bad "rh-dancer worktree missing"
grep -qF 'git commit -q -m "auto-dancer(' "$SCRIPT"                        && ok "local commit on ready" || bad "local commit missing"

# 3) no stray per-task rh-night/ branch remains (scan/report worktrees use rh-night-*, no slash)
[ "$(grep -c 'rh-night/' "$SCRIPT")" = "0" ] && ok "no rh-night/ per-task branch remains" || bad "rh-night/ still present in loop"

# 4) the runner never opens a PR (commit boundary = local only). Ignore comment lines —
# "gh pr create" appears only in prose (a PATH note + the §8 boundary comment), never as a command.
grep -vE '^[[:space:]]*#' "$SCRIPT" | grep -q 'gh pr create' \
  && bad "gh pr create present in runner (non-comment)" || ok "no gh pr create command in runner"

# 5) PLAN_ONLY DRY mode wired: --plan-only flag, is_plan_only branch in the loop, run_plan_only called
grep -qF -- '--plan-only)' "$SCRIPT"                        && ok "case has --plan-only" || bad "--plan-only case missing"
grep -qF 'run_plan_only "$tid" "$pbody" "$wt" "$resolved_settings" "$adir"' "$SCRIPT" && ok "loop calls run_plan_only" || bad "run_plan_only not wired"
grep -qF 'if is_plan_only; then' "$SCRIPT"                  && ok "is_plan_only branch present" || bad "is_plan_only branch missing"

if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
