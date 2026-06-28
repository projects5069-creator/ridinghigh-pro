---
id: TASK-200
title: איסוף תוצאות D1-D5 גם למניות MxV<=-100% שלא עברו Score>=60
status: To Do
assignee: []
created_date: '2026-06-28 03:28'
labels: []
dependencies: []
ordinal: 206000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
פער-נתון (לא באג). כיום post_analysis אוסף תוצאה עתידית (D1-D5 OHLC) רק לשורות Score>=60. timeline_live מכיל את כל היקום הנסרק (כולל MxV<=-100% שלא עברו Score>=60) אך חסר תוצאה עתידית. התוצאה: אי-אפשר לבדוק את אות-ה-MxV (ואת הזוגות MxV+TPD/ScanChange%) על כל היקום של עמיחי — רק על תת-קבוצת Score>=60. מגבלת-מבנה שזוהתה ב-TASK-199. נדרש מקור-תוצאה (collector/backfill) שמכסה MxV<=-100% ללא תלות ב-Score.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 מקור-תוצאה (D1-D5 OHLC או night) המכסה מניות MxV<=-100% שלא עברו Score>=60
- [ ] #2 אימות שהיקום החדש מאפשר בדיקת MxV/TPD/ScanChange% ללא הטיית-Score
- [ ] #3 READ-ONLY עד אישור; פער-נתון לא באג
<!-- AC:END -->
