---
id: TASK-189
title: >-
  score_backtest.py uses stale bell-curve RSI — align to overbought-only or mark
  research-only
status: To Do
assignee: []
created_date: '2026-06-22 17:08'
labels:
  - rsi
  - drift
  - backtest
  - data-quality
dependencies: []
priority: low
ordinal: 195000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
score_backtest.py:73-79 + :125-131 score RSI as a bell-curve (sweet-spot 60-70) — the OLD shape removed from production (formulas.calculate_score is overbought-only since TASK-188/c0bc60c). The file is isolated: no .py imports it, not in any workflow, classified CORE_UNSAFE (tests/overnight/test_core_unsafe.py:45) → does NOT affect live trading. BUT running this backtest scores RSI differently from production = mismatched research results (data-quality). Spin-off from TASK-129 (its scope did not include this file).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Decide: align the RSI formula in score_backtest.py to overbought-only (match formulas.calculate_score), OR add a header comment marking it an intentional historical/research scorer
- [ ] #2 If aligned: verify no other RSI scorer leaks (grep bell-curve in .py = comments only)
<!-- AC:END -->
