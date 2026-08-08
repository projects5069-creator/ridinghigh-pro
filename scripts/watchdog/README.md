# External Watchdog — installation

`watchdog_v1.gs` is a Google Apps Script. It is **not** part of the Python
system and nothing in the repo imports it. It exists because every detector we
already have (`check_04`, `check_06`, `detect_outage`) runs *inside* GitHub
Actions, so when Actions itself went down on 2026-08-06 all three stayed silent
while 374 runs piled up in the queue.

This one runs on Google's infrastructure. It needs no token, no service account
and no secret — the repo is public, so the Actions API answers unauthenticated.

---

## What it checks

Every 5 minutes, between **14:45Z and 19:45Z** only:

| signal | rule | healthy baseline (2026-08-05) |
|---|---|---|
| throughput | fewer than **10** runs completed in the last 15 min, **and** at least **40** completed in the hour before that | 26–34 per 15 min |
| queue depth | more than **25** runs sitting in `queued` | max 12 |

Either one alone triggers the mail. The second clause of the throughput rule is
what keeps weekends and holidays quiet: nothing ran, so nothing "stopped
running", so nothing fires — without the script needing a market calendar.

---

## Install — four manual steps

Everything here is by hand. There is no automated path, and that is the point:
the script's authorisation belongs to your Google account, not to any credential
the system holds.

### 1. Edit one line before pasting

Open `watchdog_v1.gs` and replace the placeholder on line 26:

```javascript
var ALERT_TO = 'PASTE_YOUR_EMAIL_HERE@example.com';   // ← EDIT ME
```

Nothing else needs editing. Leave `REPO`, the thresholds and `PER_PAGE` alone —
every one of those numbers was measured against real data, and the comment above
each says what was measured and when.

> ⚠️ `PER_PAGE` must stay **100**. At 50 the "hour before" count reads ~21 even on
> a perfectly healthy day, the gate never opens, and the watchdog never alerts.

### 2. Attach the script to the right spreadsheet

Open **`RH-Summaries`** → `Extensions` → `Apps Script`. Delete the stub
`myFunction`, paste the whole file, save.

> ⚠️ **`RH-Summaries`, not a monthly sheet.** The monthly files rotate on the 1st
> (`monthly_rotation`); a container-bound script on one of them dies at the next
> rotation.

### 3. Add the trigger

In the Apps Script editor: `Triggers` (clock icon) → `Add trigger`

| field | value |
|---|---|
| function | `rhWatchdogRun` |
| deployment | `Head` |
| event source | `Time-driven` |
| type | `Minutes timer` |
| interval | `Every 5 minutes` |

### 4. Authorise

The first run asks for permission — external requests (`UrlFetchApp`), mail
(`MailApp`) and the spreadsheet. Approve all three. Google will show an
"unverified app" warning; that is normal for a private container-bound script.

---

## Verify it works — without waiting for a real outage

### a. Prove the mail path (10 seconds)

In the editor, select **`rhWatchdogTestAlert`** from the function dropdown and
press `Run`. A mail with obviously fake numbers (`queued 999`) arrives at
`ALERT_TO`.

This function bypasses every threshold and **does not touch the dedup flag**, so
running it can never mask a real incident.

### b. Prove the checks themselves run

Select `rhWatchdogRun` and press `Run`. Then look at the `watchdog_log` tab —
the script creates it on first run. You should see one row:

```
TimestampUTC          Status           Queued  Recent15  Prior60  Alert  Reason
2026-08-06T18:05:12Z  HEALTHY          7       30        71
```

- inside the window on a trading day → `HEALTHY` with real numbers
- outside 14:45–19:45Z → `OUTSIDE_WINDOW` with blank counts (this is correct)
- `FETCH_FAILED` → the GitHub API was unreachable; **no mail is sent for this**

### c. Prove the thresholds fire, on demand

Temporarily set `QUEUE_DEPTH_MAX = -1`, save, run `rhWatchdogRun` once. Any queue
depth is then "too deep", so you get a real alert produced by the real decision
path — not a stub. **Set it back to 25 immediately afterwards**, then delete the
`RH_WATCHDOG_ALERT_ACTIVE` property (`Project Settings` → `Script Properties`) so
the next genuine incident still mails.

### d. Confirm the trigger is actually firing

After ~15 minutes there should be 3 new rows in `watchdog_log`. **A log that
stops growing during market hours is itself the signal that the watchdog died.**

---

## Mail behaviour

One mail per incident, not one every 5 minutes. Verified against the real
2026-08-06 data: 43 consecutive readings were in ALERT state and produced
**exactly one** mail.

The incident is declared over only after **3 consecutive healthy readings**
(15 minutes). One is not enough — on 2026-08-06 the readings at 16:20Z and
16:25Z came back healthy for ten minutes in the middle of the outage.

---

## Known boundaries — what this will not catch

1. **An outage that starts in the first hour of trading.** The rule needs
   "≥40 completions in the hour before". If everything is broken from 13:30Z that
   is never true and the watchdog stays silent. This is the direct price of
   having no holiday calendar.
2. **14:30–14:45Z and 19:45–20:00Z** are outside the window on purpose, to buy
   DST immunity without any DST logic.
3. **Runs that execute and fail.** It counts `completed`, not `success`. A day
   where every run fails looks perfectly healthy to it.
4. **Wrong data.** A run that succeeds and writes garbage looks perfect.
5. **A weekend reading counts toward the healthy streak.** If an incident is
   still open on Friday evening, Saturday's quiet readings will clear the flag
   and send a "recovered" mail. The following Monday's real outage would still
   alert correctly, so this is cosmetic — but it is not fixed.
6. **Google itself going down.** There is no watchdog for the watchdog. The two
   platforms failing together is the residual risk, and it is the whole reason
   this does not live in GitHub Actions.

---

## Where the numbers came from

`reports/2026-08-06_1439_watchdog_design.md` — measured against 08-05 (healthy,
973 completed runs) and 08-06 (the outage), at 5-minute steps across both days.
`reports/2026-08-06_1456_watchdog_build.md` — the dry-run that verified this file
reproduces a first alert at 16:05Z on the outage day and zero alerts on the
healthy day.
