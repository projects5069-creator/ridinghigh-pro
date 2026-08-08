#!/usr/bin/env bash
# RidingHigh Pro — Measurement-Window Guard (PreToolUse, Edit|Write|MultiEdit|NotebookEdit)
#
# Blocks mutation of the two files whose behavior DEFINES the measurement
# window (2026-08-10 → 2026-09-04): order_manager.py, decision_logic.py.
# A change to either inside the window voids the window (July HYP-002 precedent).
# Guard armed from 2026-08-10 (window open) through 2026-09-04 inclusive —
# both bounds inclusive, matching the two date tests below. Corrected 2026-08-08:
# this line previously read 2026-08-08 and contradicted the code.
#
# Design (TASK-53 lesson — a hook once locked ALL Claude Code work):
#   * NARROW: only these two basenames, only mutation tools. Everything else allowed.
#   * FAIL-OPEN on infrastructure errors (no jq / empty stdin / unparseable input):
#     this guard is an extra net on top of human review, not the only lock.
#   * Deterministic deny only when BOTH facts parse cleanly: today inside the
#     window AND target basename matches exactly.
#
# === KILL SWITCHES (style of SKILL_GATE_OFF in pretooluse_skill_gate.sh) ===
# 1. Env  (new sessions):   WINDOW_GUARD_OFF=1
# 2. File (running session): touch ~/RidingHighPro/.claude/hooks/WINDOW_GUARD_OFF
#    (presence of the file disarms; rm it to re-arm)
# 3. Global last resort: "disableAllHooks": true in ~/.claude/settings.json
#    from a NATIVE terminal — see ~/.claude/hooks/RECOVERY.md
# ==========================================================================
# Test-only override: WINDOW_GUARD_DATE=YYYY-MM-DD substitutes "today".

[ "${WINDOW_GUARD_OFF:-0}" = "1" ] && exit 0
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
[ -e "$SELF_DIR/WINDOW_GUARD_OFF" ] && exit 0

INPUT=$(cat 2>/dev/null) || exit 0
[ -z "$INPUT" ] && exit 0
command -v jq >/dev/null 2>&1 || exit 0

TODAY="${WINDOW_GUARD_DATE:-$(date +%F)}"
case "$TODAY" in
  20[0-9][0-9]-[01][0-9]-[0-3][0-9]) : ;;
  *) exit 0 ;;                                  # unparseable date -> fail-open
esac
[ "$TODAY" \< "2026-08-10" ] && exit 0
[ "$TODAY" \> "2026-09-04" ] && exit 0

path=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null)
[ -z "$path" ] && exit 0                        # no path parsed -> fail-open

base=$(basename "$path")
case "$base" in
  order_manager.py|decision_logic.py)
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"WINDOW GUARD: %s is frozen for the measurement window 2026-08-10..2026-09-04 (a change voids the window - July HYP-002 precedent). Emergency release: touch .claude/hooks/WINDOW_GUARD_OFF"}}\n' "$base"
    exit 0
    ;;
esac
exit 0
