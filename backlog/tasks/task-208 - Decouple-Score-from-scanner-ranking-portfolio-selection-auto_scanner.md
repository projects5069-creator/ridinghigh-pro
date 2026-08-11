---
id: TASK-208
title: Decouple Score from scanner ranking + portfolio selection (auto_scanner)
status: To Do
assignee: []
created_date: '2026-06-29 21:46'
updated_date: '2026-08-05 18:21'
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

RULING 2026-08-05 (עמיחי)

הכרעה: אשרור הדחייה. אשכול ה-Score כולו נדחה לאחרי הוורדיקט של HYP-002
(תחילת אוקטובר, HYPOTHESES.md:257). זה מאשרר את החלטת 30/6 שכבר מתועדת ב-Notes,
ומצמיד אותה לתאריך.

מה כן אושר לביצוע עכשיו, בנפרד מהאשכול ובקומיט נפרד:
מחיקת normalize_mxv (formulas.py:556) ו-normalize_atrx (formulas.py:567) + שתי שורות
הייבוא שלהן ב-dashboard.py:58-59.
היתכנות מאומתת 2026-08-05: grep repo-wide (ללא backups/project_sync/research) מחזיר עבור
כל אחת מהן ארבע תוצאות בלבד — ההגדרה ב-formulas.py ושורת הייבוא ב-dashboard.py. ספירת
האזכורים ב-dashboard.py היא 1 לכל אחת, כלומר שורת הייבוא בלבד ואפס קריאות. grep על
test_formulas.py, test_utils.py וכל tests/ מחזיר אפס. calculate_score (formulas.py:584)
אינו נוגע בהן — הוא קורא ל-SCORE_WEIGHTS_V2 ו-SCORE_CAPS_V2 בלבד (:594-595).

תיקון לתוכנית שהיה שגוי:
calculate_vwap_dist אינו קוד מת. יש לו שתי קריאות חיות — dashboard.py:380 ו-dashboard.py:560
— וחמש assertions ב-test_formulas.py:146-150 ש-CI מריץ כסקריפט (tests.yml:34).
auto_scanner.py:33 מייבא אותו אך אינו קורא לו (שלוש הקריאות שם הן
ל-calculate_typical_price_dist ב-:256, :936, :1246). הטיפול הנכון הוא החלפה
ב-calculate_typical_price_dist בשלושה מקומות — dashboard.py:380, dashboard.py:560,
ו-test_formulas.py — ולא מחיקה. זו עבודה נפרדת ותועדה ב-TASK-209.
אזהרה: שתי הקריאות בדשבורד יושבות בתוך "except:" עירום (dashboard.py:381, :561), ולכן
מחיקה הייתה נבלעת בשקט ומחזירה vwap_dist=0 במקום לקרוס. הטסט הוא מה שהיה תופס, לא הפרודקשן.
<!-- SECTION:NOTES:END -->

## RESTATED 2026-08-04

Half of this task is already done and the other half is deliberately parked, and the title does not say either.

DONE: AC#1, borrow selection by MxV instead of Score, landed in commit 5a127ad on 29/6, the same day as the flip. The hypothesis that it broke at the flip was disproven.

STILL LIVE, verified 2026-08-04, four sites in auto_scanner.py: line 504 portfolio selection at Score >= TRADE_ENTRY_MIN_SCORE, line 592 peak selection by Score idxmax, line 1008 ENTRY_MIN_SCORE inside update_live_trades, and line 1349 the EOD portfolio filter.

PARKED BY DECISION, not blocked: the owner decision of 30/6 is that all remaining Score work waits and is handled as one body, together with TASK-209.

NOTE ADDED 2026-08-04: line 1008 is why live_trades holds zero rows in every month. The gate is Score >= 70 and the highest scanner Score in the live run of 2026-08-03 was 60.86. See TASK-251.

## ממצא 2026-08-10 — 208 ו-260 הן החלטה אחת, לא שתיים
התיק מתאר את ארבע נקודות-הבחירה כ"שכבת תצוגה". נמדד ש**שתיים מהן קוראות מהגיליון**
ולא מהזיכרון, ולכן הן מושפעות ישירות מהכרעת-260 (הקפאת כתיבת ה-Score ל-timeline_live):
  `:503`  results_df בזיכרון      ⇒ לא מושפעת (ההקפאה עובדת על עותק, `:57-64`)
  `:591`  _save_daily_summary     ⇒ **קוראת מהגיליון** · `idxmax` ⇒ ValueError · עטוף ב-try
                                     ⇒ daily_summary מפסיק להיכתב **בשקט, בכל דקה**
  `:1110` update_live_trades      ⇒ `float(r.get("Score",0) or 0)` ⇒ 0<70 ⇒ כבר אפס שורות היום
  `:1348` run_eod portfolio       ⇒ **קוראת מהגיליון** · NaN>=70=False ⇒ בחירה ריקה, שקט
⇒ **תנאי-קדם משותף:** הפונקציה הבטוחה (`safe_idxmax` — לספור ערכים תקינים, לא לבדוק
ריקנות) חייבת לנחות לפני כל צעד בשני התיקים.
ייסגר כאשר: ארבעת אתרי-הדירוג אינם קוראים Score, או שהוכרע במפורש שהם נשארים —
והפונקציה הבטוחה קיימת ומכוסה בבדיקה דו-כיוונית.
