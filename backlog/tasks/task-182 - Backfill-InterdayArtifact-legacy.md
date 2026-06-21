---
id: TASK-182
title: Backfill InterdayArtifact on legacy post_analysis rows
status: Done
assignee: []
created_date: '2026-06-15 13:17'
updated_date: '2026-06-21 16:55'
labels:
  - data-integrity
dependencies: []
ordinal: 185000
---

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
§0 closed in a2bd740 (2026-06-16): _coerce_bool now reads numeric-truthy ('1.0'->True). Remaining = backfill of 128-NaN/51-blank InterdayArtifact column (live-write, post-market). Stays To Do.

FINDING 2026-06-21 (D1 recon): real leak confirmed. exclude_interday_artifacts is column-dependent (cross_month_loaders.py:140 reads InterdayArtifact via _coerce_bool). 128 NaN + 51 blank legacy post_analysis rows coerce to False -> not excluded -> leak into aggregates AND health_audit Check 29 (under-reports contamination%). Upgrades 182 from cosmetic to active data-integrity leak. Fix: backfill_interday_v1.py dry-run -> diff -> live write post-market.

RESOLVED 2026-06-21 via Path 2 (loader recompute-on-missing in exclude_interday_artifacts, not sheet backfill). Closes leak in aggregates + Check 29 (0.47%->4.25% correct). code-only, no live write. Sheet-backfill (Path 1) left as optional cosmetic cleanup, not required.
<!-- SECTION:NOTES:END -->
