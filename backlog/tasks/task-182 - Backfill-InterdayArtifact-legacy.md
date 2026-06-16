---
id: TASK-182
title: Backfill InterdayArtifact on legacy post_analysis rows
status: To Do
assignee: []
created_date: '2026-06-15 13:17'
updated_date: '2026-06-16 00:24'
labels:
  - data-integrity
dependencies: []
ordinal: 185000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
PROGRESS 2026-06-15 19:16: pure backfill_interday_flags DONE+committed (5434861), RED->GREEN 3/3, reuses flag_interday_artifact_chain (no threshold dup), non-destructive, object-dtype fix for string-loaded column. SCOPE refined live: 51 blank rows ALL in RH-2026-06 (was 187 this AM; column now exists since collector EOD run), 51/51 recomputable (all D0-D5 present). REMAINING for Done: (1) write-back main(): load RH-2026-06 -> backfill_interday_flags -> write back; mechanism B-targeted PREFERRED (update only the 51 rows' InterdayArtifact/InterdayArtifactPair cells -- gsheets_sync has NO cell-update helper, only save_post_analysis_to_sheets = union/concat = dup-risk); (2) dry-run; (3) live write post-market; (4) then 180-AC2 recompute (49.5->47.2) becomes demonstrable. Stays To Do until live backfill confirmed.

DRY-RUN FINDINGS 2026-06-15 19:23 (SCOPE WRONG, redesign needed): InterdayArtifact value_counts = NaN:128, '':51, 0.0:13, 1.0:1 (NO True/False strings). Loader does NOT coerce (InterdayArtifact absent from POST_ANALYSIS_NUMERIC_COLS) -> values reflect Sheet, write-back safe from coercion. BUT real scope = 179 over 3 months, NOT 51 in June: (a) 128 NaN = Apr+May rows where the COLUMN DOES NOT EXIST (added 6/14) -> backfilling them needs column-ADD to old month sheets (TASK-150 territory); (b) 51 '' = June pre-6/14 blanks (simple fill); (c) 14 rows = new collector writes flag as NUMERIC 0.0/1.0 NOT True/False -> format-inconsistency, possible collector-repr bug to investigate. DECISIONS before write: scope June-only(51) vs all-months(179+column-add); normalize the 14 numeric; why collector writes 0.0/1.0. Detector found 8 real artifacts on dry-run (TDIC/PCLA/ASTC/ENVB/AIIO/SDOTx3) - correct. Pure fn committed 5434861. Stays To Do - needs redesign, NOT a simple 51-row write.
<!-- SECTION:NOTES:END -->
