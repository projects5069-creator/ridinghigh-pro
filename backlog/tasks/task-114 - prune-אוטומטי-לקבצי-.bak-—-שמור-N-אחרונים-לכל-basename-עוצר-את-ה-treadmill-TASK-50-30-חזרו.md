---
id: TASK-114
title: >-
  prune אוטומטי לקבצי .bak — שמור N אחרונים לכל basename, עוצר את ה-treadmill
  (TASK-50/30 חזרו)
status: To Do
assignee: []
created_date: '2026-06-05 23:21'
labels:
  - infra
  - cleanup
  - automation
dependencies: []
priority: medium
ordinal: 114000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מחיקה ידנית של .bak חוזרת אחרי כל ניקוי (TASK-30 Done אך 138 נוצרו מחדש). התיקון: prune אוטומטי ב-.rh-run.sh או commit-hook ששומר N אחרונים לכל basename ומוחק ישנים. repo-scoped, auto-safe, תנאי-סיום מדיד. משימת עומק — לא לרקע.
<!-- SECTION:DESCRIPTION:END -->
