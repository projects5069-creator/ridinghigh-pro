---
id: TASK-247
title: 'Verify where SKIP decisions are recorded, decision_log 2026-07 has zero'
status: To Do
assignee: []
created_date: '2026-07-29 09:28'
labels:
  - data-integrity
  - observability
dependencies: []
priority: medium
ordinal: 245000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured live 2026-07-29 from decision_log 2026-07.

OBSERVED: the Action column contains ENTER for all 137 rows. There is not a single SKIP in the entire month. Meanwhile daily_snapshots holds 654 rows for the same period, so filtering clearly happened, roughly 500 candidates never became entries. The rejections are simply not in this tab.

HYPOTHESIS, NOT VERIFIED: SKIP is aggregated into skip_summary rather than written per decision to decision_log. TASK-125 touched aggregated skip writes and may be the reason.

WHY THIS MATTERS: TASK-241 asks for ENTER versus SKIP counts. If the ratio is computed from decision_log alone the answer is 137 to 0, which is wrong and would be silently wrong. Any analysis of gate behaviour needs to know which tab is authoritative for rejections, and whether the two are reconcilable per day.

SCOPE: read skip_summary 2026-07, confirm it carries the rejections, and establish whether decision_log is expected to hold SKIP at all or whether that is by design. Document the answer wherever the schema is described.
<!-- SECTION:DESCRIPTION:END -->
