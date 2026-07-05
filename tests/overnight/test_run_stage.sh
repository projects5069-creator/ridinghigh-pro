#!/usr/bin/env bash
# M2b — run_stage(): runs one role prompt in a worktree, extracts its result JSON to
# out_json, and echoes the tokens spent (incl. cache) on stdout. FAIL-CLOSED on any
# claude failure / empty result. Hermetic: stubs `claude` on PATH, sources the runner
# (main() does NOT run when sourced), and asserts out_json content + token math. No API.
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail=0
ok()  { echo "  ✓ $1"; }
bad() { echo "  ✗ $1"; fail=1; }

# Source the runner FIRST (it prepends RH_TOOL_DIRS to PATH at load time); THEN put our
# stub ahead of everything so run_stage resolves the stub, not the real claude.
source "$REPO/scripts/overnight/rh-overnight.sh"

mkdir -p "$TMP/bin"
write_stub() { cat > "$TMP/bin/claude"; chmod +x "$TMP/bin/claude"; }
export PATH="$TMP/bin:$PATH"

prompt="$TMP/prompt.md"; echo "do the thing" > "$prompt"

# --- happy path: result JSON + usage (10+20+5+3 = 38) ---
write_stub <<'STUB'
#!/usr/bin/env bash
cat >/dev/null   # drain stdin (the prompt)
printf '%s\n' '{"result":"{\"task\":\"TASK-1\",\"status\":\"executed\"}","usage":{"input_tokens":10,"output_tokens":20,"cache_read_input_tokens":5,"cache_creation_input_tokens":3}}'
STUB
out="$TMP/out.json"; raw="$TMP/raw.json"
tokens="$(run_stage "$prompt" opus "$TMP" /dev/null "$out" "$raw")"
[ "$tokens" = "38" ]                    && ok "tokens summed (10+20+5+3=38)"      || bad "tokens wrong: got '$tokens'"
grep -q '"status":"executed"' "$out"    && ok "out_json holds the result JSON"    || bad "out_json missing status: $(cat "$out")"
grep -q '"task":"TASK-1"' "$out"        && ok "out_json holds task id"            || bad "out_json missing task id"

# --- fail-closed: empty result → error status + 0 tokens ---
write_stub <<'STUB'
#!/usr/bin/env bash
cat >/dev/null
printf '%s\n' '{"result":"","usage":{}}'
STUB
out2="$TMP/out2.json"; raw2="$TMP/raw2.json"
tokens2="$(run_stage "$prompt" opus "$TMP" /dev/null "$out2" "$raw2")"
[ "$tokens2" = "0" ]                    && ok "fail-closed → 0 tokens"            || bad "fail-closed tokens wrong: '$tokens2'"
grep -q '"status":"error"' "$out2"      && ok "fail-closed → error status in out" || bad "fail-closed status missing: $(cat "$out2")"

if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
