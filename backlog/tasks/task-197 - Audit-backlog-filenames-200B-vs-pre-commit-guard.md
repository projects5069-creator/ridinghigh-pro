---
id: TASK-197
title: Audit backlog filenames >=200B vs pre-commit guard
status: To Do
assignee: []
created_date: '2026-06-27 18:43'
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
