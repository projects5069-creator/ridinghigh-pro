---
id: TASK-89
title: 'מייל חודשי: זיהוי ימים/עסקאות חריגים מהדאטה'
status: Done
assignee: []
created_date: '2026-06-01 01:22'
updated_date: '2026-08-04 00:32'
labels:
  - task-48
  - monthly-email
dependencies: []
ordinal: 89000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Follow-up מ-TASK-48 31/5. לזהות חריגות מהדאטה שלנו בלבד (לא feed חיצוני): ימים עם נפח-עסקאות חריג או תוצאה קיצונית, לציין במייל. הקשר-מאקרו חיצוני (VIX/חדשות) הוצא במכוון. commit נפרד.
<!-- SECTION:DESCRIPTION:END -->

## MERGED INTO TASK-39, 2026-08-04

Closed as a merge. Both are about what the email contains, and TASK-39 is about consolidating six daily emails into one.

Deciding the content of a mail that may not survive consolidation is work in the wrong order. If TASK-39 produces a single daily summary, the anomaly flagging this task asks for belongs in that summary and nowhere else.
