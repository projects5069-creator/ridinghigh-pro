---
id: TASK-123
title: >-
  backfill_ohlc_v2 — month param + any-D trigger: סגירת 70 ה-stale-PENDING של
  אפריל-מאי
status: Done
assignee: []
created_date: '2026-06-10 01:03'
updated_date: '2026-06-10 01:55'
labels: []
dependencies: []
priority: high
ordinal: 126000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Two blockers in current tool: loads active month only (gsheets_sync.py:48,357) + trigger=D1_Open-missing only (backfill_ohlc.py:76-77) so 51/70 invisible. New versioned script per §12: month arg passed to load/save + trigger on ANY missing D{i}. Run off-hours for 2026-04 then 2026-05. ~70 Alpaca fetches + full-sheet upsert per month (guard exists gsheets_sync:289-300). Delisted tickers will stay PENDING — mark them.
<!-- SECTION:DESCRIPTION:END -->
