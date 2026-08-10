---
id: TASK-283
title: Consolidate off-repo Claude artifacts under one Drive-synced root
status: To Do
assignee: []
created_date: '2026-08-09 14:23'
labels: []
dependencies: []
priority: high
ordinal: 281000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
עמיחי הכריע 9/8: הגיבוי מחוץ-למק דרך Google Drive Desktop, לא העלאה ידנית. rhpro_audit_run הוא 35MB, 283 קבצים בשורש, 19 תת-תיקיות, 720 אובייקטים. Drive אומת מותקן ורץ 9/8, חשבון aalevy305. שתי הפרדות מחייבות: העברה איננה סידור, והריפו איננו נכנס לסנכרון אלא כ-git bundle. השערים אומתו: ששה מצביעים על RidingHighPro ורק gate5_integrity.py:3 על rhpro_audit_run, דרך expanduser, ולכן symlink שקוף לכולם.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 rhpro_audit_run עבר as-is לתיקייה מסונכרנת ו-symlink מחזיר את הנתיב המקורי
- [ ] #2 gate5_integrity.py ו-gate265_watchdog.py ירו בפועל דרך ה-symlink, לא רק קיימים
<!-- AC:END -->
