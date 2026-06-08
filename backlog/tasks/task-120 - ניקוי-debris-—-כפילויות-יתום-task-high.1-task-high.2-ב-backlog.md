---
id: TASK-120
title: ניקוי debris — כפילויות-יתום task-high.1 / task-high.2 ב-backlog
status: Done
assignee: []
created_date: '2026-06-08 17:53'
updated_date: '2026-06-08 18:30'
labels:
  - backlog
  - hygiene
  - cleanup
dependencies: []
priority: low
ordinal: 123000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
תצפית מ-2026-06-08: זוהו כפילויות-יתום בשמות task-high.1 / task-high.2 ב-backlog/tasks (debris). לבדוק ולנקות. רישום בלבד — טרם נחקר; לא לאמת/למחוק במסגרת סגירת-היום, רק תועד.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
בוצע כמבחן-בפיקוח של חיבור דור-שני (TASK-94 → ריצת-לילה). 2 יתומי-debris נמחקו: backlog/archive/tasks/task-high.1 + task-high.2 — כפילויות SENT.3 עם id שבור (TASK-HIGH.1/.2, parent TASK-HIGH לא-קיים) מ-glitch של כלי-backlog 29/5; ה-SENT.3 הקנוני=TASK-57 קיים בנפרד. בוצע על branch night/TASK-120 (commit e53fcbc), נבדק ע"י Agent #8 (Task subagent מקומי) → verdict §3.3 Ready (קשיחים 1/2/6 ✅, כלל-5 ספי-עצירה לא-ודאי כהערה), squash-merged ל-main 81313d1 + נדחף + branch נמחק. אימות read-only: #8 לא ערך/מיזג. גם הוכיח end-to-end את הזרימה night/* → #8 → verdict (שלב 1 של תוכנית דור-שני).
<!-- SECTION:FINAL_SUMMARY:END -->
