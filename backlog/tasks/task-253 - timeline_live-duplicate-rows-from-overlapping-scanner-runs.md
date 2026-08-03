---
id: TASK-253
title: timeline_live duplicate rows from overlapping scanner runs
status: To Do
assignee: []
created_date: '2026-08-03 22:08'
labels:
  - bug
  - data-integrity
dependencies: []
priority: medium
ordinal: 251000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured 2026-08-03 from the August timeline_live tab, read only.

STATE: 308 exact (ScanTime, Ticker) duplicate pairs in one trading day, out of 21892 rows, so 1.4 percent. They are not spread evenly. Five minutes carry almost all of them, and those same minutes show row counts far above the median of 61: 10:20 with 92, 10:42 with 100, 12:29 with 125, 12:40 with 138, 14:08 with 152. By hour the duplicates fall at 10 with 96, 12 with 132, 14 with 78, and one each at 9 and 11.

MECHANISM, from the code: auto_scanner.py calls safe_append_rows with dedup_col=1 and dedup_vals set to this scan ScanTime. That check asks whether the ScanTime already exists BEFORE writing. GitHub Actions runs overlap, which was proven on 2026-07-31 where the run started at 17:27 was still executing when the 17:28 run began. Two overlapping runs can both pass the existence check before either has written, and both then append. A plain race.

ALTERNATIVE RULED OUT: 89 of the 388 ScanTime values come back from Sheets without a padded hour, 8:31 rather than 08:31, which would break a string comparison. It is not the cause. Those unpadded stamps are hours 8 and 9 and they carry FEWER rows, median 30 against 66 for the padded hours, and every duplicate sits in the padded hours 10 to 14.

WHY IT MATTERS: timeline_live is the source for daily_summary, ticker_follow_up and the collector. A duplicated minute inflates any per minute aggregate and any volume measure computed over it, silently.

NOT VERIFIED: whether post_analysis and daily_snapshots carry the same duplication. Not measured. Also not measured is whether the rate is stable day to day or specific to 2026-08-03.

DO NOT FIX BLIND. The dedup sits on the hot write path that runs every minute of every trading day. Build a detector first, a health check that counts duplicate (ScanTime, Ticker) pairs, get a baseline over several days, and only then touch the write. Any change needs TDD and a before and after comparison on a full trading day.
<!-- SECTION:DESCRIPTION:END -->
