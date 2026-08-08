---
id: TASK-236
title: >-
  auto-dancer VERIFY produces empty verify.json -> task_result=stage_error
  (execute-proof final stage)
status: To Do
assignee: []
created_date: '2026-07-05 23:17'
labels: []
dependencies: []
ordinal: 240000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
First full --manual run 2026-07-05: P->C->E->C all passed (plan.md 145 lines; execution status=executed; both critics pass) but VERIFY returned empty verify.json -> stage_error. Investigate verify_task.md invocation + verify.json write path. Blocks TASK-186 final.
<!-- SECTION:DESCRIPTION:END -->

--- ⚠️ נבחן לסגירה 2026-08-08 ולא נסגר — הוקפא עם TASK-186/234 ---
נבדק כמועמד ל-Done בטענה ש"שלב VERIFY אינו קיים על main" (נכון:
`git ls-tree origin/main scripts/overnight/` מחזיר אפס verify_task.md).
**אבל הבדיקה המשלימה הפריכה את הסגירה:** `verify_task.md` **כן קיים על
הענף** `fix/auto-dancer-planmd` (קומיט 1b52c13, "M2a — VERIFIER role").
כלומר הכשל שהתיק חוקר — verify.json ריק ⇒ stage_error — **לא נפתר, רק לא
מוזג**. סגירה כ-Done הייתה מאבדת באג אמיתי שיחזור ברגע שהענף יתמזג.
**מוקפא עם TASK-186/234 עד הוורדיקט של HYP-002.** אם הענף יימזג — לפתוח מיד.
