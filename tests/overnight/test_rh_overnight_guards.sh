#!/usr/bin/env bash
# Task 8 — wrapper guard functions. Source the wrapper (main() must NOT run on source)
# and exercise the circuit-breaker / auth / night-window guards in isolation.
WRAP="$(cd "$(dirname "$0")/../.." && pwd)/scripts/overnight/rh-overnight.sh"
# shellcheck source=/dev/null
source "$WRAP"
fail=0
ok()   { if "$@"; then echo "  ✓ $*"; else echo "  ✗ expected success: $*"; fail=1; fi; }
no()   { if "$@"; then echo "  ✗ expected failure: $*"; fail=1; else echo "  ✓ (rejects) $*"; fi; }

# guard_no_api_key: passes only when no API key/token in env
( unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN; guard_no_api_key ) \
  && echo "  ✓ guard_no_api_key passes when unset" \
  || { echo "  ✗ guard_no_api_key should pass when unset"; fail=1; }
( export ANTHROPIC_API_KEY=sk-test; guard_no_api_key ) \
  && { echo "  ✗ guard_no_api_key must reject a set API key"; fail=1; } \
  || echo "  ✓ guard_no_api_key rejects a set API key"

# guard_night_window: inside [00:00,05:00) ok; outside rejects
ok guard_night_window "02:10"
ok guard_night_window "00:30"
no guard_night_window "05:00"
no guard_night_window "06:30"
no guard_night_window "23:45"
# fail-closed on garbage / malformed / broken clock (never run by day on a degraded clock)
no guard_night_window "garbage"
no guard_night_window "2:5"
if ( now_lima(){ echo ""; }; guard_night_window ); then echo "  ✗ broken clock should fail-closed"; fail=1; else echo "  ✓ broken clock fails closed"; fi

# over_ceiling: spent >= ceiling
ok over_ceiling 650000 600000
ok over_ceiling 600000 600000
no over_ceiling 100000 600000

# guard_clean_secret_env: scrub secret-family env vars (RH + third-party); keep what we need
export SMTP_HOST="smtp.example.com" ALPACA_SECRET_KEY="sk-secret" GOOGLE_CREDENTIALS_JSON="{}" \
       RH_SUMMARIES_SHEET_ID="abc" AWS_SECRET_ACCESS_KEY="aws" TWILIO_AUTH_TOKEN="tw" \
       SLACK_WEBHOOK="sl" DB_PASSWORD="db" STRIPE_KEY="st" \
       CLAUDE_CODE_OAUTH_TOKEN="sk-ant-oat-keep" GH_TOKEN="gho-keep" GITHUB_TOKEN="ghp-keep"
guard_clean_secret_env || true
if [ -z "${SMTP_HOST:-}" ] && [ -z "${ALPACA_SECRET_KEY:-}" ] && [ -z "${GOOGLE_CREDENTIALS_JSON:-}" ] \
   && [ -z "${RH_SUMMARIES_SHEET_ID:-}" ] && [ -z "${AWS_SECRET_ACCESS_KEY:-}" ] \
   && [ -z "${TWILIO_AUTH_TOKEN:-}" ] && [ -z "${SLACK_WEBHOOK:-}" ] && [ -z "${DB_PASSWORD:-}" ] \
   && [ -z "${STRIPE_KEY:-}" ]; then echo "  ✓ secret env scrubbed (RH + third-party)"; else echo "  ✗ secret env remained"; fail=1; fi
if [ "${CLAUDE_CODE_OAUTH_TOKEN:-}" = "sk-ant-oat-keep" ] && [ "${GH_TOKEN:-}" = "gho-keep" ] \
   && [ "${GITHUB_TOKEN:-}" = "ghp-keep" ]; then echo "  ✓ oauth + gh tokens preserved"; else echo "  ✗ needed token lost"; fail=1; fi

# night_raw_dir: per-night subdir so a prior night's *.json can't leak into a fresh report
RAW_BASE=/tmp/rawbase
[ "$(night_raw_dir 2026-06-19)" = "/tmp/rawbase/2026-06-19" ] && echo "  ✓ per-night raw dir" || { echo "  ✗ per-night raw dir"; fail=1; }
[ "$(night_raw_dir 2026-06-19)" != "$(night_raw_dir 2026-06-18)" ] && echo "  ✓ nights isolated" || { echo "  ✗ nights not isolated"; fail=1; }

# pre-flight base pytest must match CI (--with-requirements) or it false-aborts on missing deps
grep -qE 'with-requirements requirements.txt --with pytest' "$WRAP" \
  && echo "  ✓ pre-flight pytest uses --with-requirements (matches CI)" \
  || { echo "  ✗ pre-flight pytest missing --with-requirements → would false-abort"; fail=1; }

