---
id: TASK-93
title: חיבור GitHub credentials ל-Cloud Routines — לאפשר push/PR אוטומטי בענן
status: To Do
assignee: []
created_date: '2026-06-02 02:28'
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
