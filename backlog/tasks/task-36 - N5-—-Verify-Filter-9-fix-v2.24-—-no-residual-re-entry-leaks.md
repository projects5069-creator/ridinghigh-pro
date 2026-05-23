---
id: TASK-36
title: N5 — Verify Filter 9 fix (v2.24) — no residual re-entry leaks
status: Done
assignee: []
created_date: '2026-05-23 22:32'
updated_date: '2026-05-23 22:58'
labels: []
dependencies: []
priority: high
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
PK v2.24 (19/5) fixed Filter 9 re-entry leak (counted from decision_log instead of paper_portfolio). But the fix happened AFTER both leaks already manifested: PIII×14 on 15/5 and HCAI×4 on 18/5. Verify no ticker has >3 ENTERs/day after 2026-05-19. If clean = close as verified. If not clean = real bug, escalate.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Query decision_log: count ENTERs per (date, ticker) for dates >= 2026-05-20
- [ ] #2 Confirm no ticker exceeds 3 ENTERs on any day
- [ ] #3 If any exceed: investigate which other path leaks
<!-- AC:END -->
