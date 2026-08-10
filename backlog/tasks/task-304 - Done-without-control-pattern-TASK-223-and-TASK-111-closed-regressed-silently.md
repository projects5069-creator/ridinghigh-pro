---
id: TASK-304
title: 'Done-without-control pattern: TASK-223 and TASK-111 closed, regressed silently'
status: To Do
assignee: []
created_date: '2026-08-10 19:57'
labels: []
dependencies: []
priority: medium
ordinal: 302000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
שתי דוגמאות מ-10/8: TASK-223 (DST sweep) נסגר Done ופספס את השער החי ב-orchestrator:114 (ראה תיק ה-DST); TASK-111 (איחוד מראות-הוקים) נסגר Done וב-10/8 נמדדה סטייה של 181 שורות במראה (תוקן: check_hooks_mirror.sh + מקרה 19 ב-selftest).

הדפוס: תיק-תשתית נסגר על "הפעולה בוצעה" בלי בקרה שתיכשל ברגרסיה. תיק כזה מתאר רגע, לא מצב. 219 תיקי Done קיימים; בדגימת 10 האחרונים הראיה יושבת ב-handoff ולא בגוף.

שער-קבלה: כלל כתוב (SESSION_PROTOCOL או WORK_METHOD) - תיק ממחלקת-תשתית אינו נסגר בלי אחת מהשתיים: בקרה אוטומטית שנכשלת ברגרסיה, או סימון מפורש "one-off, ללא בקרה" בגוף. והכלל הוחל רטרואקטיבית על 223 (נפתח-מחדש או תיק-המשך) - כבר קיים תיק ה-DST.
<!-- SECTION:DESCRIPTION:END -->
