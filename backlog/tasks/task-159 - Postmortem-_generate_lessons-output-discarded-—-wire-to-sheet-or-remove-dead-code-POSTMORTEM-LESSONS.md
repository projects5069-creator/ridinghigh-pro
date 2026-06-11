---
id: TASK-159
title: >-
  Postmortem _generate_lessons output discarded — wire to sheet or remove dead
  code [POSTMORTEM-LESSONS]
status: To Do
assignee: []
created_date: '2026-06-11 18:28'
updated_date: '2026-06-11 18:29'
labels:
  - TASK-134-followup
dependencies: []
priority: medium
ordinal: 162000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found in TASK-134 group F recon (empirically verified). postmortem_engine.py:104 computes lessons = self._generate_lessons(...) but the postmortem dict (115-133) has NO lessons field → the variable is discarded (dead). AutoLessons (line 130) = _build_forensic_prose (Hebrew prose: RSI-vs-winner/toxic, triggers, MFE/MAE) which does NOT contain the 7 rule strings (High ATRX / RSI 90+ / fast-outcome / extending-hold). Result: the 7-rule insights never reach the postmortems sheet; _generate_lessons still runs (verified) but output is lost. PK 3240-3262 + 687 still claim '7 auto-lesson rules' — drift vs reality (AutoLessons=prose).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 POLICY DECISION FIRST (ping-pong, not auto): was _build_forensic_prose meant to REPLACE the 7 rules or ADD to them? Recon commit cce6c12 to determine intent (replace vs augment)
- [ ] #2 If REPLACE: delete dead _generate_lessons + line 104; update PK 3240/687 to 'AutoLessons = Hebrew forensic prose' (remove 7-rules claim)
- [ ] #3 If ADD: wire _generate_lessons output to a sheet field (schema change) or append to prose; ensure PK matches
- [ ] #4 Anti-Drift PK either way (3240/687); then TDD test asserting the chosen behavior
<!-- AC:END -->
