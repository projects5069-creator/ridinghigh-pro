---
id: TASK-184
title: 'tests: hermetic clock for test_task172_coverage union test'
status: Done
assignee: []
created_date: '2026-06-16 14:06'
updated_date: '2026-06-16 15:23'
labels: []
dependencies: []
priority: high
ordinal: 187000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
CI 'tests' workflow red on main since 6/15 date rollover. test_collect_borrow_snapshot_union_and_coverage hardcodes fixture date 2026-06-14 but collect_borrow_snapshot filters daily_snapshots by utils.get_peru_time() (real today), so scanned universe empties on any other day. Fix: freeze clock to 2026-06-14 in the test (test-only, zero prod change). Also flagged: same file hardcodes 2026-06-14 at L41-43/L116-119 (not date-filtered, still green) — fragile pattern for review.
<!-- SECTION:DESCRIPTION:END -->
