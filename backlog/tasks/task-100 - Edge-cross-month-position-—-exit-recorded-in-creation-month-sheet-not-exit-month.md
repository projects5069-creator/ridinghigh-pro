---
id: TASK-100
title: >-
  Edge: cross-month position — exit recorded in creation-month sheet, not
  exit-month
status: Done
assignee: []
created_date: '2026-06-02 17:15'
updated_date: '2026-06-02 19:12'
labels: []
dependencies: []
priority: low
ordinal: 100000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A position entered in month M but exited in month M+1 lives in the paper_portfolio sheet of month M (where it was created), but its ExitDate is in M+1. The monthly summary for M filters ExitDate[:7]==M and will miss it; the summary for M+1 reads sheet M+1 and also misses it. Define canonical rule: which monthly sheet owns a cross-month exit, and how the summary captures it. Low priority (no cross-month exits in May data). Discovered 2026-06-02.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
INVESTIGATED + CLOSED 2026-06-02 (documented / won't-fix-now). Cross-month position edge: a position OPENED in month M writes its row to M's paper_portfolio (order_manager, current-month sheet), and _close_position updates THAT row with an ExitDate in M+1. build_monthly_row filters ExitDate[:7]==month_of, so M's summary skips it (ExitDate!=M) and M+1's summary reads M+1's sheet (row not there) — falls between the chairs. BUT: verified against live data — 2026-05 closed=115 cross-month=0, 2026-06 closed=0. ZERO occurrences. Structurally prevented: the agent EOD-closes positions (EXIT_EOD_CLOSE in position_manager), so entry and exit are always the same day -> same month. The edge cannot occur while there are no overnight holds. Additionally TASK-99's fix already captures it inside a straddling week. Not worth a defensive fix on a non-occurring case. CANONICAL RULE for the future (if overnight holds are ever introduced): the monthly summary must be governed by EXIT month — build_monthly_row should also scan the PREVIOUS month's sheet for rows whose ExitDate falls in month_of. Reopen this task only if overnight holds are enabled.
<!-- SECTION:NOTES:END -->
