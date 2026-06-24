---
id: TASK-168
title: Delisting auto-detector (completes TASK-149 survivorship)
status: To Do
assignee: []
created_date: '2026-06-12 22:55'
updated_date: '2026-06-24 18:37'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carry-over from TASK-149 (2026-06-24): audit_flag=NO_DATA fires on rows with valid ScanPrice>0 AND full D1-D5 OHLC, even though validate_stock_data (utils.py:729-730) should return NO_DATA only for price None/0 -> a likely SECOND tagging path. Effect: it excludes valid rows from CLEAN-only research views (score_distribution.py:255, metric_quality_analysis.py:43), shrinking n. Investigate the real NO_DATA trigger when building the auto-detector (149 disproved 'NO_DATA=delisting'; the 19 are transient flags, not lost wins). See docs/research/SURVIVORSHIP_NO_DATA_2026-06-24.md (local).
<!-- SECTION:NOTES:END -->
