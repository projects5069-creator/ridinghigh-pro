---
id: TASK-195
title: 'A: skip test_fixture_parity כש-fixture חסר → CI ירוק'
status: Done
assignee: []
created_date: '2026-06-26 12:03'
updated_date: '2026-06-26 13:47'
labels: []
dependencies: []
ordinal: 201000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ה-tests gate של main אדום מאז 99ce140 (TASK-46, 2026-06-22) כי test_fixture_parity_and_pinned_winrate קורא post_analysis_2026-04.csv שמגונן ב-git בכוונה (Decision 4: research CSVs נשארים מקומיים, ריפו ציבורי). מקומית ירוק, ב-checkout נקי נופל ב-FileNotFoundError. defect מובנה, לא רגרסיה. A=עזרה-ראשונה: skip כש-fixture חסר. מודע: parity מאבד כיסוי ב-CI (רץ רק מקומית) — B (fixture סינתטי committed) ירפא זאת בנפרד, לא נפתח עכשיו.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 כש-post_analysis_2026-04.csv חסר ב-checkout נקי → הטסט מדלג עם pytest.skip ו-reason ברור, לא נכשל
- [ ] #2 כשהקובץ קיים מקומית → הטסט רץ במלואו (parity + pinned winrate נבדקים כרגיל)
- [ ] #3 tests.yml ירוק על ה-push הבא
- [ ] #4 שינוי נקודתי בקובץ-הטסט בלבד; אפס שינוי בלוגיקת-מוצר; אפס דאטת-מסחר נכנסת לריפו
<!-- AC:END -->
