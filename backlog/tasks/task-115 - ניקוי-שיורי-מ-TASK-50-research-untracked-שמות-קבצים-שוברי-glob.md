---
id: TASK-115
title: 'ניקוי שיורי מ-TASK-50: research/ untracked + שמות-קבצים שוברי-glob'
status: Done
assignee: []
created_date: '2026-06-05 23:34'
updated_date: '2026-06-07 21:23'
labels:
  - cleanup
  - repo
dependencies: []
priority: low
ordinal: 115000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-50 נסגרה על ניקוי .bak בלבד. השארית: research/ לא-עקובות + שמות קבצים עם מקפים/רווחים ששוברים glob. repo-scoped, לא דחוף.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
WONTFIX/PARTIAL (2026-06-07): חצי (1) research/ untracked — כבר פתור אגב TASK-50 (research/.gitignore קיים, working tree נקי, אין מה לנקות). חצי (2) שמות-קבצים שוברי-glob — wontfix: "תיקון" = git mv על קבצי backlog/research, פעולה מסוכנת ששוברת הפניות (ראה homoglyph TASK-77); אי-נוחות glob שולית בלבד, TASK-85 כבר הוסיף guard לשמות >200B. הסיכון > התועלת. נסגר ללא שינוי קוד.
<!-- SECTION:NOTES:END -->
