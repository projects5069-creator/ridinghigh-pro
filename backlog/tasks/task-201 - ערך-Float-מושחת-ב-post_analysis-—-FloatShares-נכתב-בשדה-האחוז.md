---
id: TASK-201
title: ערך Float% מושחת ב-post_analysis — FloatShares נכתב בשדה האחוז
status: To Do
assignee: []
created_date: '2026-06-28 05:27'
labels: []
dependencies: []
ordinal: 207000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ב-post_analysis (MxV<=-100% subset, ~101 שורות) נמצאו 3 ערכי Float%>100, הקיצוני 42,473,000 — Float% אמור 0-100%. כנראה FloatShares raw נכתב בטעות בעמודת האחוז. מזהם את הרבעון-העליון בניתוחי-Float (התגלה במחקר 199, Float% כמסנן-זנב).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 לזהות בקוד את נתיב-הכתיבה של Float% ב-collector/enrich
- [ ] #2 לתקן קדימה — לוודא שנכתב האחוז ולא ה-raw (FloatShares)
- [ ] #3 להחליט על ניקוי/סימון רטרואקטיבי של 3 השורות המושחתות
<!-- AC:END -->
