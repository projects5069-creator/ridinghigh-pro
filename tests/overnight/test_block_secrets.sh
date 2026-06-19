#!/usr/bin/env bash
# Task 3 — secret-block PreToolUse hook. Feeds tool-call JSON and asserts deny/allow.
HOOK="$(cd "$(dirname "$0")/../.." && pwd)/.claude/hooks/block_secrets.sh"
fail=0

check_deny() { # $1=json $2=label
  out="$(printf '%s' "$1" | bash "$HOOK")"
  if printf '%s' "$out" | grep -q '"deny"'; then echo "  ✓ deny: $2"
  else echo "  ✗ EXPECTED DENY: $2 -> $out"; fail=1; fi
}
check_allow() { # $1=json $2=label
  out="$(printf '%s' "$1" | bash "$HOOK")"
  if printf '%s' "$out" | grep -q '"deny"'; then echo "  ✗ EXPECTED ALLOW: $2 -> $out"; fail=1
  else echo "  ✓ allow: $2"; fi
}

check_deny  '{"tool_name":"Read","tool_input":{"file_path":".env"}}'                         "Read .env"
check_deny  '{"tool_name":"Read","tool_input":{"file_path":"/Users/x/RidingHighPro/.env.local"}}' "Read .env.local"
check_deny  '{"tool_name":"Read","tool_input":{"file_path":"google_credentials.json"}}'      "Read google_credentials"
check_deny  '{"tool_name":"Bash","tool_input":{"command":"cat oauth_credentials.json"}}'     "Bash cat oauth_credentials"
check_deny  '{"tool_name":"Grep","tool_input":{"pattern":"x","path":".rh_summaries_sheet_id"}}' "Grep _sheet_id"
check_deny  '{"tool_name":"Bash","tool_input":{"command":"cat .streamlit/secrets.toml"}}'    "Bash secrets.toml"
check_deny  'not json at all'                                                                "fail-closed on bad input"

check_deny  '{"tool_name":"Bash","tool_input":{"command":"printenv ALPACA_SECRET_KEY"}}'     "Bash printenv secret"
check_deny  '{"tool_name":"Bash","tool_input":{"command":"env"}}'                            "Bash bare env dump"
check_deny  '{"tool_name":"Read","tool_input":{"file_path":"/Users/x/.aws/credentials"}}'    "Read aws credentials"
check_deny  '{"tool_name":"Read","tool_input":{"file_path":"/Users/x/.ssh/id_rsa"}}'         "Read ssh key"

check_allow '{"tool_name":"Read","tool_input":{"file_path":"utils.py"}}'                     "Read utils.py"
check_allow '{"tool_name":"Read","tool_input":{"file_path":"tests/test_x.py"}}'              "Read test file"
check_allow '{"tool_name":"Bash","tool_input":{"command":"git status"}}'                     "Bash git status"
check_allow '{"tool_name":"Bash","tool_input":{"command":"env PYTHONPATH=. pytest"}}'        "Bash env VAR=x (not a dump)"
check_allow '{"tool_name":"WebFetch","tool_input":{"url":"http://x"}}'                       "non-file tool passes"

[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
