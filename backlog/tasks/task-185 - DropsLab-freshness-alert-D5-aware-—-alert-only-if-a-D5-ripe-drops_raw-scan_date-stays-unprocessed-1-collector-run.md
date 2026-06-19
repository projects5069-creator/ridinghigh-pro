---
id: TASK-185
title: >-
  DropsLab freshness alert: D5-aware — alert only if a D5-ripe drops_raw
  scan_date stays unprocessed >1 collector run
status: Done
assignee: []
created_date: '2026-06-18 22:36'
updated_date: '2026-06-19 13:19'
labels:
  - data-integrity
dependencies: []
priority: medium
ordinal: 191000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Replaces the naive >2d staleness idea (TASK-183 was a false alarm caused by that naive check). A correct freshness monitor must account for the D5-ripeness window: drops_post legitimately lags drops_raw by ~5 trading days. Alert ONLY when a scan_date that is D5-ripe in drops_raw (5 trading days passed) remains absent from drops_post after >1 collector run — that distinguishes a real stall from the expected structural lag. Compare drops_raw vs drops_post per ripe scan_date.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Alert fires only for a D5-ripe scan_date missing from drops_post after >1 collector run (not for in-window lag)
- [ ] #2 No false-positive on the normal D5 lag (drops_post newest ~5 trading days behind today)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done 2026-06-19. D5-aware freshness monitor + main() wiring landed in DropsLab repo, commit 1ed640b (pushed). report_stale_freshness/freshness_exit_code reuse trading_days_after (calendar SSoT). Alert (log.warning + sys.exit(1)) fires only when a D5-ripe scan_date (5 trading days + 1-day grace = >1 collector run) is absent from drops_post; runs after all normal work on every live path incl. 'nothing new', post-state = pre-run keys ∪ this-run writes; dry-run skipped. AC#1+AC#2 covered by 11 tests (test_freshness_alert_v1.py); full suite 46 passed, py_compile clean. DropsLab PK draft bumped. Live-observe: first scheduled collector run will exercise the gate (no code pending).
<!-- SECTION:NOTES:END -->
