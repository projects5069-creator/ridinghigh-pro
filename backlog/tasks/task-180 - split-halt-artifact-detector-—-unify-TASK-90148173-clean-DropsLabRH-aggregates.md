---
id: TASK-180
title: >-
  split-halt-artifact-detector — unify TASK-90+148+173, clean DropsLab+RH
  aggregates
status: Done
assignee: []
created_date: '2026-06-14 19:07'
updated_date: '2026-06-21 17:58'
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
DropsLab-half proof obtained read-only 2026-06-16 (see TASK-90 notes): -2.3pp recovery cleanup confirmed, n=3627, 152 artifacts. Permanent port + write-back still pending (SSoT decision + post-market).

DONE 2026-06-21: AC#1 detector both systems; AC#2 recompute-clean (RH cross_month_loaders + DropsLab filter); AC#3 daily check — RH health_audit Check 29 + DropsLab report_interday_contamination (commit 50b7e00). gap C closed.
<!-- SECTION:NOTES:END -->
