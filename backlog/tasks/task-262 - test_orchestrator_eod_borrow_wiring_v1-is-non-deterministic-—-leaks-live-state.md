---
id: TASK-262
title: test_orchestrator_eod_borrow_wiring_v1 is non-deterministic — leaks live state
status: To Do
assignee: []
created_date: '2026-08-06 01:17'
updated_date: '2026-08-06 01:18'
labels:
  - tests
  - ci
  - flaky
  - data-integrity
dependencies: []
priority: medium
ordinal: 260000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Both tests in the file fail locally and pass in CI on the same commit, and the local result itself moved from 2 failures to 1 within one session with no code change. passed_tickers contains the live tickers of the day (INLF, SHPH, YXT, ZYBT) instead of the fixture values, and collect_borrow_data is called when the test asserts it must not be — the mock does not close a branch that reads real state. A suite whose result moves between runs is not a gate. Related to TASK-250.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Observed across 2026-08-05 while running the suite repeatedly for TASK-259.

THE SYMPTOM: the two tests in this file fail locally and pass in CI on the SAME commit.
Worse, they are not even stable locally. Measured on one machine, one working tree, no
code change between runs:

  19:47  2 failed, 727 passed      (both tests failed)
  20:07  1 failed, 729 passed      (only test_no_tickers_skips_collector_and_does_not_fail)

CI on the same commits, same command (tests.yml:30,
uv run --with-requirements requirements.txt --with pytest pytest -m "not integration" -q):
  52c32a7  runs 31056028703 / 31056032278  -> success
  fcdb0aa  runs 31062267689 / 31062268958  -> success

THE FAILURE ITSELF:

  >  assert passed_tickers == ["AAA", "BBB", "CCC"]
  E  AssertionError: assert ['AAA', 'BBB'...', 'YXT', ...] == ['AAA', 'BBB', 'CCC']
  E    Left contains 4 more items, first extra item: 'INLF'

  >  collect.assert_not_called()
  E  AssertionError: Expected 'collect_borrow_data' to not have been called. Called 1 times.
  E  Calls: [call(['INLF', 'SHPH', 'YXT', 'ZYBT'], <MagicMock name='AlpacaBroker()'>)]

INLF, SHPH, YXT and ZYBT are the LIVE tickers of 2026-08-05 — they appear in decision_log
2026-08 and in the agent_minute logs of that day. They are not in the fixture. The mock
therefore does not close a branch that reads real state from the machine, and the assertion
compares fixture values against production data.

WHY THE RESULT MOVES: whatever that branch reads changes during the day, so the same test
passes or fails depending on when it runs and what the live sheets/caches contain. CI has
no credentials and no local caches, so the branch returns nothing and the test goes green.
That green is an artefact of a missing environment, not evidence that the code is right.

WHY IT MATTERS BEYOND THIS FILE: a suite whose result moves between runs is not a gate. It
cannot distinguish "my change broke something" from "the market moved". During TASK-259
the baseline had to be measured before every edit just to know what a NEW failure would
look like, and the accepted baseline itself changed from 2 to 1 mid-session. Any real
regression landing in these two tests would be indistinguishable from the noise.

NOT VERIFIED: which exact call inside collect_borrow_snapshot reaches live state. The
2026-08-03 PK entry (v4.12) records a related finding — "7 unit tests read live Sheets via
collect_borrow_snapshot:57 in a branch nobody patches" — but that line was not re-confirmed
in this session and the file has 2 failing tests now, not 7.

RELATED: TASK-250 (unit tests read live Sheets, seven of them) covers the same class and
may already own this file. Decide whether this is a duplicate before working it.

NO FIX ATTEMPTED. Opened as a record only.
<!-- SECTION:NOTES:END -->
