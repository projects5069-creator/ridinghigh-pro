---
id: TASK-270
title: Back up historical skips CSV off-machine
status: Done
assignee: []
created_date: '2026-08-08 16:20'
updated_date: '2026-08-10 03:51'
labels: []
dependencies: []
priority: high
ordinal: 268000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
research/historical_skips.csv — 16MB, 138,915 SKIP records from 2026-05-11, gitignored (.gitignore:86), single copy on this Mac only (TASK-126 AC#3). GitHub Actions logs for the early window expire ~2026-08-09, after which a lost Mac = data gone forever. Deliberately deferred on 2026-08-08 (Saturday session) — recorded here so the deferral is a decision, not an oversight. Scope: one off-machine copy (Drive/external), verify byte size + row count after copy, note location in TASK-126.
<!-- SECTION:DESCRIPTION:END -->

--- השאלה הפתוחה 2026-08-08 (מתוכנית-העבודה) — לא הוכרע ---
⚠️ **הבהרה שעלתה בבניית התוכנית:** הדדליין של התיק הזה **אינו** חלון-המדידה.
הוא פקיעת לוגי GitHub Actions (~9/8) — לוח-זמנים נפרד לגמרי שבמקרה סמוך.
התיק אינו שייך לקבוצת "לפני שני" ואינו נוגע לאיסוף הדאטה.

**השאלה: לאן מעתיקים?**
1. א. Google Drive — זמין מיידית, אותו חשבון שכבר בשימוש; המחיר: 16MB בחשבון
      שכבר נושא את כל הגיליונות.
   ב. דיסק חיצוני / מכונה אחרת — הפרדה פיזית אמיתית; המחיר: דורש שהחומרה
      תהיה בהישג-יד עכשיו.
   ג. שניהם — עלות זניחה, ההגנה הטובה ביותר.
   ⚠️ אין ברירת-מחדל. **לא הוכרע.**

2. מה עם AC#2 (הפער 6/04→6/30 שלא חולץ)? הוא פוקע ~ספטמבר, לא מחר.
   האם מחלצים אותו עכשיו באותה הזדמנות או מתזמנים בנפרד? **פתוח.**

מה שאינו פתוח: העובדה שאחרי ~9/8, מק שאובד = דאטה שאבד לצמיתות ולא ניתן
לחילוץ חוזר.

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Closed 2026-08-09. Two verified off-machine archives under ~/ClaudeWork/RidingHighPro/archives, synced by Drive Desktop: historical_skips_20260511-0604_v1.csv.gz (the range the ticket asked for) and historical_skips_20260511-0630_v2.csv.gz (the same plus the 6/04-6/30 gap). Both pass gzip -t; the v2 md5 matches MANIFEST_v2. The head of the file is byte-identical to v1, so the original 138,915 rows were not disturbed by the append.
<!-- SECTION:FINAL_SUMMARY:END -->
