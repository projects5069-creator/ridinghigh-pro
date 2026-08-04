---
id: TASK-208
title: Decouple Score from scanner ranking + portfolio selection (auto_scanner)
status: To Do
assignee: []
created_date: '2026-06-29 21:46'
updated_date: '2026-07-04 01:50'
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

E2E-AUDIT S3 (3/7, קריאה-בלבד) — אימות-חי של אתרי-ה-ranking + אתר נוסף:
run_scan portfolio-selection Score>=TRADE_ENTRY_MIN_SCORE (auto_scanner.py:488-490) ·
update_live_trades ENTRY_MIN_SCORE=TRADE_ENTRY_MIN_SCORE (:994 — לא היה ברשימה המקורית) ·
run_eod פילטר Score>= + sort_values('Score') (:1332-1338). החישובים עצמם דרך formulas (SSoT תקין);
הכתיבה קפואה ב-score_cell. ראיות: plans/stateless-seeking-sifakis.md S3.
<!-- SECTION:NOTES:END -->

## RESTATED 2026-08-04

Half of this task is already done and the other half is deliberately parked, and the title does not say either.

DONE: AC#1, borrow selection by MxV instead of Score, landed in commit 5a127ad on 29/6, the same day as the flip. The hypothesis that it broke at the flip was disproven.

STILL LIVE, verified 2026-08-04, four sites in auto_scanner.py: line 504 portfolio selection at Score >= TRADE_ENTRY_MIN_SCORE, line 592 peak selection by Score idxmax, line 1008 ENTRY_MIN_SCORE inside update_live_trades, and line 1349 the EOD portfolio filter.

PARKED BY DECISION, not blocked: the owner decision of 30/6 is that all remaining Score work waits and is handled as one body, together with TASK-209.

NOTE ADDED 2026-08-04: line 1008 is why live_trades holds zero rows in every month. The gate is Score >= 70 and the highest scanner Score in the live run of 2026-08-03 was 60.86. See TASK-251.
