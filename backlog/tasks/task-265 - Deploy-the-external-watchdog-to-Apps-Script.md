---
id: TASK-265
title: Deploy the external watchdog to Apps Script
status: In Progress
assignee: []
created_date: '2026-08-06 20:12'
updated_date: '2026-08-09 00:46'
labels: []
dependencies: []
priority: high
ordinal: 263000
---


## Description

The code landed in `scripts/watchdog/watchdog_v1.gs` (commit 4406a92). It does
nothing until it is installed by hand. This ticket is the installation.

It is deliberately manual. The authorisation belongs to the owner's Google
account, not to any service account or GitHub secret the system holds — which is
the whole point: the watchdog survives every credential the system has expiring,
and it survives GitHub Actions being down, which is what happened on 2026-08-06.

## The four steps

1. **Edit one line.** `ALERT_TO` at the top of `watchdog_v1.gs`, currently
   `PASTE_YOUR_EMAIL_HERE@example.com`. Nothing else needs editing.
   ⚠️ Leave `PER_PAGE = 100` alone. At 50 the prior-hour count reads ~21 even on
   a healthy day, the anti-false-alarm gate never opens, and the watchdog never
   alerts at all. Measured against both 08-05 and 08-06 before the file was written.
2. **Attach it to `RH-Summaries`** → Extensions → Apps Script → paste → save.
   ⚠️ `RH-Summaries`, NOT a monthly sheet. The monthly files rotate on the 1st
   (`monthly_rotation`); a container-bound script on one of them dies at the next
   rotation.
3. **Add the trigger:** function `rhWatchdogRun`, time-driven, minutes timer,
   every 5 minutes.
4. **Authorise** UrlFetchApp + MailApp + the spreadsheet on first run. Google
   shows an "unverified app" warning; that is normal for a private
   container-bound script.

## Three ways to verify without waiting for a real outage

- `rhWatchdogTestAlert()` from the editor → a mail with obviously fake numbers.
  It does not touch the dedup flag, so it cannot mask a real incident.
- `rhWatchdogRun()` manually → one row appears in the `watchdog_log` tab, which
  the script creates on first run.
- `QUEUE_DEPTH_MAX = -1` temporarily → a real alert through the real decision
  path, not a stub. Set it back to 25 and delete the
  `RH_WATCHDOG_ALERT_ACTIVE` script property afterwards.

## Acceptance Criteria

- [ ] #1 A row exists in `watchdog_log` from a real trigger firing — not from a
      manual `Run` in the editor. Confirmed by three or more consecutive rows
      five minutes apart during market hours.
      ❌ 2026-08-08: NOT met — but only one half of it is missing now.
      The trigger DOES fire on its own: `watchdog_log` holds four automatic rows
      at 00:30:27 · 00:35:28 · 00:40:27 · 00:45 (5:00 and 4:59 apart), after the
      manual 00:27:47. What is still missing is that they fall INSIDE market
      hours: all five read `OUTSIDE_WINDOW`, correct for 00:2x-00:4xZ against a
      14:45-19:45Z window (`watchdog_v1.gs:35-36`). Saturday makes it impossible
      before Monday. Gate: `audit_gate/gate265_watchdog.py`.
- [x] #2 A test mail from `rhWatchdogTestAlert()` was received at `ALERT_TO`.
      ✅ 2026-08-08: MET. Gmail screenshot — delivered to `projects5069@gmail.com`
      at 19:28, subject "RH WATCHDOG: GitHub Actions pipeline is not producing",
      body `Detected at 2026-08-09T00:28:21.024Z` with
      "MANUAL TEST — triggered by hand from the Apps Script editor" and the
      deliberately fake numbers: queued 999 (ceiling 25) · completions 15 min 0
      (floor 10) · completions 60 min 120 (gate 40).
      Independent corroboration: `projects5069@gmail.com` is the repo owner
      identity (`git log -1 --format='%an <%ae>'` → `Amihay <projects5069@gmail.com>`).
      The fake numbers also confirm it came from `rhWatchdogTestAlert()` and not
      from a live breach.
- [x] #3 `ALERT_TO` no longer contains the placeholder string.
      ✅ 2026-08-08: MET, derived from #2. A mail addressed to
      `PASTE_YOUR_EMAIL_HERE@example.com` cannot land in עמיחי's inbox —
      `example.com` is RFC-2606 reserved and accepts no mail. Delivery to
      `projects5069@gmail.com` is therefore proof that `ALERT_TO` was edited.
      ⚠️ Note the earlier reasoning that this REVERSES: "Execution completed"
      alone would NOT have proven it, because `MailApp.sendEmail` to
      `…@example.com` completes without throwing. It is the RECEIPT, not the
      execution, that closes this.
      ⚠️ The repo copy still reads
      `watchdog_v1.gs:24  var ALERT_TO = 'PASTE_YOUR_EMAIL_HERE@example.com';`
      — correct and intentional: the repo copy is the TEMPLATE, and the address
      belongs in the installed copy only, never in a public repo.
