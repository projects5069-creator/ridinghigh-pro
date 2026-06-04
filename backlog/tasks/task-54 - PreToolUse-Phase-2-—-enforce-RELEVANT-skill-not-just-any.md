---
id: TASK-54
title: 'PreToolUse Phase 2 — enforce RELEVANT skill, not just any'
status: To Do
assignee: []
created_date: '2026-05-29 00:32'
updated_date: '2026-06-04 15:54'
labels: []
dependencies: []
priority: medium
ordinal: 54000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Current Phase-1 gate accepts ANY SKILL.md read (Test 3 loaded time-check for a pwd and passed). Phase 2: map tool_input.command -> relevant skill so the gate requires the CORRECT skill, not merely some skill.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Hook must enforce the RELEVANT skill per task-type (not just 'any SKILL.md loaded'). Current PreToolUse gate is fail-open + accepts any skill (CLAUDE.md RULE #11 v3.1 'KNOWN HOLE'). v3.2 end-of-output proof now gives visibility; this task closes the matching gap. Risk: bad hook can block ALL Claude Code actions (happened in TASK-53 Stage D) — implement carefully with kill-switch.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
4/6: RULE #11 v3.3 hook hardening — added mandatory scan-line + TASK-TYPE mapping (guidance). NOT closing: still fail-open, any SKILL.md passes. Deterministic enforcement (block on wrong skill) still required per AC#1.
<!-- SECTION:NOTES:END -->
