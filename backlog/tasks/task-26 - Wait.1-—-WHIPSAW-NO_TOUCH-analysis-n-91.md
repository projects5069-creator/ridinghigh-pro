---
id: TASK-26
title: Wait.1 — WHIPSAW + NO_TOUCH analysis (n>91)
status: Done
assignee: []
created_date: '2026-05-23 19:35'
updated_date: '2026-06-12 21:16'
labels: []
dependencies: []
priority: medium
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigate WHIPSAW and NO_TOUCH trade categories. BLOCKED on data: currently n=62, need n>91 for statistical significance. Expected unblock: end of May 2026.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 RESOLVED by TASK-155 minute-bars (2026-06-12): the 26 WHIPSAW resolve to 8 WIN / 17 LOSS / 1 UNRESOLVED (XNDU, one-side-only on IEX). resolver=utils.resolve_whipsaw, cache=intraday_cache; per-row CSV in docs/research/WHIPSAW_RESOLUTION_2026-06-12/. WHIPSAW skew strongly negative (68% LOSS) — confirms RH-6.3 edge concern.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-12. WHIPSAW half resolved via TASK-155 (8W/17L/1U, resolved WR 49.2%, skews negative=RH-6.3). NO_TOUCH half: n=3 (SBLX/ARKR/OSS), too few to analyze — qualitative only: all low-Score near the 60 threshold (61-66), consistent with the weak-signal hypothesis (Score is the signal). Characterization study (offline, docs/research/TASK26_WHIPSAW_CHARACTERIZATION_2026-06-12/, gitignored): WHIPSAW vs decided WIN/LOSS entry-metric medians — WHIPSAW *relatively* more extended (RunUp +82% / Gap +45% / ATRX +19% vs decided; REL_VOL -27% / Float -19%). EXPLORATORY n=26 LOW (tier 10-29) — a HYPOTHESIS, not a validated filter; no trade decision on this. Any whipsaw-prone filter requires re-run on n>50 with a proper separation test = a FUTURE task (not a reopen of 26). Data blocker (n>91) lifted (n=128). Zero code/trading change.
<!-- SECTION:NOTES:END -->
