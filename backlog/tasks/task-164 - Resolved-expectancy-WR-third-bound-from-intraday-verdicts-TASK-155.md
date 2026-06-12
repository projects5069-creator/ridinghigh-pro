---
id: TASK-164
title: Resolved expectancy/WR third-bound from intraday verdicts (TASK-155)
status: In Progress
assignee: []
created_date: '2026-06-12 18:27'
updated_date: '2026-06-12 20:19'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 167000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Deferred from TASK-162 (AC #6). TASK-155 resolved the 26 WHIPSAW on minute bars (8 WIN/17 LOSS/1 UNRESOLVED) but the per-row verdicts live in a gitignored research CSV, not in deploy. To show a RESOLVED third bound (between optimistic and pessimistic) on the live WR + expectancy surfaces, the verdicts need a persistence mechanism (e.g. a post_analysis column or a small committed verdicts file) so the dashboard can fold them in live. Resolver=utils.resolve_whipsaw, cache=intraday_cache already exist.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Persist the per-row WHIPSAW intraday verdicts (WIN/LOSS/UNRESOLVED) somewhere deploy-visible
- [ ] #2 Add a RESOLVED third bound to the headline WR and the expectancy surface (between optimistic and pessimistic)
- [ ] #3 UNRESOLVED rows (e.g. XNDU) stay excluded from the resolved bound
<!-- AC:END -->
