---
id: TASK-118
title: תיעוד/הסדרת sandbox egress — כל push/gh/RemoteTrigger דורש השבתת sandbox
status: To Do
assignee: []
created_date: '2026-06-08 17:53'
labels:
  - infra
  - sandbox
  - agent8
dependencies: []
priority: medium
ordinal: 121000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
תצפית מ-2026-06-08 (TASK-94.3 Phase 2): כל פעולת-רשת יוצאת (git push, gh, RemoteTrigger) נחסמת תחת ה-sandbox של Bash (SSL_ERROR_SYSCALL) ודרשה dangerouslyDisableSandbox. נצפה עקבי לאורך כל TASK-93/94. לתעד כהתנהגות-קבע ו/או לבדוק הסדרה מסודרת (allowlist egress / הגדרת permissions) כדי שמסילת-הבוקר האוטונומית של Agent #8 תוכל לרוץ בענן בלי התערבות. רישום בלבד — טרם נחקר.
<!-- SECTION:DESCRIPTION:END -->
