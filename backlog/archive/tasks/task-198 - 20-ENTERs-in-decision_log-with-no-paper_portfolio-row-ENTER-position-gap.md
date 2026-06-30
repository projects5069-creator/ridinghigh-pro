---
id: TASK-198
title: 20 ENTERs in decision_log with no paper_portfolio row (ENTER->position gap)
status: To Do
assignee: []
created_date: '2026-06-27 20:42'
updated_date: '2026-06-30 14:16'
labels: []
dependencies: []
ordinal: 204000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
התגלה ב-TASK-65 recon 2026-06-27. 20 ENTER DecisionIDs רשומים ב-decision_log אך אין להם שורת-פוזיציה ב-paper_portfolio → אין פוזיציה ולכן אין postmortem. זה NOT postmortem-gap קלאסי. השערות לא-אומתו: (א) כניסות-כפולות באותו יום/טיקר — re-entry בזמן-החזקה שלא פתח פוזיציה (EHGO-124202 ליד 085304, NXTS-124200 ליד 084759, ANY-124257 ליד 122426); (ב) ENTER שנדחה לפני פתיחת-פוזיציה (borrow/shares/rejection) — AZI/RGNT/SUNE/SDOT ×2, singles HCWB/XOS/EDHL/BYAH/EPSM/ADIL/CRVO. נדרש recon: לאמת איזה דפוס, והאם זה פער-pipeline אמיתי (ENTER->position) או duplicate-logging תקין. related: TASK-65.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 לאמת לכל אחד מ-20: re-entry-duplicate מול rejected-ENTER מול pipeline-gap אמיתי
- [ ] #2 להחליט אם זה באג (ENTER לא הפך לפוזיציה) או התנהגות-תקינה (re-entry blocked)
- [ ] #3 read-only recon; אפס תיקון עד הכרעה
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
צ'אט-recon 2026-06-27 (READ-ONLY): היפותזה שורש משותף עם MetricsAtEntry-ריק (TASK-65) — ה-join postmortem<->decision_log עובר ב-_read_decision(position_id) (linear-scan, מחזיר {} ב-miss). 20 ה-ENTER-ללא-pp עשויים לחלוק את אותו מנגנון (PositionID!=DecisionID או drop בכתיבה). לחקור את ה-lookup כחשוד יחיד. אין מסקנת-edge (הופרך, PK v3.63).

CANCELLED→MERGED 30/6: מוזג ל-TASK-65 (חקירת-שורש _read_decision משותפת).
<!-- SECTION:NOTES:END -->
