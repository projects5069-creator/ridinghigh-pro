---
id: TASK-196
title: 'Decision 4 leak: research CSVs present in public git history (5b34304)'
status: Done
assignee: []
created_date: '2026-06-26 15:50'
updated_date: '2026-08-04 00:50'
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

## WON'T-DO 2026-08-04

Closed because the scope is aimed at the wrong target, and that was established inside TASK-154 rather than here.

This task asks to assess what is exposed in commit 5b34304 and decide between a history scrub and a private migration. The recon of 2026-07-02 found that the research CSVs are not the exposure. The exposure is the PK and the report markdown, which carry the strategy verdicts. An assessment scoped to the CSVs would conclude that little is at risk and would be right about the CSVs and wrong about the repository.

Nothing here is being dismissed as unimportant. The finding stands: the CSVs are in public history. It is simply not separable from the larger question, and the larger question is owned by TASK-154 which is also closed, as an owner decision rather than a task.

WHAT WOULD REOPEN THIS: a decision to act on the real exposure. If that ever happens it will be one action covering the PK, the reports and the CSVs together, and it will be opened fresh with the correct scope.
