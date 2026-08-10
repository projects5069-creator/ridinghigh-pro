---
id: TASK-309
title: >-
  Four doc alignments: TASK-248 title, TASK-128 title+status, WORK_PLAN 259,
  concurrency comment
status: To Do
assignee: []
created_date: '2026-08-10 19:57'
labels: []
dependencies: []
priority: medium
ordinal: 307000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ארבעה מסמכים שסותרים את המצב החי, כל אחד שלח לחקירה מיותרת ב-10/8:
1. כותרת TASK-248: "pins finvizfinance 0.14.6" מול requirements.txt:8 = 1.3.0 (הגוף עדכני; השארית = post_analysis.yml:30 + backfill_ohlc.yml:29).
2. TASK-128: כותרת "shadow mode" + סטטוס In Progress מול config.py:374 EXPLICIT_GATE_MODE="active" מ-29/6 (הגוף מודה, §AUDIT 3/8).
3. WORK_PLAN v1.6 מציג את הכרעת-259 כפתוחה; הוכרעה 9/8 (לא פורסים) - דורש bump 1.7 + changelog.
4. הערת ה-concurrency: תוקנה בעץ-העבודה ב-10/8 מול התיעוד הרשמי, אך README של ה-patch ב-ClaudeWork/decisions עדיין נושא את התיאור ההפוך ("ריצה שממתינה נזרקת") - רשומת-החלטה, דורש אישור עמיחי לתקן.

שער-קבלה: ארבעת המקומות מיושרים, כל אחד עם תאריך ומקור; אימות ב-grep שאף אחד מהניסוחים הישנים לא נותר.
<!-- SECTION:DESCRIPTION:END -->
