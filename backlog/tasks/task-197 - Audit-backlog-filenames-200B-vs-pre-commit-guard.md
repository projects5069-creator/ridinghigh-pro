---
id: TASK-197
title: Audit backlog filenames >=200B vs pre-commit guard
status: Done
assignee: []
created_date: '2026-06-27 18:43'
updated_date: '2026-06-27 19:09'
labels: []
dependencies: []
ordinal: 203000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ה-pre-commit guard (TASK-85/133) חוסם קומיטים שנוגעים בקבצים ששמם >=200B. התגלה 2026-06-27 בסגירת TASK-63 — שם-הקובץ היה 204B (כותרת עברית ארוכה מוטבעת בשם), תוקן ב-git mv ל-83B. סיכון: ייתכן עוד קבצי-task ב-origin עם שמות >=200B שיחסמו כל קומיט עתידי שייגע בהם — תקלה שתתגלה רק באמצע סגירת-משימה אחרת. נדרש audit חד-פעמי + החלטה אם לקצר מראש. scope: backlog/tasks/ בלבד.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 לסרוק את כל backlog/tasks/*.md ולמדוד אורך-שם-קובץ בבייטים
- [ ] #2 לזהות כל שם >=200B; לסמן גם 180-200B כ-warning קרוב-לסף
- [ ] #3 להחליט מסלול: לקצר מראש (git mv, שמירת prefix task-N) מול טיפול ad-hoc
- [ ] #4 read-only audit בלבד — אפס rename מבוצע במשימה זו, רק זיהוי + רשימה + החלטה
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Audit done 2026-06-27. Swept all backlog/tasks/*.md by BASENAME bytes (the metric the guard checks). Offenders >=200B: task-62 (217B), task-64 (219B) — plus task-63 (204B) already shortened earlier same session. All three renamed via git mv to short English filenames (<100B), task-N prefix preserved so backlog resolves IDs, internal Hebrew titles untouched. Post-fix max basename = 174B (task-80); zero files >=200B, and the 180-200B warning band is EMPTY (top basenames: task-80=174, task-65=173, task-73=170 — all <180). Guard now clean. AC#4 honored: read-only audit + chosen-route renames only, no content changes.
<!-- SECTION:NOTES:END -->