- [ ] #4 PK updated. Anti-Drift was deliberately deferred at commit time because
      an uninstalled file changes nothing about the live system; once the trigger
      is firing the watchdog IS part of the system and §4 applies (health checks).
      ❌ 2026-08-08: not done. Becomes due once #1 passes.

════════════════════════════════════════════════════════════════════════════════
## ✅ ההתקנה בוצעה 2026-08-08 (עמיחי) — ⚠️ התיק **לא נסגר**

**השאלה הפתוחה "מתי מתקינים" הוכרעה: אופציה א׳ — לפני פתיחת החלון.** בוצע.

### ארבעת צעדי-ההתקנה — מה שהראיות מכסות

| צעד | ראיה | מצב |
|---|---|---|
| 2 · מוצמד ל-**RH-Summaries** | טאב `watchdog_log` **נוצר ב-RH-Summaries** (הסקריפט יוצר אותו בריצה הראשונה) | ✅ ועל הקובץ הנכון — לא על גיליון חודשי שמתחלף ב-1 לחודש |
| 3 · טריגר | ‏`rhWatchdogRun` · Time-based · Head · Owned by Me | ✅ **רשום** |
| 4 · הרשאות | ‏`rhWatchdogRun` ידני 19:27:47→19:28:01 "Execution completed"; השורה נושאת `Queued=1` | ✅ ‏UrlFetchApp אושר וקריאת GitHub API החזירה מספר — `decide_()` מקבל `queued` כפרמטר, כלומר ה-fetch קרה לפני ה-early-return |
| 1 · `ALERT_TO` נערך | המייל נחת ב-`projects5069@gmail.com` — ‏`@example.com` שמור ב-RFC 2606 ואינו מקבל דואר | ✅ ‏AC#3 |
| — | ‏`rhWatchdogTestAlert` 19:28:20→19:28:21, **והמייל התקבל** ב-19:28 | ✅ ‏AC#2 |
| — | שם הפרויקט שונה ל-**`RH Watchdog`** | ✅ |

השורה הראשונה שנרשמה:
`2026-08-09T00:2* · OUTSIDE_WINDOW · Queued=1 · Recent15/Prior60 ריקים`
— **תואם בדיוק את הקוד:** ב-00:2xZ הריצה חוזרת מוקדם ב-`watchdog_v1.gs:113-114`
ולכן `recent`/`prior` נשארים `null`. התנהגות תקינה, לא תקלה.

### ⚠️ למה התיק לא נסגר — נותר **חוסר אחד**

‏**AC#1 בלבד** (ואחריו AC#4). ‏AC#2 ו-AC#3 נסגרו 8/8 — ראו הראיות אצל
הקריטריונים עצמם.

**מה כן הוכח ב-AC#1:** הטריגר **יורה מעצמו** — ארבע שורות אוטומטיות רצופות
במרווחי 5:00/4:59 (‏00:30:27 · 00:35:28 · 00:40:27 · 00:45), אחרי הידנית
ב-00:27:47. **טריגר רשום אינו טריגר שיורה — וכאן כבר הוכח שהוא יורה.**

**מה עדיין חסר:** שהשורות ייפלו **בתוך שעות-המסחר**. כולן `OUTSIDE_WINDOW`, כי
זו שבת. ⇒ מה שנבדק בשני אינו "האם הטריגר יורה" אלא **האם ה-watchdog עושה את
עבודת-הספירה** כשהחלון פתוח — ‏`Recent15`/`Prior60` מתמלאים ו-`Status` חדל
להיות `OUTSIDE_WINDOW`.

‏AC#4 (PK) יבוצע כשה-#1 יעבור — כלשון הקריטריון עצמו.

### מה נדרש כדי לסגור

```
שני 10/8, בין 14:45 ל-19:45Z:  ./gate265_watchdog.py 2026-08-10   ⇒ AC#1
ואז:                            עדכון PK                          ⇒ AC#4 → סגירה
✅ AC#2 · AC#3 נסגרו 8/8 — ראו למעלה
```

════════════════════════════════════════════════════════════════════════════════
## עדכון 2026-08-08 · הטריגר **יורה מעצמו** — ו-AC#1 עדיין לא נסגר

קריאה ישירה של `watchdog_log` דרך חשבון-השירות (‏`gc.open("RH-Summaries")`,
קריאה בלבד) — לא צילום-מסך:

```
TimestampUTC              Status          Queued
2026-08-09T00:27:47.274Z  OUTSIDE_WINDOW  1     ← הריצה הידנית
2026-08-09T00:30:27.816Z  OUTSIDE_WINDOW        ← טריגר אוטומטי
2026-08-09T00:35:28.001Z  OUTSIDE_WINDOW        ← +5:00
2026-08-09T00:40:27.972Z  OUTSIDE_WINDOW  1     ← +4:59
2026-08-09T00:45:…        OUTSIDE_WINDOW        ← נחתה בזמן הבדיקה
```

