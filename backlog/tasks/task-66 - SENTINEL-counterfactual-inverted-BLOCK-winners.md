---
id: TASK-66
title: >-
  SENTINEL counterfactual הפוך: עסקאות שהיו מקבלות BLOCK ביום הכניסה הן דווקא
  המנצחות (WR 64% vs 41% not-blocked, n=36 RELIABLE). רוב ה-BLOCKs
  scan_freshness (6188/7466). הפעלת active mode היתה חוסמת את הטובות. לחקור לפני
  כל מעבר ל-active
status: To Do
assignee: []
created_date: '2026-05-31 01:47'
updated_date: '2026-06-28 01:54'
labels:
  - bug
  - sentinel
  - blocker
  - from-task-62
dependencies: []
ordinal: 66000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
עלה ב-TASK-62 ריצה 2ג. SENTINEL ב-shadow. scan_freshness block מתואם חיובית עם מנצחות (סקאן ישן=מהלך חד=שורט טוב). חוסם הפעלת active. n=36/68 RELIABLE אך רגיים יחיד. קשור ל-TASK-28 (scan_freshness verify). P1.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
אישור-חקירה (צ'אט 2026-06-27, READ-ONLY): מ-sentinel_events (45,008 שורות) — scan_freshness = 25,311 events (הרכיב הדומיננטי), price_freshness 15,456. מתוך 13,033 ה-CRITICAL — כולם SENTINEL_BLOCK בשאדו (EXPLICIT_GATE_MODE=shadow → לא-נאכף = רעש-לוג). counterfactual would-block n=36 (כפי שכבר רשום). הנמכת ה-severity מכוסה ב-TASK-96.
<!-- SECTION:NOTES:END -->
