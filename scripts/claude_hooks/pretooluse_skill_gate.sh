#!/usr/bin/env bash
# RidingHigh Pro — PreToolUse Skill Gate
#   Phase 1 (unchanged): block (exit 2) when NO SKILL.md was ever loaded this session.
#   Phase 2 (TASK-54, 2026-07-02, WARN-MODE): when /tmp/cc-task-type maps this
#   prompt to a specific skill, warn on stderr (exit 0, never block) if that
#   skill was not loaded since the last prompt.
# Fail-OPEN on any error or missing dependency.
#
# === KILL SWITCHES ===
# 1. Env (Phase-1+2, this gate only):  SKILL_GATE_OFF=1
# 2. Global: edit ~/.claude/settings.json top level:
#        "disableAllHooks": true,
#    from a NATIVE terminal (Terminal.app, NOT Claude Code). Full guide:
#        ~/.claude/hooks/RECOVERY.md   (see same directory)
# ====================

[ "${SKILL_GATE_OFF:-0}" = "1" ] && exit 0

# --- Read stdin ---
INPUT=$(cat 2>/dev/null) || exit 0
[ -z "$INPUT" ] && exit 0

# --- Require jq (fail-open if missing — but LOUDLY, 2026-08-10) ---
# A silent fail-open here disables the entire gate with nothing in the output to
# say so. Same failure family as the "tool that looks like it checks and does
# not" lessons of 2026-08-09.
command -v jq >/dev/null 2>&1 || {
  echo "⚠️ skill-gate: jq not found — gate is OPEN (fail-open). Install jq to restore enforcement." >&2
  exit 0
}

