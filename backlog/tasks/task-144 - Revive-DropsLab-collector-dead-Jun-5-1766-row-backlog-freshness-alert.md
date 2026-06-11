---
id: TASK-144
title: 'Revive DropsLab collector (dead Jun 5, 1766-row backlog) + freshness alert'
status: To Do
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-11 04:27'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 147000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV DL-7.1: drops_collect.yml cancelled daily since 5/6 (timeout 20m death-spiral, repeat of 19/5 pattern); drops_post frozen at scan_date 27/5; 1,766 raw rows unprocessed. Fix: checkpoint/batch processing + freshness alert (post max date vs raw max date). Evidence: phase7_evidence.md
<!-- SECTION:DESCRIPTION:END -->
