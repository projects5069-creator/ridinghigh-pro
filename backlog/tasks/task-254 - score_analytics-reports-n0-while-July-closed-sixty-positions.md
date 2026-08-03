---
id: TASK-254
title: score_analytics reports n=0 while July closed sixty positions
status: To Do
assignee: []
created_date: '2026-08-03 22:08'
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
