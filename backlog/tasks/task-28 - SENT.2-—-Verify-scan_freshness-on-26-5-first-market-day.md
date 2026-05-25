---
id: TASK-28
title: SENT.2 — Verify scan_freshness on 26-5 first market day
status: To Do
assignee: []
created_date: '2026-05-24 19:25'
labels: []
dependencies: []
priority: high
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
First market day after the lex-compare bug fix (commits 5cc658b + 2ef7ceb). Verify scan_freshness BLOCK rate is below 5% on 2026-05-26 (Tuesday, post-Memorial Day).
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Acceptance criteria:
1. Pull system_events for 2026-05-26 end-of-day.
2. Count BLOCK events. Compare to total signals processed.
3. If BLOCK rate < 5% then fix confirmed, mark Done.
4. If BLOCK rate > 5% then drill into specific BLOCKs and re-investigate.

Reference: SENT.1 investigation 2026-05-24 (PK v2.32). Root cause of 21-22/5 explosion was lex-compare bug, now fixed in commits 5cc658b + 2ef7ceb.
<!-- SECTION:NOTES:END -->
