---
id: TASK-139
title: >-
  Activate borrow_data daily collection (sheet empty) via Alpaca
  shortability+fee [BORROW]
status: In Progress
assignee: []
created_date: '2026-06-11 04:01'
updated_date: '2026-06-11 16:01'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 142000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-3.1/RH-6.3: borrow_data 2026-05+06 have 0 rows (verified live); tradability fully mocked in DRY_RUN (is_shortable=True, borrow_fee=12.5 const). Real fees are the missing input for the cost model — edge breakeven ~388pct/yr. Evidence: docs/research/INVESTIGATION_2026-06-10/phase3_evidence.md + phase6_evidence.md
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 borrow_collector.py: per active ticker call broker.get_asset_info() and fill IsShortable / IsETB(=easy_to_borrow) / IsHTB(=shortable AND NOT ETB) / Source=ALPACA / CheckDate+CheckTime (Peru tz)
- [ ] #2 BorrowFeePct = explicit NULL (empty cell — not 12.5 nor 0.0; Alpaca exposes no fee). SharesAvailable = value only if exposed by API else NULL
- [ ] #3 Batched write: one row per ticker per day; a single safe_append_rows at end of collection (NOT per-ticker-per-minute); dedup on (Ticker CheckDate)
- [ ] #4 Non-fatal: any broker/Sheets failure -> try/except + log; never crashes orchestrator; not counted as error (same model as flush_skip_summary)
- [ ] #5 Wiring: one call/day from orchestrator_eod (16:00 Peru) with already-written-today guard; ZERO change to ENTER/SKIP logic
- [ ] #6 DRY_RUN: collector reads REAL Alpaca (read-only get_asset) even under AGENT_DRY_RUN, else tab fills with mock; credentials already in env
- [ ] #7 Schema: 9 existing columns Ticker/CheckDate/CheckTime/IsShortable/IsETB/IsHTB/BorrowFeePct/SharesAvailable/Source
<!-- AC:END -->
