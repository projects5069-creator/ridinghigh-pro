---
id: TASK-134
title: >-
  Unit suite: 16 pre-existing failures (decision_id_generator, decision_logic
  43-fields, EOD window, order/position_manager, postmortem) — triage vs
  baseline
status: In Progress
assignee: []
created_date: '2026-06-10 17:40'
updated_date: '2026-06-11 17:30'
labels: []
dependencies: []
priority: medium
ordinal: 137000
---

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All 16 broken unit tests fixed; suite green (222/222 with full requirements.txt)
- [ ] #2 Test-only fixes — ZERO production-code change (all 6 groups triaged stale, each with documenting commit/PK)
- [ ] #3 Per-group documented fix: A(new ID format + drop max_counter), B(assert vs len(FIELD_MAPPING)), C(patch AGENT_FORCE_EOD_CLOSE=True), D(22->25 cols + Status index), E(get_latest_bar/quote mock), F(assertions vs Hebrew prose)
<!-- AC:END -->
