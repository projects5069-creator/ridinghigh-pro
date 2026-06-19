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

# over_ceiling: spent >= ceiling
ok over_ceiling 650000 600000
ok over_ceiling 600000 600000
no over_ceiling 100000 600000

# guard_clean_secret_env: scrub secret-family env vars; keep the OAuth token
export SMTP_HOST="smtp.example.com" ALPACA_SECRET_KEY="sk-secret" GOOGLE_CREDENTIALS_JSON="{}" \
       RH_SUMMARIES_SHEET_ID="abc" CLAUDE_CODE_OAUTH_TOKEN="sk-ant-oat-keep"
guard_clean_secret_env || true
if [ -z "${SMTP_HOST:-}" ] && [ -z "${ALPACA_SECRET_KEY:-}" ] && [ -z "${GOOGLE_CREDENTIALS_JSON:-}" ] \
   && [ -z "${RH_SUMMARIES_SHEET_ID:-}" ]; then echo "  ✓ secret env scrubbed"; else echo "  ✗ secret env remained"; fail=1; fi
if [ "${CLAUDE_CODE_OAUTH_TOKEN:-}" = "sk-ant-oat-keep" ]; then echo "  ✓ oauth token preserved"; else echo "  ✗ oauth token lost"; fail=1; fi

[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
