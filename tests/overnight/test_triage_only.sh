#!/usr/bin/env bash
# --triage-only runs stages 0-1 ONLY (pre-flight + triage -> emit queue/needs_human) and stops
# BEFORE the execute phase: no per-task worktrees, no PRs, no report publish. We assert the gate
# decision (is_triage_only) and that the early-return is positioned before every execute/PR/publish
# action in the source (a live run needs real auth+classifier — that's the watched gate-5).
WRAP="$(cd "$(dirname "$0")/../.." && pwd)/scripts/overnight/rh-overnight.sh"
# shellcheck source=/dev/null
source "$WRAP"
fail=0

# unit: the gate decision
TRIAGE_ONLY=1 is_triage_only && echo "  ✓ is_triage_only true when TRIAGE_ONLY=1" || { echo "  ✗ should be true"; fail=1; }
( unset TRIAGE_ONLY; is_triage_only ) && { echo "  ✗ should be false by default"; fail=1; } || echo "  ✓ is_triage_only false by default"

# dispatch present
grep -q -- '--triage-only)' "$WRAP" && echo "  ✓ --triage-only dispatch present" || { echo "  ✗ no dispatch"; fail=1; }

# MAX_CANDIDATES cap: bounds classifier calls; default high enough to sample the distribution
{ [ "${MAX_CANDIDATES:-0}" -ge 15 ]; } 2>/dev/null && echo "  ✓ MAX_CANDIDATES default ≥15 (representative sample)" || { echo "  ✗ MAX_CANDIDATES default too low/unset (${MAX_CANDIDATES:-unset})"; fail=1; }
MAX_CANDIDATES=25; cap_reached 25 && echo "  ✓ cap_reached at limit" || { echo "  ✗ cap_reached should be true at limit"; fail=1; }
cap_reached 10 && { echo "  ✗ should not cap below limit"; fail=1; } || echo "  ✓ not capped below limit"
grep -q 'cap_reached' "$WRAP" && echo "  ✓ triage loop references cap_reached" || { echo "  ✗ loop doesn't use cap_reached"; fail=1; }

# runner python scripts must use a shim-proof interpreter (bare python3 is hijacked by the modern-python PATH shim)
grep -q 'python3 "\$REPO/scripts/overnight' "$WRAP" && { echo "  ✗ bare python3 for runner scripts (shim-prone)"; fail=1; } || echo "  ✓ runner python scripts use shim-proof interpreter"

# structural ordering: the triage-only early-return precedes EVERY execute/PR/publish action
guard_ln=$(grep -n 'if is_triage_only' "$WRAP" | head -1 | cut -d: -f1)
task_wt_ln=$(grep -n 'b "rh-night/\$tid"' "$WRAP" | head -1 | cut -d: -f1)
publish_ln=$(grep -n 'HEAD:overnight-reports' "$WRAP" | head -1 | cut -d: -f1)
exec_claude_ln=$(grep -n 'execute_task.md' "$WRAP" | tail -1 | cut -d: -f1)
for pair in "task-worktree:$task_wt_ln" "publish:$publish_ln" "execute:$exec_claude_ln"; do
  name="${pair%%:*}"; ln="${pair##*:}"
  if [ -n "$guard_ln" ] && [ -n "$ln" ] && [ "$guard_ln" -lt "$ln" ]; then
    echo "  ✓ triage-only returns before $name (L$guard_ln < L$ln)"
  else
    echo "  ✗ triage-only NOT before $name (guard=$guard_ln $name=$ln)"; fail=1
  fi
done

[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit "$fail"
