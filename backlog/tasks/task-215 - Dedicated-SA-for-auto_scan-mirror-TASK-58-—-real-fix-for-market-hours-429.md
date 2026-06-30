---
id: TASK-215
title: Dedicated SA for auto_scan (mirror TASK-58) — real fix for market-hours 429
status: To Do
assignee: []
created_date: '2026-06-30 17:53'
labels:
  - quota
  - market-hours
  - service-account
  - task-214-followup
dependencies: []
priority: medium
ordinal: 221000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Recon 30/6 (TASK-214 deep-recon) proved read de-dup is NOT the fix for auto_scan 429: portfolio de-dup saves only ~1 read/5min (line 510 writes portfolio between reads, breaks cache), and most per-minute reads are write-accompanied (not cache-able). The architecturally correct fix mirrors TASK-58 (which solved health_audit's 429 via dedicated SA + ROOT folder inheritance): give auto_scan its own SA so it stops competing on the shared commercial SA quota (project 591299446687). AC#1: create dedicated auto_scan SA in GCP. AC#2: share ROOT folder with it (inherits all tabs, incl future months — same as TASK-58). AC#3: point auto_scanner gc to its own credential (env var + truthy-guard fallback, same pattern as TASK-58 health_audit). AC#4: inject secret in auto_scan.yml. AC#5: verify live — 429 frequency drops + 'cancelled' overlap runs drop. evidence: auto_scan 429-crashed live 30/6 12:22+12:42 Peru. NOTE: auto_scan is the LIVE TRADING data path — higher stakes than health_audit; needs careful verify. NOTE: TASK-214 de-dup track CLOSED (documented in QUOTA_AUDIT_auto_scan_v1.md REVISED FINDING).
<!-- SECTION:DESCRIPTION:END -->
