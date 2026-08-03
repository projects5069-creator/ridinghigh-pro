---
id: TASK-252
title: 'Three missing health checks: symbol sanity, position over HOLD, row count'
status: To Do
assignee: []
created_date: '2026-08-03 21:02'
labels:
  - health-audit
  - monitoring
dependencies: []
priority: medium
ordinal: 250000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Mapped 2026-08-03. None of the three exists. All three would have caught a real failure earlier than it was caught.

Injection point is uniform: health_audit.py around line 2005, one results.append(check_NN_...(gc)) per check, same shape as check_29_interday_artifacts at line 1252. That check already calls load_post_analysis_all_months(), and _HA_SHEET_CACHE at line 1088 memoises reads, so a new check that runs after it costs close to zero extra quota. Verify the memoisation actually covers the loader before relying on that.

Check one, symbol sanity. Run formulas.is_confirmed_phantom over the tickers written today. WARN at one or more, FAIL at five percent of rows or more. Would have fired on 2026-07-15, the first day of the finviz corruption. It was found on 29/7, fourteen days later, and by then 71 rows and 83 positions were affected.

Check two, position older than the hold window. Count DRY_RUN_OPEN rows whose EntryDate is older than MAX_HOLDING_DAYS. WARN at three, FAIL at ten. On 29/7 twenty nine of eighty three had already exceeded it, so this would have fired around 22/7. Measured again on 3/8: eighty four open, median calendar age twelve days, oldest nineteen.

Check three, rows written rather than a date being present. Compare today's row count against the trailing five day average. WARN on a deviation over fifty percent. This is the one that would have caught the scan volume drop of TASK-245 on the day it happened.

Why thresholds and not presence. check_22 today answers Post-analysis ran today with PASSED even when the sheet is empty; the run of 2026-08-03 13:35Z printed exactly that, Before scheduled time, not expected to run yet, on an empty August tab. A date being present is not evidence that data arrived.

Each check needs TDD with a fixture, and each needs a stated threshold that produces a real alert rather than noise. Do not add all three in one commit.
<!-- SECTION:DESCRIPTION:END -->
