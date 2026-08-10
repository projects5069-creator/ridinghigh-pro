---
id: TASK-291
title: Organize audit archive internals without breaking repo path references
status: To Do
assignee: []
created_date: '2026-08-10 00:27'
labels: []
dependencies: []
priority: medium
ordinal: 289000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
rhpro_audit_run הועבר as-is ל-ClaudeWork/RidingHighPro/audit עם symlink. הסידור הפנימי לתת-תיקיות עדיין לא נעשה כי מסמכי הריפו מצביעים על שמות-קבצים מדויקים. הרשימה המדויקת של הקבצים המופנים חושבה ונשמרה ב-_machine/audit_referenced_files_20260809.txt. הפתרון: לסדר לתת-תיקיות ולהשאיר symlink ברמה השטוחה לכל קובץ מופנה. שער-קבלה: כל נתיב שמופיע במסמכי הריפו עדיין נפתח, ואומת בפועל.
<!-- SECTION:DESCRIPTION:END -->
