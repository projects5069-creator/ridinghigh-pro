---
id: TASK-205
title: Display D6-D25 forward journey in dashboard
status: To Do
assignee: []
created_date: '2026-06-29 04:15'
updated_date: '2026-06-29 15:21'
labels: []
dependencies: []
ordinal: 211000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Display the already-collected D6-D25 forward data (D{i}_Low + D{i}_Close, scanned >=2026-06-13) in the dashboard. Data is already written by the collector and already flows into _cached_post_analysis() — no collection or schema work needed. Pure display layer: a per-ticker 25-day journey as both a table and a price-path chart. No classification — raw Low/Close documentation only (no High beyond D5, so no symmetric WIN/LOSS).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 New dashboard page/section: each ticker D1-D25 journey in table form (row per ticker, columns D6_Low/D6_Close .. D25_Low/D25_Close)
- [ ] #2 Price-path chart (plotly _go.Figure, mirroring existing overlay) of the Low path across D1-D25 for a selected ticker
- [ ] #3 Rows scanned before 2026-06-13 (no D6-D25) handled gracefully — empty/NA, not errors or fake zeros
- [ ] #4 Zero touch to collector/schema/classify_trade — display layer only, reads existing _cached_post_analysis() columns
<!-- AC:END -->