# --- Object-level skill-load detection (2026-08-10, TASK-54 follow-up) -------
# The previous greps matched a whole JSONL LINE, so ANY tool_use whose input
# merely CONTAINED the path string satisfied the gate — `wc -l .../SKILL.md`
# passed without loading a thing (measured RED 2026-08-10: harness case
# NEG-print-paths returned exit 0). This parses the tool_use OBJECTS instead.
# A load is exactly one of two things:
#   • a Skill tool call            -> input.skill  (plugin prefix stripped)
#   • a Read of the skill's file   -> input.file_path ending /skills/<n>/SKILL.md
# Printing, echoing or naming the path is not a load.
# ⚠️ TWO serialisations exist and both are real (measured 2026-08-10):
#   nested — a live CC transcript: {"message":{"content":[{"type":"tool_use",...}]}}
#   flat   — headless / overnight: {"type":"tool_use","name":"Skill","input":{...}}
# The first version of this helper handled only the nested form, which broke
# tests/overnight/test_skill_gate_satisfied.sh (measured exit=1). The union
# below cannot double-count: a nested line has .type "assistant"/"user" at the
# top level, so it never satisfies the flat branch, and vice versa.
_skill_events() {   # stdin: transcript jsonl -> stdout: one skill name per real load
  jq -R -r '
    (fromjson? // empty) as $l
    | ( (($l.message.content? // []) | if type=="array" then .[] else empty end), $l )
    | select(.type? == "tool_use")
    | if .name == "Skill" then ((.input.skill // "") | split(":") | last)
      elif .name == "Read" then
        ((.input.file_path // "")
         | if endswith("/SKILL.md") and test("/skills/")
           then (split("/skills/") | last | split("/") | first)
           else empty end)
      else empty end
    | select(. != null and . != "")' 2>/dev/null
}

# --- Allowlist (TASK-54): trivial read-only commands skip ALL checks ---
# One command-prefix per line in skill_gate_allowlist.txt; '#' = comment.
# Matches exact command or "<entry> <anything>". Bash tool only (Edit/Write
# have no .command and fall through to the gate).
ALLOWLIST_FILE="$HOME/.claude/hooks/skill_gate_allowlist.txt"
CMD=$(printf "%s" "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
TOOL=$(printf "%s" "$INPUT" | jq -r '.tool_name // "?"' 2>/dev/null)

# --- Block log (2026-08-10) --------------------------------------------------
# Without a log there is no way to answer "has this gate ever actually fired?" —
# silence and health look identical. Every block writes one line. The log must
# never be able to break the gate, so every step is guarded and it always
# returns 0. Path follows claudework-filing: machine-wide state under _machine/.
# SKILL_GATE_LOGDIR redirects the log — the selftest sets it to a temp dir so
# its 7 synthetic blocks never enter the operational count. Measured 2026-08-10:
# without this the startup-check line read "77 blocks since yesterday" and every
# one of them was the selftest counting itself.
_gate_log() {   # $1 = phase label   $2 = detail
  d="${SKILL_GATE_LOGDIR:-$HOME/ClaudeWork/_machine/skill_gate}"
  mkdir -p "$d" 2>/dev/null || return 0
  c=$(printf '%s' "${CMD:-<no-command>}" | tr '\n' ' ' | cut -c1-120)
  printf '%s | %s | tool=%s | %s | cmd=%s\n' \
    "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$1" "${TOOL:-?}" "$2" "$c" \
    >> "$d/blocks.log" 2>/dev/null
  return 0
}
# 2026-08-10: matching was PREFIX-only, so `echo hi; <anything>` skipped BOTH
# phases for ANY command — measured exit 0 against an empty transcript. An
# allowlisted command must now be a SIMPLE command: no separator, pipe,
# redirect, substitution or newline. Anything else falls through to the gate
# (where it still passes as soon as a real skill is loaded — no lockout).
ALLOW_OK=1
case "$CMD" in
  *";"*|*"&"*|*"|"*|*"<"*|*">"*|*'`'*|*'$('*|*'${'*|*$'\n'*) ALLOW_OK=0 ;;
esac
if [ "$ALLOW_OK" -eq 1 ] && [ -n "$CMD" ] && [ -r "$ALLOWLIST_FILE" ]; then
  CMD_TRIM=$(printf "%s" "$CMD" | sed 's/^[[:space:]]*//')
  while IFS= read -r entry || [ -n "$entry" ]; do
    [ -z "$entry" ] && continue
    case "$entry" in \#*) continue ;; esac
    case "$CMD_TRIM" in
      "$entry"|"$entry "*) exit 0 ;;
    esac
  done < "$ALLOWLIST_FILE"
fi

# --- Extract transcript_path ---
TRANSCRIPT=$(printf "%s" "$INPUT" | jq -r ".transcript_path // empty" 2>/dev/null)
[ -z "$TRANSCRIPT" ] && exit 0
[ ! -r "$TRANSCRIPT" ] && exit 0

# --- Phase 1 (unchanged): count Read(*SKILL.md) + Skill(*) calls, ever ---
# CRITICAL: $() captures stdout (the number). Pipeline exit status is NOT
# propagated to the assignment when set -e is unset (it is unset here).
# We additionally normalize COUNT to a numeric value so non-numeric never
# reaches the arithmetic test.
# 2026-08-10: was a 3-stage LINE grep — a Read of an unrelated file on the same
# JSONL line as a text mention of "SKILL.md" satisfied it, and so did a Read of
# any file called SKILL.md anywhere (e.g. /tmp/SKILL.md). Now object-level.
COUNT=$(_skill_events < "$TRANSCRIPT" | grep -c . 2>/dev/null)
case "$COUNT" in
  ""|*[!0-9]*) COUNT=0 ;;
esac

if [ "$COUNT" -eq 0 ]; then
  cat >&2 <<MSG
🛑 PreToolUse blocked — no SKILL.md loaded in this session yet.
Per RULE #11: Read or Skill-load at least one relevant SKILL.md before
invoking Bash/Edit/Write/NotebookEdit.
Recovery: ~/.claude/hooks/RECOVERY.md  (kill-switch in NATIVE terminal)
MSG
  _gate_log "PHASE1-BLOCK" "reason=no-skill-loaded-this-session"
  exit 2
fi

# --- Phase 2 (TASK-54, WARN-ONLY — always exits 0 from here) ---
# State written by skill_enforcement_hook.sh at UserPromptSubmit:
#   "<type>:<skill>:<offset>"  (offset = transcript line count at prompt time)
# SKILL_GATE_STATE redirects the state path for the RED/GREEN harness only —
# the same test-override pattern as WINDOW_GUARD_DATE and GATE265_WINDOW. It
# cannot weaken Phase-1, and it announces itself on stderr.
STATE_FILE="${SKILL_GATE_STATE:-/tmp/cc-task-type}"
[ -n "${SKILL_GATE_STATE:-}" ] && echo "⚠️ skill-gate: state override active ($STATE_FILE) — TEST MODE" >&2
[ -r "$STATE_FILE" ] || exit 0
STATE=$(head -1 "$STATE_FILE" 2>/dev/null)
[ -z "$STATE" ] && exit 0
TYPE=${STATE%%:*}
REST=${STATE#*:}
SKILL=${REST%%:*}
OFFSET=${REST##*:}
case "$OFFSET" in ""|*[!0-9]*) OFFSET=0 ;; esac
[ -z "$SKILL" ] && exit 0
[ "$SKILL" = "none" ] && exit 0

# --- Turn boundary (2026-08-10, phase 2) -------------------------------------
# The boundary used to be OFFSET = wc -l at UserPromptSubmit time. When that
# hook did not run, OFFSET stayed at an EARLIER prompt and skills loaded in a
# previous turn counted as loaded for this one. The transcript carries a
# per-prompt id: the prompt line, every tool_use of that turn and every tool
# result share one promptId. The FIRST line carrying the newest promptId is
# therefore the start of the current turn.
# ⚠️ Measured 2026-08-10 before this was applied: the LAST line carrying it is a
# tool RESULT, not the prompt. Anchoring on "last" would have counted zero
# skills and locked the session out. Hence: first occurrence.
TURN_START=""
LASTID=$(jq -R -r 'fromjson? // empty | .promptId // empty' "$TRANSCRIPT" 2>/dev/null | tail -1)
if [ -n "$LASTID" ]; then
  TURN_START=$(grep -nF "\"promptId\":\"$LASTID\"" "$TRANSCRIPT" 2>/dev/null | head -1 | cut -d: -f1)
fi
case "$TURN_START" in ""|*[!0-9]*) TURN_START="" ;; esac
if [ -n "$TURN_START" ]; then
  SCAN_FROM="$TURN_START"
else
  SCAN_FROM=$((OFFSET + 1))   # transcript carries no promptId (headless/tests)
fi

# --- Stale-state detector (2026-08-10) ---------------------------------------
# More than one distinct promptId after OFFSET means UserPromptSubmit missed at
# least one prompt, so the declared LIST belongs to an older turn.
# The COUNT is unaffected — SCAN_FROM comes from the transcript, not from the
# offset — so enforcement continues. A stale list can only over-require, which
# is recoverable by loading the named skill; skipping enforcement here would
# re-open exactly the hole this phase closes. Warn loudly and log, do not exit.
if [ -n "$TURN_START" ]; then
  NIDS=$(tail -n +"$((OFFSET + 1))" "$TRANSCRIPT" 2>/dev/null \
         | jq -R -r 'fromjson? // empty | .promptId // empty' 2>/dev/null \
         | sort -u | grep -c . 2>/dev/null)
  case "$NIDS" in ""|*[!0-9]*) NIDS=0 ;; esac
  if [ "$NIDS" -ge 2 ]; then
    echo "⚠️ skill-gate: STALE STATE — /tmp/cc-task-type is from an older prompt ($NIDS prompt ids since its offset). Counting still uses the transcript boundary; the declared LIST may belong to a previous turn." >&2
    _gate_log "STALE-STATE" "distinct_prompt_ids_after_offset=$NIDS state=$STATE"
  fi
fi

# TASK-54, 2026-08-09: SKILL may now be a comma-separated list (type=declared).
# Every declared skill must be loaded; report all that are missing, not just
# the first — a gate that names one of three missing skills teaches a
# one-at-a-time loop instead of the point.
if [ "$TYPE" = "declared" ]; then
  MISSING=""
  # One parse of the tail, then an exact FIXED-STRING match per declared skill.
  # -F closes a second hole: the declared name was interpolated into a regex, so
  # a name like ".*" in the REQUIRE-SKILLS line matched everything.
  LOADED_SET=$(tail -n +"$SCAN_FROM" "$TRANSCRIPT" 2>/dev/null | _skill_events | sort -u)
  OLDIFS=$IFS; IFS=','
  for one in $SKILL; do
    [ -z "$one" ] && continue
    printf '%s\n' "$LOADED_SET" | grep -Fqx -- "${one##*:}" || MISSING="$MISSING $one"
  done
  IFS=$OLDIFS
  [ -z "$MISSING" ] && exit 0
  if [ -f "$HOME/.claude/hooks/.skill_gate_enforce" ]; then
    cat >&2 <<EOM
🛑 skill-gate BLOCKED — declared skills not loaded:$MISSING
A skill counts as loaded ONLY via a Skill tool call, or a Read of its
SKILL.md. Printing, echoing or naming the path does NOT count (2026-08-10).
  → invoke  Skill(skill="<name>")  for each of:$MISSING
    then retry this exact call, unchanged.
If one genuinely does not apply, say so explicitly and load the others.
Turn enforcement off: rm ~/.claude/hooks/.skill_gate_enforce
EOM
    _gate_log "PHASE2-BLOCK" "missing=${MISSING# } turn_start=${TURN_START:-offset+$OFFSET}"
    exit 2
  fi
  echo "⚠️ skill-gate warn: declared skills not loaded:$MISSING" >&2
  _gate_log "PHASE2-WARN" "missing=${MISSING# }"
  exit 0
fi

# Loaded SINCE the last prompt (lines after OFFSET), via Read of the skill's
# SKILL.md (any path: ~/.claude/skills or plugin cache) or a Skill-tool call
# (with or without a plugin prefix like "superpowers:").
LOADED=$(tail -n +"$SCAN_FROM" "$TRANSCRIPT" 2>/dev/null \
         | _skill_events | grep -Fxc -- "${SKILL##*:}" 2>/dev/null)
case "$LOADED" in ""|*[!0-9]*) LOADED=0 ;; esac

if [ "$LOADED" -eq 0 ]; then
  # Enforce mode is a marker FILE, not an env var: an env var set through
  # settings.local.json loads hot but does not clear when the line is removed
  # (observed 2026-08-08). A file can simply be deleted to turn this off.
  if [ -f "$HOME/.claude/hooks/.skill_gate_enforce" ]; then
    cat >&2 <<EOM
🛑 skill-gate BLOCKED (TASK-54 Phase-2, enforce mode)
Task type '${TYPE}' expects skill '${SKILL}', which has not been loaded since
the last prompt. This is a redirect, not a dead end: load that skill and retry.
If it genuinely does not apply, say so explicitly and proceed — the same tool
call succeeds once any relevant skill is loaded for this prompt.
Turn enforcement off: rm ~/.claude/hooks/.skill_gate_enforce
EOM
    _gate_log "PHASE2-BLOCK" "type=$TYPE expected=$SKILL turn_start=${TURN_START:-offset+$OFFSET}"
    exit 2
  fi
  echo "⚠️ skill-gate warn (TASK-54 Phase-2, warn-mode): expected skill '${SKILL}' (task-type: ${TYPE}) — not loaded since the last prompt. Load it or state why it does not apply." >&2
  _gate_log "PHASE2-WARN" "type=$TYPE expected=$SKILL"
fi
exit 0
