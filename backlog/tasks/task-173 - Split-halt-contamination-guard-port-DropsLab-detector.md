---
id: TASK-173
title: Split/halt contamination guard (port DropsLab detector)
status: To Do
assignee: []
created_date: '2026-06-13 01:26'
updated_date: '2026-06-14 22:56'
labels:
  - TASK-171
dependencies: []
priority: high
ordinal: 176000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
171-A2 / PT-7. 5.6% of DropsLab post rows and ~3% of RH rows are >100% inter-day artifacts (PCLA +150%, INHD +107%, ENVB, SDOT x3) — reverse-splits/halts polluting outcome stats. Port/build a detector that flags or excludes them. Ties TASK-148/TASK-90.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Detector flags >100% inter-day moves as suspect-artifact in both RH post_analysis and DropsLab
- [ ] #2 Research loaders can exclude flagged rows; contamination % reported
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tracked under parent TASK-180. RH-half done (AC#2 loader exclude + contamination% in code, 019d8d2); DropsLab flagging pending TASK-144.
<!-- SECTION:NOTES:END -->
