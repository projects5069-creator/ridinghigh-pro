---
id: TASK-235
title: >-
  auto-dancer: classify_verdict claude -p gets empty stdin -> 'Input must be
  provided...' -> fail-closed needs_human -> blocks --manual execute
status: To Do
assignee: []
created_date: '2026-07-05 21:07'
updated_date: '2026-07-05 23:17'
labels: []
dependencies: []
ordinal: 239000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ROOT CONFIRMED (2026-07-05 live): non-ASCII char (em-dash) in task body chokes classify_verdict claude -p --json-schema -> empty stdin -> 'Input must be provided' -> fail-closed needs_human -> queue empty -> no execute. Proven: same body with em-dash->hyphen ASCII passed classify (queue:TASK-232 needs_human:0). Fix: sanitize/normalize non-ASCII in classify body before claude -p (or route via redirect-file like run_stage).
<!-- SECTION:DESCRIPTION:END -->
