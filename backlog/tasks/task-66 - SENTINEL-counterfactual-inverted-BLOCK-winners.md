---
id: TASK-66
title: >-
  SENTINEL counterfactual הפוך: עסקאות שהיו מקבלות BLOCK ביום הכניסה הן דווקא
  המנצחות (WR 64% vs 41% not-blocked, n=36 RELIABLE). רוב ה-BLOCKs
  scan_freshness (6188/7466). הפעלת active mode היתה חוסמת את הטובות. לחקור לפני
  כל מעבר ל-active
status: Done
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

## ACCURACY FIX 2026-08-04

The investigation note above says EXPLICIT_GATE_MODE=shadow, so the CRITICAL events are unenforced log noise. That is no longer true.

Verified live: config.py line 374 sets EXPLICIT_GATE_MODE to "active", and it has been active since the flip of 2026-06-29. Line 378 sets ENTRY_GATE_MINIMAL to True.

What has NOT changed, and is the reason this task still stands: SENTINEL_MODE is still "shadow" at config.py line 359. The two are separate switches. The sentinel still logs rather than blocks, so the counterfactual this task records is still a counterfactual and no trade was actually blocked by it.

What the correction does change is the framing of the 13,033 CRITICAL rows. They are not noise from an unenforced explicit gate; they are sentinel events under a sentinel that is deliberately in shadow. The finding itself is untouched: would-block correlates positively with winners, WR 64 percent against 41 percent on n=36, single regime.

This task remains the blocker on ever moving SENTINEL_MODE to active.

--- הומר לתיעוד ונסגר 2026-08-08 (מרשם TASK_REGISTER_2026-08-08 §3) ---
זה לא היה משימה אלא הכרעה שכבר התקבלה. ההכרעה, הנימוקים והמספרים הועברו
במלואם ל-`docs/DECISIONS_2026-08-08.md`, סעיף **D6 · TASK-66 — ה-counterfactual ההפוך (וטו עומד על SENTINEL active)**.
גוף התיק נשאר כאן כמקור-היסטורי ואינו נמחק. אם ההכרעה תשתנה — לפתוח תיק חדש
שמפנה לסעיף שם, לא להחיות את זה.
