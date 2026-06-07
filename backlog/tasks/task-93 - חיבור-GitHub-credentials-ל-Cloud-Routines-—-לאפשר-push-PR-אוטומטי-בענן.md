---
id: TASK-93
title: חיבור GitHub credentials ל-Cloud Routines — לאפשר push/PR אוטומטי בענן
status: To Do
assignee: []
created_date: '2026-06-02 02:28'
updated_date: '2026-06-07 15:53'
labels:
  - infra
  - routines
  - cloud
  - github
dependencies: []
priority: high
ordinal: 93000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
פיילוט 1/6 הראה ש-Cloud Routine מבצע ומאמת נכון אך נחסם ב-push/PR כי לסביבת הענן אין GitHub credentials (no token/SSH) + signing service 400 missing source (session ללא repo source registered). מטרה: להוסיף ל-Routine הרשאת GitHub (token/connector) כך שיוכל לדחוף branch ולפתוח PR לבד = end-to-end אמיתי. SCOPE: (1) להוסיף GitHub auth ל-Routine config; (2) לרשום repo source כדי לאפשר signing; (3) לאמת בריצת test שה-PR נפתח; (4) least-privilege — רק push, בלי הרשאות מיותרות. עד אז: Cloud Routines רק למשימות שלא צריכות push, או הרצה ב-Local.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 AC1: Claude GitHub App מותקן על projects5069-creator/ridinghigh-pro (write: Contents + Pull requests); ריצת-טסט דוחפת branch בלי כשל 403. (OAuth-בלבד = נתיב רעוע, באג #57009 → 403; הקריטריון הוא התקנת App.)
- [ ] #2 AC2: session_context.sources=[{git_repository:{url:".../ridinghigh-pro"}}] רשום ב-config של ה-routine — מבטל "400 missing source".
- [ ] #3 AC3: ריצת run-once פותחת PR מ-branch claude/* מול main, ללא merge; מוחזר PR URL ללא push ידני.
- [ ] #4 AC4: Least-privilege מאומת ומתועד: (א) ה-App מוגבל לריפו היחיד הזה (לא all-repos/org/admin); (ב) push מוגבל ל-working branch ע"י proxy התשתית — ברירת מחדל מובנית.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
A חיבור GitHub ידני → B routine JSON עם sources → C run-once test PR → D אימות PR פתוח → E ניקוי branch/PR → F Runbook+PK
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Runbook ב-docs/ (צעדי App + JSON מאומת + פקודות אימות)
- [ ] #2 PK bump + changelog
- [ ] #3 TASK-93→Done רק אחרי שה-test PR נצפה פתוח ואז נוקה (אין branch/PR יתום)
- [ ] #4 ממצאי הפיילוט מתועדים
<!-- DOD:END -->
