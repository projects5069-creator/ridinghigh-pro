---
id: TASK-62
title: >-
  ניתוח רחב למיילים: per-trade לפי תאריך + פירוק MxV/ATRX/Gap/Volume נצחונות מול
  הפסדים + פירוק סוכנים + תובנות שיפור (חסום חלקית על n>91)
status: To Do
assignee: []
created_date: '2026-05-30 22:18'
updated_date: '2026-05-30 22:46'
labels: []
dependencies: []
priority: medium
ordinal: 62000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
כלול הבחנת %-edge מול $-edge: net pnl_pct מול net$ (השבוע net%=-1.6% אך net$=+144 → edge אחוזי שטוח/שלילי, הרווח מגודל פוזיציה לא מיתרון). הצג net%/median% ליד ה-$ לשקיפות. AvgWin<AvgLoss = דגל.

הערה (TASK-78, 2026-06-03): טענת 'DropsLab EMPTY' שעלתה כאן ב-30/5 הייתה Sheet ID שגוי (homoglyph I/l, תוקן TASK-77), לא מקור ריק. הגיליון מלא — אומת חי (drops_raw 2851 / drops_post 2156). הניתוח עצמו (%-edge מול $-edge) נשאר רלוונטי.
<!-- SECTION:NOTES:END -->
