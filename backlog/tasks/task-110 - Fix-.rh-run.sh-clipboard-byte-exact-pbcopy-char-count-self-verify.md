---
id: TASK-110
title: 'Fix .rh-run.sh clipboard: byte-exact pbcopy + char-count self-verify'
status: Done
assignee: []
created_date: '2026-06-04 14:46'
updated_date: '2026-06-04 14:51'
labels: []
dependencies: []
ordinal: 110000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
wrapper now does pbcopy < OUTFILE and verifies clipboard char count matches file (815=815 proven live). Closes recurring morning clipboard confusion — root cause was selecting folded screen text, not pbcopy. Verified: 30-line folded output copied full via direct Cmd+V.
<!-- SECTION:DESCRIPTION:END -->
