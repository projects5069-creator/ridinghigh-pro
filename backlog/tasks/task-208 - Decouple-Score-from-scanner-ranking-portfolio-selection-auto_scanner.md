---
id: TASK-208
title: Decouple Score from scanner ranking + portfolio selection (auto_scanner)
status: To Do
assignee: []
created_date: '2026-06-29 21:46'
updated_date: '2026-06-30 19:09'
labels: []
dependencies: []
priority: low
ordinal: 214000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
auto_scanner selects/ranks by Score (TRADE_ENTRY_MIN_SCORE>=70, idxmax/sort) at :490/578/1335/1338. After 194/S1 decoupled Score from entry gate, decide MxV-ranking vs lower threshold. Display/portfolio layer, separate from entry decision.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 borrow_collector.py:40 selects borrow targets by score>=min_score — switch to MxV (scoreless-era: score is blank, breaks selection)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RECON 30/6 (READ-ONLY): החצי של borrow-selection כבר תוקן —
commit 5a127ad (29/6, יום ה-flip): get_scanned_universe בוחר לפי MxV<=mxv_max, לא Score.
חי + מחובר ל-orchestrator_eod (collect_borrow_snapshot, רץ off-hours 16:00 Peru via agent_eod.yml).
ההשערה 'שבור מאז flip' הופרכה — התיקון ליווה את ה-flip באותו יום, אין חלון-שבירה. AC#1 סומן done.
⚠️ ה-scope הנותר ב-208 = decoupling של Score מ-ranking/display ב-auto_scanner (4 אתרים: 490/578/1335/1338,
שכבת display/portfolio, נפרד מהחלטת-כניסה). זה Score-work → שייך לאשכול-Score, נדחה עם TASK-209
(החלטת עמיחי 30/6: כל עבודת-Score בהמשך, לא עכשיו). לא לבצע את הנותר עד שנטפל ב-Score כמכלול.
<!-- SECTION:NOTES:END -->
