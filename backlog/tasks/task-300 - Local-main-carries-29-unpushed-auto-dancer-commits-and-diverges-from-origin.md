---
id: TASK-300
title: Local main carries 29 unpushed auto-dancer commits and diverges from origin
status: To Do
assignee: []
created_date: '2026-08-10 04:13'
labels: []
dependencies: []
priority: high
ordinal: 298000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמצא 9/8 בהכנת בסיס-העבודה לחלון. ה-checkout ל-main נעצר, והחקירה גילתה שני דברים.

ה-main המקומי מפגר 92 קומיטים אחרי origin, ובמקביל מחזיק 29 קומיטים שאינם ב-origin - כלומר הוא מסועף, לא רק ישן. 29 הקומיטים הם עבודת auto-dancer מ-4-5 ביולי: 1,664 שורות ב-scripts/overnight ו-tests/overnight, כולל תשתית RPI מלאה - PLANNER, CRITIC, EXECUTOR, VERIFIER, scope-lock, תקציב-טוקנים לכל משימה, וטסטים הרמטיים לכל שלב.

הסיכון: הקוד קיים רק על המק הזה. מדיניות-הגיבוי מ-9/8 מניחה ששנים-עשר הריפואים מגובים דרך ה-remote שלהם, וההנחה הזאת שגויה כאן. בנוסף, git branch -f main origin/main - פעולת-ניקוי שנראית שגרתית - היתה מייתמת אותם. הפעולה הזאת כמעט בוצעה ב-9/8 ונמנעה רק בגלל בדיקת ahead-count.

הוקטן ב-9/8: bundle של main נשמר ב-ClaudeWork/_machine/repo_bundles/ridinghigh-pro_local-main_29-unpushed_2026-08-09.bundle ומגובה ל-Drive. זה מנטרל את סיכון-האובדן אך לא את השאלה.

באותה הכרעה נכללת docs/auto-dancer/: ארבעה קבצים untracked, שניים מהם .bak, ושניים תורי-הרצה מ-4-5 ביולי. הם שייכים לאותו מאמץ ואין טעם להכריע עליהם בנפרד.

שער-קבלה: הוכרע מה קורה ל-29 הקומיטים - נדחפים לענף, נזרקים, או נשארים מקומיים במודע עם גיבוי; ואם הם נשארים מקומיים, הוסף אזהרה מפורשת ב-BACKUP_POLICY שה-remote אינו מכסה אותם. הוכרע גם מה קורה ל-docs/auto-dancer/.
<!-- SECTION:DESCRIPTION:END -->
