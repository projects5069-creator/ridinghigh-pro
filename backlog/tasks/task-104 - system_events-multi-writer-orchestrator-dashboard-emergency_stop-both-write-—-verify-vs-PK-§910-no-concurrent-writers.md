---
id: TASK-104
title: >-
  system_events multi-writer: orchestrator + dashboard emergency_stop both write
  — verify vs PK §910 no-concurrent-writers
status: Done
assignee: []
created_date: '2026-06-03 00:58'
updated_date: '2026-06-04 16:41'
labels: []
dependencies: []
priority: low
ordinal: 104000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Discovered during TASK-64 recon (2026-06-02): system_events Sheet is written by agent/orchestrator.py (pipeline events) AND agent/dashboard/_data_loaders.py::log_emergency_stop() (user EMERGENCY_STOP from dashboard). PK §910 states Read-once write-once, no concurrent writers. Verify: is this a real §910 violation or benign (different event types, emergency_stop is a rare manual action)? Decide: document the dual-writer as allowed exception, or refactor. Low priority — emergency_stop M9 only logs (M10 will add halt). Source: docs/DATA_SOURCES_MAP.md.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Audit 4/6: BENIGN, not a §910 violation. Writers: dashboard log_emergency_stop (append_row, manual/rare) + orchestrator_eod._system_events_alert (safe_append_row, EOD). orchestrator.py READ-ONLY (premise that it writes pipeline events was WRONG). All append-only → atomic server-side, no RMW clobber → concurrent appends benign. Documented as allowed exception in PK §910 (line ~1079). No refactor needed.
<!-- SECTION:NOTES:END -->
