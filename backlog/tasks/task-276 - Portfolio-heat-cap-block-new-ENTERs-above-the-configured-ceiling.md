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

════════════════════════════════════════════════════════════════════════════════
## ✅ הכרעה 2026-08-08 (עמיחי) — אופציה ג׳: **לא מנחיתים לפני החלון**

**ההכרעה:** תקרת-החום **אינה** נכנסת לפני פתיחת חלון-המדידה. היא נכנסת
**אחרי 4/9, יחד עם TASK-279**. אפס שינוי קוד עכשיו. ‏`order_manager.py` לא נגע.

**מקור הנימוקים:** ‏recon מלא של 8/8 — `~/rhpro_audit_run/TASK276_RECON.md`.
⚠️ ההכרעה **אינה** פותחת מחדש את D3: ‏8% · ‏ε 0.02/0.05 · אכיפה ב-order_manager
עומדים בעינם. מה שהוכרע כאן הוא **מתי**, שהתיק עצמו סימן כלא-מוכרע.

### ארבעת הנימוקים

1. **מיקום-האכיפה אינו מה שנראה.** ‏`execute()` שולח את ההזמנה ב-`:121`
   וכותב את השורה רק ב-`:166`. אכיפה "צמודה-לכתיבה" כלשונה — בין `:163`
   ל-`:166` — תחסום את **השורה** אחרי שההזמנה כבר חיה בברוקר, כלומר תייצר
   פוזיציה בלי רישום: בדיוק מחלקת B-07 / TASK-105. המקום הנכון הוא **בראש
   `execute()` לפני `:121`** (עדיין order_manager ⇒ 128:22 ✅; עדיין קריאה
   טרייה ⇒ 259:44 ✅). זה שינוי-תכנון, לא פרט-מימוש.

2. **הקורא המשותף הוא fail-OPEN מעצם בנייתו.**
   ‏`sheets_manager.get_sheet_values` מחזיר `[]` גם כשהקריאה נכשלה
   (`if ws is None: return []`), ו-`get_sheet_records` מחזיר `[]` גם על
   `len(rows) < 2`. ⇒ סכימת-חום על `[]` נותנת **חום 0 ⇒ כניסה מאושרת**
   בדיוק כשהקריאה נפלה. זה מה ש-TASK-244:51 אוסר, והוא מגיע בחינם עם
   הקורא הקיים. ⚠️ ובנוסף `_SHEET_CACHE_TTL = 60` — "קריאה טרייה" עלולה
   להיות בת 60 שניות, מול חפיפת-ריצות 92.5% (‏259:44).

3. **המכנה אינו קיים בקוד.** אין `AGENT_MAX_PORTFOLIO_HEAT_PCT` ואין הון
   ב-`config.py`. ‏`orchestrator.py:183` נושא `buying_power` (ברירת-מחדל
   100,000), ו-`alpaca_broker.py:240-241` מחזיר ב-DRY_RUN `buying_power
   "200000.00"` לצד `equity "100000.00"`. **8% מהם נבדלים פי-2: 16,000$ מול
   8,000$.** ‏11,060/100,000 = 11.06% מרמז על `equity`, אך זו הסקה מהחשבון
   ולא הכרעה כתובה. ‏`build_account_state` אינו נושא `equity` כלל.

4. **⚠️ המכריע — חסימה על בסיס כמויות שגויות.** ‏`gate3_risk.py` מדד היום
   **205 מתוך 291 שורות מפרות** את אינווריאנטי-הזהות (E×Q≠PS), והמספר מאושר
   במקור בגוף TASK-279 ("205 of 291 rows violate the identity, worst case
   25,975 dollars on TTC"). החום הוא Σ0.10·E×Q. ⇒ תקרה שתיכנס עכשיו **תחסום
   כניסות אמיתיות על בסיס חישוב שידוע שחלקו שגוי**, ותיקון-הכמויות
   (‏TASK-279) מתוזמן ממילא אחרי 4/9. להנחית את הצרכן לפני הספק זה הסדר ההפוך.

### ⚠️ המחיר של ההכרעה — נרשם כדי שלא ייעלם

**החלון ייפתח בלי תקרת-חום, וההטיה תיקבע על המדגם כולו.** זה בדיוק הנימוק
המרכזי של D3 עצמו: בלי תקרה, ה-win-rate והאחוזים שנאספים מגיעים מפרופיל-חשיפה
**שאינו יכול להתקיים בחשבון חי**, ולכן המדידה אינה רפרודוקטיבית. החום הנמדד
היום, ‏$11,060 = 11.1%, כבר מעל תקרת 8% ומעל טווח 6-8% של `position-sizer` KP#6.

⇒ **זו הטיה ידועה, מכוונת ומתועדת** — לא פער שהתגלה בדיעבד. חייבת להירשם
בדוח-הכרעת-7/9 כהסתייגות, ולא להיקרא כתוצאה נקייה.

### התזמון

```
אחרי 4/9 · תלוי-TASK-279 · לא לפני שתוקנו הכמויות
```

════════════════════════════════════════════════════════════════════════════════
## ⚠️ שלוש שאלות פתוחות שה-recon חשף — **לא הוכרעו**

הן נרשמות כאן כדי שהמימוש שאחרי 4/9 לא יתחיל מאפס, ולא כדי לרמוז על תשובה.

1. **מהו המכנה של ה-8%?** ‏`equity` (100,000 ב-DRY_RUN) או `buying_power`
   (200,000)? המדידה שבתיק מרמזת על `equity`, אך הדבר לא הוכרע בכתב, וההפרש
   הוא פי-2 בתקרה. **פתוח.**

2. **איך נקראות הפוזיציות הפתוחות?** קורא ייעודי שמבחין בין כשל-קריאה לגיליון
   ריק, או `get_sheet_values` + בדיקת שורת-כותרת כמבחין (`rows[0]` ריק ⇒
   READ FAILURE ⇒ חסימה)? בשני המקרים נדרש `invalidate_cache` מיד לפני
   הקריאה, בגלל מטמון 60 השניות. **פתוח.**

3. **האם `position_manager` / `cached_portfolio_reader` מתאים יותר?** שניהם
   קיימים ונטענים ב-`orchestrator.py`, וייתכן שיש בהם קורא-פוזיציות מתאים
   מזה שנבחן. **לא נבדק ב-recon.** **פתוח.**

### הערת-היקף למימוש שאחרי 4/9

`tests/agent/unit/test_order_manager.py::TestEnterDecision` קורא `execute()`
על החלטת ENTER בסביבה בלי גיליון. שער חוסם בראש `execute()` יזהה זאת
כ-read-failure ⇒ יחסום ⇒ **הטסט ייפול**. זו ההתנהגות הנכונה, אך לפי חוק-2 של
`/rh-task` טסט קיים שנשבר = STOP מלא. ⇒ המימוש יידרש למנגנון-הזרקה
(‏`heat_reader` ב-`__init__`) או לדגל-כיבוי. ⚠️ **הסקה מקריאת-קוד, לא מדידה** —
הסוויטה לא הורצה.
