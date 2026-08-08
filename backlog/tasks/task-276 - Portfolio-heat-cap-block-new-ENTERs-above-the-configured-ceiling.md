---
id: TASK-276
title: Portfolio heat cap - block new ENTERs above the configured ceiling
status: To Do
assignee: []
created_date: '2026-08-08 17:53'
labels: []
dependencies: []
priority: high
ordinal: 274000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
T-302 (S7_TASKS_v1.md, gate 3 heat component). DECIDED 2026-08-08 in docs/DECISIONS_2026-08-08.md D3: ceiling 8 percent of equity, eps 0.02 identity / 0.05 risk, ENFORCED AT THE ORDER-WRITE SITE (order_manager), NOT at decision time. PROBLEM: open heat measured at 11,060 dollars = 11.1 percent, above the 6-8 percent of position-sizer KP#6, with zero mechanism in code. WHY THE WRITE SITE: the decision-time snapshot was proven to lie - run 29940103210 took a 429 on paper_portfolio and carried on reporting 0 open positions while 69 were open (TASK-244:40). WHY AT ALL, GIVEN DRY_RUN: the cap does not protect money, it makes the collected data reproduce a real account's exposure profile - without it the percentages we gather are not reproducible live. THREE BINDING CONSTRAINTS, all quoted in D3: TASK-128:22 - do NOT edit the shared _check_filters while HYP-002 runs; TASK-244:51 - the account-state snapshot is fail-open under 429, so the heat computation must fail CLOSED (read failure means no entry, not no heat); TASK-259:44 - cross-process TOCTOU, agent_minute runs overlap 92.5 percent, so the check must run adjacent to the write on the freshest read, never inherit a snapshot taken minutes earlier at the top of run(). SCOPE: config.py AGENT_MAX_PORTFOLIO_HEAT_PCT default 8; compute sum of 0.1*EntryPrice*Quantity over OPEN rows; block the entry with a stated reason. NOT IN SCOPE: do not close existing positions - entry-block only. GATE: gate3 heat component + unit - a 9 percent state yields a blocked entry carrying the reason. RED-first: test_heat_cap_blocks_v1.py fails today (no such filter).
<!-- SECTION:DESCRIPTION:END -->

--- השאלה הפתוחה 2026-08-08 (מתוכנית-העבודה) — לא הוכרע ---
ההכרעה על **מה** (8%, ε 0.02/0.05, אכיפה באתר-כתיבת-הפקודה) כבר נפלה —
`docs/DECISIONS_2026-08-08.md` §D3. מה שנשאר פתוח הוא **מתי**.

**השאלה: לפני החלון או בתוכו?**
1. א. **לפני פתיחת החלון** — פרופיל-החשיפה של כל המדגם (n≥100) נאסף תחת
      התקרה, כלומר רפרודוקטיבי לחשבון אמיתי. המחיר: זהו **קוד-מסחר חדש**
      שנכתב בסופ"ש תחת לחץ-שעון, עם RED-first ו-suite מלאה, ואישור מפורש.
   ב. בשבוע הראשון של החלון — הימים הראשונים נאספים ללא תקרה; המדגם מעורב
      (חלק עם, חלק בלי) ויידרש לתעד את נקודת-המעבר.
   ג. אחרי 4/9 — המדגם כולו נאסף בפרופיל-חשיפה שלא ניתן לשחזר בחשבון חי;
      זו הטיה ידועה שתירשם בדוח-ההכרעה.
   ⚠️ אין ברירת-מחדל. **לא הוכרע.**

2. אם נבחר (א) ו-ה-RED-first יחשוף הפתעה ב-`order_manager` — האם ממשיכים
   בלחץ או נסוגים ל-(ב)? **פתוח מראש**, כדי שההחלטה לא תתקבל בתוך הלחץ.

⚠️ תלות-תוכן: חישוב-החום קורא E×Q, ולכן נכונותו יורשת מ-TASK-279 (חישוב-
הכמות-מחדש) — שמתוזמן אחרי 4/9. עד אז החום נמדד על כמויות שחלקן שגויות.
