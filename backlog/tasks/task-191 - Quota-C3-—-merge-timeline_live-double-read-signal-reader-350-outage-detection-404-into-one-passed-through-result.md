---
id: TASK-191
title: >-
  Quota C3 — merge timeline_live double-read (signal-reader :350 +
  outage-detection :404) into one passed-through result
status: To Do
assignee: []
created_date: '2026-06-24 14:11'
labels:
  - agent
  - infra
  - quota
dependencies: []
priority: medium
ordinal: 197000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Spawned by TASK-136 audit (docs/QUOTA_AUDIT_agent_minute_2026-06-24.md). orchestrator reads timeline_live twice per run via get_sheet_records (orchestrator.py:350 signal reader, :404 outage detection). Both 60s-cached so usually 1 API call, but the second is redundant. Pass the signal-reader result into outage detection instead of re-reading. timeline_live is the life-line — keep the single authoritative fetch; only remove the duplicate. Each cut = own PING-PONG commit.
<!-- SECTION:DESCRIPTION:END -->
