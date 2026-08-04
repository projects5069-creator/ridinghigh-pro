---
id: TASK-250
title: 'Unit tests read live Sheets, seven of them'
status: To Do
assignee: []
created_date: '2026-08-03 21:01'
labels:
  - bug
  - tests
  - quota
dependencies: []
priority: high
ordinal: 248000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-08-03 after market close. tests/agent/unit/test_orchestrator_eod_borrow_wiring_v1.py went red on the local suite after being green all day, without any edit to it.

The file docstring says: All-mocked (MagicMock + patch), zero real API/Sheets. That is false. The tests patch agent.orchestrator.build_account_state, but orchestrator_eod.collect_borrow_snapshot has a second ticker source nobody patches: line 57 calls sheets_manager.get_worksheet(daily_snapshots) and line 59 calls get_all_values(). The helper returns the union of both sources.

Why it turned red today and not before: the active month rotated to August on the first, and the August daily_snapshots tab was empty until today. From the moment today's rows were written, real tickers entered the assertion. Observed failure: assert ['AAA','BBB',...,'HYFM',...] == ['AAA','BBB','CCC'], first extra item DFNS. DFNS was in the live scan of 2026-08-03.

Three consequences. First, seven tests in that file call collect_borrow_snapshot, so every local pytest run performs seven live Sheets reads. That is a direct contribution to TASK-55, from a file that claims to touch nothing. Second, CI is green only because tests.yml has no credentials, so the read raises and scanned falls back to an empty set. That is a false green: the mock contract is never actually exercised in CI. Third, the suite is now red locally for anyone with working OAuth, which hides real regressions.

Fix direction, not chosen yet: patch sheets_manager.get_worksheet in the test file so the scanned branch is deterministic, and correct the docstring. Consider whether a repo wide guard is warranted, for example a conftest fixture that fails any test under tests/agent/unit that opens a real client.

Not verified: whether other unit tests outside this file also reach live Sheets. That sweep has not been run.
<!-- SECTION:DESCRIPTION:END -->

## ABSORBS TASK-228, 2026-08-04

TASK-228 closed as a merge into this task. Same family: unit tests that are not hermetic, in the same suite.

228 is an order dependent state leak in tests/agent/integration/test_scanner_agent_match.py, which fails in a full run and passes in isolation. This task is a live Sheets read from tests/agent/unit/test_orchestrator_eod_borrow_wiring_v1.py. Both are solved by the same conftest level isolation, and leaving one open keeps the suite unreliable regardless of the other.

Carried from 228: local triage must stay aware of -m "not integration", because the sibling test_write_real_decision_to_sheet attempts a real Sheets write.
