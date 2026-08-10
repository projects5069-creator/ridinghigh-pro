---
id: TASK-303
title: >-
  Hardcoded market-hours windows: orchestrator gate + 3 more sites - DST
  deadline Nov 1
status: To Do
assignee: []
created_date: '2026-08-10 19:56'
labels: []
dependencies: []
priority: high
ordinal: 301000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
agent/orchestrator.py:114 is_market_hours = "8*60+30 <= minutes < 15*60" (פרו מקובע) והוא שער-הריצה החי (:562 halt OUTSIDE_MARKET_HOURS); :124 is_eod_window = "hour==14 and minute>=55". בחורף (EST, מ-1/11) החלון האמיתי 09:30-16:00 פרו: הסוכן ירוץ שעה לפני הפתיחה ויעצור שעה לפני הסגירה; EOD יירה שעה מוקדם.

עוד מופעים מקובעים שנמצאו בסריקת 10/8 ואינם ב-TASK-223 (שסגור Done): health_check.py:39 · agent/dashboard/live_agent_page.py:95 · agent/execution/position_manager.py:51 (EOD 14:55) · config.py:180-186 (תיעודי).

המימוש הנכון קיים: utils.is_market_hours:160 נגזר מ-America/New_York (a0d63fe). TASK-135 תיקן רק עיוורון-חגים באותה פונקציה.

דדליין: לפני 2026-11-01. מחוץ לחלון-המדידה (נסגר 4/9) - אינו מאיים עליו.

שער-קבלה: אפס חלונות-שעה מקובעים בקוד חי (grep על "8 \* 60|15 \* 60|hour == 14" נקי מלבד תיעוד), והוכחה דו-כיוונית עם תאריך-חורף מוזרק: הסוכן רץ ב-15:30 פרו בחורף ולא רץ ב-08:45 פרו בחורף.
<!-- SECTION:DESCRIPTION:END -->
