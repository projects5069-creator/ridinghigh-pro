# Work Log — RidingHigh Pro

> Tracks hours per category per session. Read BEFORE picking next task.
> See docs/WORK_ALLOCATION.md §3 for decision rule.

## How to use

At session start: read current week table, compute M_pct/D_pct/A_pct, apply Rule §3 → next category.
At session end: append a row, update running totals, update "Next required category".

## Week of 2026-05-23 (Mon 18/5 — Sun 24/5)

| Date | Tasks | Category | Hours | Notes |
|---|---|---|---|---|
| 2026-05-23 | Skills infra + backlog seed (D1, D2) | Maintenance | 4.0 | earlier sessions |
| 2026-05-23 | META.1 policy + docs | Meta | 0.5 | excluded from budget |

### Running totals (excluding Meta)

| Category | Hours | % |
|---|---|---|
| Maintenance | 4.0 | 100% |
| Development | 0.0 | 0% |
| Analysis | 0.0 | 0% |
| Total budgeted | 4.0 | 100% |

### Rule §3 evaluation

D_pct = 0% < 20% → Rule §3.1 fires → next task MUST be Development.

### Next required category: Development

## Formula reference

budgeted = maintenance + development + analysis (Meta excluded)
M_pct = maintenance / budgeted
D_pct = development / budgeted
A_pct = analysis / budgeted

Priority (first match wins):
1. D_pct < 20% → Development required
2. A_pct < 10% → Analysis required
3. M_pct > 50% → Development or Analysis required
4. otherwise → free choice

## Week summaries

(none yet — first weekly review: end of week 2026-05-24)
