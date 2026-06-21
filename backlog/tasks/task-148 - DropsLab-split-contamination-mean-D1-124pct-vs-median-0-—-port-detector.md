---
id: TASK-148
title: DropsLab split contamination (mean D1 +124pct vs median 0) — port detector
status: Done
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-21 14:20'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 151000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV DL-7.2: drops_post d1_pct mean +124pct vs median 0.00 — unflagged reverse-split artifacts poison all D-day metrics. Port the same D-day-jump detector planned for RidingHigh (ties TASK-90). Evidence: phase7_evidence.md
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tracked under parent TASK-180. RH-half done in code; DropsLab d1_pct detector pending TASK-144.

PARENT: TASK-180 (DropsLab-half of the split/halt detector; tracked under 180-AC#1 detector-both-systems / AC#2 recompute-clean). RH-half done; DropsLab-half unblocked by TASK-144. Close together when DropsLab-half lands.
<!-- SECTION:NOTES:END -->
