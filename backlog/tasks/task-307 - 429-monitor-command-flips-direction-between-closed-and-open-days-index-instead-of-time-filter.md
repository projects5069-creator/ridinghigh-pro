---
id: TASK-307
title: >-
  429 monitor command flips direction between closed and open days - index
  instead of time filter
status: To Do
assignee: []
created_date: '2026-08-10 19:57'
labels: []
dependencies: []
priority: medium
ordinal: 305000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
פקודת-הניטור (א) בתוכנית-הבסיס בוחרת ריצות עם .[-5:] (זנב הרשימה). כוילה ב-9/8 (ראשון, שוק סגור): "0/25 מהראש, 5/5 מהזנב". נמדד 10/8 (יום מסחר): הזנב = ריצות טרום-פתיחה 13:00-13:04Z בלי סיכום (0/5), הראש = ריצות חיות (5/5). הכיוון מתהפך כי אינדקס-מיקום אינו זמן.

ניסוח נכון בשני המצבים: סינון לפי createdAt בתוך חלון-המסחר (13:30-20:00Z בקיץ) ואז 5 האחרונות, במקום אינדקס.

שער-קבלה: הפקודה המתוקנת מחזירה 5/5 סיכומים גם ביום סגור (מריצות היום האחרון עם סיכומים) וגם ביום פתוח - נמדד בשני המצבים לפני שנכתבת לתוכנית-הבסיס.
<!-- SECTION:DESCRIPTION:END -->