# launchd PATH fix: the WRAPPER must prepend the dirs where the external tools live.
# launchd's minimal PATH is /usr/bin:/bin:/usr/sbin:/sbin — it lacks claude
# (~/.npm-global/bin) and gh (~/bin), which is why the 2026-06-20 run died exit 127.
# Prove the wrapper adds them by starting from launchd's exact PATH in an isolated
# shell, sourcing, then re-reading PATH — so a pass means the WRAPPER did it, not the
# tester's ambient PATH.
WRAPPER_PATH=$(env -i HOME="$HOME" /bin/bash -c \
  'PATH=/usr/bin:/bin:/usr/sbin:/sbin; source "'"$WRAP"'" >/dev/null 2>&1; printf "%s" "$PATH"')
case ":$WRAPPER_PATH:" in *":$HOME/.npm-global/bin:"*) echo "  ✓ wrapper adds claude dir (~/.npm-global/bin) to launchd PATH";; \
  *) echo "  ✗ wrapper does NOT add claude dir to launchd PATH"; fail=1;; esac
case ":$WRAPPER_PATH:" in *":$HOME/bin:"*) echo "  ✓ wrapper adds gh dir (~/bin) to launchd PATH";; \
  *) echo "  ✗ wrapper does NOT add gh dir to launchd PATH"; fail=1;; esac
case ":$WRAPPER_PATH:" in *":/usr/local/bin:"*) echo "  ✓ wrapper adds node dir (/usr/local/bin) to launchd PATH";; \
  *) echo "  ✗ wrapper does NOT add node dir to launchd PATH"; fail=1;; esac

# Smoke check must NOT swallow stderr — a launchd auth/PATH failure has to land in the
# run log (main already tee's fd1+fd2 to it), not /dev/null, or we're blind again.
if grep -E 'output-format json "ok"' "$WRAP" | grep -qE '2>&1|2>\s*/dev/null'; then
  echo "  ✗ smoke check still swallows stderr (2>&1 / 2>/dev/null)"; fail=1
else
  echo "  ✓ smoke check lets stderr reach the run log"
fi

# --- robustness: a single classify failure must FAIL CLOSED, never kill the run ----------
# Repro of the 2026-06-20 exit-1: the unguarded `verdict=$(claude…|jq…)` (rh-overnight.sh
# L155-160) under `set -euo pipefail` died on candidate 52/59 (TASK-174), orphaning the scan
# worktree and skipping the report. The fix = a classify_verdict() helper that FAILS CLOSED
# (auto_safe=false → needs_human, NEVER auto_safe=true) and never propagates the failure, so
# one bad classify in 59 sequential calls can't abort the whole sweep.
mkdir -p /tmp/rh-classify-test-wt; CLASSIFY_ERR=/tmp/rh-classify-test.err; : > "$CLASSIFY_ERR"

# (1) the helper must exist
if declare -F classify_verdict >/dev/null 2>&1; then
  echo "  ✓ classify_verdict() helper defined"
else
  echo "  ✗ classify_verdict() helper missing (robustness fix not applied)"; fail=1
fi

# (2-4) under set -euo pipefail, a failing classify must NOT abort, must fail closed to
#       auto_safe=false, and must let execution continue past the call.
ROB="$(
  set -euo pipefail
  claude() { return 1; }                       # simulate a transient classify failure
  v="$(classify_verdict 'task body' /tmp/rh-classify-test-wt /tmp/none.json "$CLASSIFY_ERR" 2>/dev/null)" \
     || { echo 'PROPAGATED_FAILURE'; v=''; }
  echo 'CONTINUED'
  # NB: read .auto_safe directly — `// empty`/`// false` would collapse a fail-closed `false`
  # to empty (jq treats false as falsy for //), masking the very value we assert.
  echo "AUTO_SAFE=$(printf '%s' "$v" | jq -r '.auto_safe' 2>/dev/null)"
)"
printf '%s\n' "$ROB" | grep -q 'CONTINUED'         && echo "  ✓ failed classify does not kill the run" || { echo "  ✗ failed classify aborted the run (the exit-1 bug)"; fail=1; }
printf '%s\n' "$ROB" | grep -q 'AUTO_SAFE=false'   && echo "  ✓ failed classify → auto_safe=false (FAIL-CLOSED)" || { echo "  ✗ failed classify not fail-closed to auto_safe=false"; fail=1; }
printf '%s\n' "$ROB" | grep -q 'PROPAGATED_FAILURE' && { echo "  ✗ classify_verdict propagated non-zero (would abort the loop under set -e)"; fail=1; } || echo "  ✓ classify_verdict returns clean (no propagation)"

[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
