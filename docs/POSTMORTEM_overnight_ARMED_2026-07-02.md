# Postmortem — Overnight Runner ARMED-in-fact despite documented DISARMED

**תאריך:** 2026-07-02 · **חומרה:** גבוהה (safety/autonomy) · **נזק בפועל:** אפס · **TASK-220**

**סיכום במשפט:** ה-overnight runner (`com.rh.overnight`) תועד כ-DISARMED מ-6/20, אך
בפועל ירה 9 לילות (6/20, ו-6/25→7/02) — **כולם ABORTED לפני שלב ה-execute**. השורש:
ב-6/20 בוצע `launchctl unload` בלבד, וה-plist נשאר על הדיסק ב-`~/Library/LaunchAgents/`,
כך ש-login/עֵרוּת מאוחרים טענו אותו מחדש. שני שומרים (auth-smoke + base-RED) עצרו כל
ריצה לפני עבודה אמיתית. תוקן ב-7/02 ע"י rename ל-`.disabled` + גיבוי, עם `launchctl list`
ריק מאומת.

---

## 1. Timeline (מבוסס לוגים)

מקור: `docs/overnight/raw/launchd.out.log` (מצרפי) + `docs/overnight/raw/<date>/run_<date>.log` (per-run).

| # | לילה (Lima) | שעה | Guard שעצר | Abort |
|---|-------------|-----|-----------|-------|
| 1 | 2026-06-20 | 02:11 | auth-smoke | `subscription auth smoke check failed` |
| 2 | 2026-06-25 | 02:04 | auth-smoke | `... (claude exit 1)` |
| 3 | 2026-06-26 | 02:10 | auth-smoke | `... (claude exit 1)` *(מופיע ב-per-run log; הושמט מהמצרפי)* |
| 4 | 2026-06-27 | 02:00 | auth-smoke | `... (claude exit 1)` |
| 5 | 2026-06-28 | 02:10 | **base-RED** | `base test suite is RED — refusing to build on a broken base` (base 12132d6) |
| 6 | 2026-06-29 | 02:12 | auth-smoke | `... (claude exit 1)` |
| 7 | 2026-06-30 | 02:10 | auth-smoke | `... (claude exit 1)` |
| 8 | 2026-07-01 | 02:11 | auth-smoke | `... (claude exit 1)` |
| 9 | 2026-07-02 | 02:13 | **base-RED** | `base test suite is RED ...` (base 17f7c78) |

- **פער 6/21–6/24 (4 לילות): אין ריצה** — עקבי עם Mac כבוי/ישן/logged-out ב-02:00 (ה-plist
  עם `RunAtLoad=false`, כך שטעינה-מחדש ב-login לא יורה מיד — היא רק רושמת מחדש את
  `StartCalendarInterval`, וה-02:00 הבא יורה).
- **גילוי:** 2026-07-02 — נצפה `base test suite RED` בלוג ה-launchd, שהוביל לחקירה שגילתה
  שהרנר פעיל-בפועל.
- **תיקון:** 2026-07-02 — `cp plist → .bak_20260702` (11:15) ואז `mv plist → plist.disabled`;
  `launchctl bootout` / ריקון מאומת.

---

## 2. Root Cause

**`launchctl unload` ≠ disable.** ב-6/20 השבתנו את הרנר ב-`launchctl unload` בלבד. זה מסיר
את ה-job מה-session הנוכחי של launchd, אבל **משאיר את קובץ ה-plist במקומו** ב-
`~/Library/LaunchAgents/com.rh.overnight.plist`. macOS טוען אוטומטית כל plist בתיקייה הזו
ב-login / הפעלה-מחדש של user session. לכן, ב-login מאוחר יותר (או יציאה-מ-sleep שיצרה
session חדש), ה-plist נטען מחדש, `StartCalendarInterval` (02:00) נרשם שוב, והרנר חזר לירות.

האימות ב-6/20 ("לא ב-`launchctl list`") היה **נכון לרגע-הבדיקה בלבד** ולא עמיד ל-login הבא —
זו בדיוק מלכודת ה-unload.

---

## 3. Why No Damage — Defense in Depth

אף ריצה לא הגיעה ל-execute. שני שומרים עצמאיים, בסדר, חסמו כל לילה:

