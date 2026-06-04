---
id: TASK-47
title: AUDIT.12 — portfolio sheet deprecation audit
status: Done
assignee: []
created_date: '2026-05-25 10:25'
updated_date: '2026-06-04 16:19'
labels: []
dependencies: []
priority: low
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The portfolio sheet (6 cols: PositionKey, Date, Ticker, Score, BuyPrice, Status) has 65 rows all status=Open with no PnL/Exit columns. Read only twice in dashboard.py (lines 1019 and 2819) — once as fallback in _cached_portfolio (Issue #PORT-MONTH), once in Score Tracker page as a ticker list. Not used by any WR computation. Candidate for deprecation if confirmed dead weight.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Audit 4/6: ALIVE. auto_scanner writes (468/1319) + reads SoT (604/1139 D1-D3); dashboard displays (2819 Score Tracker/1019 fallback); monthly_rotation (57/85). PK 14 line 1301 EXPANDED with purpose (source-of-truth + D1-D3 tracking, not deprecated) to prevent future re-deprecation (task-44 mistake). Deprecation premise WRONG.
<!-- SECTION:NOTES:END -->
