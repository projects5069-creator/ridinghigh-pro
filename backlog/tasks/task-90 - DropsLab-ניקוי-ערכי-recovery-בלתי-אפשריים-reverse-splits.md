---
id: TASK-90
title: 'DropsLab: ניקוי ערכי recovery בלתי-אפשריים (reverse-splits)'
status: To Do
assignee: []
created_date: '2026-06-01 01:22'
updated_date: '2026-06-14 22:56'
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

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 TASK-139-INV evidence (RH-4.2 + DL-7.2, docs/research/INVESTIGATION_2026-06-10/REPORT.md): TDIC 2026-05-12 split sits CLEAN inside n=123 as fake LOSS; DropsLab d1_pct mean +124pct vs median 0 — same unflagged-split disease both systems
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tracked under parent TASK-180 (split/halt detector). RH-half done in code; DropsLab recovery/pattern_tag recompute pending TASK-144. Stays open.
<!-- SECTION:NOTES:END -->
