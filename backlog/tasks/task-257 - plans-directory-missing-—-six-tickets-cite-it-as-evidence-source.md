---
id: TASK-257
title: plans/ directory missing — six tickets cite it as evidence source
status: To Do
assignee: []
created_date: '2026-08-05 18:23'
labels:
  - docs
  - evidence
  - tech-debt
dependencies: []
priority: medium
ordinal: 255000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
plans/stateless-seeking-sifakis.md אינו קיים בריפו, ומצוטט כמקור ראיה ב-TASK-208, 209, 223, 224, 226 ו-229. ה-RULING של 3/7 ב-TASK-224 וארבעת ממצאי ה-E2E-audit ב-TASK-209 נשענים עליו ואינם ניתנים לאימות. פירוט ב-Implementation Notes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
מקור: ביקורת ההחלטות 2026-08-05 (RULING עמיחי). התגלה תוך כדי אימות הראיה של TASK-224.

הממצא, מאומת 2026-08-05:
  $ ls -d plans
  ls: plans: No such file or directory
  $ find . -name "*sifakis*" -not -path './.git/*'
  (אפס תוצאות)
  $ grep -n "^plans" .gitignore
  (אפס — הנתיב אינו מוחרג, כלומר הוא פשוט לא קיים)

הקובץ plans/stateless-seeking-sifakis.md מצוטט כמקור ראיה בשישה תיקים:
  TASK-208  "ראיות: plans/stateless-seeking-sifakis.md S3"
  TASK-209  "ראיות: plans/stateless-seeking-sifakis.md S1/S2/S3/S4"
  TASK-223  (E2E-audit)
  TASK-224  "Evidence: plans/stateless-seeking-sifakis.md S2"
  TASK-226  "Evidence: plans/stateless-seeking-sifakis.md S3"
  TASK-229  "plans/stateless-seeking-sifakis.md"

ההשלכה הקונקרטית: ה-RULING של עמיחי מ-3/7 ב-TASK-224 ("direction 'up to $1000' —
qty<1 => SKIP with a dedicated skip_reason") מפנה לקובץ הזה כמקור. ההכרעה עצמה מתועדת
בגוף התיק, אבל הראיה שמאחוריה אינה ניתנת לאימות מהריפו. אותו דבר חל על ארבעת ממצאי
ה-E2E-audit של 3/7 ב-TASK-209.

מה לברר:
(1) האם הקובץ נמחק, שונה שמו, או מעולם לא נדחף.
(2) האם הוא קיים על המק מקומית מחוץ לריפו.
(3) האם הוא קיים על ענף אחר — לבדוק ב-git log --all --diff-filter=D ובכל הענפים
    הפעילים, ולא רק ב-main.
(4) אם אינו ניתן לשחזור — לתעד זאת בשישה התיקים כדי שהפניה למקור שאינו קיים לא תיקרא
    כראיה קיימת.

הערה: docs/plans/ כן קיים בריפו אבל מכיל קובץ אחד בלבד (dev1_devils_advocate.md) ואינו
אותו נתיב.
<!-- SECTION:NOTES:END -->
