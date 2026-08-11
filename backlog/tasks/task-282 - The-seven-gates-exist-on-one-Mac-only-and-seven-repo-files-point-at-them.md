---
id: TASK-282
title: 'The seven gates exist on one Mac only, and seven repo files point at them'
status: To Do
assignee: []
created_date: '2026-08-09 03:09'
labels:
  - process
  - docs
  - risk
dependencies: []
priority: medium
ordinal: 280000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-08-08 in the final close audit. All seven acceptance gates live only in ~/rhpro_audit_run/audit_gate/ - gate1_truth.py, gate2_detection.py, gate3_risk.py, gate4_measurement.py, gate5_integrity.py, gate265_watchdog.py, gate266_timeout.sh. That directory is not a git repo, has no .git, and is not backed up anywhere known. Seven files inside the repo reference the two new gates by name, and fifteen reference rhpro_audit_run in total. TASK-265 AC#1 is literally run gate265_watchdog.py - so if the Mac is lost, a ticket cites an acceptance criterion that cannot be executed. Same class as TASK-257, where plans/stateless-seeking-sifakis.md is cited as evidence in six tickets and does not exist. The difference is that this one is still preventable.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
--- הממצא, מאומת 2026-08-08 22:0x ---

```
~/rhpro_audit_run/audit_gate/    gate1_truth.py · gate2_detection.py ·
                                 gate3_risk.py · gate4_measurement.py ·
                                 gate5_integrity.py · gate265_watchdog.py ·
                                 gate266_timeout.sh
~/rhpro_audit_run/.git           לא קיים — זו אינה ריפו
git ls-files | grep gate265/266  NOT IN GIT
```

**‏7 קבצים בריפו מפנים לשני השערים החדשים בשמם:**
`task-265` · `task-266` · `task-268` · `MASTER_REGISTER.md` ·
`RidingHigh_Pro_PK_v2.md` · `SESSION_HANDOFF_2026-08-08.md` · `WORK_PLAN.md`.
ובסך-הכל **15 קבצים** מפנים ל-`rhpro_audit_run`.

⚠️ **החומרה אינה בקבצים אלא בתלות:** ‏**AC#1 של TASK-265 הוא ממש "הרץ את
`gate265_watchdog.py`"**. אם המק אובד, התיק מצטט קריטריון-קבלה שאי-אפשר
להריץ — כלומר **הקריטריון הופך לבלתי-ניתן-לאימות**, לא רק לא-נוח.

**זו אותה מחלקה של TASK-257:** `plans/stateless-seeking-sifakis.md` מצוטט
כמקור-ראיה בשישה תיקים ואינו קיים; ה-RULING של 3/7 נשען עליו ואינו ניתן
לאימות. ההבדל היחיד: **כאן זה עוד ניתן למניעה.**

--- ⚠️ הנימוק שהוליד את המוסכמה — נמצא, ואינו "לא ידוע" ---

חיפשתי לפני שכתבתי, ויש נימוק מפורש בכתב:

> `TASK-277`: "SCOPE: `audit_gate/gate6_purity.py` **(outside the repo, zero
> production risk)**"

ובנוסף, שתי עובדות תומכות שאומתו: **הריפו הוא PUBLIC** (`gh repo view` →
`"PUBLIC"`), ו-`.gitignore:86` מחריג `research/` — כלומר יש עמדה עקבית
של "כלי-מחקר ותוצרי-ביקורת אינם נכנסים לריפו הציבורי".

⇒ **המיקום מכוון ומנומק. מה שאינו קיים הוא גיבוי.** "מחוץ-לריפו במכוון"
ו-"מגובה" הם שני דברים שונים, והתיק הזה עוסק רק בשני.

⚠️ **מה שכן נשאר פתוח כשאלה:** האם "zero production risk" נכתב כנימוק
לאי-הכנסה לריפו **בכלל**, או רק כהצדקה לכך שבניית שער אינה מסוכנת? הניסוח
תומך בשני הפירושים ואיני יודע להכריע ביניהם מהמקור. **שאלה לעמיחי.**

