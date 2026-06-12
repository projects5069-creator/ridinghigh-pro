---
id: TASK-168
title: Delisting auto-detector (completes TASK-149 survivorship)
status: To Do
assignee: []
created_date: '2026-06-12 22:55'
labels:
  - vision
dependencies: []
priority: medium
ordinal: 171000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Vision via TASK-156. Auto-detect delisted/NO_DATA tickers and classify: delisting of a short candidate is typically a WIN (price->0), so survivorship loss inflates apparent losses. Completes TASK-149 (19 NO_DATA rows).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Detect NO_DATA/delisted rows automatically
- [ ] #2 Classify delisting outcome (likely short WIN); surface as a known survivorship correction in WR/expectancy
<!-- AC:END -->
