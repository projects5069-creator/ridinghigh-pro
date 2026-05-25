---
id: TASK-44
title: AUDIT.9 — Scanner vs Trader split analysis
status: Done
assignee: []
created_date: '2026-05-24 21:50'
labels: []
dependencies: []
updated_date: '2026-05-25 10:05'
priority: medium
ordinal: 44000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
DONE. 4 distinct WR metrics across 4 dashboard pages. Only Home page had a bug (TP10_Hit.mean() counted whipsaws as wins, showed 78%). Fixed to use classify_trade_row → 69%. Other 3 metrics are legitimately different measures. Full analysis in research/2026-05-25_winrate_audit.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Investigation goals:
1. Confirm gap is real (different trade sets) vs measurement artifact
2. Reconcile WR delta — are Trader's extra filters hurting, or is Scanner WR inflated?
3. Decide policy: keep both / merge / deprecate Scanner sim

Acceptance criteria:
- Written analysis in research/2026-05-XX_scanner_vs_trader.md
- Recommendation for which stream to trust + why
- If "deprecate Scanner sim" — separate task for deprecation work

Related: PK §8 (architecture), v2.16 (classify_trade fix), AUDIT.1 (calc_score_v2 removal)
<!-- SECTION:NOTES:END -->
