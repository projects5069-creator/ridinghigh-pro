---
id: TASK-245
title: 'Scan volume halved starting 2026-07-15, same date as ticker corruption'
status: To Do
assignee: []
created_date: '2026-07-29 09:28'
labels:
  - bug
  - data-integrity
dependencies: []
priority: medium
ordinal: 243000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured live 2026-07-29 from daily_snapshots 2026-07, rows per scan day.

OBSERVED: through 2026-07-14 the daily row count runs 80, 46, 68, 34, 25, 59, 42, 36, 55. From 2026-07-15 onward it runs 23, 14, 12, 20, 38, 20, 18, 14, 22, 28. Median falls from roughly 46 to roughly 20. The break lands on exactly the same scan day as the first confirmed doubled letter tickers.

WHY THIS MATTERS: fewer rows per scan means a smaller candidate universe reaching the gate, which changes how many ENTER opportunities exist per day and therefore any per day rate computed over July. 2026-07-17 is the thinnest day at 12 rows, under half the July median.

TWO COMPETING EXPLANATIONS, NEITHER VERIFIED: (a) same root as the finviz parse change, where a corrupted row fails downstream and is dropped, so the loss is an artifact; (b) a genuine change in market breadth or in what the scanner filter admitted. These have opposite implications and the distinction must be measured, not assumed.

SCOPE: compare row counts against the raw finviz result count per scan if it is recorded anywhere, and check whether any drop or exception path silently discards rows. Blocked in practice on the ticker corruption scope.
<!-- SECTION:DESCRIPTION:END -->
