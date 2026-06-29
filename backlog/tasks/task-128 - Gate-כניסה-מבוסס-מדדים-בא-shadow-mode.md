---
id: TASK-128
title: Gate כניסה מבוסס-מדדים בא shadow mode
status: In Progress
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-29 04:16'
labels: []
dependencies: []
priority: medium
ordinal: 131000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Design from validated metrics only (Price band 5-10 strongest so far; D1-gap needs re-anchor test). Build as shadow layer (log would-block like Sentinel shadow) for 2+ weeks multi-regime before any active gating. Depends on Score-decouple decision + freed data.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 shadow observer: would-enter is MxV below -100 AND price at least 3 ONLY, in a SEPARATE path, NOT the shared _check_filters, since editing it would change live
- [ ] #2 Score, Toxic, ROCKET_GUARD are NOT blocking; recorded as tracking metrics only
- [ ] #3 would-enter table written in DRY_RUN shadow; zero change to d.action or live decisions
- [ ] #4 promote shadow to active only after multi-regime and shadow-benign about 2026-07-27, via TASK-194
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
קלט-מדדים מאומת (מחקר 199, צ'אט 2026-06-28, raw/exploratory MxV<=-100%): הצעת-גייט מבוססת 4 ממדים עצמאיים בחלוקת-תפקידים (ablation): מנוע-רווח = MxV<=-100 (בסיס, כבר בגייט) + TPD>=6 (תוספת +6.5pp רווח, אורתוגונלי); מסנני-זנב = REL_VOL>=15 (קטסט 8->4%) + Float%>=60 (קטסט 4->0%). כולם בלתי-תלויים (Spearman ~0 ביניהם). חסמים לפני shadow/active: (1) TASK-201 — Float% מושחת (42M) לתיקון; (2) TASK-200 — נתון מוגבל ל-Score>=60 (היקום החלקי); (3) ניתוק-Score Filter1 — TASK-194/127. גבול-אמינות: שמיש עד MxV+TPD+REL_VOL (n=28); הוספת Float% קורסת ל-n=13. אזהרה: raw, ריכוז-יוני, 8 קטסטרופליות = exploratory; דורש 2+ שבועות multi-regime (~2026-07-27) לפני shadow->active. recon אישר: כיום רק MxV בגייט, 3 ממדים חסרים, Filter1 (Score) עדיין פעיל.

master plan 2026-06-29: core AC added for MxV+price shadow observer separate from _check_filters; Score/Toxic/ROCKET_GUARD non-blocking tracking metrics. Source-trace proved protective filters were NOT part of the 2yr real-money method, all added May-2026, repo born 2026-03-18; re-validation deflated them: 129pp became 19.7pp; ROCKET_GUARD blocks 12 wins vs 7 losses. Sequenced as T-B with TASK-203..206 + 202/194.
<!-- SECTION:NOTES:END -->
