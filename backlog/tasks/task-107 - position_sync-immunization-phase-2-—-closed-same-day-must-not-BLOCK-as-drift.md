---
id: TASK-107
title: position_sync immunization phase-2 — closed-same-day must not BLOCK as drift
status: To Do
assignee: []
created_date: '2026-06-03 19:22'
labels:
  - sentinel
  - robustness
dependencies: []
priority: high
ordinal: 107000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up to TASK-105/106 + the TASK-66 shadow switch. When ALL paper_portfolio rows are DRY_RUN_CLOSED/CLOSED (readable, open_count=0) AND today_enters>0, position_sync currently returns BLOCK POSITION_SYNC_FAILED ('real drift') — a FALSE POSITIVE for positions that legitimately opened and closed the same day. Observed live 2026-06-03 afternoon (9 rows all DRY_RUN_CLOSED → continuous HALT under active mode). The TASK-106 immunization only converts the UNREADABLE case (pf_total_rows>0 AND pf_status_recognized_count==0) to WARN; the closed-same-day case has recognized statuses so it still BLOCKs. Need: treat 'today_enters>0, open=0, but entries accounted for by today's closes (matching PositionID/Ticker with CLOSED status today)' as ALLOW/OK, not drift.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 When today's ENTERs are all accounted for by same-day-closed paper_portfolio rows (readable CLOSED status), position_sync returns ALLOW (not BLOCK).
- [ ] #2 A genuine drift (ENTER with no row at all, or unreadable status) still BLOCKs/handled per TASK-105/106.
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 position_sync distinguishes closed-same-day from real drift; unit test covers: all-closed→ALLOW, genuine-missing→BLOCK, unreadable→WARN (regression). py_compile + test_formulas 107/107 + sentinel_selftest green. PK bump + changelog. branch + PR.
<!-- DOD:END -->
