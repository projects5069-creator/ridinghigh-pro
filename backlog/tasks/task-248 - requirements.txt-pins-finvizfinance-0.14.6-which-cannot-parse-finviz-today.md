---
id: TASK-248
title: requirements.txt pins finvizfinance 0.14.6 which cannot parse finviz today
status: To Do
assignee: []
created_date: '2026-07-29 10:11'
labels:
  - bug
  - ci
dependencies: []
priority: high
ordinal: 246000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verified live 2026-07-29. requirements.txt line 4 pins finvizfinance==0.14.6. That version looks for a table with class table-light, and the live finviz screener page no longer contains it, only screener_table and styled-table-new. A real fetch under 0.14.6 raises AttributeError NoneType has no attribute findAll. The pin is not merely stale, it is poisonous.

The scanner survives only because all three workflows install finvizfinance unpinned and get 1.3.0, so they ignore the pin entirely. Anyone running pip install -r requirements.txt gets a dead scanner, and the local development environment does not reflect production for this dependency.

DECISION NEEDED: pin to the version CI actually resolves, or drop the pin and let it float. Pinning is safer for reproducibility but must be to a version that parses the current page. Note that the TASK-238 fix subclasses _get_table, so any version change must be checked against that hook.

Do not change the pin without a live fetch proving the chosen version parses. Also decide whether the workflows should install via -r requirements.txt instead of listing packages inline, which is the reason the pin was silently bypassed.
<!-- SECTION:DESCRIPTION:END -->
