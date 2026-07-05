#!/usr/bin/env bash
# M2b-3c-ii — run_rpi_chain(): one P→C→E→C→V round for a task, each stage via run_stage,
# artifacts → .dancer/. Hermetic: a `claude` stub returns a DIFFERENT result per call
# (ordered by a counter file), so the whole chain runs with no API. Asserts final
# chain_status + that the 5 stage artifacts landed, plus the post-plan bounce early-stop.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
ok()  { echo "  ✓ $1"; }
bad() { echo "  ✗ $1"; fail=1; }

source "$REPO/scripts/overnight/rh-overnight.sh"   # main() does NOT run when sourced

mkdir -p "$TMP/bin"
export STUB_COUNTER="$TMP/counter"
export PATH="$TMP/bin:$PATH"

# --- happy path: 5 stages return planned→pass→executed→pass→ready ---
cat > "$TMP/bin/claude" <<'STUB'
#!/usr/bin/env bash
cat >/dev/null   # drain the prompt
n=$(cat "$STUB_COUNTER" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "$STUB_COUNTER"
case "$n" in
  1) r='{"role":"planner","status":"planned"}' ;;
  2) r='{"role":"critic","verdict":"pass"}' ;;
  3) r='{"role":"executor","status":"executed"}' ;;
  4) r='{"role":"critic","verdict":"pass"}' ;;
  5) r='{"role":"verifier","verdict":"ready"}' ;;
  *) r='{"status":"error"}' ;;
esac
rs=$(printf '%s' "$r" | jq -Rs .)
printf '{"result":%s,"usage":{"input_tokens":1,"output_tokens":1,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}\n' "$rs"
STUB
chmod +x "$TMP/bin/claude"

wt="$TMP/wt"; mkdir -p "$wt"; adir="$wt/.dancer"
echo 0 > "$STUB_COUNTER"
out="$(run_rpi_chain TASK-1 "$wt" /dev/null "$adir")"
status="${out%%$'\t'*}"; tokens="${out##*$'\t'}"

[ "$status" = "ready" ] && ok "full chain → ready" || bad "chain_status wrong: '$status'"
[ "$tokens" = "10" ]    && ok "tokens summed across 5 stages (5×2=10)" || bad "tokens wrong: '$tokens'"
for f in plan_result critique_plan execution critique_exec verify; do
  [ -f "$adir/$f.json" ] && ok "artifact $f.json written" || bad "artifact $f.json MISSING"
done

# --- bounce at post-plan: stage 2 returns bounce → early stop ---
cat > "$TMP/bin/claude" <<'STUB'
#!/usr/bin/env bash
cat >/dev/null
n=$(cat "$STUB_COUNTER" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "$STUB_COUNTER"
case "$n" in
  1) r='{"role":"planner","status":"planned"}' ;;
  2) r='{"role":"critic","verdict":"bounce"}' ;;
  *) r='{"status":"error"}' ;;
esac
rs=$(printf '%s' "$r" | jq -Rs .)
printf '{"result":%s,"usage":{"input_tokens":1,"output_tokens":1,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}\n' "$rs"
STUB
chmod +x "$TMP/bin/claude"

wt2="$TMP/wt2"; mkdir -p "$wt2"; adir2="$wt2/.dancer"
echo 0 > "$STUB_COUNTER"
out2="$(run_rpi_chain TASK-2 "$wt2" /dev/null "$adir2")"
status2="${out2%%$'\t'*}"
[ "$status2" = "bounced_plan" ]        && ok "post-plan bounce → bounced_plan"        || bad "bounce status wrong: '$status2'"
[ ! -f "$adir2/execution.json" ]       && ok "bounce stops before EXECUTE"             || bad "execute ran despite bounce"

if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
