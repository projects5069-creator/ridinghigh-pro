---
id: TASK-228
title: >-
  Test-order state leak: test_agent_score_matches_scanner fails in full suite,
  passes isolated
status: To Do
assignee: []
created_date: '2026-07-04 01:49'
labels: []
dependencies: []
priority: low
ordinal: 234000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S4 (3/7): tests/agent/integration/test_scanner_agent_match.py::test_agent_score_matches_scanner FAILS in a full local 'pytest tests/' run (624 passed, 2 failed) but PASSES in isolation (1 passed, 7.14s) => order-dependent state leak from an earlier test (module-level cache/config/monkeypatch not undone), NOT a code bug. In CI it is skipped anyway (-m 'not integration', tests.yml:30). Triage: bisect test order (pytest -p no:randomly --lf / --stepwise or pytest-random reorder) to find the leaking test; fix the leak (fixture teardown), not the victim. Local triage MUST use -m 'not integration' awareness — the sibling test_write_real_decision_to_sheet needs live creds and attempts a REAL Sheets write.
<!-- SECTION:DESCRIPTION:END -->
