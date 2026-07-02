---
id: TASK-220
title: >-
  Postmortem: overnight runner ARMED-in-fact despite documented DISARMED (fired
  9 nights 6/25-7/2, all ABORTED pre-execute)
status: Done
assignee: []
created_date: '2026-07-02 16:21'
updated_date: '2026-07-02 18:23'
labels:
  - safety
  - postmortem
dependencies: []
priority: high
ordinal: 226000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
root-cause: unload-only 6/20; login reloads plist from ~/Library/LaunchAgents. Fixed 7/2 via rename->.disabled + verified empty launchctl. Deliverable: document lesson, correct handoff/PK claims that stated DISARMED, add re-arm checklist (bootout AND rename).
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Postmortem written (POSTMORTEM_overnight_ARMED_2026-07-02.md, 93e56cf) + 6 stale DISARMED docs corrected (674b0b3) + 2 memory files fixed. Root-cause: unload-only 6/20 didn't hold, login reloads plist. 9 nightly fires all ABORTED (auth-smoke x7, base-RED x2 — defense-in-depth held). Truly disarmed 2026-07-02 via rename->.disabled+bootout, launchctl verified empty. Re-arm checklist: bootout AND rename.
<!-- SECTION:NOTES:END -->
