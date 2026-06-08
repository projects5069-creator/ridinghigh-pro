---
id: TASK-94
title: 'Agent #8 — Routine Checker: בקרת איכות על עבודת לילה אוטונומית'
status: Done
assignee: []
created_date: '2026-06-02 03:00'
updated_date: '2026-06-08 17:52'
labels:
  - agent
  - agent8
  - routine
  - review
  - qa
dependencies: []
priority: high
ordinal: 94000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מטרה: סוכן שמבקר את עבודת הפיתוח שנעשתה ברוטינים/בלילה (לא מסחר — זה The Critic) ומפיק לעמיחי דוח בוקר עברית אחד: מה ביקשו, מה בוצע בפועל, אילו פערים ודילמות עלו, וציון איכות/verdict. הפעלה: או אוטומטית כל בוקר אחרי רוטיני לילה, או ידנית מהמערכת (כשאין ריצת לילה). זמן ריצה מקובל: 10-30 דק, עמיחי ממתין. הבחנה מ-The Critic: Critic=סיכומי מסחר יומי/שבועי/חודשי (ויזואליזציה PowerPoint); Agent #8=ביקורת עבודת dev. SCOPE: (1) לנתח את כל היכולות הקיימות מ'רמה 2' (ראה TASK הבא) ולבחור מה לאמץ; (2) להגדיר את הפער הייחודי שעמיחי צריך (רחב יותר, ממוקד למערכת שלו, דוח עברית מאחד על כל ענפי הלילה); (3) לבנות עם עזרת agent-builder (עמיחי יספק מקור); (4) wiring: routine בוקר שמריץ reviewer על branches של הלילה ומאחד לדוח אחד. תלוי ב-TASK-93 (GitHub creds לענן) להפעלה מלאה.
<!-- SECTION:DESCRIPTION:END -->
