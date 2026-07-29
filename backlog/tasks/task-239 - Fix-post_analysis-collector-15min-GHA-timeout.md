---
id: TASK-239
title: Fix post_analysis collector 15min GHA timeout
status: To Do
assignee: []
created_date: '2026-07-28 12:40'
labels:
  - bug
  - perf
dependencies: []
ordinal: 243000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
post_analysis.yml timeout-minutes:15. Runs cancelled 23/7, 24/7, 27/7 at 15m1Xs; also 23/6. Time burned in the collector step: yfinance_provider.py:316 yf.Ticker(ticker).info blocks ~18s per dead symbol, no timeout, no skip-cache, no dedup; called once per row plus sleep 0.3 at :632. Same failure class as TASK-190. Independent of the finvizfinance root: fixing perf alone returns the job under 15 minutes. Consider raising timeout-minutes as an interim palliative before month end. Verify against the next scheduled run.
<!-- SECTION:DESCRIPTION:END -->
