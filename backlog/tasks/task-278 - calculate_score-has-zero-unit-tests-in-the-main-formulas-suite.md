---
id: TASK-278
title: calculate_score has zero unit tests in the main formulas suite
status: To Do
assignee: []
created_date: '2026-08-08 18:18'
labels: []
dependencies: []
priority: medium
ordinal: 276000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
FOUND 2026-08-08 while mapping Score (rhpro_audit_run/SCORE_MAP_2026-08-08.md). test_formulas.py defines 18 test functions and runs 125 assertions, and NOT ONE of them touches calculate_score: grep -ic score test_formulas.py returns 0. The scorer that gated every entry until 2026-06-29, and still orders the scan output at auto_scanner.py:429, has never had a unit test in the main suite. What does exist is peripheral: tests/test_rsi_scoring_v1.py covers the RSI ladder only, tests/test_score_gate_flip_v1.py and tests/agent/unit/test_explicit_gate_score_skippable_v1.py cover the gate switch rather than the arithmetic, and tests/test_stage0_score_writers_v1.py plus tests/test_stage1_score_freeze_v1.py cover the freeze. The formula itself - seven weighted components, each wrapped in a bare try/except that contributes 0 on a missing metric - is unverified. WHY IT MATTERS EVEN THOUGH SCORE IS BEING RETIRED: the removal happens in two stages and the behaviour stage waits until after 2026-09-04. Until then the code is live and any refactor near it has no safety net; and the retirement itself needs a before/after equivalence check that requires a characterisation test to exist first. ACCEPTANCE: (1) a test module asserting the documented weight/cap contract - MxV 25 cap 200 negative-only, RunUp 25 cap 30 positive-only, ATRX 20 cap 5 always, RSI ladder 90/85/80 to 10/7/4 else 0, TypicalPriceDist 10 cap 8 positive-only, ScanChange 5 cap 60 positive-only, REL_VOL 5 cap 15 always - each verified at, below and above its cap; (2) a test that a metric missing from the dict contributes exactly 0 rather than raising, which is the current silent behaviour of the seven try/except blocks; (3) a test that a full-marks input returns 100.0 and an empty dict returns 0.0; (4) the suite runs clean and the existing 747 + 125 + 38 baseline does not regress. NOT IN SCOPE: do not change calculate_score, the weights or the caps - this is characterisation only, pinning what the code does today, not what it should do. Related: TASK-208 and TASK-209 own the retirement; DECISIONS_2026-08-08 records that the weights 25/25/20/10/10/5/5 were never justified in writing.
<!-- SECTION:DESCRIPTION:END -->
