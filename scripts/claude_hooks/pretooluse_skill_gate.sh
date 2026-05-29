#!/usr/bin/env bash
# RidingHigh Pro — PreToolUse Skill Gate (Phase 1: any SKILL.md read)
# Fail-OPEN on any error or missing dependency.
# Blocks ONLY when transcript is verifiably readable AND contains zero
# Read(*SKILL.md) / Skill(*) entries.
#
# === KILL SWITCH ===
# If this hook locks you out, open a NATIVE terminal (Terminal.app, NOT
# Claude Code) and edit ~/.claude/settings.json to add at the top level:
#     "disableAllHooks": true,
# The file watcher will pick it up automatically. Full guide:
#     ~/.claude/hooks/RECOVERY.md   (see same directory)
# ====================

# --- Read stdin ---
INPUT=$(cat 2>/dev/null) || exit 0
[ -z "$INPUT" ] && exit 0

# --- Require jq (fail-open if missing) ---
command -v jq >/dev/null 2>&1 || exit 0

# --- Extract transcript_path ---
TRANSCRIPT=$(printf "%s" "$INPUT" | jq -r ".transcript_path // empty" 2>/dev/null)
[ -z "$TRANSCRIPT" ] && exit 0
[ ! -r "$TRANSCRIPT" ] && exit 0

# --- Count Read(*SKILL.md) + Skill(*) calls ---
# CRITICAL: $() captures stdout (the number). Pipeline exit status is NOT
# propagated to the assignment when set -e is unset (it is unset here).
# We additionally normalize COUNT to a numeric value so non-numeric never
# reaches the arithmetic test.
COUNT=$(grep -E '"type":"tool_use"' "$TRANSCRIPT" 2>/dev/null \
        | grep -E '"name":"(Read|Skill)"' \
        | grep -cE 'SKILL\.md|"skill":"[^"]+"' 2>/dev/null)
case "$COUNT" in
  ""|*[!0-9]*) COUNT=0 ;;
esac

if [ "$COUNT" -gt 0 ]; then
  exit 0
fi

# --- Verified zero — block ---
cat >&2 <<MSG
🛑 PreToolUse blocked — no SKILL.md loaded in this session yet.
Per RULE #11: Read or Skill-load at least one relevant SKILL.md before
invoking Bash/Edit/Write/NotebookEdit.
Recovery: ~/.claude/hooks/RECOVERY.md  (kill-switch in NATIVE terminal)
MSG
exit 2
