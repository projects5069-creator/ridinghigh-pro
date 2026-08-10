#!/usr/bin/env bash
# RidingHigh Pro — Mandatory Skill Activation Hook
# Fires on UserPromptSubmit; injects skill-activation instruction before Claude Code sees the prompt.
# Source: Anthropic official docs (code.claude.com/docs/en/skills) — hooks are the deterministic mechanism.
# Hebrew + tailored to RH skills inventory (verified 2026-05-28).
#
# TASK-54 Phase-2 (2026-07-02): classify task-type from the prompt text and
# record "<type>:<skill>:<transcript-line-offset>" to /tmp/cc-task-type.
# The PreToolUse gate reads it and WARNS (never blocks) when the mapped skill
# was not loaded since this prompt. Classification is fail-open: any error
# leaves state as none:none:0 and the gate skips the check.

# --- Phase-2: read stdin (fail-open on every step) ---
INPUT=$(cat 2>/dev/null) || INPUT=""
PROMPT=""
TRANSCRIPT=""
if [ -n "$INPUT" ] && command -v jq >/dev/null 2>&1; then
  PROMPT=$(printf "%s" "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
  TRANSCRIPT=$(printf "%s" "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
fi

# Offset = transcript length at prompt time; the gate greps only lines AFTER it
# ("loaded since the last prompt", not "ever"). Missing transcript -> 0 (whole file).
OFFSET=0
if [ -n "$TRANSCRIPT" ] && [ -r "$TRANSCRIPT" ]; then
  OFFSET=$(wc -l < "$TRANSCRIPT" 2>/dev/null | tr -d ' ')
fi
case "$OFFSET" in ""|*[!0-9]*) OFFSET=0 ;; esac

# --- Task-type mapping (first match wins; specific types before the RH catch-all).
# Warn-mode makes false positives cheap; false negatives fall through to none.
P=$(printf "%s" "$PROMPT" | tr '[:upper:]' '[:lower:]')
TYPE="none"; SKILL="none"

# TASK-54, 2026-08-09: an explicit declaration beats keyword guessing.
# The planner writes "# REQUIRE-SKILLS: a b c" into the block; the prompt CC
# receives contains that line verbatim. Guessing from prose mis-fired before:
# a prompt merely *naming* backtest-expert in a skills list was classified as
# a backtest task. A declaration removes the guess.
REQ=$(printf "%s" "$PROMPT" | grep -m1 -oE 'REQUIRE-SKILLS:.*' | sed 's/REQUIRE-SKILLS: *//' | tr -s ' ' | sed 's/ *$//')
if [ -n "$REQ" ]; then
  printf "declared:%s:%s\n" "$(printf '%s' "$REQ" | tr ' ' ',')" "$OFFSET" > /tmp/cc-task-type 2>/dev/null
  cat <<INJ

═══ REQUIRED SKILLS (declared by the planner) ═══
$REQ
Load each one before any tool call. If one does not apply, say so and why.
═══════════════════════════════════════════════

INJ
  exit 0
fi
if [ -n "$P" ]; then
  if   printf "%s" "$P" | grep -qE 'ניתוח|(^|[^[:alpha:]])score([^[:alpha:]]|$)|data[ -_]quality'; then
    TYPE="analysis";   SKILL="data-quality-checker"
  elif printf "%s" "$P" | grep -qE 'backtest|בקטסט'; then
    TYPE="backtest";   SKILL="backtest-expert"
  elif printf "%s" "$P" | grep -qE 'position siz|sizing|סייזינג|(^|[^[:alpha:]])risk([^[:alpha:]]|$)|כמה מניות'; then
    TYPE="sizing";     SKILL="position-sizer"
  elif printf "%s" "$P" | grep -qE 'postmortem|whipsaw|פוסטמורטם'; then
    TYPE="postmortem"; SKILL="signal-postmortem"
  elif printf "%s" "$P" | grep -qE '(^|[^[:alpha:]])thesis|תזה'; then
    TYPE="thesis";     SKILL="trader-memory-core"
  elif printf "%s" "$P" | grep -qE '(^|[^[:alpha:]])bug|באג|debug'; then
    TYPE="bug";        SKILL="systematic-debugging"
  elif printf "%s" "$P" | grep -qE 'ridinghigh|riding high|dropslab|רידינגהיי|דרופסלאב|rhpro'; then
    TYPE="rhpro";      SKILL="rhpro-live"
  fi
fi

printf "%s:%s:%s\n" "$TYPE" "$SKILL" "$OFFSET" > /tmp/cc-task-type 2>/dev/null || true

# --- Injection (unchanged, RULE #11 v3.3) ---
cat <<'INJECT_EOF'

═══════════════════════════════════════════════════════════
🛠️ MANDATORY SKILL ACTIVATION — RidingHigh Pro RULE #11 v3.3
═══════════════════════════════════════════════════════════

BEFORE any tool call or implementation, you MUST:

1. SCAN ALL available skills (8 RH-dedicated + superpowers + anthropic) for
   relevance — do NOT default to rhpro-live without examining the rest.

2. (v3.3 — mandatory) State an explicit SCAN line BEFORE the active-skills block:
   "🔍 סריקת סקילים — נטענו: X (כי...). נשקלו ונדחו: Y (לא רלוונטי כי...)."
   • Cover at minimum the 8 dedicated skills by name.
   • Group clearly-irrelevant ones into one phrase (e.g. "נדחו: anthropic docx/pdf/pptx/xlsx — לא מסמכים").
   • TASK-TYPE MAPPING — verify the matching dedicated skill is LOADED, not skipped:
       ניתוח / score / data quality      → data-quality-checker
       backtest / strategy validation     → backtest-expert
       position sizing / risk shares      → position-sizer
       postmortem / win-rate / WHIPSAW    → signal-postmortem
       thesis lifecycle / trading journal → trader-memory-core
       bug / investigation                → systematic-debugging

3. If ANY skill is relevant, state:
   "🛠️ סקילים פעילים:" followed by skill name + 1-line reason for each.
4. Read the relevant SKILL.md file(s) via Read tool (not just mention).
5. ONLY THEN proceed with implementation.

Available RH-specific skills (~/.claude/skills/):
  rhpro-live, rhpro-session, backtest-expert, data-quality-checker,
  position-sizer, signal-postmortem, trader-memory-core, time-check

Available superpowers (~/.claude/plugins/cache/.../superpowers/*/skills/):
  systematic-debugging (any bug/investigation)
  brainstorming (open-ended/new direction)
  writing-plans (multi-step refactor)
  verification-before-completion (before declaring done)
  test-driven-development (new feature with tests)
  using-superpowers (meta-skill)

Available anthropic-skills (~/.claude/skills/anthropic-skills/skills/):
  docx, pdf, pptx, xlsx, frontend-design, skill-creator, mcp-builder

If NO skill applies to the request, state explicitly:
  "🛠️ סקילים: אין סקיל רלוונטי למשימה זו"

END-OF-OUTPUT PROOF (RULE #11 v3.2 — mandatory):
At the END of every response that did real work, write:
   "✅ סקילים שבוצעו:" + for each skill used: name | full SKILL.md path | wc -l
If no skill was used: "✅ סקילים שבוצעו: אין — לא נדרש".
Path+linecount = unfakeable proof. Plugin skills are under
~/.claude/plugins/cache/<mp>/.../skills/<name>/SKILL.md, NOT ~/.claude/skills/.

Failure to declare = RULE #11 v3 violation. Do not silently skip.
═══════════════════════════════════════════════════════════

INJECT_EOF
