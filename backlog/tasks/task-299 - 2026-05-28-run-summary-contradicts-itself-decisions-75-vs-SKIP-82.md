---
id: TASK-299
title: 2026-05-28 run summary contradicts itself - decisions 75 vs SKIP 82
status: To Do
assignee: []
created_date: '2026-08-10 02:05'
labels: []
dependencies: []
priority: medium
ordinal: 297000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמצא 9/8 בהשוואת-בקרה. הסיכום של ריצה ב-28/5 אומר signals=82, decisions=75, ENTER=0, SKIP=82, sentinel_blocks=7. אבל decisions אמור להיות סכום ENTER ו-SKIP, כלומר 82 ולא 75. פער של 7, שהוא בדיוק מספר ה-sentinel_blocks - חשד שחסימות-סנטינל נספרות באחד המונים ולא בשני.
שער-קבלה: הוכרע איזה מונה נכון, והסיכום הפך לעקבי או שהאי-עקביות תועדה כמכוונת.
<!-- SECTION:DESCRIPTION:END -->
