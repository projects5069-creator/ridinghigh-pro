---
id: TASK-264
title: borrow_coverage contains rows written by unit tests
status: To Do
assignee: []
created_date: '2026-08-06 14:37'
updated_date: '2026-08-06 15:03'
labels:
  - data-integrity
  - tests
  - borrow
  - task-262-followup
dependencies: []
priority: medium
ordinal: 262000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-06 read-only: 144 of 216 rows in 2026-07 and 54 of 74 in 2026-08 carry a CheckTime outside the agent_eod window of 16:00 Peru. The off-hour rows cluster on ScannedUniverse 1 and 3, which are exactly the test fixtures, with WithBorrowData 0 because the broker is a MagicMock. Four rows on 2026-08-06 are traceable to the TASK-262 baseline runs, and nothing was written after the fix landed. Affects the row counts in TASK-261. Nothing deleted or marked.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-08-06, read-only, from the live borrow_coverage tabs. Zero writes were made
by this measurement. Companion to TASK-263, which owns the code defect.

THE WRITER. agent_eod.yml:5 runs `python -m agent.orchestrator_eod` on cron '0 21 * * 1-6'
= 16:00 Peru, Mon-Sat. Legitimate rows should therefore carry a CheckTime near 16:00, and
in practice 16:00-17:10 (the EOD run plus a later self-heal pass).

THE NUMBERS.
  2026-07: 216 rows total. 72 inside 16:00-17:59. 144 OUTSIDE = 67 percent.
  2026-08:  74 rows total. 20 inside 16:00-17:59.  54 OUTSIDE = 73 percent.

THE SIGNATURE. The off-hour rows cluster on ScannedUniverse values of 1 and 3:
  2026-07 off-hour universes: {1: 87, 3: 45, 6: 5, 4: 3, 8: 2, 5: 2}   -> 132 of 144 are 1 or 3
  2026-08 off-hour universes: {1: 15, 3: 9, 5: 15, 7: 8, 4: 7}
The fixtures in tests/agent/unit/test_orchestrator_eod_borrow_wiring_v1.py build states of
exactly 3 tickers (["BBB","AAA","CCC"]) and 1 ticker (["AAA"]). WithBorrowData is 0 on the
1-and-3 rows because the broker in those tests is a MagicMock.

Off-hour rows by date, 2026-07: 07-01 11, 07-02 21, 07-03 6, 07-04 30, 07-05 52,
07-29 15, 07-30 6, 07-31 3.  2026-08: 08-03 23, 08-05 27, 08-06 4.

DIRECT CONFIRMATION. The four 2026-08-06 rows are 09:23:54 (univ 3), 09:23:59 (univ 1),
09:24:10 (univ 1), 09:24:18 (univ 3). Those are the three baseline runs of the TASK-262
build, executed at 09:23-09:25 Lima. The last row in the whole tab is 09:24:18: the
GREEN runs at 09:26-09:28, after the autouse fixture landed, wrote nothing. That is a
direct before/after proof of both the contamination and the fix.

⚠️ NOT ALL OFF-HOUR ROWS ARE TESTS. The 08-05 rows at 19:29-20:11 carry universes of 4, 5
and 7 with WithBorrowData=4 — a real broker answered. Those are more likely other test
files (tests/test_task172_coverage_v1.py also calls collect_borrow_coverage) or manual
runs, not this file's fixtures. The 1-and-3 rows are the confident subset.

WHAT IT MEANS FOR MEASUREMENT. TASK-261 recorded "borrow_coverage measures a universe of
2-5 tickers per day" from the tail of the August tab. Part of that tail is test output, not
measurement. TASK-261's conclusion about get_scanned_universe still stands on its own code
reading, but its ROW COUNTS should be re-derived from the 16:00-17:59 subset only.

NOT DECIDED HERE. Whether to delete the contaminated rows, mark them, or leave them.
Deleting is a write to a live sheet and needs explicit approval and a dated backup first —
the same rule TASK-246 records. Nothing was deleted or marked.

NOT VERIFIED. Which other test files write here. tests/test_task172_coverage_v1.py and
tests/test_task172_names_gap_v1.py both reference collect_borrow_coverage and were not
inspected. That belongs with TASK-250.

CORRECTION 2026-08-06 — a suspicion recorded in this ticket is refuted. NOT a closure.

WHAT THIS TICKET GOT WRONG. The "NOT VERIFIED" paragraph named
tests/test_task172_coverage_v1.py and tests/test_task172_names_gap_v1.py as possible
contamination sources. The first was read in full while working TASK-263:

  tests/test_task172_coverage_v1.py:176   monkeypatch.setattr(sheets_manager, "get_worksheet",
                                            lambda tab,*a,**k: _WS() if tab=="daily_snapshots" else None)
  tests/test_task172_coverage_v1.py:177   monkeypatch.setattr(bc, "collect_borrow_coverage", lambda universe, **k: ...)

Both hops are patched. That file was already isolated and CANNOT have written to the live
tab. The suspicion against it is refuted. test_task172_names_gap_v1.py was still not read.

THE ONE PROVEN WRITER is tests/agent/unit/test_orchestrator_eod_borrow_wiring_v1.py, and
the proof is a matched before/after, not an inference:
  four rows on 2026-08-06 at 09:23:54, 09:23:59, 09:24:10, 09:24:18 with ScannedUniverse
  3, 1, 1, 3 — exactly the fixtures — written during that build's three baseline runs;
  after the fix landed, ~10 further test runs in the same session added nothing, and the
  tab still ends at 09:24:18.
That path is now closed twice over: the autouse fixture (TASK-262) and the injected seams
(TASK-263, commit 9a12942).

WHAT REMAINS OPEN, and it is the substance of this ticket. Of the 198 out-of-window rows,
only 4 are attributed with certainty. The other 194 are not:
  2026-07: 07-01 11 · 07-02 21 · 07-03 6 · 07-04 30 · 07-05 52 · 07-29 15 · 07-30 6 · 07-31 3
  2026-08: 08-03 23 · 08-05 27
The 08-05 rows at 19:29-20:11 carry ScannedUniverse of 4, 5 and 7 with WithBorrowData=4 —
a real broker answered, so those are NOT this file's fixtures. Candidates not yet checked:
test_task172_names_gap_v1.py, manual local runs of orchestrator_eod, and any ad-hoc script.

ALSO STILL OPEN: TASK-261's row counts. It read the tail of the August tab, which contains
test output. Its conclusion about get_scanned_universe rests on code reading and stands;
its NUMBERS should be re-derived from the 16:00-17:59 subset only.

Nothing deleted, nothing marked. That is still an owner decision and a live-sheet write.
<!-- SECTION:NOTES:END -->
