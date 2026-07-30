---
id: TASK-238
title: Pin finvizfinance in CI and sanitize doubled-letter tickers
status: Done
assignee: []
created_date: '2026-07-28 12:40'
updated_date: '2026-07-30 11:52'
labels:
  - bug
  - data-integrity
dependencies: []
ordinal: 242000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ROOT: post_analysis.yml:22, backfill_ohlc.yml:22, auto_scan.yml:24 run 'pip install finvizfinance' unpinned while requirements.txt pins 0.14.6 (dead pin). Installed=1.3.0. Overview path extracts Ticker via base.py:127 col.text raw; the dedicated ticker.py:30 view sanitizes with split(chr(160))[1] but Overview lacks it -> first character doubled (25/25 observed: SSOBR NNVVE AATPC). Three tracks: (1) pin the dependency in all three workflows via -r requirements.txt and choose a known-good version; (2) sanitizer guard on scanner output before writing daily_snapshots, defense-in-depth; (3) clean corrupted daily_snapshots rows in a quota-safe window. Open questions needing network: exact FINVIZ HTML shape, whether 0.14.6 parsed correctly.
<!-- SECTION:DESCRIPTION:END -->

## MEASURED SCOPE (2026-07-29, read only)

Onset is 2026-07-15, not 2026-07-22. Zero confirmed phantoms on every scan day through 07-14, then 52 percent of daily_snapshots rows on 07-15 and 18 to 45 percent every day after. 54 distinct confirmed phantom symbols across 11 trading days. 71 of 654 daily_snapshots rows and 16 of 77 post_analysis rows.

Confirmed means the stripped symbol also appears as a real ticker in the same data. Raw doubled letter matching gives 151 rows and overcounts by roughly a factor of two, since legitimate tickers match it and it flags rows from before the bug existed. Any cleanup rule must use the confirmed test, not the raw one.

Downstream impact measured: 64 of 137 July ENTERs fired on a confirmed phantom, and all 83 open positions sit on suspect symbols with zero on a clean ticker. Filed separately as TASK-246.
