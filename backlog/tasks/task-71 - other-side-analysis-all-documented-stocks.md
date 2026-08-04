---
id: TASK-71
title: >-
  ניתוח 'הצד השני' — מכל המניות שתועדו (לא רק 104 שנכנסו): אילו ירדו/עלו הכי
  הרבה ואילו מדדים אפיינו אותן בדיעבד. edge חדש משני הצדדים (שורט+לונג)
status: To Do
assignee: []
created_date: '2026-05-31 02:32'
labels:
  - metric
  - exploration
  - retrospective
  - from-task-62
dependencies: []
ordinal: 71000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-62 סעיף 1: הופך 'האם המדדים שלי עובדים' ל'אילו מדדים היו צריכים להוביל'. P2.
<!-- SECTION:DESCRIPTION:END -->

## ABSORBS TASK-72 AND TASK-75, 2026-08-04

Both closed as merges into this task. Three research questions on one sample, blocked on one thing.

72 asked which collected metrics beat the entry metrics, listing Price_vs_SMA20, Gap, PriceToHigh, Consecutive_Up, DaysSinceIPO and the Score aggregates. 75 is one candidate from that same scan: DaysSinceIPO correlates with MaxDrop at r=+0.261 on n=73 against a threshold of about 0.229, so marginal and single regime.

ALL THREE depend on TASK-74, outcomes for the roughly 946 scanned stocks that were never entered, and TASK-74 has not moved in 65 days.

VALUE NOTE 2026-08-04: the July sample is contaminated beyond repair. 84 positions opened between 15/7 and 29/7 will never close, because the symbol does not resolve at the provider, so no metric to outcome analysis over that window is usable. Whatever this task eventually runs on, it is not July.
