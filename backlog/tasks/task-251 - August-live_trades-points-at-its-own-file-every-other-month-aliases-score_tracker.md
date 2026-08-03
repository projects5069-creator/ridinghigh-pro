---
id: TASK-251
title: >-
  August live_trades points at its own file, every other month aliases
  score_tracker
status: To Do
assignee: []
created_date: '2026-08-03 21:01'
labels:
  - data-integrity
  - sheets
dependencies: []
priority: medium
ordinal: 249000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verified 2026-08-03 from sheets_config.json on origin/main and from the code. No task owned this before.

State: for 2026-04, 05, 06, 07 and 09 the live_trades id equals the score_tracker id. For 2026-08 it does not. August points at 1b0Vb..., score_tracker at 1_NC6....

Root cause is a section 10 violation, two lists of the same thing that disagree. sheets_manager.SHEET_NAMES has nine entries and includes live_trades as a file of its own. prepare_next_month.SHEET_NAMES has eight, omits it, carries the comment that live_trades will be a tab inside score_tracker, and line 240 does created_ids['live_trades'] = created_ids['score_tracker']. So the automatic convention is an alias. scripts/fix_august_provisioning_v1.py line 305 iterates sheets_manager.SHEET_NAMES, so the manual repair of 29/7 created a standalone August live_trades file.

Why the repair ran at all: prepare_next_month failed on 1/7 with RuntimeError DUPLICATE MONTH GUARD (TASK-143), two folders named 2026-08 across roots, so it exited before the alias step and August was left half provisioned. See TASK-242 and TASK-243.

Not broken today. The auto_scan log of 2026-08-03 shows live_trades updated: 0 rows, 0 pending with no error, because sheets_manager.get_worksheet falls back to sheet1 when the named tab is absent (line 627). But August is the only month of six with a different physical layout, which is the kind of difference that breaks a cross month research script silently. archive_live_trades also creates live_trades_archive inside whichever file live_trades points at, so August archives would land somewhere else than every other month.

Not verified: whether a tab named live_trades exists inside 1b0Vb, or whether writes are landing on sheet1 through the fallback.

Options, none chosen: leave it and document, or realign August to score_tracker. Realigning is a write to a live month sheet for consistency alone, which is the more dangerous of the two. Either way the two SHEET_NAMES lists must be unified and fix_august_provisioning_v1 needs a guard that checks the existing convention before creating anything. That part belongs with TASK-243.

Related orphan, do not delete: the pre-created September live_trades 1l6j9c... was overwritten by the 1/8 automatic run and is now unreferenced.
<!-- SECTION:DESCRIPTION:END -->
