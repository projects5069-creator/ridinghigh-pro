---
id: TASK-41
title: AUDIT.6 — Filter order distribution analysis
status: Done
assignee: []
created_date: '2026-05-24 20:59'
updated_date: '2026-06-07 20:56'
labels: []
dependencies: []
priority: low
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Analyze decision_log skip_reason distribution to validate filter order in decision_logic.py.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Analysis-only 2026-06-04 (read-only, local research 24-25/5 — NO live Sheets). decision_log: 16231 decisions, 16145 SKIP (99.5%), ENTER 86. Score median SKIP=32.6 vs ENTER=89.1. Top SKIP base reasons: MXV_TOO_HIGH + SCORE_TOO_LOW (+ EXISTING_POSITION). Current filter order (_check_filters, first-fail-wins): SCORE -> MXV -> RUNUP -> VOLUME -> PRICE -> BLACKLIST -> TOXIC -> MARKET_CAP -> QUALITY -> EXISTING_POSITION -> COLD_START -> REENTRY -> BUYING_POWER -> ROCKET_GUARD. KEY INSIGHT: filter order = ATTRIBUTION not BEHAVIOR (first-fail-wins => reorder changes only the recorded skip_reason, NOT which trades skip; all checks cheap so efficiency gain negligible). Inference: SCORE_TOO_LOW likely largest base bucket (filter #1 + SKIP median 32.6 < 50); MXV dominant secondary. DATA GAP: exact base-reason totals need re-aggregation of live decision_log (Sheets) — NOT done (not justified: reorder is behavior-neutral). CONCLUSION: reorder = LOW value, behavior-neutral; current order already ~frequency-optimal (SCORE->MXV early). RECOMMEND: mark wontfix OR leave LOW open. decision_logic untouched; action-half (reorder) NOT done.

WONTFIX (2026-06-07): הניתוח הושלם — filter order משפיע על attribution (skip_reason) בלבד, לא על behavior (אילו signals עוברים). reorder הוא behavior-neutral ולכן אינו נדרש. נסגר ללא שינוי קוד. ראה Implementation Notes הקיימות (16231 decisions analyzed).
<!-- SECTION:NOTES:END -->
