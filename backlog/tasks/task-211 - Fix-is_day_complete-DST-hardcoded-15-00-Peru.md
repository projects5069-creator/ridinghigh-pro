---
id: TASK-211
title: 'Fix is_day_complete DST (hardcoded 15:00 Peru)'
status: Done
assignee: []
created_date: '2026-06-30 02:06'
updated_date: '2026-07-02 19:54'
labels: []
dependencies: []
ordinal: 217000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
is_day_complete in utils.py uses hardcoded 15:00 Peru like is_market_hours did pre-DST-fix; winter EST close is 16:00 Peru so a 15:00-16:00 winter window is wrongly 'complete'. Derive from ET (America/New_York) same as the is_market_hours DST fix. Latent, surfaces ~November.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
is_day_complete (utils.py:200) derived close dynamically from 16:00 ET (America/New_York) instead of hardcoded MARKET_CLOSE_HOUR_PERU=15. Latent DST bug (winter/EST window 15:00-16:00 Peru wrongly marked complete, surfaces ~Nov). Same pattern as is_market_hours a0d63fe. 622 pass 0 fail, targeted 7/7. Committed fe2f226. Follow-up TASK-222 for dashboard._is_day_complete duplicate carrying same bug.
<!-- SECTION:NOTES:END -->
