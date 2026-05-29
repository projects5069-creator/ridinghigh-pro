---
id: TASK-53
title: PreToolUse skill-gate — hard skill enforcement (DONE)
status: Done
assignee: []
created_date: '2026-05-29 00:32'
labels: []
dependencies: []
ordinal: 53000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Kernel-level PreToolUse hook blocks Bash/Edit/Write/NotebookEdit until a SKILL.md is Read or Skill-loaded in the session. Fixed tool_name->name regex (Stage D caught it). Tested 3/3 live: block / Read-unblock / Skill-unblock. Hook+RECOVERY mirrored to scripts/claude_hooks/. PK v2.46, CLAUDE.md RULE #11 v3.1.
<!-- SECTION:DESCRIPTION:END -->
