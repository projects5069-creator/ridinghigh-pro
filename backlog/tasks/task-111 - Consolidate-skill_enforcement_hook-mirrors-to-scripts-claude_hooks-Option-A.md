---
id: TASK-111
title: Consolidate skill_enforcement_hook mirrors to scripts/claude_hooks (Option A)
status: Done
assignee: []
created_date: '2026-06-04 17:01'
updated_date: '2026-06-04 17:01'
labels: []
dependencies: []
priority: low
ordinal: 111000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
3 drifted copies of the skill-enforcement hook unified to ONE canonical git mirror: scripts/claude_hooks/ (full bundle skill_enforcement_hook.sh + pretooluse_skill_gate.sh + RECOVERY.md, mirrors live ~/.claude/hooks/). Done in-session 2026-06-04: (1) synced claude_hooks/skill_enforcement_hook.sh to v3.3; (2) git rm redundant loose scripts/skill_enforcement_hook.sh; (3) unified PK 316 with 291 (two conflicting canonical claims); (4) install.sh now deploys scripts/claude_hooks/ to ~/.claude/hooks/. LIVE hook unchanged.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done in-session 2026-06-04. All 4 Option-A steps executed: sync v3.3, rm loose dup, unify PK 316/291, install.sh deploy block. Verified: install.sh bash -n OK, PK 2.80, single canonical mirror scripts/claude_hooks/. LIVE ~/.claude/hooks unchanged (settings.json still points there).
<!-- SECTION:NOTES:END -->
