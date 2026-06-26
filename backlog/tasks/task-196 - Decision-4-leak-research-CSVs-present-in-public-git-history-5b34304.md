---
id: TASK-196
title: 'Decision 4 leak: research CSVs present in public git history (5b34304)'
status: To Do
assignee: []
created_date: '2026-06-26 15:50'
labels: []
dependencies: []
ordinal: 202000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-195 הגן על ה-HEAD (skip + לא להוסיף CSV), אבל ה-research CSVs כבר נמצאים בהיסטוריית-git של הריפו הציבורי (commit 5b34304) — Decision 4 מודלף חלקית כבר עכשיו. הממצא צץ בקריאת TASK-154. נדרשת הערכת-חומרה + החלטה: history-scrub (git filter-repo) או מעבר ל-private (חופף ל-154). ממצא חשיפת-דאטה, לא תחזוקה. related: TASK-154.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 להעריך מה בדיוק חשוף ב-5b34304 — אילו CSVs, כמה שורות, איזו דאטת-מסחר
- [ ] #2 להעריך חומרה — כמה זמן חשוף, מה הסיכון בפועל
- [ ] #3 להחליט מסלול: history-scrub מול private-migration (תלות ב-TASK-154)
- [ ] #4 תיעוד-בלבד — אפס scrub מבוצע במשימה זו, רק הערכה + החלטה
<!-- AC:END -->
