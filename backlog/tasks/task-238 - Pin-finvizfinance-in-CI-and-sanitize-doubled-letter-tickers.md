---
id: TASK-238
title: Pin finvizfinance in CI and sanitize doubled-letter tickers
status: To Do
assignee: []
created_date: '2026-07-28 12:40'
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
