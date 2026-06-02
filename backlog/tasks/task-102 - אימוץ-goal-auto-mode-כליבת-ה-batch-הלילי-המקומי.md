---
id: TASK-102
title: אימוץ /goal + auto mode כליבת ה-batch הלילי המקומי
status: To Do
assignee: []
created_date: '2026-06-02 17:44'
labels:
  - infra
  - auto-mode
  - goal
  - claude-code
  - batch
dependencies: []
priority: high
ordinal: 102000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
אומת מול claude --help, claude auto-mode, ו-claude-code-guide (2/6/2026). שתי יכולות מובנות מקומיות לליבת ריצת-לילה אוטונומית: (1) /goal (מאומת; הוצג ב-CLI v2.1.139+, מקומי 2.1.156 OK) — תנאי-סיום ברמת session; Claude ממשיך תור-אחר-תור, ומודל מהיר (Haiku ברירת מחדל) בודק אחרי כל תור אם התנאי התקיים, ואם לא — תור נוסף; מונע 'סיימתי' שקרי. UI: אינדיקטור '/goal active' + timer/turns/token-spend (הערה: 'תורים/queues' מהטקסט המקורי לא מתועד). (2) auto mode (claude --permission-mode auto; 'auto' ערך תקף ב-choices — מאומת; דורש CLI >= v2.1.83) — מאשר אוטומטית read + in-project edits, ומסנן shell/network/spawn דרך classifier; ספים מאומתים: 3 חסימות רצופות או 20 בסה'כ -> pause + חזרה לבקשת קלט; פעולה מאושרת מאפסת את מונה-הרצופות, מונה-הסה'כ נשמר לסשן. תיקון חשוב לטקסט המקורי: auto mode זמין בכל המסלולים (לא ספציפי ל-Max), דורש Opus 4.6+ או Sonnet 4.6 (לא 4.7; המודל הנוכחי Opus 4.8 OK), ואינו ברירת-מחדל — מפעילים עם ה-flag או defaultMode:auto ב-~/.claude/settings.json (Team/Enterprise: admin צריך לאפשר). למה מקומי ולא ענן: /goal+auto רצים בסשן המקומי עם הסקילים/creds/GitHub — בניגוד ל-Cloud Routine/ultraplan/ultrareview המבודדים (פיילוט TASK-77: ענן לא דוחף בלי creds). אבטחת auto mode: בטוח לקבוצה A (repo-scoped, לא קוראת תוכן חיצוני); משימות שקוראות FINVIZ/news/Sheets = needs-approval (חשיפת prompt-injection). הנחיה תפעולית: הסוכן רשאי ומוזמן להשתמש ב-/goal ובכל יכולת מובנת רלוונטית ביוזמתו כשהיא משפרת ביצוע — בלי אישור פרטני לכל שימוש — כל עוד נשמרים כללי הבטיחות (branch+PR, recon-first, verification-before-completion, לא auto-mode עיוור על תוכן חיצוני). SCOPE: (1) template פרומפט-לילה שמשלב /goal עם תנאי-סיום אובייקטיבי; (2) batch קבוצה-A תחת auto mode; (3) לאמת ש-/goal עוצר נכון בהשגת/אי-השגת המטרה; (4) תיעוד עלות (auto/goal רצים בסשן המקומי תחת המנוי הרגיל — לא חיוב נפרד; ultra* = ענן מחויב). תלוי: סיווג auto-safe (מפתיחת היום) + TASK-101 (security-guidance כשכבה). משלים TASK-93/94. תיקונים מהטקסט המקורי: 'Max/Opus 4.7+ ברירת-מחדל בלי flag' (שגוי, ראה לעיל); 'overlay תורים' (לא מתועד); הופרדה גרסת auto mode (v2.1.83+) מגרסת /goal (v2.1.139+).
<!-- SECTION:DESCRIPTION:END -->
