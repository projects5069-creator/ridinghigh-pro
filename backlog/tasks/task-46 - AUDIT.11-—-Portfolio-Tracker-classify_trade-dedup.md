---
id: TASK-46
title: AUDIT.11 — Portfolio Tracker classify_trade dedup
status: Done
assignee: []
created_date: '2026-05-25 10:25'
updated_date: '2026-06-23 00:01'
labels: []
dependencies: []
priority: low
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Portfolio Tracker (dashboard.py:2043-2089, _simulate_short_trades) has its own D1->D5 first-touch classification logic instead of calling utils.classify_trade_row. Violates Single Source of Truth (PK Iron Rule §10). Not a bug — produces a legitimately different metric (whipsaws counted as losses vs canonical which excludes them) — but code duplication candidate.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Discovered during task-44 (AUDIT.9). Full audit: research/2026-05-25_winrate_audit.md.

Approach: refactor _simulate_short_trades to call classify_trade_row, then apply "whipsaws-as-losses" as display-time decision in the simulator. This keeps the Portfolio Tracker metric (55.8%) intact but eliminates the duplicate classification logic.

Acceptance criteria:
- _simulate_short_trades uses classify_trade_row internally
- Portfolio Tracker still shows 55.8% (or close to it — whipsaws still count as losses)
- No regression in any other dashboard page

Estimated effort: 1h.
Priority: LOW — code quality, not user-facing bug.
<!-- SECTION:NOTES:END -->
