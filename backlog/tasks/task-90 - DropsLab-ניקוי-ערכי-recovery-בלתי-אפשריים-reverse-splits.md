---
id: TASK-90
title: 'DropsLab: ניקוי ערכי recovery בלתי-אפשריים (reverse-splits)'
status: To Do
assignee: []
created_date: '2026-06-01 01:22'
labels:
  - dropslab
  - data-quality
  - from-task-80
dependencies: []
ordinal: 90000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
עלה ב-TASK-80 מבט-נקי 31/5. max_recovery_5d_pct מכיל ערכים בלתי-אפשריים: CTNT +28567%, RDGT +22400%, HAO +17820%, CODX. סיבה: reverse-split או scan_close~0. השפעה: מזהם ממוצעי recovery + עלול לתייג Full Recovery בטעות (82 אנומליות, 4.3%; ניקוי הזיז 49.5%->47.2%). נדרש: זיהוי splits, cap/סינון אחוז לא-סביר, חישוב מחדש pattern_tag. read-only עד אישור.
<!-- SECTION:DESCRIPTION:END -->
