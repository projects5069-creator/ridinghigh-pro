---
id: TASK-45
title: AUDIT.10 — Cleanup obsolete tracked files
status: To Do
assignee: []
created_date: '2026-05-24 22:00'
labels: []
dependencies: []
priority: low
ordinal: 45000
---
## Description
<!-- SECTION:DESCRIPTION:BEGIN -->
Claude Project capacity at 32%, approaching RAG threshold. Reduce file count + capacity by archiving or deleting obsolete files that are still tracked in git.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes
<!-- SECTION:NOTES:BEGIN -->
Candidates: mark_score_version.py, apply_text_format_v1.py, setup_health_audit_sheet.py, upload_enriched_pa_v3.py (one-shot scripts). OPEN_ISSUES_archive.md, NEXT_SESSION.md, README_health_audit.md (obsolete docs). research/2026-05-05_phase1_day1/ (Phase 1 snapshots). For each: verify not imported, git rm, update PK if needed.
<!-- SECTION:NOTES:END -->
