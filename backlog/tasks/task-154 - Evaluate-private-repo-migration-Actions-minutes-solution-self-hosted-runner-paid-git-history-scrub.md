---
id: TASK-154
title: >-
  Evaluate private-repo migration: Actions minutes solution (self-hosted runner
  / paid) + git history scrub
status: Done
assignee: []
created_date: '2026-06-11 04:26'
updated_date: '2026-08-04 00:50'
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

## WON'T-DO 2026-08-04

Closed without doing the work. The recommendation this task was opened to produce was already produced, on 2026-07-02, and it was not to migrate.

The three findings that decided it, all from that recon and all measured rather than assumed. There are no leaked secrets: zero pasted credentials and zero PRIVATE KEY across 998 commits, and LEGACY_SPREADSHEET_ID exposes existence only behind auth. The real exposure is not what this task targets: it is the PK and the report markdown, which carry the strategy verdicts, and scrubbing the 17 research CSVs alone misses all of it. And the cost is concrete: going private breaks free Actions minutes so a per minute workflow busts the 2000 minute cap and needs a self hosted runner or paid minutes, while a history scrub is a force push rewriting 998 commits that breaks every hash reference in the PK, the docs and the backlog.

The mitigating fact recorded there still holds: most of the research verdict is negative or noise, so there is little real edge to protect.

WHAT WOULD REOPEN THIS: a decision to go fully private including the PK, together with a self hosted runner. That is an all or nothing move and it is an owner decision, not a task. The half step this task describes, scrubbing CSVs, has been shown to solve nothing.
