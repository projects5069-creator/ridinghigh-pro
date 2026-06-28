---
id: TASK-200
title: איסוף תוצאות D1-D5 גם למניות MxV<=-100% שלא עברו Score>=60
status: Done
assignee: []
created_date: '2026-06-28 03:28'
updated_date: '2026-06-28 23:51'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
עדכון (צ'אט 2026-06-27): בדיקה תוך-יומית של צמד MxV+TPD כבר עקפה חלקית את מגבלת-המבנה — רצה על 372 ticker-days (כל היקום MxV<=-100%) דרך מחירי timeline_live התוך-יומיים, פי-3.6 מ-101 שורות Score>=60. אך זה כיסה רק תוצאה תוך-יומית (round-trip); תוצאת-לילה (night) עדיין מוגבלת ל-post_analysis Score>=60 → הפער המקורי (D1-D5/night ליקום המלא) נשאר פתוח.
<!-- SECTION:NOTES:END -->
