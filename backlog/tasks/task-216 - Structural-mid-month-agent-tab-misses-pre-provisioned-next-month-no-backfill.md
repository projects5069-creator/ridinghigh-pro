---
id: TASK-216
title: >-
  Structural: mid-month agent-tab misses pre-provisioned next month (no
  backfill)
status: To Do
assignee: []
created_date: '2026-07-01 01:12'
labels: []
dependencies: []
priority: medium
ordinal: 222000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
כשטאב-agent נוסף לקוד אמצע-חודש, החודש-הבא שכבר הוכן ב-1 לחודש לא מקבל אותו (אין backfill). קרה עם shadow_gate_events (24/6) + borrow_coverage (14/6) → 2026-07 חסר אותם עד תיקון ידני 30/6 (c19e246). יחזור בכל feature עתידי שמוסיף agent-tab אחרי ה-1. פתרון אפשרי: rotation יריץ create_agent_sheets --month <current> (idempotent) גם על החודש הפעיל.
<!-- SECTION:DESCRIPTION:END -->