1. **auth-smoke (guard #1)** — בדיקת אימות מנוי `claude` בתחילת הריצה. נכשלה ב-7/9 הלילות
   (6/20,25,26,27,29,30,7/1) → ABORT מיידי לפני כל שלב.
2. **base-RED (guard #2)** — "refusing to build on a broken base": כשה-auth **עבר**
   (6/28, 7/02), בדיקת חבילת-הטסטים של ה-base תפסה RED ועצרה. (זה אותו base-RED שמקורו
   ב-TASK-221 — טסט מיושן, לא רגרסיה; ראה postmortem נפרד.)

**אין ולו לילה אחד ששני השומרים עברו בו.** זה, ולא ה-unload, מה שמנע נזק. חשוב:
auth-smoke **לא "נשחק"** ב-7/2 — הוא עבר, וה-base-RED הוא שתפס. ההגנה שכבתית עבדה כמתוכנן.

בנוסף, אימות אפס-residue: אין branches חדשים מסוג auto/night מהחלון, אין draft PRs מ-
6/25→7/2 (ה-PRs האחרונים מ-6/08–6/12), `launchd.err.log` = 0 שורות.

---

## 4. Fix (בוצע 2026-07-02)

```
cp  ~/Library/LaunchAgents/com.rh.overnight.plist  ...plist.bak_20260702   # גיבוי (11:15)
mv  ~/Library/LaunchAgents/com.rh.overnight.plist  ...plist.disabled       # rename = login לא יטען
launchctl bootout  gui/$(id -u)/com.rh.overnight    # הסרה מה-session
```

**מצב מאומת אחרי התיקון:**
- `launchctl list | grep com.rh.overnight` → **ריק**.
- `~/Library/LaunchAgents/`: קיימים `com.rh.overnight.plist.disabled` + `com.rh.overnight.plist.bak_20260702`
  בלבד — **אין** `com.rh.overnight.plist` חשוף → login אינו יכול לטעון.

הסיבה ש-rename עובד היכן ש-unload נכשל: login-load סורק רק `*.plist`. סיומת `.disabled`
מוציאה את הקובץ מטווח-הסריקה לחלוטין.

---

## 5. Re-arm Checklist (כשנרצה להפעיל מחדש — supervised §11)

1. `mv ...plist.disabled ...plist` (החזרת השם).
2. `launchctl bootstrap gui/$(id -u) ...plist` (טעינה).
3. אמת: `launchctl list | grep com.rh.overnight` → **מופיע** עם Label.
4. אשר ששני השומרים חיים: auth-smoke + base-RED ירוקים.

## 5b. Re-DISARM Checklist (הנכון — לא unload בלבד)

1. `launchctl bootout gui/$(id -u)/com.rh.overnight` **וגם** `mv ...plist ...plist.disabled`.
2. אמת: `launchctl list | grep com.rh.overnight` → **ריק**.
3. אמת: אין `com.rh.overnight.plist` חשוף ב-`~/Library/LaunchAgents/`.

**bootout AND rename — שניהם. אחד לבד לא מספיק.**

---

## 6. Lesson

> **`launchctl unload` מסיר job מה-session; הוא לא משבית אותו.** כל plist שנשאר ב-
> `~/Library/LaunchAgents/` ייטען מחדש ב-login/reboot. השבתה עמידה = **הוצאת ה-plist
> מטווח-הסריקה** (rename ל-`.disabled` או העברה מחוץ לתיקייה) **בנוסף** ל-bootout.
> אימות "לא ב-launchctl list" תקף רק לרגע-הבדיקה — לא ל-login הבא.

**פעולת-המשך (לא בוצעה כאן):** תיקון מקורות שתיעדו DISARMED-שגוי — ראה §7.

---

## 7. Sources that documented DISARMED (to correct, not touched here)

| קובץ | שורה/הקשר |
|------|-----------|
| `docs/SESSION_HANDOFF_2026-06-20_overnight-disarmed.md` | :17 "Runner DISARMED — launchctl unload (מאומת: לא ב-launchctl list...)" |
| `docs/SESSION_HANDOFF_2026-06-19_overnight-armed.md` | :24 "`launchctl unload ~/Library/LaunchAgents/com.rh.overnight.plist`" |
| `docs/SESSION_HANDOFF_2026-06-24.md` | :49 "TASK-186 — overnight runner, parked/disarmed" |
| `docs/SESSION_HANDOFF_2026-06-27.md` | :5, :28 "TASK-186 ... [disarmed]" |
| `docs/SESSION_HANDOFF_2026-06-29.md` | :9 "TASK-186 overnight-runner [disarmed]" |
| `docs/WORK_PLAN_PRIORITIZED_2026-06-25.md` | :41 "DISARMED 6/20 ... להשאיר DISARMED" |
| `docs/BACKLOG_DETAILED.md` | :23 "במצב DISARMED (launchctl unload, 6/20)" |
| (memory) `project_overnight_runner.md` | "DISARMED 6/20 (launchctl unload; verified not listed...)" |

כל אלה יש לתקן ל-"DISARMED 7/02 (rename→.disabled + bootout, launchctl ריק מאומת);
ה-unload מ-6/20 לא החזיק — ראה postmortem זה."
