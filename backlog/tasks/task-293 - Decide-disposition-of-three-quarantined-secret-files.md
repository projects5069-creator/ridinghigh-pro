---
id: TASK-293
title: Decide disposition of three quarantined secret files
status: To Do
assignee: []
created_date: '2026-08-10 00:27'
labels: []
dependencies: []
priority: medium
ordinal: 291000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
בודדו 9/8 ל-.secrets_quarantine_20260809 עם chmod 600, מחוץ ל-ClaudeWork כדי שלא יסונכרנו: google_credentials.ridinghigh.bak, oauth_pattern.txt, system_recon_full.txt. שער-קבלה: לכל אחד הוכרע - נדרש ונשמר במקום מוגן, או מיותר ונמחק אחרי אימות שאין תלות.
<!-- SECTION:DESCRIPTION:END -->

## הכרעת עמיחי 2026-08-10 — להמתין ל-15/8
אין מחיקה ואין הכרעה פרטנית לפני החלפת המפתח בשבת 15/8 (TASK-296).
הנימוק: אחרי ההחלפה, גיבוי המפתח מ-19/4 מחזיק מפתח מבוטל — ערכו יורד לאפס והסיכון שבו
נעלם באותו רגע. הכרעה לפניה תהיה או מחיקה מוקדמת מדי (אם ההחלפה תיכשל ויידרש גיבוי)
או שמירה מיותרת. שלושת הקבצים נשארים בבידוד עם chmod 600, מחוץ לכל סנכרון.
⚠️ שני קבצי-הסריקה (oauth_pattern.txt, system_recon_full.txt) — דינם ייקבע אחרי 15/8,
ורק אחרי חיפוש שמותיהם בכל הריפואים והמסמכים הפעילים. אפס תוצאות ⇒ מחיקה בטוחה.
