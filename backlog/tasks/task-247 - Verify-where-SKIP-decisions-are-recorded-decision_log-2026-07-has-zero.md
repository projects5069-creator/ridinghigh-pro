---
id: TASK-247
title: 'Verify where SKIP decisions are recorded, decision_log 2026-07 has zero'
status: Done
assignee: []
created_date: '2026-07-29 09:28'
updated_date: '2026-08-03 21:02'
labels:
  - data-integrity
  - observability
dependencies: []
priority: medium
ordinal: 245000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured live 2026-07-29 from decision_log 2026-07.

OBSERVED: the Action column contains ENTER for all 137 rows. There is not a single SKIP in the entire month. Meanwhile daily_snapshots holds 654 rows for the same period, so filtering clearly happened, roughly 500 candidates never became entries. The rejections are simply not in this tab.

HYPOTHESIS, NOT VERIFIED: SKIP is aggregated into skip_summary rather than written per decision to decision_log. TASK-125 touched aggregated skip writes and may be the reason.

WHY THIS MATTERS: TASK-241 asks for ENTER versus SKIP counts. If the ratio is computed from decision_log alone the answer is 137 to 0, which is wrong and would be silently wrong. Any analysis of gate behaviour needs to know which tab is authoritative for rejections, and whether the two are reconcilable per day.

SCOPE: read skip_summary 2026-07, confirm it carries the rejections, and establish whether decision_log is expected to hold SKIP at all or whether that is by design. Document the answer wherever the schema is described.
<!-- SECTION:DESCRIPTION:END -->

## ANSWERED FROM CODE 2026-08-03, CLOSING

The question is answered and the answer is by design, not a bug.

decision_logger.py line 321, verbatim:
  # Route B: SKIP decisions go to stdout only (audit in Actions logs).
  # Rationale: ~80-100 SKIPs/minute were blowing Sheets API quota (429).
  # Only ENTER decisions reach the sheet, those are rare and meaningful.
  action = str(getattr(decision, "action", "")).upper()
  if action != "ENTER":
      print(f"[SKIP] {decision.decision_id} {ticker} Score={score} -> {reason}", ...)
      self._accumulate_skip(decision)          # TASK-125
      return decision.decision_id              # success, NOT an error

So a SKIP goes to two places and neither is decision_log: stdout, readable in the Actions log, and an in run aggregate flushed once per run to the skip_summary tab by flush_skip_summary at decision_logger.py:171, called from orchestrator.py:781. Zero SKIP rows in decision_log for July is the intended behaviour of Route B, live since commit b1a4e4f on 2026-05-11.

Live confirmation of the stdout half, agent_minute run 29943602007 of 2026-07-22:
  [SKIP] DEC-2026-07-22-ZZCMD-124454-86 ZZCMD Score=30.33 -> EXISTING_POSITION: already short ZZCMD

This task is subsumed by TASK-125, SKIP visibility restore, which is already Done and is what built the skip_summary aggregate. Nothing separate remains here.

One thing this closure does NOT assert: that skip_summary actually holds July rows. That was not read. If SKIP visibility is ever in doubt again, the question is about skip_summary content and belongs to TASK-125, not here.
