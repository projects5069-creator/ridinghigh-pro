---
id: TASK-254
title: score_analytics reports n=0 while July closed sixty positions
status: To Do
assignee: []
created_date: '2026-08-03 22:08'
updated_date: '2026-08-05 20:33'
labels:
  - investigation
  - analytics
dependencies: []
priority: low
ordinal: 252000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Noticed 2026-08-03 while auditing which tabs get written.

OBSERVED: the score_analytics tab is empty for both 2026-07 and 2026-08. That is not a missing writer. agent/orchestrator_eod.py lines 170 to 182 runs ScoreAnalytics().run_daily() every evening, and the EOD log of 2026-07-30 printed: Daily analytics: tier=INSUFFICIENT, n=0.

score_analytics.py writes nothing when the tier is INSUFFICIENT, which is defined as fewer than ten trades. So the tab being empty is the documented behaviour of the code.

THE PART THAT IS NOT EXPLAINED: n was zero, not merely below ten. July paper_portfolio held sixty DRY_RUN_CLOSED positions at that point. A sample size of zero against sixty closed trades means the module is either reading a different source, filtering on something that excludes them all, or scoped to a window that contained none of them.

NOT VERIFIED: where run_daily reads its sample from. The source was not traced.

WHY IT IS LOW: nothing downstream consumes score_analytics. config.py line 351 states it is excluded on purpose, frozen and diagnostic, not decision bearing. This is worth understanding rather than worth fixing, and it may turn out that the tab should be retired along with the rest of the Score demotion work in TASK-208 and TASK-209.

Related: pending_suggestions and config_history are also empty in both months and genuinely have no writer anywhere in the code. Both were added in the same commit, 1092a95 feat(phase1-m2) agent sheets setup, as scaffolding that was never wired. dashboard.py line 4307 already documents config_history as having no writer. They are noted here rather than filed separately.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
ANSWERED 2026-08-05 (read-only trace, no code change).

ROOT CAUSE — confirmed, structural:
  orchestrator_eod.py:173  analytics = ScoreAnalytics()      # no arguments
  orchestrator_eod.py:191  analytics = ScoreAnalytics()      # weekly, same
  score_analytics.py:61-75 __init__(postmortem_reader=None, analytics_writer=None,
                                    suggestion_writer=None)
  score_analytics.py:131   if not self._postmortem_reader: return pd.DataFrame()
n=0 is independent of the data. Sixty closed July positions could not have changed it.
No live call site anywhere passes a single callable; only tests do
(tests/agent/unit/test_score_analytics.py:90,138,176).

TWO FACTS THIS TICKET DID NOT HAVE:
1. _analytics_writer is None as well (score_analytics.py:215). Injecting only the reader
   still writes nothing. A working wiring needs reader + writer, and a third for
   pending_suggestions on Saturdays (:226).
2. run_daily filters ExitDate == today exactly (:91 start=end, :143 range filter). Even
   with a correct reader the daily n is only same-day closes, which is < 10 nearly always,
   so tier stays INSUFFICIENT and nothing is written regardless.

WHY NOT WIRE IT: wiring opens two new EOD Sheets write paths (score_analytics daily,
pending_suggestions weekly) to tabs never written, adding quota load in the EOD window, in
order to activate a Score-diagnostic module while TASK-208 and TASK-209 are dismantling
Score. Recommend folding the tab into the 208/209 retirement list rather than repairing it.

pending_suggestions and config_history CONFIRMED writer-less: create_agent_sheets.py
creates the tabs (:45,:46), the dashboard reads them, and _data_loaders.update_suggestion_status
(:179-216) only updates an existing row found by ws.find() — it never creates one.

MEASURED 2026-08-05 — live confirmation of the static trace recorded earlier today.

Source: reports/2026-08-05_1455_measurement.md Q-254. One read per tab, after the close.

  score_analytics        @2026-08: data rows = 0
  score_analytics        @2026-07: data rows = 0
  pending_suggestions    @2026-08: data rows = 0
  config_history         @2026-08: data rows = 0

All three tabs are empty in the live sheets, in both months where applicable. This
matches the code trace in the ANSWERED block above: orchestrator_eod.py:173 and :191
construct ScoreAnalytics() with no arguments, so _postmortem_reader is None and
score_analytics.py:131 returns an empty DataFrame regardless of the data, AND
_analytics_writer is None (score_analytics.py:215) so nothing would be written even if
the sample were non-empty.

Nothing here changes the recommendation already recorded: fold the tab into the Score
retirement work in TASK-208 and TASK-209 rather than wiring the injections.

Stays To Do.
<!-- SECTION:NOTES:END -->
