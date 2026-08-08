---
id: TASK-265
title: Deploy the external watchdog to Apps Script
status: To Do
assignee: []
created_date: '2026-08-06 20:12'
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
- [ ] #2 A test mail from `rhWatchdogTestAlert()` was received at `ALERT_TO`.
- [ ] #3 `ALERT_TO` no longer contains the placeholder string.
- [ ] #4 PK updated. Anti-Drift was deliberately deferred at commit time because
      an uninstalled file changes nothing about the live system; once the trigger
      is firing the watchdog IS part of the system and §4 applies (health checks).

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
