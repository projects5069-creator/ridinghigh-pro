---
id: TASK-126
title: חילוץ SKIPs היסטוריים מלוגי GitHub Actions לפני פקיעת retention
status: To Do
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-30 19:39'
labels: []
dependencies: []
priority: medium
ordinal: 129000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Route B prints [SKIP] lines to Actions stdout. Logs retained ~90 days: May-12 runs expire ~Aug-10. One-off scraper (gh run list + gh run view --log, grep [SKIP]) to rebuild counterfactual dataset May-12..today into local CSV. Read-only, no Sheets writes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RECON 30/6 (READ-ONLY, gh+CSV מקומי): הליבה כבר בוצעה.
research/extract_historical_skips.py קיים+מלא (gh log-zips → grep [SKIP → CSV, masking ]→***,
resume/checkpoint, per-run count anti-silent-fail). רץ 10/6: research/historical_skips.csv =
138,915 רשומות SKIP, טווח 5/11→6/04 (checkpoint עצר 2026-06-04T20:54Z).
מצב: (1) החלון הדחוף נשמר — ה-retention (~90 יום) מאיים קודם על המוקדם (5/11-5/12 פוקע ~9/8),
וזה כבר חולץ. (2) פער 6/04→6/30 לא חולץ — לא דחוף (פוקע ~ספטמבר); resume בעתיד.
(3) DR-RISK: ה-CSV (16MB) local-only — research/ ב-gitignore (שורה 86). קיים רק על המק.
אם המק נופל + הלוגים המוקדמים פקעו (~9/8) → דאטה אבוד לתמיד. שווה גיבוי מחוץ-למכונה לפני 9/8.
<!-- SECTION:NOTES:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ליבת-חילוצה בוצעה — 138,915 SKIPs, טווח 5/11→6/04 (Done 10/6)
- [ ] #2 resume להשלמת פער 6/04→6/30 (לא דחוף, פוקע ~ספטמבר)
- [ ] #3 DR: גיבוי ה-CSV המוקדם מחוץ-למכונה לפני ~9/8 (local-only ב-gitignore)
<!-- AC:END -->
