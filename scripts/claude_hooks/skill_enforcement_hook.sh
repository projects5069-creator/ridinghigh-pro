#!/usr/bin/env bash
# RidingHigh Pro — Mandatory Skill Activation Hook
# Fires on UserPromptSubmit; injects skill-activation instruction before Claude Code sees the prompt.
# Source: Anthropic official docs (code.claude.com/docs/en/skills) — hooks are the deterministic mechanism.
# Hebrew + tailored to RH skills inventory (verified 2026-05-28).

cat <<'INJECT_EOF'

═══════════════════════════════════════════════════════════
🛠️ MANDATORY SKILL ACTIVATION — RidingHigh Pro RULE #11 v3
═══════════════════════════════════════════════════════════

BEFORE any tool call or implementation, you MUST:

1. Check <available_skills> for relevance to the user's request.
2. If ANY skill is relevant, state:
   "🛠️ סקילים פעילים:" followed by skill name + 1-line reason for each.
3. Read the relevant SKILL.md file(s) via Read tool (not just mention).
4. ONLY THEN proceed with implementation.

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
