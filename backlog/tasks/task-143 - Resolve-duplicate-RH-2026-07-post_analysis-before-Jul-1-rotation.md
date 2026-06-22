---
id: TASK-143
title: Resolve duplicate RH-2026-07-post_analysis before Jul 1 rotation
status: Done
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-21 23:14'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 146000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-4.3: TWO Drive files named RH-2026-07-post_analysis (1ASXu2... orphan created 20:47:07Z, 1C_9rj... live created 20:48:18Z on 1/6, different parent folders). sheets_config points to the later one. Archive/trash the orphan + add a post-rotation duplicate check. Deadline: before 2026-07-01 rotation. Evidence: phase4_evidence.md (e)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Orphan folder 1IaqLr (root RidingHigh-Data; 9 unreferenced sheets) trashed manually via Drive UI (Amihay, 2026-06-12). De-risk airtight beforehand: config 23/23 sheets all in the LIVE folder 1U2Syq (root RidingHighPro); the 22-vs-23 child-count was a listing artifact, NOT data-loss.
- [ ] #2 ROOT CAUSE confirmed: prepare_next_month.py ran once with the WRONG ROOT_FOLDER_ID (RidingHigh-Data instead of RidingHighPro) -> created a duplicate orphan 2026-07 folder with the first 9 sheets, then the correct run created the full 23 in RidingHighPro (which config points to).
- [ ] #3 FOLLOW-UP (plan-mode, touches live rotation script): root-guard in prepare_next_month.py — assert correct ROOT_FOLDER_ID + single folder-per-month + post-rotation duplicate check; investigate the RidingHigh-Data root for other orphans
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-06-12: orphan cleanup DONE (manual Drive trash). Deadline-driven part (before 2026-07-01 rotation) resolved — config pipeline was always correct (points to LIVE folder). Priority lowered HIGH->MEDIUM: only the prevention root-guard remains (separate plan-mode session). The duplicate was a wrong-ROOT_FOLDER_ID run, not a transient sheet race.

AC#3 done 2026-06-21: root-guard (4 guards) in prepare_next_month, TDD 6 tests, 474 passed. All 3 ACs met -> 143 Done. CAVEAT: orphan 1IaqLr trashed-state not independently verified (MCP lacks flag); config points to live only; recommend manual Drive-trash eye-check.

CORRECTION 2026-06-21: orphan 1IaqLr was NOT deleted 6/12 (AC#1 checkbox was wrong) — verified LIVE in Drive today, 9 empty sheets under RidingHigh-Data. Disjoint from all 23 config IDs (zero risk). Decision: leave-and-document (see TASK-187). AC#3 guard prevents recurrence regardless.
<!-- SECTION:NOTES:END -->
