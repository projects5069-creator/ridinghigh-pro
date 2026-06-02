---
id: TASK-84
title: Health Audit exits 1 on missing health_audit_sheet_id in CI
status: Done
assignee: []
created_date: '2026-05-31 18:27'
updated_date: '2026-06-02 04:38'
labels:
  - bug
  - ci
  - health-audit
dependencies: []
priority: high
ordinal: 84000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Since 2026-05-31 (was green 5/30 17:59) Health Audit runs fully but exits 1: '.health_audit_sheet_id' (gitignored local file) not found in CI -> 'CRITICAL issues detected' + alert email on every run. Masks real audit findings. Surfaced after the checkout blocker was fixed (commit e7dc0dd; run 26720225139, 1m1s, all checks passed except this). TODO: find which commit introduced it; either provision/commit the sheet id in CI, or make the check non-fatal/skip in CI like the PK-sync check (#19).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root commit identified
- [x] #2 Health Audit returns success (exit 0) on CI
- [x] #3 No more false CRITICAL alert emails
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Already-resolved. Task premise disproven: sheet_id read only in write_to_sheet (warning, never affects exit). Real exit1 = check_06 (Actions success<80%) firing on long-Hebrew-filename checkout failures from 5/31 - a true alarm, not a bug. Root fixed by e7dc0dd + TASK-85 guard; success back to 100% (self-healed). No code touched - the requested 'fix' would be silent-failure alarm suppression.
<!-- SECTION:FINAL_SUMMARY:END -->
