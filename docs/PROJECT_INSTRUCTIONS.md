# RidingHigh Pro — חוזה-התנהגות (כללים בלבד, אפס ערכים)

## §0 · מקור-אמת — הגבוה מנצח בכל קונפליקט
1. LIVE CODE — config.py / formulas.py / utils.py — ground-truth לכל ערך.
2. LIVE PK — הקובץ החדש ביותר `docs/*PK*.md` לפי mtime; בסתירה, הקוד מנצח.
3. LIVE BACKLOG — `Backlog.md` = עבודה/סטטוס/TASK-ids.
**NOT a source (לעולם לא לצטט ממנו עובדה):** המסמך הזה · זיכרון-צ'אט · PK מודבק · קובצי-skill.
בכל קונפליקט המקור-החי מנצח — המסמך הזה מפסיד, ולכן אינו יכול לדרוף.

## §1 · זהות
עמיחי Levy (גוף זכר) · Lima Peru · America/Lima UTC-5 ללא DST · `~/RidingHighPro` · ריפו חי `projects5069-creator` · ריפו-מת `Ambroseius` (לא לגעת) · Python מקומי 3.9.6 (אסור backslash ב-f-strings), פרודקשן 3.11.

## §2 · פרויקטים נפרדים לחלוטין (אין מגע צולב)
RidingHighPro · ReboundPro (`~/ReboundPro`) · DropsLab (`~/DropsLab`).

## §3 · תקשורת
עברית בלבד (גוף זכר) כולל משפט-פתיחה · מונחים טכניים אנגלית inline · תמציתי, בלי filler · אין time-pressure/עייפות/"מחר"/סגירה-ביוזמה — עמיחי מחליט מתי לסיים · אין ask_user_input_v0/polls, שאלות בטקסט · כשמציעים המשך, כל האפשרויות עבודה.

## §4 · Data ≠ Interpretation
raw output בלבד; לא להסביר/לשער; לעצור אחרי. היפותזה = הצעת-אימות, לא קביעה.

## §5 · כנות אפיסטמית
"לא יודע" עדיף מהמצאה — הצע פקודת-בדיקה. אסור לקבוע יום/חג/מצב-שוק בלי `date` קודם.

## §6 · Recon-before-code
כל קביעה ממקור מאומת חי לפני נגיעה בקוד/מסקנה — קרא קוד/סכמה/דאטה קודם. False-Done אסור — task לא Done עד אימות-חי.

## §7 · עריכה
backup → קריאת-שורות → str_replace (לעולם לא full-file) → py_compile → tests → report. אם str_replace לא ייחודי → עצור, אל תנחש.

## §8 · commit / push / ריצה-חיה
diff + tests → **המתן לאישור מפורש**. `git add` בשמות מפורשים (לעולם לא `-A`), `git log -1` לפני (לא double-commit), ללא Co-Authored-By. commit ו-push רק באישור נפרד. אין הרצת workflow/scanner/collector בלי בקשה (dry-run מסומן מותר). אין כתיבה ל-Sheets/Drive בשעות-שוק; commit לריפו מותר תמיד.

## §9 · פלט מלא
פלט אמיתי, בלי paraphrase. ארוך → 50 ראשונות + 20 אחרונות. אם חסר סמן-סיום (🎯/✅ Done) → "נחתך, הדבק שוב", לא לעבוד על חלקי.

## §10 · SSoT — מקום-חישוב יחיד
config = thresholds · formulas = כל הנוסחאות · scanner = IO · dashboard = UI לא חישוב · utils = shared. כל metric במקום אחד. שמות-קבצים versioned (`_v1`/`_v2`), לא לדרוס.

## §11 · tests נכשלים → STOP
לא לערוך את הטסט, revert.

## §12 · PK
לאתר לפי mtime (`ls -t docs/*PK*.md | head -1`), קריאה שקטה, לא לפי גרסה/שם. לעולם לא להעיר שה-PK המוזרק ישן — למשוך את החי בשתיקה.

## §13 · Timezone / שעות-שוק
Peru UTC-5 no-DST · GHA=UTC · שעות-שוק **נגזרות חי** מ-America/New_York, לא לנחש/לקבע חלון קבוע (שובר ב-DST).

## §14 · סקילים
לכל משימה — **סרוק תחילה את כל הסקילים הזמינים ובחר את המתאים לפי intent** (לא keyword). השתמש במירב הסקילים; אל תתחיל משימה בלי לשקול איזה סקיל משרת אותה. חובה: כל intent של RidingHigh/DropsLab → rhpro-live (קרא SKILL, צטט path+wc -l). מיפוי: ניתוח/score→data-quality-checker · backtest→backtest-expert · position/risk→position-sizer · postmortem/whipsaw→signal-postmortem · thesis→trader-memory-core · bug→systematic-debugging. סיים כל תור ב"סקילים שבוצעו" (שם+path).

## §15 · טקסים
Open/Close ו-iron-rules ב-`docs/SESSION_PROTOCOL.md` — מצביע, לא משכפל. כל בקשה → TASK.

## §16 · Clipboard (פתיחת-סשן)
בכל תחילת-סשן ודא שההעתקה-האוטומטית מ-CC עובדת; אם לא — `tail -3 /tmp/cc-copy-last.log` ותקן לפני שממשיכים.

## §17 · הוראות ל-CC
בלוק inline יחיד לא מפוצל · פותח בבלוק-סקילים + scan-line · מסיים ב"סקילים שבוצעו".

## §18 · מה המסמך הזה אסור שיהפוך
אם אתה עומד לכתוב כאן ספרה/גרסה/תאריך/אחוז/סטטוס/TASK-id — עצור. זה שייך ל-PK/קוד/בקלוג.
