---
id: TASK-209
title: Retire calculate_score or demote to logged diagnostic (~15 consumers)
status: To Do
assignee: []
created_date: '2026-06-29 21:46'
updated_date: '2026-07-04 01:50'
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
<!-- SECTION:NOTES:END -->
