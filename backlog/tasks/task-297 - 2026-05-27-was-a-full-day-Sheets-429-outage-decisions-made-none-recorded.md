---
id: TASK-297
title: '2026-05-27 was a full-day Sheets 429 outage - decisions made, none recorded'
status: To Do
assignee: []
created_date: '2026-08-10 02:04'
labels: []
dependencies: []
priority: high
ordinal: 295000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נפתר 9/8 מקריאת לוגים אמיתיים. שלוש דגימות מפוזרות על פני היום מראות אותו דפוס: signals=38 decisions=38 errors=38, signals=57 decisions=57 errors=57, signals=65 decisions=65 errors=65. השגיאה בכל אחת: Read requests per minute per user של sheets.googleapis.com - כלומר 429.
387 ריצות מוצלחות רצו באותו יום. אפס שורות SKIP נרשמו.

מסקנה: אין מה לחלץ מחדש. שורות ה-SKIP מעולם לא הגיעו ללוג כי הכתיבה נפלה לפניהן. היום אבוד ומוסבר, ואינו פער-חילוץ.

זו סערת-429 מוקדמת ורחבה יותר מאלה של 22/7 ו-5/8, ומחזקת את TASK-215 - חשבון-שירות ייעודי ל-auto_scan - כתיקון השורשי.

ראיה נשמרה: חמישה לוגים מלאים ב-ClaudeWork/RidingHighPro/archives/evidence_may27_429, כי לוגי GitHub של אותו יום פוקעים ב-2026-08-25.
שער-קבלה: 27/5 מתועד כיום-חנק בהסתייגויות של דוח 7/9, ולא נספר כפער-דאטה.
<!-- SECTION:DESCRIPTION:END -->
