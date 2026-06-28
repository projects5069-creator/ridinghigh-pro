---
id: TASK-128
title: Gate כניסה מבוסס-מדדים בא shadow mode
status: In Progress
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-28 05:44'
labels: []
dependencies: []
priority: medium
ordinal: 131000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Design from validated metrics only (Price band 5-10 strongest so far; D1-gap needs re-anchor test). Build as shadow layer (log would-block like Sentinel shadow) for 2+ weeks multi-regime before any active gating. Depends on Score-decouple decision + freed data.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
קלט-מדדים מאומת (מחקר 199, צ'אט 2026-06-28, raw/exploratory MxV<=-100%): הצעת-גייט מבוססת 4 ממדים עצמאיים בחלוקת-תפקידים (ablation): מנוע-רווח = MxV<=-100 (בסיס, כבר בגייט) + TPD>=6 (תוספת +6.5pp רווח, אורתוגונלי); מסנני-זנב = REL_VOL>=15 (קטסט 8->4%) + Float%>=60 (קטסט 4->0%). כולם בלתי-תלויים (Spearman ~0 ביניהם). חסמים לפני shadow/active: (1) TASK-201 — Float% מושחת (42M) לתיקון; (2) TASK-200 — נתון מוגבל ל-Score>=60 (היקום החלקי); (3) ניתוק-Score Filter1 — TASK-194/127. גבול-אמינות: שמיש עד MxV+TPD+REL_VOL (n=28); הוספת Float% קורסת ל-n=13. אזהרה: raw, ריכוז-יוני, 8 קטסטרופליות = exploratory; דורש 2+ שבועות multi-regime (~2026-07-27) לפני shadow->active. recon אישר: כיום רק MxV בגייט, 3 ממדים חסרים, Filter1 (Score) עדיין פעיל.
<!-- SECTION:NOTES:END -->
