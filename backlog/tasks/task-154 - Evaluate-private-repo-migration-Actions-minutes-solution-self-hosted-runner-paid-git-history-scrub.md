---
id: TASK-154
title: >-
  Evaluate private-repo migration: Actions minutes solution (self-hosted runner
  / paid) + git history scrub
status: To Do
assignee: []
created_date: '2026-06-11 04:26'
updated_date: '2026-07-02 19:09'
labels:
  - TASK-139-INV
dependencies: []
priority: medium
ordinal: 157000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up to decision 4 (2026-06-10): repo stays public for now, CSVs untracked but PRESENT IN HISTORY (5b34304). Evaluate: private + self-hosted runner vs paid minutes (~12k min/month vs 2k free); git history scrub (filter-repo) for research CSVs; strategy exposure tradeoff. Ties task-146 (Done)
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Recon 2026-07-02: recommend NOT migrating now. (1) No leaked secrets — 0 pasted creds, 0 PRIVATE KEY in 998 commits; LEGACY_SPREADSHEET_ID exposes existence only (auth-gated). (2) Real exposure is PK/REPORT markdown (strategy verdicts: Score-kill r~-0.02, WR 53-55%, negative edge) — NOT the 17 research CSVs the task targets; scrubbing CSVs alone misses it. (3) Cost concrete: private breaks free Actions -> per-minute workflow busts 2000min cap -> needs self-hosted runner or paid; history-scrub = force-push rewriting 998 commits, breaks all hash-refs in docs/PK/backlog. Mitigator: research verdict is mostly negative/noise -> little real edge to protect. Re-scope: decision is all-or-nothing (full private incl PK + self-hosted runner), not half-step CSV scrub. Keeping To Do, evaluated-not-actioned.
<!-- SECTION:NOTES:END -->
