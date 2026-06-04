---
id: TASK-109
title: enable RECONCILE_AUTO_REPAIR after flag-only proves accurate
status: To Do
assignee: []
created_date: '2026-06-04 00:27'
labels:
  - reconciler
  - activation
dependencies: []
priority: low
ordinal: 109000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Activation-only follow-up to TASK-108 (auto-repair built dormant, flag OFF). Flip config.RECONCILE_AUTO_REPAIR to True. GATE: only after the flag-only reconciler (TASK-106) shows a clean track record over time with ZERO false positives — merging the code is NOT activation. auto-repair WRITES to paper_portfolio, so a false positive would create a wrong row.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 flag-only TASK-106 verified accurate over a meaningful period with zero false positives before flipping the flag
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 RECONCILE_AUTO_REPAIR=True committed; verified live on an EOD run; PK bump + changelog
<!-- DOD:END -->
