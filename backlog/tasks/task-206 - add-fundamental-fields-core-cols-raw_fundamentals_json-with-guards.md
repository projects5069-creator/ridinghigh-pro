---
id: TASK-206
title: add fundamental fields (core cols + raw_fundamentals_json) with guards
status: To Do
assignee: []
created_date: '2026-06-29 04:15'
labels: []
dependencies: []
ordinal: 212000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Maximize per-stock documentation for better hindsight evaluation. yfinance .info is one call already made (free extra fields) but unreliable for nano-caps (floatShares proven garbage in 201). FINVIZ Overview already carries unused fields; FINVIZ Custom view gets a rich subset in one per-scan call. Hybrid: promote core fields to columns + raw_fundamentals_json catch-all.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 core columns: Sector, Industry, P/E, ShortFloat, IPO-age, InstOwn, InsiderOwn, Beta
- [ ] #2 raw_fundamentals_json catch-all column (max documentation without schema bloat)
- [ ] #3 guard + NaN-tolerance + source-tag for every provider field (reuse TASK-203 pattern)
- [ ] #4 one FINVIZ-Custom call per scan (not per-ticker) for reliable ShortFloat/InstOwn
- [ ] #5 schema-union write; zero reader breakage
<!-- AC:END -->
