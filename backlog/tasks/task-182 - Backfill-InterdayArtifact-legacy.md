---
id: TASK-182
title: Backfill InterdayArtifact on legacy post_analysis rows
status: To Do
assignee: []
created_date: '2026-06-15 13:17'
updated_date: '2026-06-16 00:17'
labels:
  - data-integrity
dependencies: []
ordinal: 185000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PROGRESS 2026-06-15 19:16: pure backfill_interday_flags DONE+committed (5434861), RED->GREEN 3/3, reuses flag_interday_artifact_chain (no threshold dup), non-destructive, object-dtype fix for string-loaded column. SCOPE refined live: 51 blank rows ALL in RH-2026-06 (was 187 this AM; column now exists since collector EOD run), 51/51 recomputable (all D0-D5 present). REMAINING for Done: (1) write-back main(): load RH-2026-06 -> backfill_interday_flags -> write back; mechanism B-targeted PREFERRED (update only the 51 rows' InterdayArtifact/InterdayArtifactPair cells -- gsheets_sync has NO cell-update helper, only save_post_analysis_to_sheets = union/concat = dup-risk); (2) dry-run; (3) live write post-market; (4) then 180-AC2 recompute (49.5->47.2) becomes demonstrable. Stays To Do until live backfill confirmed.
<!-- SECTION:NOTES:END -->
