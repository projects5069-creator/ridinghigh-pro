---
id: TASK-62
title: >-
  ניתוח רחב למיילים: per-trade לפי תאריך + פירוק MxV/ATRX/Gap/Volume נצחונות מול
  הפסדים + פירוק סוכנים + תובנות שיפור (חסום חלקית על n>91)
status: To Do
assignee: []
created_date: '2026-05-30 22:18'
updated_date: '2026-07-02 21:11'
labels: []
dependencies: []
priority: medium
ordinal: 62000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Measured 2026-07-02 (n=229 joined closed trades, analyze_trades_vix_v1.py): MxV WIN mean -1315/med -698 vs LOSS mean -1395/med -559 — no monotonic separation, median inverted. ATRX WIN 5.00 vs LOSS 4.90 — negligible. Conclusion: MxV/ATRX do NOT predict per-trade outcome in this data. Consistent with TASK-199 (MxV = candidate-selection engine not per-trade predictor; ATRX = noise). Null result — documented.
<!-- SECTION:NOTES:END -->
