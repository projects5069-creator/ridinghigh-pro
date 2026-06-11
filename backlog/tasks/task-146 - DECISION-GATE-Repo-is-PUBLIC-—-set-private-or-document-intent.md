---
id: TASK-146
title: '[DECISION GATE] Repo is PUBLIC — set private or document intent'
status: Done
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-11 04:27'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 149000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV RH-5.5: gh repo view -> isPrivate=false. All code+backlog+Sheet IDs exposed (credentials NOT in git, verified). Going private costs Actions minutes: ~12k min/month usage vs 2k free quota. DECISION = Amihay: private (and fund minutes) or stay public deliberately + document in PK
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 DECISION 2026-06-10 (Amihay): repo STAYS PUBLIC for now, but research CSVs removed from tracking (git rm --cached + local .gitignore *.csv in INVESTIGATION_2026-06-10; files remain on disk). NOTE: git HISTORY still contains the CSVs (commit 5b34304) — full scrub deferred to the new private-migration task
<!-- AC:END -->
