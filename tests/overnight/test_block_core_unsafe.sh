#!/usr/bin/env bash
# A2-1 — core-unsafe Edit/Write deny hook (symmetric to block_secrets). Reuses
# core_unsafe.py --anchored. Read of a core file passes (only Edit/Write are gated).
HOOK="$(cd "$(dirname "$0")/../.." && pwd)/.claude/hooks/block_core_unsafe.sh"
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

check_deny  '{"tool_name":"Edit","tool_input":{"file_path":"formulas.py"}}'                          "Edit formulas.py"
check_deny  '{"tool_name":"Write","tool_input":{"file_path":"agent/x.py"}}'                          "Write agent/x.py"
check_deny  '{"tool_name":"Edit","tool_input":{"file_path":"/Users/adilevy/RidingHighPro/config.py"}}' "Edit abs config.py"
check_deny  '{"tool_name":"Edit","tool_input":{"file_path":"../rh-night-T1/providers/finviz.py"}}'   "Edit worktree providers"
check_deny  '{"tool_name":"Write","tool_input":{"file_path":"backfill_ohlc_v2.py"}}'                 "Write backfill_*"
check_deny  'not json at all'                                                                        "fail-closed bad input"

check_allow '{"tool_name":"Edit","tool_input":{"file_path":"scripts/overnight/build_report.py"}}'    "Edit non-core file"
check_allow '{"tool_name":"Write","tool_input":{"file_path":"tests/test_new.py"}}'                   "Write a test file"
check_allow '{"tool_name":"Read","tool_input":{"file_path":"formulas.py"}}'                          "Read core file (not Edit/Write) passes"

[ "$fail" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit $fail
