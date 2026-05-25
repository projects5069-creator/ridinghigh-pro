---
id: TASK-47
title: AUDIT.12 — portfolio sheet deprecation audit
status: To Do
assignee: []
created_date: '2026-05-25 10:25'
labels: []
dependencies: []
priority: low
ordinal: 47000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The portfolio sheet (6 cols: PositionKey, Date, Ticker, Score, BuyPrice, Status) has 65 rows all status=Open with no PnL/Exit columns. Read only twice in dashboard.py (lines 1019 and 2819) — once as fallback in _cached_portfolio (Issue #PORT-MONTH), once in Score Tracker page as a ticker list. Not used by any WR computation. Candidate for deprecation if confirmed dead weight.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Discovered during task-44 (AUDIT.9). Full audit: research/2026-05-25_winrate_audit.md.

Investigation steps:
1. Who writes to portfolio sheet? (auto_scanner.update_live_trades per PK §14, but verify against actual code)
2. Does Score Tracker page actually USE the data, or just load it? (line 2819 reads, but is the output displayed?)
3. If dead — git rm the sheet creation from sheets_manager.py? Or just stop populating it?
4. Update sheets_config.json if removed.

Acceptance criteria:
- Definitive answer: dead or alive?
- If dead — deprecation plan with backward compat for old months
- If alive — document its actual purpose in PK §14

Estimated effort: 30min.
Priority: LOW — disk/quota cleanup, not user-facing.
<!-- SECTION:NOTES:END -->
