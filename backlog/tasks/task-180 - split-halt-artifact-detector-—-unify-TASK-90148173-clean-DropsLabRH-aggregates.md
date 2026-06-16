---
id: TASK-180
title: >-
  split-halt-artifact-detector — unify TASK-90+148+173, clean DropsLab+RH
  aggregates
status: To Do
assignee: []
created_date: '2026-06-14 19:07'
updated_date: '2026-06-16 01:28'
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

live-verify 2026-06-15: AC#3 wiring LIVE-VERIFIED (check_29 runs on live Sheets via health_audit --local, no crash, advisory PASSED). AC#2 recompute(49.5->47.2) + AC#3 detection BLOCKED: 187 live rows are legacy (no InterdayArtifact col); exclude_interday_artifacts is column-based by design -> backfill required first. Backfill opened as TASK-182.

CHILDREN nested 2026-06-15: TASK-90 (DropsLab recovery/pattern_tag recompute), TASK-148 (port d1_pct detector), TASK-173 (unified >100% detector + loader-exclude) = the DropsLab-half, covered by 180-AC#1/#2. RH-half done; DropsLab-half unblocked by TASK-144 (done). Close children together when DropsLab-half lands.
<!-- SECTION:NOTES:END -->