--- שלוש האפשרויות — ⚠️ לא הוכרע, אין ברירת-מחדל ---

**א · להכניס את `audit_gate/` לריפו**
- *בעד:* מקור-אמת אחד; מגובה אוטומטית בכל clone ובכל push; ה-15 ההפניות
  מהריפו מפסיקות להיות מצביעים-החוצה; ‏AC בר-הרצה לכל מי שמושך את הריפו.
- *נגד:* סותר את הנימוק המתועד של TASK-277; הריפו ציבורי, וחלק מהשערים
  קוראים `~/rhpro_audit_run` (`gate5_integrity.py:3`) ⇒ ייתכן שחושפים
  מבנה-ביקורת פנימי; ומגדיל את הריפו בכלי-מחקר.

**ב · להשאיר מחוץ לריפו ולגבות מחוץ למק**
- *בעד:* משמר את המוסכמה ואת הנימוק שלה; פותר בדיוק את הסיכון שהתיק מתאר;
  זול — זו תיקייה קטנה.
- *נגד:* גיבוי ידני נשכח, בדיוק כפי שקרה ל-handoff ב-TASK-281 (ההעתקה
  הידנית שנפתחת מחדש בכל סשן); ואין מנגנון שמוודא שהגיבוי עדכני.
  ⚠️ אם נבחרת — נדרש **שער** או צעד בפרוטוקול, ולא הבטחה.

**ג · להשאיר כמות-שהוא ולתעד את הסיכון**
- *בעד:* אפס עבודה; הסיכון מוכר ורשום.
- *נגד:* **זה בדיוק המצב של TASK-257** — סיכון מתועד שכבר התממש פעם אחת
  בפרויקט הזה. ותיעוד אינו מונע אובדן.

⚠️ **אין ברירת-מחדל. לא הוכרע.** הכרעת עמיחי.

## Acceptance Criteria

- [ ] #1 עמיחי מכריע בין א׳ / ב׳ / ג׳, וההכרעה נרשמת בגוף התיק עם הנימוק.
- [ ] #2 נענית השאלה הפתוחה: האם "zero production risk" הוא נימוק לאי-הכנסה
      לריפו בכלל, או רק לכך שבניית שער בטוחה.
- [ ] #3 אם (א) או (ב): **אימות חי שהעותק השני קיים ובר-הרצה** — לא שהוא
      הועתק, אלא ששער אחד לפחות רץ ממנו ומחזיר את אותה תוצאה. (‏`gate266`
      כבר הודגם כרץ משני מיקומים 8/8 — אותה שיטה.)
- [ ] #4 אם (ב): מנגנון שמוודא עדכניות — שער או צעד-פרוטוקול, **עם בקרה
      דו-כיוונית**: גיבוי מיושן חייב להיכשל, לא רק גיבוי חסר.
- [ ] #5 בכל מקרה: ‏7 ההפניות מהריפו לשערים נבדקות — קובץ שמצוטט כ-AC
      חייב להיות בר-הגעה מהמקום שבו התיק נקרא.
<!-- SECTION:NOTES:END -->

## הכרעת עמיחי 2026-08-10 — לגבות + לדחוף
השערים מגובים **וגם** נדחפים. עמיחי מוסיף עובדה שלא הייתה בתיק: התיקייה מגובה גם ל-Drive.
זה מרכך את הנימוק המרכזי של התיק (אובדן המק), אך אינו מבטל אותו — גיבוי-ענן אינו הופך
קובץ לבר-הרצה ממקום שבו התיק נקרא, ו-AC#1 של TASK-265 הוא ממש "הרץ את gate265_watchdog.py".
⚠️ תנאי-אימות שנשאר בעינו: **שער אחד לפחות חייב לרוץ מהעותק השני ולהחזיר את אותה תוצאה** —
לא די בכך שהועתק. gate266 כבר הודגם כרץ משני מיקומים (8/8); אותה שיטה.
⚠️ שאלת ה-scope של AC#2 ("zero production risk" — נימוק לאי-הכנסה לריפו בכלל, או רק
לכך שבניית שער בטוחה) **לא נענתה** בהכרעה זו.
