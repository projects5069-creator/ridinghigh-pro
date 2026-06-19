#!/usr/bin/env bash
# PreToolUse core-protection hook for the overnight runner — symmetric to
# block_secrets.sh, but for WRITES. Hard-DENIES Edit/Write on any CORE_UNSAFE file
# (formulas/config/utils/Sheets/score/backfill/providers/**/agent/**). Reading core
# files is allowed; only mutation is blocked. Reuses scripts/overnight/core_unsafe.py
# (--anchored, stdlib-only). FAIL-CLOSED on any parse/classifier error.

input="$(cat)"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"          # repo root from .claude/hooks/
CORE="$REPO/scripts/overnight/core_unsafe.py"
# Use the system interpreter directly: it is stdlib-only sufficient for core_unsafe.py
# and bypasses the modern-python PATH shim that would otherwise hijack a bare `python3`.
PYBIN="${RH_PYBIN:-/usr/bin/python3}"

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}
allow() { printf '{}\n'; exit 0; }

tool="$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || echo "__ERR__")"

case "$tool" in
  Edit|Write|MultiEdit|NotebookEdit)
    path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null || echo "__ERR__")"
    [ "$path" = "__ERR__" ] && deny "core-guard: unparseable file_path (fail-closed)"
    [ -z "$path" ] && deny "core-guard: Edit/Write with no file_path (fail-closed)"
    verdict="$("$PYBIN" "$CORE" --anchored "$path" 2>/dev/null | awk 'NR==1{print $1}')"
    [ "$verdict" = "UNSAFE" ] && deny "CORE_UNSAFE file is off-limits to the overnight runner: $path"
    [ "$verdict" = "safe" ] || deny "core-guard: classifier produced no verdict (fail-closed)"
    allow
    ;;
  Bash)
    # Best-effort: deny a Bash command whose tokens reference a CORE_UNSAFE write target.
    # NOT exhaustive (e.g. `git apply`, `uv run` can still write tracked files) — the real
    # backstop is the two-stage review + human merge gate (main is never auto-pushed).
    cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "__ERR__")"
    [ "$cmd" = "__ERR__" ] && deny "core-guard: unparseable command (fail-closed)"
    [ -z "$cmd" ] && allow
    verdict="$("$PYBIN" "$CORE" --scan "$cmd" 2>/dev/null | awk 'NR==1{print $1}')"
    [ "$verdict" = "UNSAFE" ] && deny "Bash command targets a CORE_UNSAFE path (best-effort guard): $cmd"
    [ "$verdict" = "safe" ] || deny "core-guard: scan produced no verdict (fail-closed)"
    allow
    ;;
  __ERR__) deny "core-guard: jq missing or input unparseable (fail-closed)" ;;
  *) allow ;;                                          # Read/Grep/etc. not gated here
esac
