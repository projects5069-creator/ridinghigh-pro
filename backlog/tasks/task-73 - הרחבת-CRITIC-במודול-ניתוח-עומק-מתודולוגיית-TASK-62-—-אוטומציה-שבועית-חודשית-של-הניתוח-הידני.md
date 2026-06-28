---
id: TASK-73
title: >-
  הרחבת CRITIC במודול ניתוח-עומק (מתודולוגיית TASK-62) — אוטומציה שבועית/חודשית
  של הניתוח הידני
status: To Do
assignee: []
created_date: '2026-05-31 02:32'
updated_date: '2026-06-28 01:54'
labels:
  - critic
  - analysis
  - from-task-62
dependencies: []
ordinal: 73000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מאחד Weekly Engine + CRITIC. CRITIC (critic_v1.py, 835 שורות) כבר עושה סיכום: build_weekly_row/build_monthly_row (WR/TotalPnL/AvgWin/AvgLoss), scorecard, anomalies. חסר לו שכבת ניתוח-עומק. להוסיף: KPI מלא (Profit Factor, Expectancy, R:R, MaxDrawdown), קורלציית כל מדד-כניסה ל-PnL מדורגת, counterfactual 4 הסוכנים (SENTINEL would-BLOCK וכו'), פילוחים, דגלים אוטומטיים (מדד לא-Score עוקף / סוכן בכיוון הפוך / Score r<0.05), ודוח עברית ל-research/. מפרט מלא: research/TASK-62_weekly_analysis_2026-05-30.md. הרחבת CRITIC קיים, לא סוכן חדש (כבוד ל-FREEZE). קושר ל-TASK-48 (שכבר code-complete לסיכום הבסיסי).
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
מרחיב את TASK-48: TASK-48 מספק את שכבת הסיכום (build_weekly_row/monthly_row — WR/TotalPnL/AvgWin/AvgLoss, code-complete 30/5). TASK-73 מוסיף מעליו את שכבת הניתוח-עומק (Profit Factor/Expectancy/MaxDrawdown, קורלציות מדורגות, counterfactual סוכנים, דגלים אוטומטיים, דוח research). שני החלקים יחד = הניתוח האוטומטי המלא.

אישור-חקירה (צ'אט 2026-06-27, READ-ONLY): ה-Critic חי ומחווט (3 workflows יומי/שבועי/חודשי + מייל + agent_scorecard) — לא להסיר. score_analytics=0 שורות = downstream של MetricsAtEntry-ריק (TASK-65), לא Critic מת.
<!-- SECTION:NOTES:END -->
