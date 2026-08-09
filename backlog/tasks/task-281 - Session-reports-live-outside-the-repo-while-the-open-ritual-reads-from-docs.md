---
id: TASK-281
title: Session reports live outside the repo while the open ritual reads from docs
status: To Do
assignee: []
created_date: '2026-08-09 02:32'
labels:
  - process
  - docs
  - session
dependencies: []
priority: medium
ordinal: 279000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Found 2026-08-08 during day close. SESSION_PROTOCOL.md section 3 step 2 requires docs/SESSION_HANDOFF_<date>.md, and the open ritual finds the latest via ls -1t docs/SESSION_HANDOFF_*.md | head -1. But the day reports of 2026-08-08 were written to ~/rhpro_audit_run/, which is outside the repo and outside git. The 8/8 handoff was copied into docs/ by hand so the next session is not stranded, and ls -1t now returns it - but the copy was manual, so the same gap reopens on the next session that forgets. This ticket is about the POLICY, not that one file.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
--- השאלה הפתוחה 2026-08-08 — ⚠️ לא הוכרע, הכרעת עמיחי בפתיחת שני ---

**מה שקרה בפועל 8/8:** דוחות-היום נכתבו ל-`~/rhpro_audit_run/` (מחוץ לריפו),
וה-handoff ביניהם. פתיחת-הסשן הבא הייתה מוצאת את
`docs/SESSION_HANDOFF_2026-08-06.md` — ישן ביומיים — ומפספסת יום שלם שכלל
חמישה PR מוזגים, שלוש הכרעות ושני שערים חדשים.

**נסגר נקודתית:** הקובץ הועתק **במלואו** ל-`docs/SESSION_HANDOFF_2026-08-08.md`,
ו-`ls -1t docs/SESSION_HANDOFF_*.md | head -1` מחזיר אותו (אומת גם לפי mtime
וגם לפי שם, כדי שלא יהיה תלוי בשיטת-המיון).

⚠️ **אבל ההעתקה הייתה ידנית** — ולכן אותו פער נפתח מחדש בכל סשן שיישכח.
זו בדיוק מחלקת-הכשל של 8/8: **"נראה מחובר ואינו"**.

**השאלה: איפה חי דוח-סשן, ואיך מובטח שריטואל-הפתיחה ימצא אותו?**

1. **א. הריפו הוא המקום היחיד.** ‏handoff נכתב ישירות
   ל-`docs/SESSION_HANDOFF_<תאריך>.md`, ו-`~/rhpro_audit_run/` נשאר לחומרי-גלם
   בלבד (‏recon, tsv, לוגים).
   *בעד:* מקור-אמת אחד; מסונכרן לכל מכונה; נשמר בהיסטוריה.
   *נגד:* דוחות-סשן נכנסים לריפו הציבורי ומגדילים אותו.

2. **ב. שני מקומות + אכיפה.** הדוחות נשארים ב-`audit_run`, וההעתקה ל-`docs/`
   הופכת לצעד-אכיפה: שער-CI או צעד בפרוטוקול שמוודא שקיים
   `docs/SESSION_HANDOFF_<היום>.md` בסוף כל סגירה.
   *בעד:* שומר על הריפו רזה.
   *נגד:* שני עותקים = סיכון-סטייה; והשער עצמו צריך בקרה דו-כיוונית, אחרת
   הוא עוד "נראה מחובר ואינו".

⚠️ **אין ברירת-מחדל. לא הוכרע.**

**הערת-היקף:** אם תיבחר (ב), השער חייב להיבדק בשני הכיוונים — יום בלי handloff
ב-`docs/` **חייב** להיכשל. שער שרק "עובר" ביום תקין אינו ראיה, כפי שהוכח
שלוש פעמים ב-8/8 (`gate266` grep-שווא · `gate265` כשל-ריק · שער-אזכור-הכלי
שנבדק ברנר בשני הכיוונים).

--- שאלה פתוחה שנייה 2026-08-08: שני קבצים בריפו שאינם במעקב ---

הביקורת הסופית של 8/8 מצאה שני קבצים **בתוך** הריפו שאינם ב-git ואינם
מוחרגים:

```
docs/auto-dancer/queue/QUEUE_2026-07-04.md   mtime 2026-07-04 22:52   252 B
docs/auto-dancer/queue/QUEUE_2026-07-05.md   mtime 2026-07-05 14:12   209 B
git check-ignore → exit 1   ⇒ אינם gitignored; לא-במעקב באמת
```

**נרשם כאן ולא כתיק חדש** כי זו אותה שאלה — **היכן חיים תוצרים ומה נמצא
במעקב** — רק בכיוון ההפוך: ‏281 עוסק בקבצים **מחוץ** לריפו שהריטואל צריך,
וזה קובץ **בתוך** הריפו שאיש אינו עוקב אחריו.

⚠️ **מה שאיני יודע, ומדווח ככזה:** למה `docs/auto-dancer/` קיים, מי יצר
אותו, ומה תפקיד קבצי ה-QUEUE. **אין להם אזכור באף מקום אחר בריפו** ואין
להם תיק. הם **מ-4-5 ביולי, לא מהיום** — לא נוצרו בעבודה של 8/8.

**השאלה:** האם הם תוצר-עבודה שצריך לעקוב אחריו · פלט זמני שצריך להיות
ב-`.gitignore` · או שריד שאפשר להסיר?
⚠️ **לא הוכרע, ולא נגעתי בהם.** ‏3 אפשרויות, אין ברירת-מחדל.

## Acceptance Criteria

- [ ] #1 עמיחי מכריע בין א׳ לב׳, וההכרעה נרשמת בגוף התיק.
- [ ] #2 אם (א): `SESSION_PROTOCOL.md` §3 שלב-2 מנוסח מחדש כך שהוא אומר
      במפורש שהכתיבה היא ל-`docs/`, ולא נשאר מקום לפרשנות.
- [ ] #3 אם (ב): שער שנכשל כשחסר `docs/SESSION_HANDOFF_<היום>.md` ביום שהיה
      בו סשן — **עם בקרה דו-כיוונית מוכחת**: יום עם קובץ עובר, יום בלי נכשל.
- [ ] #4 בשני המקרים: פתיחת-סשן אחת בפועל מוצאת את ה-handoff הנכון דרך
      `ls -1t`, ולא מהזיכרון.
- [ ] #5 הוכרע מה דינם של `docs/auto-dancer/queue/*` — מעקב · gitignore ·
      או הסרה. ⚠️ לא לפני שנקבע מה תפקידם; אין למחוק על סמך "לא מוכר".
<!-- SECTION:NOTES:END -->
