---
id: TASK-210
title: Minimal entry gate - MxV+price+quality only
status: Done
assignee: []
created_date: '2026-06-30 00:31'
updated_date: '2026-06-30 02:06'
labels: []
dependencies: []
ordinal: 216000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ENTRY_GATE_MINIMAL disables 6 quality-filters (RunUp/Volume/Blacklist/Toxic/MarketCap/ROCKET), leaving MxV<=-100 + price>=3 + quality + integrity-rails. Reversible (flag off=all return). Re-entry 3->1. Owner decision; future investigations decide whether to re-add disabled filters or add new metrics.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 ENTRY_GATE_MINIMAL flag wraps the 6 filters; off restores all (TDD)
- [x] #2 MxV + price + quality + safety-rails stay ON under minimal
- [x] #3 AGENT_MAX_REENTRIES_PER_TICKER 3->1 (only first scanner appearance enters)
- [x] #4 7 default-dependent tests pinned minimal=False; full regression green except 2 pre-existing
- [x] #5 PK + ADR updated; live-verify tomorrow that entries match MxV+price population
<!-- AC:END -->
