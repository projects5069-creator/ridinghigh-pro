---
id: TASK-211
title: 'Fix is_day_complete DST (hardcoded 15:00 Peru)'
status: To Do
assignee: []
created_date: '2026-06-30 02:06'
labels: []
dependencies: []
ordinal: 217000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
is_day_complete in utils.py uses hardcoded 15:00 Peru like is_market_hours did pre-DST-fix; winter EST close is 16:00 Peru so a 15:00-16:00 winter window is wrongly 'complete'. Derive from ET (America/New_York) same as the is_market_hours DST fix. Latent, surfaces ~November.
<!-- SECTION:DESCRIPTION:END -->
