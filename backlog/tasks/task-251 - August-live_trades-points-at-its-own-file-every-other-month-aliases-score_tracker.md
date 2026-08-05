---
id: TASK-251
title: >-
  August live_trades points at its own file, every other month aliases
  score_tracker
status: To Do
assignee: []
created_date: '2026-08-03 21:01'
updated_date: '2026-08-05 20:33'
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

## AUDIT NOTE 2026-08-03: THE TAB IS NEVER WRITTEN, IN ANY MONTH

Measured after this task was filed: live_trades holds zero rows in 2026-07 and zero in 2026-08.

The reason is the entry criterion, not the sheet id. auto_scanner.update_live_trades appends a row only when a scanner Score reaches TRADE_ENTRY_MIN_SCORE, which config.py line 106 sets to 70. The highest scanner Score in the live run of 2026-08-03 was 60.86. On top of that, config.py line 341 sets SCORE_WRITE_FROZEN to True under ADR-009 and TASK-127.2, and the whole Score demotion programme, TASK-208, TASK-209 and TASK-174, is retiring the metric this gate depends on.

CONSEQUENCE FOR THIS TASK: the divergence recorded here is real in the config but has no observable effect, because nothing writes to either target. The section 10 problem, two SHEET_NAMES lists that disagree, is still worth fixing and belongs with TASK-243. The August specific question, whether to realign the id, is close to moot and this task may be closable on that basis.

Not verified: whether live_trades was ever written in an earlier month, before the Score freeze.

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
CORRECTION + SCOPE CUT 2026-08-05 (read-only, from sheets_config.json in the repo — no API call).

FACTUAL CORRECTION. The Description says 2026-09 aliases score_tracker. It does not.
  2026-04 1shVEIrA / 1shVEIrA  ALIAS      2026-08 1b0VbCM1 / 1_NC6LOT  STANDALONE
  2026-05 1tQg2Le9 / 1tQg2Le9  ALIAS      2026-09 1l6j9cXz / 1ca4J5tI  STANDALONE
  2026-06 1MQwNUeh / 1MQwNUeh  ALIAS
  2026-07 1_lhYPO6 / 1_lhYPO6  ALIAS
Two months diverge, not one. This was already true when the ticket was written: the last
commit touching sheets_config.json is dd38543 (2026-07-29) and the working tree is identical
to HEAD, so no change occurred between 2026-08-03 and today.

FOLLOWS FROM THAT: the September live_trades id 1l6j9cXz, described here as "overwritten by
the 1/8 automatic run and now unreferenced", is still referenced — it is what
sheets_config.json 2026-09.live_trades points at. Treat it as live config, not as an orphan,
until that is re-verified.

ALSO: the 1/8 rotation did not commit sheets_config.json at all (last commit 2026-07-29),
consistent with TASK-243's note that the pre-created September short-circuits the run on
_already_done. The current layout is the product of the 29/7 manual repair, not of rotation.

SCOPE. The section 10 root — sheets_manager.SHEET_NAMES (9, includes live_trades) vs
prepare_next_month.SHEET_NAMES (8, plus the :240 alias) vs fix_august_provisioning_v1.py:305
iterating the 9-list — moves to TASK-243. Note that TASK-243's five listed fixes do not
currently mention SHEET_NAMES, so this must be ADDED there as item (6), not merely
referenced.

WHAT REMAINS HERE: the owner decision on whether to realign 2026-08 and 2026-09 to the
score_tracker file. That is a write to a live month sheet for consistency alone. Also
remaining: archive_live_trades will place August and September archives in a different file
from every other month.

MEASURED 2026-08-05 — the "Not verified" line in this ticket is now verified.

Source: reports/2026-08-05_1455_measurement.md Q-251. Read-only inspection of the file
structure through gspread; no cell was written.

2026-08: live_trades=1b0VbCM1...  score_tracker=1_NC6LOT...  alias=False
  file title  = 'RH-2026-08-live_trades'
  worksheets  = ['Sheet1']
  'live_trades' tab present = False
  tab 'Sheet1': row_count=1000 col_count=26 non_empty_rows=1

2026-07: live_trades=1_lhYPO6...  score_tracker=1_lhYPO6...  alias=True
  file title  = 'RH-2026-07-score_tracker'
  worksheets  = ['Sheet1', 'live_trades']
  'live_trades' tab present = True
  tab 'Sheet1':      row_count=2619 col_count=26 non_empty_rows=2619
  tab 'live_trades': row_count=1000 col_count=30 non_empty_rows=1

ANSWER TO "Not verified: whether a tab named live_trades exists inside 1b0Vb, or whether
writes are landing on sheet1 through the fallback": there is NO tab named live_trades in
the August file. Sheet1 is the only worksheet. Any write routed to the live_trades tab
lands on Sheet1 through the get_worksheet fallback described in the Description.

A SECOND FACT THE TICKET DID NOT HAVE: July's live_trades tab exists but holds ONE
non-empty row — a header. So live_trades is effectively empty in BOTH months, not just
August. That is consistent with the entry criterion already recorded here (a scanner
Score must reach TRADE_ENTRY_MIN_SCORE = 70, config.py:106, while SCORE_WRITE_FROZEN is
True) rather than with the sheet-id divergence.

Stays To Do. The owner decision — realign 2026-08 and 2026-09 to the score_tracker file,
or leave it and document — is unchanged, and the section 10 root moved to TASK-243 item (6).
<!-- SECTION:NOTES:END -->
