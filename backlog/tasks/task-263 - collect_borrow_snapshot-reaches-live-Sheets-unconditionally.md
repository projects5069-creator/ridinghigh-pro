---
id: TASK-263
title: collect_borrow_snapshot reaches live Sheets unconditionally
status: To Do
assignee: []
created_date: '2026-08-06 14:37'
updated_date: '2026-08-06 14:37'
labels:
  - bug
  - testability
  - agent
  - task-262-followup
dependencies: []
priority: high
ordinal: 261000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
orchestrator_eod.py:54 imports sheets_manager inside the function, :57 reads daily_snapshots and :95 calls collect_borrow_coverage which appends a row to borrow_coverage. Neither is injectable, so a test cannot close the path without patching the layer itself. TASK-262 neutralised it in tests/ only and marked the invariant test xfail strict. The fix is to inject the reader/writer and then delete the xfail.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Found during the TASK-262 build, 2026-08-06. Full evidence:
reports/2026-08-06_0923_task262_build.md and reports/2026-08-06_0934_task262_land.md.

THE DEFECT. collect_borrow_snapshot reaches the Sheets layer unconditionally, with no
seam a caller or a test can close:

  agent/orchestrator_eod.py:54   import sheets_manager            (its own import)
  agent/orchestrator_eod.py:57   ws = sheets_manager.get_worksheet("daily_snapshots")
  agent/orchestrator_eod.py:59   vals = ws.get_all_values()
  agent/orchestrator_eod.py:70   universe = scanned | existing
  agent/orchestrator_eod.py:95   cov = borrow_collector.collect_borrow_coverage(universe)
                                 -> reads borrow_data, APPENDS a row to borrow_coverage

Everything else in the helper is injectable in practice: build_account_state, AlpacaBroker
and collect_borrow_data are all reachable as patch targets. These two are not — the module
is imported inside the function body, so the name resolves at call time against the real
sheets_manager, and collect_borrow_coverage is a different function from
collect_borrow_data, which is the one the existing tests patch.

WHAT IT COST. The unit tests for this helper wrote rows to the live borrow_coverage tab on
every run. Measured 2026-08-06: 144 of 216 rows in 2026-07 and 54 of 74 in 2026-08 carry a
CheckTime outside the agent_eod window. See the companion ticket for the data.

WHAT TASK-262 DID, AND DID NOT DO. An autouse fixture in
tests/agent/unit/test_orchestrator_eod_borrow_wiring_v1.py returns None from
sheets_manager.get_worksheet, which makes the snapshots branch skip and the coverage branch
fall into its own try/except. That neutralises the calls; it does not remove them. The
invariant test test_collect_borrow_snapshot_never_touches_live_sheets is therefore marked
xfail(strict=True) and will flip to a failure the moment production stops calling out.

THE FIX. Give collect_borrow_snapshot the same shape the rest of the module already has:
inject the data source. Something in the direction of

    def collect_borrow_snapshot(summary, snapshots_reader=None, coverage_writer=None)

with the current behaviour as the default, so no call site changes. Then delete the xfail
marker — its removal is the acceptance test.

NOT DECIDED HERE: whether the same seam is needed for the other call sites in
orchestrator_eod (there is a second in-function `import sheets_manager as _sm` at :132,
inside _system_events_alert). That one was NOT investigated.
<!-- SECTION:NOTES:END -->
