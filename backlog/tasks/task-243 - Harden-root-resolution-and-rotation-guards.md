---
id: TASK-243
title: Harden root resolution and rotation guards
status: To Do
assignee: []
created_date: '2026-07-29 08:57'
labels:
  - bug
  - infra
dependencies: []
priority: medium
ordinal: 241000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up to TASK-242. Interim mitigation already applied: 2026-09 was pre-created via OAuth in the canonical root, so the 1/8 rotation short-circuits on _already_done and never reaches the SA path. That buys one month; it does not fix the loop. Real fixes: (1) _get_root_folder_id resolves ROOT_FOLDER_ID through the shared SA, which has no permission on the canonical root, so the 404 is real and the RidingHigh-Data fallback fires on every SA-only run. Resolve via OAuth instead, or grant the shared SA on the canonical root (security decision, also relocates the backups folder since backup_manager calls the same function). (2) assert_correct_root(ROOT_FOLDER_ID) in prepare_next_month compares a constant to itself and catches nothing. (3) The duplicate-folder guard runs after prepare_next_month itself created the folder, so it fires on its own work and aborts the step that creates the agent tabs. (4) check_28 only inspects the active month, so a missing next month surfaces a month late. (5) Empty orphan folders 2026-07 and 2026-08 remain under RidingHigh-Data; review and remove manually, never automatically. (6) Unify the two SHEET_NAMES lists. sheets_manager.py:38-48 has nine entries and treats live_trades as its own file; prepare_next_month.py:22-31 has eight, omits live_trades, and line 240 aliases it to score_tracker. scripts/fix_august_provisioning_v1.py:305 iterates the nine-entry list, which is how 2026-08 and 2026-09 ended up standalone. Whichever convention wins, one list must be the source and the repair script must check the existing convention before creating anything. Evidence and the per-month state are in TASK-251. Added 2026-08-05 from the stage-1 closure review.
<!-- SECTION:DESCRIPTION:END -->
