---
id: TASK-271
title: Delete quota_health check per T-206 decision
status: To Do
assignee: []
created_date: '2026-08-08 16:20'
labels: []
dependencies: []
priority: medium
ordinal: 269000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decision 2026-08-08 (docs/DECISIONS_2026-08-08.md): quota_health is structurally unfireable — wrong axis (counts writes while 429s are on reads), wrong scale (<=6 writes/process vs threshold 50), wrong timing (runs before the writes happen; in-process deque empty at check time). Sources: S5_DEEP_v1.md cluster K, S7_TASKS_v1.md T-206, STAGE2_RANKING_v3_delta §2 K-01. Scope: remove the check from check_system; do NOT tune thresholds (rejected). Future alternative if read-quota detection is wanted: wire record_read/get_read_counts (sheets_manager:431-438, exist unwired) to a read threshold. Code change - separate approval before commit.
<!-- SECTION:DESCRIPTION:END -->

## הכרעת עמיחי 2026-08-10 — לא למחוק בלי תחליף
quota_health לא נמחק עד שיהיה במקומו גלאי שמודד את הציר הנכון (קריאות, לא כתיבות).
הנימוק: החנק הוא אירוע חי ולא תיאורטי — ב-10/8 נמדדו 145 שורות שגיאת-מכסה בחמש ריצות
שנדגמו. מחיקה בלי תחליף משאירה אירוע חי בלי גלאי.
⚠️ **תיקון עובדתי לגוף התיק:** הוא כותב ש-record_read/get_read_counts "exist unwired".
נמדד 10/8 שהמונה **כן** מחווט (sheets_manager.py:459) ומודפס בכל ריצה — כלומר התחליף
זול בהרבה ממה שהתיק מתאר, וחלק מהעבודה כבר עשוי.
