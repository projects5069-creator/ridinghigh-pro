---
id: TASK-180
title: >-
  split-halt-artifact-detector — unify TASK-90+148+173, clean DropsLab+RH
  aggregates
status: To Do
assignee: []
created_date: '2026-06-14 19:07'
updated_date: '2026-06-14 22:56'
labels:
  - data-integrity
dependencies: []
priority: high
ordinal: 183000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
reverse-split/halt artifacts poison every aggregate (DropsLab d1 mean +124% vs median 0; CTNT +28567%, RDGT +22400%, PCLA +150%/day; 5.6% DropsLab + ~3% RH rows >100% inter-day). One detector for both systems. PHASE 0 item 1 — blocks all research/178/decision-gates.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 detector flags split/halt rows in both DropsLab and RH
- [ ] #2 aggregates recompute clean (recovery 49.5%→47.2% example)
- [ ] #3 wired to a daily check
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RH-half: AC#1-3 implemented in code (commits 843e4d1 detector / e74b64a collector / 019d8d2 loader-exclude / 61a52b3 health_audit). Remaining: live-verify collector+check_29 (RULE #6); recompute clean aggregates (49.5->47.2); DropsLab-half blocked on TASK-144. Stays open.
<!-- SECTION:NOTES:END -->
