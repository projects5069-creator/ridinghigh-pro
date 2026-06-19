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

[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
