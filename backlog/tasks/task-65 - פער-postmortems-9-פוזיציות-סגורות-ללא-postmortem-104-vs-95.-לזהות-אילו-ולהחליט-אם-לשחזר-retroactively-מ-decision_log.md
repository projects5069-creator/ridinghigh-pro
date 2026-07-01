---
id: TASK-65
title: >-
  פער postmortems: 9 פוזיציות סגורות ללא postmortem (104 vs 95). לזהות אילו
  ולהחליט אם לשחזר retroactively מ-decision_log
status: To Do
assignee: []
created_date: '2026-05-31 00:48'
updated_date: '2026-07-01 00:52'
labels:
  - data-quality
  - postmortems
  - from-task-62
dependencies: []
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
עלה ב-TASK-62 ריצה 1.5. רשימה שמית ידועה (DEC-2026-05-14-00003 וכו'). P2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 read-only עד שלב-ההחלטה; כל backfill בפועל = צעד מאושר נפרד
- [ ] #2 scope multi-month GLOBAL set-diff (לא per-month isolated): לאחד ENTER DecisionIDs מכל החודשים (2026-05/06/07), לאחד PositionIDs מכל ה-postmortems, missing = enters_global − pm_global. הכרחי כי postmortem נכתב בחודש-הסגירה ועלול לשבת ב-spreadsheet שונה מה-ENTER — per-month isolated מנפח false-missing
- [ ] #3 FINAL scope 2026-06-27: gap אמיתי = 36 פוזיציות CLOSED-בלי-postmortem (ב-paper_portfolio עם ExitDate+ExitReason: TP_HIT/SL_HIT + 3 MANUAL_CLEANUP). 0 pending. ה-20 ENTERs ללא שורת-paper_portfolio הופרדו ל-task נפרד (לא postmortem-gap). backfill של ה-36 = החלטת-עיצוב נפרדת (שחזור-מלא מול חלקי מול תיעוד) טרם בוצעה — read-only עד אישור backfill
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
צ'אט-recon 2026-06-27 (READ-ONLY, נפרד+נוסף ל-scope=36 שכבר תועד): מעבר על 182 ה-postmortems הקיימים מצא MetricsAtEntry ריק (={}) ב-55% (101/182) — בעיה מובחנת מ-36 ה-חסרים (כאן ה-postmortem קיים אך חסר-מדדים). היפותזה-לשורש (לא מאומת): postmortem_engine._get_decision_context קורא ל-_read_decision(position_id) שעושה linear-scan ב-decision_log ומחזיר {} ב-miss — לחקור quota-drop של כתיבת decision_log מול PositionID!=DecisionID מול eventual-consistency. רלוונטי גם ל-TASK-198. הערה: אין כאן מסקנת-edge — ה-edge-verdict השלילי הופרך בדוח IB (PK v3.63).

MERGED TASK-198 (30/6): חקירת-שורש אחת על _read_decision (linear-scan→{} ב-miss) המכסה שני סימפטומים — 36 postmortems חסרי-MetricsAtEntry + 20 ENTERs ללא שורת paper_portfolio. read-only עד הכרעה.

--- ראיה חיה 2026-06-30 (recon end-to-end, נתון חי) ---
GVH (ENTER 08:54) + SDOT (ENTER 09:27): ENTER מלא ב-decision_log, כל השערים עברו, אך אפס שורת paper_portfolio = ENTER-ללא-pp חי בפרודקשן (2 מקרים חדשים, לא רק היסטוריים).
- cap נשלל ישירות: ColdStartConcurrentLeft=1(GVH)/5(SDOT) >0; DailyLeft=5/4; BuyingPower=200k; IsShortable=TRUE. לא cap, לא gate, לא buying-power.
- ה-reconciler זיהה את שניהם @16:00 EOD: RECONCILE_MISSING_PORTFOLIO_ROW (WARNING, flag-only — לא תיקן כי RECONCILE_AUTO_REPAIR כבוי = TASK-109).
ניואנס root-cause: הכשל כאן = צינור entry->order->pp (ENTER מלא -> אין pp -> reconciler-flagged). ייתכן באג נפרד מ-root-cause המשוער _read_decision->{} (שמסביר MetricsAtEntry-ריק). בדוק אם 65 מכיל 2 באגים שונים מוזגים לפני שמתקנים.
מחזק גם TASK-109 (auto-repair כבוי — לו היה פעיל, GVH/SDOT היו מ-backfilled @16:00).

--- חידוד root-cause (recon קוד+נתון, 2026-06-30) ---
GVH/SDOT זהים ל-CUPR (שנפתח) בכל שדות-ההחלטה -> הכשל בכתיבת-pp, לא בנתונים.
OWNER מדויק = TASK-105 (silent paper_portfolio write loss). מאומת בקוד:
- orchestrator.py:329 — 'paper_portfolio write FAILED for ENTER ... surfaced, not counted'
- decision_logic.py:118 — flag 'True until a paper_portfolio write fails' (TASK-105)
- reconciler.py:127 — 'likely a swallowed/failed write (TASK-105)' -> RECONCILE_MISSING_PORTFOLIO_ROW @16:00
גורם סביר = 429 בשעות-שוק (append נבלע). -> TASK-65 מערבב 2 מנגנונים: (1) write-failure=TASK-105 [ENTER-ללא-pp], (2) _read_decision->{}=MetricsAtEntry-ריק. שני באגים נפרדים.
פתרון: TASK-105 (robust write/retry) + TASK-109 (auto-repair כבוי כרגע).
מחר בסיכון חלקי: כל 429 ברגע כתיבת-ENTER יפיל pp. הקלה צפויה: TASK-215 (SA נפרד ל-auto_scan, פעיל מ-1/7) מפחית 429 -> למדוד השפעה על דליפת-pp מחר.

--- תיקון (recon חי TASK-105, 2026-06-30) ---
תיקון ל-note הקודם: TASK-105 הוא DONE (03/6, PR#4 dc3ddbf, PK v2.66) — לא באג פתוח.
ה-pp-write כבר מוקשח: safe_append_row (order_manager.py:290) עם dedup לפי PositionID + retry 3x (backoff 2/4/8s) + חשיפת-כשל (:283 מחזיר False על retry-exhaustion -> orchestrator:141 סופר ככשל).
מה קרה ל-GVH/SDOT: ה-retry מוצה תחת 429-storm מתמשך (>3 ניסיונות) -> False -> reconciler flag @16:00. 105 עשה את תפקידו (שקט->גלוי); הוא לא מונע אובדן כש-429 נמשך מעבר ל-retry — by-design, לא באג.
השארית (לא ב-105): (1) TASK-109 — RECONCILE_AUTO_REPAIR (auto-backfill השורה, gated על track-record; GVH/SDOT=2 true-positives). (2) TASK-215 — SA נפרד מפחית 429 במקור (פעיל 1/7). GVH/SDOT מחזקים שניהם.
<!-- SECTION:NOTES:END -->
