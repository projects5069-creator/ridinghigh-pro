---
id: TASK-112
title: >-
  Add read-counter to auto_scanner (mirror agent Phase 1) — enable live
  verification of timeline_live 4->2 (Phase 2 S1)
status: Done
assignee: []
created_date: '2026-06-04 17:29'
updated_date: '2026-06-04 17:52'
labels: []
dependencies: []
priority: low
ordinal: 112000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Currently timeline_live 4->2 is code-confirmed only (v2.70: _read_timeline_live via 60s cache + invalidate_cache after write), NOT live-confirmed — auto_scanner emits no read-counter (Phase 1 counter was agent-only). Add a per-run Sheets-API read summary line to auto_scanner (mirror orchestrator.py:779) so timeline_live cache-miss count is observable in the scanner log. Then verify 4->2 live.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Done 2026-06-04. Acceptance met: per-run read-counter added to auto_scanner __main__ and verified LIVE (run 26969287592 17:47Z post-deploy; absent at 17:45 pre-deploy). Live finding: timeline_live=1 cache-miss/run, total=1 — caching effective, Phase 2 S1 goal (lower API pressure) achieved. CAVEAT: counter measures cache-MISSES not raw reads; v2.70 4->2 raw-read claim not literally observable via this counter.
<!-- SECTION:NOTES:END -->
