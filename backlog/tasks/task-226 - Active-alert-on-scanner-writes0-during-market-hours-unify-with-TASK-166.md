---
id: TASK-226
title: Active alert on scanner-writes=0 during market hours (unify with TASK-166)
status: To Do
assignee: []
created_date: '2026-07-04 01:49'
labels: []
dependencies: []
priority: medium
ordinal: 232000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S3 (3/7): a scanner run that produces 0 rows during market hours is SILENT — auto_scanner.py:65 'No results' path prints and continues; the only detector is sentinel scan_freshness (WARN>=3m/BLOCK>=5m, checks/scan_freshness.py:8-9) which in shadow mode only logs; nothing alerts until nightly health_audit. Write-EXCEPTIONS are already loud (safe_append_rows raise). Needed: an active alert (system_events/email) when timeline_live gets 0 new rows for N consecutive market-hours minutes. Natural home: unify with TASK-166 (daily lineage sentinel). Evidence: plans/stateless-seeking-sifakis.md S3.
<!-- SECTION:DESCRIPTION:END -->
