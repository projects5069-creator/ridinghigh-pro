---
id: TASK-191
title: >-
  Quota C3 — merge timeline_live double-read (signal-reader :350 +
  outage-detection :404) into one passed-through result
status: Done
assignee: []
created_date: '2026-06-24 14:11'
updated_date: '2026-06-24 20:04'
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
DONE 2026-06-24 (read-only recon, no code). Premise WEAKENED — the 60s read-cache already collapses the double-read to 0 extra API calls: detect_outage (orchestrator.py:404, called :485) populates the timeline_live cache; read_latest_signals (:350, called :655) is a same-run cache HIT (timeline_live is not written by the orchestrator, so no invalidation between them). A real 2nd API call would need a run >60s between :485 and :655 (never — runs are seconds). The merge would be a 2-function-signature refactor (thread shared records into detect_outage+read_latest_signals) on the life-line, for ~0 API savings (CPU micro-opt only). Logically safe (same snapshot, no logic/read change) but zero-value + regression risk on the life-line. Closed like 149/168 (premise disproven). The C3 audit row in QUOTA_AUDIT_agent_minute_2026-06-24.md already noted 'usually 1 API call'.
<!-- SECTION:NOTES:END -->
