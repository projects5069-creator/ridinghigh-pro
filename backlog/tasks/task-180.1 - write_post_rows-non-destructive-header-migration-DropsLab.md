---
id: TASK-180.1
title: write_post_rows non-destructive header migration (DropsLab)
status: To Do
assignee: []
created_date: '2026-06-17 15:12'
labels:
  - data-integrity
dependencies: []
parent_task_id: TASK-180
priority: high
ordinal: 188000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
write_post_rows (DropsLab drops_collector.py:250-253) calls ws.clear() on any header mismatch -> any POST_HEADER change wipes all ~3733 historical drops_post rows on the next collector run. Footgun + the gate for Option A (persisted interday_artifact column, TASK-90/148/173). Fix: port ensure_grid_width to DropsLab gsheets_sync.py and rewrite write_post_rows to migrate the header in-place (update row 1 only, never clear), with an append-only guard (old header must be a prefix of new) + an RH-style data-loss abort guard. Stage 1 only (footgun fix); Option A column is a follow-up.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 write_post_rows never calls ws.clear() on header drift; in-place migration preserves existing rows (mocked-ws test)
- [ ] #2 append-only guard raises on reorder/removal; data-loss abort guard raises on wide-grid-but-empty-values (both before any destructive op)
- [ ] #3 POST-MARKET (RULE #6): a normal live run preserves row-count >=3733 (no-regression; migration branch exercised live in Stage 2)
<!-- AC:END -->
