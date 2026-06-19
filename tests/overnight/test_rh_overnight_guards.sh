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

[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
