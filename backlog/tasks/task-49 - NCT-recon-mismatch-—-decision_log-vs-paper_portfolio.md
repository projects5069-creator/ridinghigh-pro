---
id: TASK-49
title: NCT recon mismatch — decision_log vs paper_portfolio
status: To Do
assignee: []
created_date: '2026-05-28 15:21'
updated_date: '2026-06-03 19:06'
labels: []
dependencies: []
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
אנומליה שצצה בוריפיקציה 28/5 09:20 Peru: NCT מופיע 1x ב-decision_log אך 2x ב-paper_portfolio (dl=1, pp=2). ATPC ו-WGRX תקינים (OK). השערה / לחקור — 3 אפשרויות: (א) כתיבה כפולה ל-paper_portfolio ב-order_manager, (ב) ENTER שני של NCT שלא נכתב ל-decision_log (כשל 429), (ג) שורת NCT ישנה מיום קודם שנספרה כהיום. חקירה לפני תיקון — אסור לגעת ב-order_manager עד שהשורש ברור.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-06-03: NOT covered by TASK-106. TASK-106 detects the opposite direction — decision_log ENTER WITHOUT a paper_portfolio row (pp<dl). TASK-49 is pp>dl (NCT dl=1, pp=2): a DUPLICATE/orphan paper_portfolio row. Remaining: add a reverse reconciliation check (pp row without a decision_log ENTER, + duplicate-PositionID detection). Reconciler scaffold from TASK-106 can be extended.
<!-- SECTION:NOTES:END -->
