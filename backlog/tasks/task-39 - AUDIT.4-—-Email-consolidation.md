---
id: TASK-39
title: AUDIT.4 — Email consolidation
status: To Do
assignee: []
created_date: '2026-05-24 20:59'
labels: []
dependencies: []
priority: medium
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Consolidate 6 emails/day (3 health + morning + daily + critic) into 1 daily summary + immediate alerts on errors only.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Current: 6 emails/day mostly green. Proposed: single daily summary at 16:30 Peru. Health emails only on CRITICAL/WARNING.
<!-- SECTION:NOTES:END -->

## ABSORBS TASK-89, 2026-08-04

TASK-89 closed as a merge into this task. Both are about email content, and this task decides whether the emails survive at all.

89 asked to flag days with unusual trade volume or extreme outcomes, from our own data only, with external macro context deliberately excluded. If this task produces a single daily summary, that flagging belongs inside it. Deciding the content of a mail that may be consolidated away is work in the wrong order.
