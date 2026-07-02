---
id: TASK-217
title: >-
  Fix paper_portfolio column misalignment (entry-write TPPrice/SLPrice vs
  header)
status: In Progress
assignee: []
created_date: '2026-07-01 21:25'
updated_date: '2026-07-02 04:43'
labels: []
dependencies: []
ordinal: 223000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
REFINED root cause (code is CORRECT): create_agent_sheets.py:87 header DOES define TPPrice/SLPrice, matching order_manager 25-elem row. The LIVE 2026-07 paper_portfolio tab was provisioned with a STALE 23-col header (no TPPrice/SLPrice); order_manager's 25-value append shifted values +2 from CurrentPrice and Sheets auto-extended 2 phantom cols. Result: Status value lands in ExitDate -> reads empty -> 8 rows orphaned from monitor_all Status filter (never TP/SL-closed). SCOPE: ONLY 2026-07 tab affected (2026-05/06 correct: TPPrice/SLPrice present, 0 phantom). HIGH severity: live paper-trading record corrupted. Fix = migrate 2026-07 header to canonical + repair 8 rows + defensive by-name entry-write + prevent recurrence (link TASK-216/91). Related TASK-105.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Core misalign FIXED end-to-end + live-verify (Task1-3 pushed: dd46470/7c6f079/0c441b7). Task4 guard funcs done (ad95806); WIRING = TASK-219. 2026-07 tab migrated (backup research/…231931.json), 8 rows MANUAL_CLEANUP.
<!-- SECTION:NOTES:END -->
