---
id: TASK-185
title: non-hermetic borrow-wiring tests hit live daily_snapshots
status: To Do
assignee: []
created_date: '2026-06-16 20:41'
labels: []
dependencies: []
priority: medium
ordinal: 188000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
tests/agent/unit/test_orchestrator_eod_borrow_wiring_v1.py: test_collects_unified_deduped_tickers_and_passes_to_collector + test_no_tickers_skips_collector_and_does_not_fail patch account/broker/collect but NOT sheets_manager.get_worksheet. After TASK-172 wired the scanned-universe (daily_snapshots) source into collect_borrow_snapshot, these read LIVE Sheets -> fail locally during market hours when daily_snapshots has rows (observed 2026-06-16: collect called with ['CRVO','VNCE']). Family of TASK-184 (non-hermetic, live-state dependent). Pass in CI (no creds -> get_worksheet fails -> caught -> scanned empty). Proven pre-existing via git stash on clean HEAD. Fix: mock sheets_manager like the sibling test at line 82-84 (patch('agent.perception.borrow_collector.sheets_manager', sm)). LANDMINE: green in CI, red locally with creds during market hours.
<!-- SECTION:DESCRIPTION:END -->
