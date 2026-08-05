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
E2E-audit S3 (3/7): a scanner run that produces 0 rows during market hours is SILENT — auto_scanner.py:65 'No results' path prints and continues; the only detector is sentinel scan_freshness (WARN>=3m/BLOCK>=5m, checks/scan_freshness.py:8-9) which in shadow mode only logs; nothing alerts until nightly health_audit. Write-EXCEPTIONS are already loud (safe_append_rows raise). Needed: an active alert (system_events/email) when timeline_live gets 0 new rows for N consecutive market-hours minutes. NOT covered by TASK-166 (verified 2026-08-05, 166 is Done). check_30_lineage_sentinel (health_audit.py:1339) recomputes ONE random settled post_analysis row and WARNs on field drift; an empty sheet returns INFO "post_analysis is empty", i.e. zero rows is a reason to SKIP, not to alert. It never reads timeline_live and never runs during market hours (health_audit fires 06:00 / 15:30 / 22:00 Peru). Nearest overlap is TASK-252 check three (today's row count vs trailing 5-day average) — but that is nightly, on post_analysis, and threshold-based. This ticket is the intraday half: timeline_live, N consecutive market-hours minutes at zero, alert to system_events + email. Keep both; sequence 252 first if only one gets built. Evidence: plans/stateless-seeking-sifakis.md S3.
<!-- SECTION:DESCRIPTION:END -->
