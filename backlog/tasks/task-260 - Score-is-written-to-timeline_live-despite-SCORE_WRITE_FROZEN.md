---
id: TASK-260
title: Score is written to timeline_live despite SCORE_WRITE_FROZEN
status: To Do
assignee: []
created_date: '2026-08-05 20:34'
updated_date: '2026-08-05 20:35'
labels:
  - data-integrity
  - score
  - adr-009
  - measured
dependencies: []
priority: medium
ordinal: 258000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-05: timeline_live 2026-08 holds 5,903 distinct numeric Score values and zero blank cells across 71,397 rows, while SCORE_WRITE_FROZEN=True (config.py:341). The freeze is applied per write-site via score_write_value (auto_scanner.py:50-54) at six call sites, but the timeline_live write at :441-448 builds rows straight from results_df and is not one of them. The scoreless era does not cover the highest-volume tab. Touches ADR-009 and the TASK-208/209 cluster.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-08-05. Source: reports/2026-08-05_1455_measurement.md Q-240.

THE MEASUREMENT
timeline_live 2026-08, live read after the close:
  rows                  = 71,397 (71,556 on a second read minutes later)
  Score blank cells     = 0  (0.00 percent)
  distinct Score values = 5,903
  most common           = ('0', 1051), ('0.01', 587), ('1.52', 318), ('0.9', 312),
                          ('3.08', 305), ('3.81', 304), ('10.91', 280), ('46.2', 232)
  config.py:341 SCORE_WRITE_FROZEN = True

Every row carries a numeric Score. Not one cell is blank.

WHY THE OTHER TABS ARE BLANK AND THIS ONE IS NOT — verified in code 2026-08-05:
  auto_scanner.py:50-54   score_write_value(v) returns "" when SCORE_WRITE_FROZEN
  auto_scanner.py:57-64   apply_snapshot_score_freeze(df) blanks the Score COLUMN on a copy
  six call sites apply the freeze: :518, :597, :954, :1123, :1261, :1370
  auto_scanner.py:441-448 timeline_live is built directly from results_df:
      new_rows = results_df.reindex(columns=data_cols)
      ... new_rows = new_rows[slim_cols]
    No score_write_value and no apply_snapshot_score_freeze on this path.

So the freeze is applied per write-site rather than centrally, and the highest-volume tab
in the system is not one of the sites. The "forward-only scoreless-data era" described in
config.py:341 and ADR-009 does not hold for timeline_live.

WHAT THIS TOUCHES
  - ADR-009 and the scoreless-era claim in the PK.
  - TASK-208 and TASK-209, which are dismantling Score. Any statement that Score is no
    longer being persisted needs qualifying: it is still persisted, 71k rows per month.
  - Anyone reading timeline_live for research will find a populated Score column and may
    reasonably assume it is current and meaningful.

CORRECTION TO THE LINE NUMBERS AS FIRST DRAFTED: the freeze helpers are at
auto_scanner.py:50-54 and :57-64 (not :50-64 as a single block), and the timeline_live
write is at :441-448 (not :445-448). Verified by reading the file.

NOT ESTABLISHED: whether this is deliberate (timeline_live kept as the raw research
record) or an omission. Nothing in the code comments at :441-448 says either way.
No fix proposed here.
<!-- SECTION:NOTES:END -->
