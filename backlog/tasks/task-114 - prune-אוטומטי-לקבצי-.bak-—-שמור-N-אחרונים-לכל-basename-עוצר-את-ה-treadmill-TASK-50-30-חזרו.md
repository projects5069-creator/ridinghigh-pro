---
id: TASK-114
title: >-
  prune אוטומטי לקבצי .bak — שמור N אחרונים לכל basename, עוצר את ה-treadmill
  (TASK-50/30 חזרו)
status: Done
assignee: []
created_date: '2026-06-05 23:21'
updated_date: '2026-06-08 19:38'
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

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
בוצע כריצת-לילה בפיקוח (attended, שלב 2a של TASK-121 דור-שני). נוצר scripts/prune_baks.sh — שומר N=3 .bak אחרונים לכל basename, מוחק ישנים; dry-run כברירת-מחדל (--apply למחיקה), מדלג על git-tracked, תואם bash 3.2 (counter רץ במקום declare -A). אומת: fixture 5 baks→נשמרו 3 חדשים/נמחקו 2 ישנים; dry-run ריפו=0 candidates (≤2 לכל basename). בוצע על branch night/TASK-114 (commit 96d0bff) + Run Log ב-docs/NIGHT_RUN_2026-06-08_TASK114.md → Agent #8 §3.3 verdict Ready, וכלל-5=✅ (קרא stop-counters: goal-met, counters=0) — בניגוד ל-TASK-120 שבו כלל-5 היה 'לא-ודאי'. squash-merged PR #14 → main 7298004. הוכיח end-to-end את חיווט run-log→כלל-5 (AC#2/#3 של TASK-121). הסתייגות: attended ולא auto-mode עיוור (classifier לא-מפוקח נשאר ל-2c של TASK-121).
<!-- SECTION:FINAL_SUMMARY:END -->
