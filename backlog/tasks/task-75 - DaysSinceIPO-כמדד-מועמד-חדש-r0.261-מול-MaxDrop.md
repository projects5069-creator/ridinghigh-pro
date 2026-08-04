---
id: TASK-75
title: DaysSinceIPO כמדד מועמד חדש (r=+0.261 מול MaxDrop)
status: Done
assignee: []
created_date: '2026-05-31 03:03'
updated_date: '2026-08-04 00:32'
labels:
  - metric
  - exploration
  - days-since-ipo
  - from-task-62
dependencies: []
ordinal: 75000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
[כותרת מלאה] DaysSinceIPO כמדד מועמד חדש — בסריקה הרחבה (73 מניות, MaxDrop בפועל) DaysSinceIPO r=+0.261: מניות צעירות (IPO טרי) יורדות חזק יותר = שורט טוב יותר. מדד שלא בציון ולא נבדק. לבחון הוספה לסכמת המדדים.

TASK-62 סריקה רחבה 30/5. RELIABLE n=73, עובר מובהקות חלקית (crit≈0.229). מתחבר ל-TASK-72 (מדדים מורחבים — כבר מונה DaysSinceIPO ברשימת הסריקה; זו המשך-אדופציה ספציפי, לא כפילות). רגיים יחיד. P2.
<!-- SECTION:DESCRIPTION:END -->

## MERGED INTO TASK-71, 2026-08-04

Closed as a merge. This is one candidate metric out of the same scan that TASK-71 and TASK-72 cover, and it depends on the same missing outcomes.

The finding itself is carried over: DaysSinceIPO correlates with MaxDrop at r=+0.261 on n=73, against a significance threshold of about 0.229, so it passes marginally and on a single regime. The task itself calls it partial significance. It is a candidate worth testing when the sample supports it, not a result.
