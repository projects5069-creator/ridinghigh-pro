#!/usr/bin/env bash
# M2b-3c-iii — run_rpi_task(): drives one task through up to MAX_ROUNDS P→C→E→C→V rounds
# with retry / marginal-collapse / PARK semantics (spec §6). Hermetic: a `claude` stub keyed
# by a per-invocation counter + STUB_MODE derives (round, stage) so multi-round loops run
# with no API. Covers happy, retry-then-ready, marginal early-park, exhaust, and blocked.
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

# One stub for all modes: counter → (stage 1..5, round). STUB_MODE picks the stage-5 verdict.
cat > "$TMP/bin/claude" <<'STUB'
#!/usr/bin/env bash
cat >/dev/null
n=$(cat "$STUB_COUNTER" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "$STUB_COUNTER"
stage=$(( (n-1) % 5 + 1 ))
round=$(( (n-1) / 5 + 1 ))
emit() { rs=$(printf '%s' "$1" | jq -Rs .); printf '{"result":%s,"usage":{"input_tokens":1,"output_tokens":1,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}}\n' "$rs"; }
if [ "$STUB_MODE" = "blocked" ] && [ "$stage" = 1 ]; then
  emit '{"role":"planner","status":"blocked","reason":"missing info"}'; exit 0
fi
case "$stage" in
  1) emit '{"role":"planner","status":"planned"}' ;;
  2) emit '{"role":"critic","verdict":"pass"}' ;;
  3) emit '{"role":"executor","status":"executed"}' ;;
  4) emit '{"role":"critic","verdict":"pass"}' ;;
  5)
    case "$STUB_MODE" in
      happy)       emit '{"role":"verifier","verdict":"ready"}' ;;
      retry_ready) [ "$round" = 1 ] && emit '{"role":"verifier","verdict":"reject","reason":"first try"}' || emit '{"role":"verifier","verdict":"ready"}' ;;
      marginal)    emit '{"role":"verifier","verdict":"reject","reason":"same problem"}' ;;
      exhaust)     emit "{\"role\":\"verifier\",\"verdict\":\"reject\",\"reason\":\"r$round\"}" ;;
      *)           emit '{"role":"verifier","verdict":"reject","reason":"default"}' ;;
    esac ;;
esac
STUB
chmod +x "$TMP/bin/claude"

# helper: fresh worktree + reset counter, run one task in a given mode → "status<TAB>tokens"
run_mode() {
  local mode="$1" wtd="$TMP/$2"; mkdir -p "$wtd"
  echo 0 > "$STUB_COUNTER"
  STUB_MODE="$mode" run_rpi_task TASK-9 "$wtd" /dev/null "$wtd/.dancer"
}

# 1) happy → ready in 1 round
out="$(run_mode happy w1)"; st="${out%%$'\t'*}"
[ "$st" = "ready" ] && ok "happy → ready" || bad "happy status: '$st'"
r="$(jq -r .rounds "$TMP/w1/.dancer/task_result.json" 2>/dev/null)"
[ "$r" = "1" ] && ok "happy rounds=1 + task_result.json" || bad "happy rounds: '$r'"

# 2) retry-then-ready → ready in 2 rounds
out="$(run_mode retry_ready w2)"; st="${out%%$'\t'*}"
r="$(jq -r .rounds "$TMP/w2/.dancer/task_result.json" 2>/dev/null)"
[ "$st" = "ready" ] && [ "$r" = "2" ] && ok "retry-then-ready → ready, rounds=2" || bad "retry_ready: status='$st' rounds='$r'"

# 3) marginal: identical reject twice → park BEFORE round 5
out="$(run_mode marginal w3)"; st="${out%%$'\t'*}"
r="$(jq -r .rounds "$TMP/w3/.dancer/parked.json" 2>/dev/null)"
[ "$st" = "parked" ] && ok "marginal → parked" || bad "marginal status: '$st'"
[ "$r" = "2" ] && ok "marginal parks at round 2 (no exhaust)" || bad "marginal rounds: '$r'"
[ -f "$TMP/w3/.dancer/parked.json" ] && ok "marginal wrote parked.json" || bad "marginal parked.json missing"

# 4) exhaust: 5 distinct rejects → parked, rounds=5
out="$(run_mode exhaust w4)"; st="${out%%$'\t'*}"
r="$(jq -r .rounds "$TMP/w4/.dancer/parked.json" 2>/dev/null)"
[ "$st" = "parked" ] && [ "$r" = "5" ] && ok "exhaust → parked, rounds=5" || bad "exhaust: status='$st' rounds='$r'"

# 5) blocked: planner blocks → stop immediately, no retry
out="$(run_mode blocked w5)"; st="${out%%$'\t'*}"
r="$(jq -r .rounds "$TMP/w5/.dancer/task_result.json" 2>/dev/null)"
[ "$st" = "blocked" ] && [ "$r" = "1" ] && ok "blocked → stop at round 1, no retry" || bad "blocked: status='$st' rounds='$r'"

if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
