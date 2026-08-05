---
id: TASK-209
title: Retire calculate_score or demote to logged diagnostic (~15 consumers)
status: To Do
assignee: []
created_date: '2026-06-29 21:46'
updated_date: '2026-08-05 18:21'
labels: []
dependencies: []
priority: low
ordinal: 215000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
calculate_score feeds ~15 display/analysis consumers (dashboard, post_analysis_collector, health_check, health_audit). After 194 decoupled Score from entry, decide full retire vs keep as documented diagnostic. High blast-radius; likely keep as diagnostic.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
E2E-AUDIT S1-S5 (3/7) — scope נספג מהחקירה (4 פריטים, כולם אשכול-Score):
(1) dead-code: normalize_mxv/normalize_atrx (formulas.py:457/468) — אפס call-sites repo-wide; import-רפאים dashboard.py:59-60 + import calculate_score מת ב-post_analysis_collector.py:34 — למחוק יחד עם ה-retire.
(2) dashboard.py:378 קורא calculate_vwap_dist (deprecated alias, formulas.py:596) → להחליף ב-calculate_typical_price_dist; וכן dashboard.py:63 מייבא calculate_score דרך auto_scanner במקום מ-formulas — ליישר.
(3) d.score מחושב פר-החלטה על הנתיב-הקריטי גם בעידן scoreless: decision_logic.py:266 דרך calculate_agent_score; חילוץ-המפתחות signal[...] (:258-264) יזרוק KeyError→SKIP DATA_ERROR למרות שה-score אינו מגייט (gate=active). ההכרעה demote-vs-remove שייכת לכאן. נתיב-מסחר חי — רק עם go.
(4) health_audit checks עידן-Score: check_07_score_range (:738, בלי מודעות-SCORE_WRITE_FROZEN) + check_12_score_weights_sum (:1008) — לרענן/להחריג בהחלטת-הסיום; אגב: generate_sheets_schema.py:9 doc-drift ('14 sheets' ↔ 16 בפועל).
ראיות: plans/stateless-seeking-sifakis.md S1/S2/S3/S4.

RULING 2026-08-05 (עמיחי)

הכרעה: אשרור הדחייה. אשכול ה-Score נדחה לאחרי הוורדיקט של HYP-002 (תחילת אוקטובר).
blast-radius אמיתי: d.score מחושב בכל החלטה על הנתיב הקריטי (decision_logic.py:270)
ונכתב ל-decision_log בכל ENTER.

מה אושר לביצוע עכשיו, בקומיט נפרד (מפורט ב-TASK-208):
מחיקת normalize_mxv (formulas.py:556) + normalize_atrx (formulas.py:567) + שתי שורות
הייבוא ב-dashboard.py:58-59. אפס call-sites, אפס טסטים, אפס נגיעה ב-calculate_score.

תיקון מחייב לפריט (2) ב-Notes של E2E-AUDIT:
הפריט אומר להחליף את calculate_vwap_dist ב-calculate_typical_price_dist. זה נכון, אבל
ההקשר שבו הוא מופיע (סעיף "dead-code") מטעה. calculate_vwap_dist אינו קוד מת:
  - dashboard.py:380  -> קריאה חיה
  - dashboard.py:560  -> קריאה חיה
  - test_formulas.py:20 (ייבוא) + :146-150 (חמש assertions)
  - tests.yml:34 מריץ את test_formulas.py כסקריפט ב-CI
מחיקה במקום החלפה => ImportError ב-test_formulas.py => CI אדום, ובנוסף כשל שקט בדשבורד
כי שתי הקריאות עטופות ב-"except:" עירום (dashboard.py:381, :561).
העבודה הנכונה: החלפה בשלושה מקומות (dashboard.py:380, dashboard.py:560, test_formulas.py),
כאשר calculate_vwap_dist הוא alias של שורה אחת (formulas.py:176).
auto_scanner.py:33 מייבא אותו ואינו קורא לו — הייבוא ניתן להסרה באותה עבודה.

מספרי שורה בפריט (1) שהתיישנו ותוקנו באימות 2026-08-05:
  normalize_mxv    -> formulas.py:556 (בתיק כתוב 457)
  normalize_atrx   -> formulas.py:567 (בתיק כתוב 468)
  calculate_vwap_dist -> formulas.py:168 (בתיק כתוב 596)
  dashboard.py ייבוא calculate_score דרך auto_scanner -> :62 (בתיק כתוב 63)
  d.score = calculate_agent_score -> decision_logic.py:270 (בתיק כתוב 266)
פריט (4) נבדק ונמצא נכון כלשונו: check_07_score_range ב-health_audit.py:738,
check_12_score_weights_sum ב-:1008.
<!-- SECTION:NOTES:END -->
