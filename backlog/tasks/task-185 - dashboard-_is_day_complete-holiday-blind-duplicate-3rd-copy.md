---
id: TASK-185
title: dashboard _is_day_complete holiday-blind duplicate (3rd copy)
status: To Do
assignee: []
created_date: '2026-06-16 18:03'
labels: []
dependencies: []
priority: medium
ordinal: 188000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-135 found dashboard.py:1912 _is_day_complete is a THIRD holiday-blind copy of day-complete logic (day < today and day.weekday() < 5), used in _simulate_short_trades (Table A/B exit eval, line 2035). Same bug family as TASK-135 (weekday-only, no holiday). Currently unreachable (day_date fed from get_trading_days_after, holiday-free per TASK-130) so latent, but it's an SSoT/§10 violation. Fix: replace with utils.is_day_complete (now holiday-aware, c508879) and delete the local copy. Verify _row_trading_days source + dashboard import path. Low risk, DRY cleanup.
<!-- SECTION:DESCRIPTION:END -->