**זה מוכיח את החלק הקשה של AC#1: הטריגר יורה מעצמו, בקצב 5 דקות.** ארבע שורות
רצופות שלא נוצרו ביד.

⚠️ **ובכל זאת AC#1 לא נסגר**, כי הקריטריון דורש את השורות **בשעות-מסחר**, וכולן
`OUTSIDE_WINDOW` — שבת. מה שנותר לאמת בשני אינו "האם הטריגר יורה" אלא **האם
ה-watchdog עושה את עבודת-הספירה שלו** כשהחלון פתוח: ‏`Recent15`/`Prior60`
מתמלאים והשורש `Status` חדל להיות `OUTSIDE_WINDOW`.

### שער-קבלה ל-AC#1 — קיים ובר-הרצה

```
~/rhpro_audit_run/audit_gate/gate265_watchdog.py     (chmod +x, לצד gate266)
   /usr/bin/python3 gate265_watchdog.py 2026-08-10
```

⚠️ ‏`gate6_` שמור לשער-הטוהר של TASK-277 (‏WORK_PLAN, M3) — ולכן הקובץ נושא את
מספר-**התיק**, כמו `gate266_timeout.sh`. אל תשנה ל-gate6.
⚠️ בניגוד ל-`gate4_measurement.py`, השער הזה **אינו** חוסם כששוק פתוח — הוא
נועד לרוץ דווקא אז.

**נבדק דו-כיוונית 8/8, לא רק נכתב:**
```
שלילי (חלון אמיתי, שבת):        streak 0  → FAIL exit=1  ✅ כדין
חיובי (GATE265_WINDOW=00:25-01:00): streak 4  → PASS exit=0  ✅ המונה עובד
```
הבקרה החיובית נדרשה כי הריצה השלילית לבדה נכשלת על "אפס שורות בחלון" — כשל ריק
שאינו בודק את מונה-הרצף כלל. ה-override הוא לבדיקה בלבד, בסגנון
`WINDOW_GUARD_DATE` ב-`window_guard.sh`, ומדפיס אזהרה כשהוא פעיל.

⚠️ **מה השער לא יכול להוכיח:** הוא רואה שורות, לא את מקורן — שורה ידנית נראית
כמו שורה מטריגר. ההפרדה היא הקצב (‏≥3 ברצף במרווח 3-8 דקות). מי שילחץ Run שלוש
פעמים בדיוק במרווחי 5 דקות יטעה אותו; זו הטעיה עצמית מכוונת, לא כשל שקט.

**ובנוסף:** שם פרויקט ה-Apps Script שונה מ-`Untitled project` ל-**`RH Watchdog`**.

## Known boundaries, recorded so they are not rediscovered as bugs

- Silent if the outage starts in the first hour of trading — the rule needs
  "40 completions in the hour before" and that is never true from 13:30Z.
- 14:30-14:45Z and 19:45-20:00Z are outside the window on purpose, to buy DST
  immunity without DST logic.
- Counts `completed`, not `success`: a day where every run fails looks healthy.
- A weekend reading advances the healthy streak, so an incident still open on
  Friday evening gets a cosmetic "recovered" mail on Saturday.

Design: `reports/2026-08-06_1439_watchdog_design.md`
Build + dry run: `reports/2026-08-06_1456_watchdog_build.md`

--- השאלה הפתוחה 2026-08-08 (מתוכנית-העבודה) — לא הוכרע ---
הקוד קיים, ההתקנה ידנית ובחשבון-Google של עמיחי בלבד. ארבעת הצעדים מפורטים
בגוף התיק (שורות 26-39) ואינם משתנים.

**השאלה: מתי מתקינים?**
1. א. **לפני פתיחת החלון (עד 10/8)** — כיסוי מהיום הראשון; נפילה שקטה בתוך
      החלון מתגלה תוך 5 דקות במקום בדיעבד. המחיר: חצי-שעה מהזמן שלך היום-מחר.
   ב. בשבוע הראשון של החלון — פער-כיסוי של ימים ספורים; אם דווקא בהם תיפול
      המערכת, אותם ימים אבודים ובלתי-ניתנים לשחזור (בדיוק מה שקרה ב-7/8).
   ג. אחרי החלון — החלון כולו ללא רשת-ביטחון.
   ⚠️ אין ברירת-מחדל. **לא הוכרע** — זו פעולה שרק אתה יכול לבצע.

2. מה קורה ל-TASK-268 בינתיים? `detect_outage` סומן למחיקה **מותנית** בהתקנה
   הזו. כל עוד לא הותקן — אין למחוק, אחרת המערכת נשארת בלי שום גלאי-נפילות.
   ⇒ **268 חסום על התיק הזה. הסדר אינו הפיך.**
