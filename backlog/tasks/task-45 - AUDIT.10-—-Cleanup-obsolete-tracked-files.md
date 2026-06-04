---
id: TASK-45
title: AUDIT.10 — Cleanup obsolete tracked files
status: Done
assignee: []
created_date: '2026-05-24 22:00'
updated_date: '2026-06-04 15:18'
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
Done 4/6. Removed 5 (mark_score_version, upload_enriched_pa_v3, OPEN_ISSUES_archive, NEXT_SESSION, README_health_audit; 975 lines). KEPT 2 the task wrongly labeled one-shot: apply_text_format_v1.py (LIVE in prepare_next_month.yml:42) + setup_health_audit_sheet.py (recovery path in health_audit.py). Fixed dangling refs. research/ 67MB deferred.
<!-- SECTION:NOTES:END -->
