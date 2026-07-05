#!/usr/bin/env bash
# PLAN_ONLY step-1 — run_plan_only(): runs ONLY the PLANNER for a task (read-only DRY),
# writes .dancer/plan.md + plan_result.json, echoes "<status>\t<tokens>". Hermetic: a `claude`
# stub returns the PLANNER's result JSON; no critic/execute/verify, no API.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
ok()  { echo "  ✓ $1"; }
bad() { echo "  ✗ $1"; fail=1; }

source "$REPO/scripts/overnight/rh-overnight.sh"   # main() does NOT run when sourced

mkdir -p "$TMP/bin"
export PATH="$TMP/bin:$PATH"
write_stub() { cat > "$TMP/bin/claude"; chmod +x "$TMP/bin/claude"; }

# --- planned: PLANNER returns status=planned ---
write_stub <<'STUB'
#!/usr/bin/env bash
cat >/dev/null
printf '%s\n' '{"result":"{\"task\":\"TASK-1\",\"role\":\"planner\",\"status\":\"planned\"}","usage":{"input_tokens":1,"output_tokens":1,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}'
STUB

wt="$TMP/wt"; mkdir -p "$wt"; adir="$wt/.dancer"
out="$(run_plan_only TASK-1 "do the thing" "$wt" /dev/null "$adir")"
status="${out%%$'\t'*}"; tokens="${out##*$'\t'}"
[ "$status" = "planned" ]            && ok "planner → planned"           || bad "status wrong: '$status'"
[ "$tokens" = "2" ]                  && ok "tokens summed (1+1=2)"        || bad "tokens wrong: '$tokens'"
[ -f "$adir/plan.md" ]               && ok ".dancer/plan.md written"      || bad "plan.md MISSING"
[ "$(jq -r .mode "$adir/plan_result.json" 2>/dev/null)" = "plan_only" ] && ok "plan_result.json mode=plan_only" || bad "plan_result mode wrong"

# --- blocked: PLANNER returns status=blocked → passed through ---
write_stub <<'STUB'
#!/usr/bin/env bash
cat >/dev/null
printf '%s\n' '{"result":"{\"task\":\"TASK-2\",\"role\":\"planner\",\"status\":\"blocked\",\"reason\":\"missing info\"}","usage":{"input_tokens":1,"output_tokens":1,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}'
STUB
wt2="$TMP/wt2"; mkdir -p "$wt2"; adir2="$wt2/.dancer"
out2="$(run_plan_only TASK-2 "body" "$wt2" /dev/null "$adir2")"
[ "${out2%%$'\t'*}" = "blocked" ]    && ok "planner blocked → blocked"    || bad "blocked status wrong: '${out2%%$'\t'*}'"

if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
