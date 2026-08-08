---
id: TASK-266
title: 'agent_minute runs are killed by the 5-minute timeout, 188 of 487'
status: To Do
assignee: []
created_date: '2026-08-06 20:12'
updated_date: '2026-08-08 23:05'
labels: []
dependencies: []
priority: medium
ordinal: 264000
---


## Description

Found while measuring something else (queue recon, 2026-08-06). Not caused by
the outage — it predates it and is a normal-day condition.

Sampled 60 runs from the busiest hour of 2026-08-05 (19:00-20:00Z) and read
`started_at`/`completed_at` at the **job** level, which is the only API that
exposes the real execution moment:

```
n=60   job duration: median 315s · max 317s · min 36s
conclusions: cancelled=58, success=2
```

`agent_minute.yml:16` sets `timeout-minutes: 5` (=300s). 315s is 300s plus
runner overhead. These are not manual cancellations — they are the timeout
cutting the job off mid-work.

Full count across two days:

```
2026-08-05  agent_minute  cancelled 188  success 299   ->  38.6% cancelled
2026-08-05  auto_scan     cancelled  72  success 414   ->  14.8% cancelled
```

## Why it matters beyond the runs themselves

1. **Nearly two in five agent runs did not finish their work.** Whatever the
   orchestrator was doing at 300s — monitoring positions, writing decisions —
   stopped there.
2. **It silently poisons the baseline.** The "median 203s" figure that TASK-259
   is built on was measured on a day where 38.6% of runs were being cut at 300s.
   A truncated run cannot report a duration longer than the truncation.
3. **It feeds `check_06`.** `cancelled` lands in the denominator but not the
   numerator, and does not trigger the RECOVERING gate — see TASK-267.

## Acceptance Criteria

- [x] #1 Determine what the run is doing when it hits 300s — is the timeout too
      tight, or is the run genuinely stuck?
      ✅ 2026-08-08: neither. The run was CRAWLING on Sheets 429, not working.
      Two killed runs read in full — see the decision section below.
- [x] #2 Decide: raise `timeout-minutes`, or fix what makes the run slow.
      ⚠️ `.github/workflows/` is a protected path; the change needs explicit approval.
      ✅ 2026-08-08 (עמיחי): NEITHER — option ג׳, leave the ceiling, measure Monday.
      Zero code change. Reasoning in the decision section below.
- [ ] #3 Re-measure the `agent_minute` duration baseline on a day with no
      timeout truncation, and correct TASK-259 with the honest number.
      ⇒ superseded by the runnable acceptance gate below (Monday 10/8).

Evidence: `reports/2026-08-06_1406_queue_recon.md` §3ב

--- השאלה הפתוחה 2026-08-08 (מתוכנית-העבודה) — לא הוכרע ---
`agent_minute.yml:16` קובע `timeout-minutes: 5`, וחציון-הריצה 315 שניות —
כלומר התקרה חותכת את הריצה החציונית. ‏38.6% מבוטלות ביום מדוד.

**השאלה: מה עושים עם התקרה לפני פתיחת החלון?**
1. א. **להעלות את התקרה** (למשל ל-8-10 דקות) — הריצות מסיימות את עבודתן,
      ואובדן-הכתיבות של B-07 מצטמצם מיידית; המחיר: ריצות ארוכות יחפפו יותר
      (מחמיר את הבעיה של TASK-259), ועלות-דקות-Actions עולה.
   ב. לתקן את האיטיות במקום להעלות — נכון יותר לטווח ארוך; המחיר: דורש
      אבחון של מה קורה ב-300 השניות, ולא בטוח שיסתיים לפני שני.
   ג. לא לגעת — ‏38.6% מהריצות ימשיכו להיקטע לאורך כל החלון, וכל יום מאבד
      חלק מהכתיבות.
   ⚠️ `.github/workflows/` נתיב מוגן — כל שינוי דורש אישור מפורש.
   ⚠️ אין ברירת-מחדל. ~~**לא הוכרע.**~~ ✅ **הוכרע 8/8 — ראו למטה.**

2. אם נבחר (א) — באיזה ערך בדיוק? הנתון שיש: חציון 315ש, מקסימום 317ש
   במדגם n=60. **פתוח.** ⇒ התייתר: נבחרה ג׳.

⚠️ **תלות-סדר:** ההכרעה כאן חייבת לקדום את TASK-259 — ה-baseline של 259
מזוהם כל עוד ריצות נקטעות.

════════════════════════════════════════════════════════════════════════════════
## ✅ הכרעה 2026-08-08 (עמיחי) — אופציה ג׳: לא נוגעים בתקרה, מודדים בשני

**ההכרעה:** `timeout-minutes: 5` נשאר כמות שהוא. מודדים ביום שני 10/8 על
נתונים אמיתיים, ומחליטים על הנתונים. אפס שינוי קוד עכשיו.

**חמשת הנימוקים — כולם מה-recon של 8/8** (מלא: `~/rhpro_audit_run/TASK266_RECON.md`):

1. **‏38.6% לא מתאר את המערכת היום.** הוא נמדד ב-8/5, במשטר שלפני `fcdb0aa`
   (SMA20 בבקשה אחת) ו-`1df9cba` (handle של sentinel פעם-בריצה), ובתוך סערת-429.
   ‏8/7, אחרי שני התיקונים: **492 ריצות, 0 מבוטלות, חציון-job 48ש, p90 56ש.**

2. **התקרה שוברת לולאת-משוב מתגברת — העלאתה מעמיקה את הסערה.** השרשרת
   שנמדדה ב-8/5: חפיפת-ריצות → ‏QPS מצטבר על Sheets → מכסה ממוצה → ‏429 → כל
   ריצה זוחלת → עוד חפיפה. תקרת 300ש היא מה שמגביל היום את מספר הזוחלות
   במקביל ל-‏~5 (cron דקתי × 5 דקות). תקרת 10 דקות ⇒ עד ~10 זוחלות על אותה
   מכסה ממוצה. **וביום בריא (חציון 48ש) התקרה לא נוגעת באף ריצה** ⇒ ההעלאה
   משנה התנהגות **רק** בסערה, ושם לרעה.

3. **אין שום מספר שתומך בערך חלופי.** "חציון 315ש / מקס 317ש" הוא **הד-החיתוך**:
   ריצה שנחתכת ב-300ש מדווחת ~315ש עם runner overhead. משך-האמת של ריצה
   זוחלת-429 אינו ידוע וכנראה בלתי-חסום. כל ערך שנבחר (8? 10?) הוא ניחוש.

4. **נימוק-העלות שבתיק בטל.** `gh repo view` → `"visibility": "PUBLIC"` ⇒ דקות
   Actions חינם. "עלות-דקות-Actions עולה" שנכתב באופציה א׳ אינו קיים.

5. **הריצות ההרוגות זחלו, לא עבדו.** בשתי ריצות שנקראו לוג-מלא
   (`31041934094`, `31041857711`): ה-orchestrator עלה תוך ~52ש, ואז שרשרת
   `Failed to log sentinel event … APIError: [429]`, ובסוף
   `skip_summary flush failed … [429]` + `shadow_gate flush failed … [429]`,
   ואז `Terminate orphan process (python)` ב-~317ש. **גם ה-flushes שכן הספיקו
   לרוץ נכשלו על 429** ⇒ בסערה הכתיבות מתות גם בלי החיתוך. תקרה גבוהה יותר
   לא הייתה מצילה אותן.

### ⚠️ הקלף-הנגד — נרשם כדי שלא ייעלם

**אם סערת-429 תחזור בשבוע הראשון של החלון, כל יום כזה מאבד כתיבות עד שתיפול
הכרעה חוזרת.** זה בדיוק התרחיש שהתיק נפתח עליו. ההכרעה ג׳ מהמרת על כך
ש-8/7 מייצג את המשטר החדש — והימור זה מה שהמדידה בשני אמורה לאשש או להפריך.
אם השער נכשל, זה לא "התיק נפתח מחדש" בלבד: זו עדות שההימור היה שגוי.

### ⚠️ שני סייגים על נתוני-הבסיס של ההכרעה

- **‏8/7 חשוד כמדגם:** זהו יום ה-FINVIZ השבור (תוקן 8/8, PR #37). בלוגים חוזר
  `No signals to process this minute` ⇒ הריצות קצרות גם משום שלא הייתה
  עבודת-סיגנלים. **המדידה בשני היא הראשונה עם סיגנלים אמיתיים אחרי התיקונים.**
- **אין אף יום נקי עד היום:** ‏8/5 לפני-תיקונים+סערה · 8/6 outage של GitHub
  (‏13 cancelled + 15 failure) · 8/7 בלי סיגנלים.

════════════════════════════════════════════════════════════════════════════════
## שער-קבלה (מחליף את AC#3) — להריץ ביום מסחר עם סיגנלים אמיתיים

הרצה ראשונה מתוכננת: **שני 10/8, אחרי סגירת-הייצור.** ‏קריאה-בלבד ⇒ מותר בחלון.

**מה נמדד:** אחוז ריצות מבוטלות (יום שלם) · חציון ו-p90 של משך-job · האם
הופיעו 429 אמיתיים · חפיפת-ריצות בפועל.

**ספים:**
- **מבוטלות < 5.0% ⇒ PASS — התיק נסגר.** התקרה אינה חותכת ריצות.
- **מבוטלות ≥ 5.0% ⇒ FAIL — התיק נפתח מחדש** עם המספרים שנמדדו, וההכרעה
  בין א׳ ל-ב׳ נשקלת שוב על נתונים ולא על 8/5.
- החציון / p90 / חפיפה / 429 **נרשמים בכל מקרה** — הם ה-baseline הישר של
  TASK-259 (ראו הערה שם).

**איפה הוא יושב — זה העותק הקנוני:**

```
~/rhpro_audit_run/audit_gate/gate266_timeout.sh     (chmod +x, לצד חמשת השערים)
   ./gate266_timeout.sh 2026-08-10
```

⚠️ ‏`gate6_` **שמור** לשער-הטוהר של TASK-277 (‏WORK_PLAN, אבן-דרך M3) — ולכן
הקובץ נושא את מספר-**התיק** ולא מספר-נושא. אל תשנה לו שם ל-gate6.

**הפקודה** — הורצה בפועל 8/8 מול 8/7, גם מ-`~/RidingHighPro` וגם מ-`audit_gate/`,
ושתי הריצות החזירו את אותם מספרים:

```bash
#!/bin/bash
# TASK-266 acceptance gate.  Usage:  ./gate266_timeout.sh 2026-08-10
set -eu
DAY="${1:?usage: ./gate266_timeout.sh YYYY-MM-DD}"
GH=~/bin/gh; REPO=projects5069-creator/ridinghigh-pro; WF=agent_minute.yml; SAMPLE=60

echo "════ TASK-266 GATE — $WF on $DAY ════"
# ⚠️ --repo is REQUIRED. `gh run list` / `gh run view` infer the repo from the git
# context of the CWD. Run this from audit_gate/ (not a git repo) without it and the
# gate dies on "failed to determine base repo". Caught 2026-08-08 by running it from
# the new location instead of assuming the copy worked. `gh api` already carries the path.
CONC=$($GH run list --repo "$REPO" --workflow=$WF --created "$DAY" --limit 1000 --json conclusion \
       --jq 'group_by(.conclusion) | map({c: .[0].conclusion, n: length}) | .[] | "\(.c)\t\(.n)"')
echo "--- conclusions (whole day) ---"; echo "$CONC"
TOT=$(echo "$CONC" | awk -F'\t' '{s+=$2} END {print s+0}')
CAN=$(echo "$CONC" | awk -F'\t' '$1=="cancelled" {s+=$2} END {print s+0}')
PCT=$(awk -v c="$CAN" -v t="$TOT" 'BEGIN {printf "%.1f", (t?100*c/t:0)}')
echo "total=$TOT  cancelled=$CAN  => ${PCT}%"; echo

# API returns newest-first, so per_page=60 over the session window = the LAST 60
# runs = consecutive minutes, which is what the overlap metric needs.
# Verified 2026-08-07: starts ran 19:01:09Z .. 19:59:12Z, unbroken.
echo "--- job-level timing, last $SAMPLE runs of the 14:00-20:00Z session ---"
: > /tmp/g266.tsv
for id in $($GH api "repos/$REPO/actions/workflows/$WF/runs?created=${DAY}T14:00:00Z..${DAY}T19:59:59Z&per_page=$SAMPLE" \
            --jq '.workflow_runs[].id'); do
  $GH api "repos/$REPO/actions/runs/$id/jobs" \
    --jq ".jobs[0] | [\"$id\", .conclusion, .started_at, .completed_at] | @tsv" >> /tmp/g266.tsv
done
awk -F'\t' '
  function t(s){ gsub(/[TZ:-]/," ",s); split(s,a," "); return a[3]*86400+a[4]*3600+a[5]*60+a[6] }
  $3!="" && $4!="" { print t($3)"\t"t($4)"\t"(t($4)-t($3))"\t"$2 }
' /tmp/g266.tsv | sort -n > /tmp/g266_sorted.tsv
N=$(wc -l < /tmp/g266_sorted.tsv | tr -d ' ')
[ "$N" -eq 0 ] && { echo "NO JOB DATA — check the date"; exit 1; }
cut -f3 /tmp/g266_sorted.tsv | sort -n > /tmp/g266_d.txt
MED=$(awk '{a[NR]=$1} END {print (NR%2)? a[int(NR/2)+1] : int((a[NR/2]+a[NR/2+1])/2)}' /tmp/g266_d.txt)
P90=$(awk '{a[NR]=$1} END {print a[int(0.9*NR+0.5)?int(0.9*NR+0.5):1]}' /tmp/g266_d.txt)
MAX=$(tail -1 /tmp/g266_d.txt)
echo "n=$N  median=${MED}s  p90=${P90}s  max=${MAX}s"
OV=$(awk -F'\t' 'NR>1 && $1 < prevend {c++} {prevend=$2} END {print c+0}' /tmp/g266_sorted.tsv)
PAIRS=$((N-1))
echo "overlapping consecutive pairs: $OV / $PAIRS => $(awk -v o=$OV -v p=$PAIRS 'BEGIN{printf "%.1f", (p?100*o/p:0)}')%"
echo

# ⚠️ A bare grep for "429" is a false-positive machine — it matches hex temp-dir
# names, byte counts and package versions. Verified 2026-08-07: a bare grep
# reported 9 "hits" across 5 runs and ALL NINE were coincidental substrings
# (e.g. HOME='/home/runner/work/_temp/fe8f5ddd-9429-44b1-…'). Zero real 429s.
# Two-way control on this pattern: 57 hits on the killed 8/5 run 31041934094,
# 0 on the three 8/7 runs the bare grep falsely flagged.
PAT='APIError.*\[429\]|Quota exceeded|RESOURCE_EXHAUSTED|rateLimitExceeded'
echo "--- real Sheets 429 in logs (5 sampled runs) ---"
HITS=0
for id in $(cut -f1 /tmp/g266.tsv | head -5); do
  n=$($GH run view "$id" --repo "$REPO" --log 2>/dev/null | grep -acE "$PAT" || true)
  echo "  run $id: $n line(s)"; HITS=$((HITS+n))
done
echo "total real 429 lines across sample: $HITS"; echo

echo "════ VERDICT ════"
echo "cancelled ${PCT}%   (threshold: < 5.0%)"
awk -v p="$PCT" 'BEGIN {
  if (p+0 < 5.0) print "PASS -> the timeout is not cutting runs. TASK-266 closes.";
  else print "FAIL -> runs are still being cut. Reopen TASK-266 with these numbers." }'
```

**פלט ההרצה מול 8/7 (אימות שהשער עובד, לא מדידת-ההכרעה):**

```
total=492  cancelled=0  => 0.0%
n=60  median=48s  p90=56s  max=244s
overlapping consecutive pairs: 6 / 59  => 10.2%
total real 429 lines across sample: 0
VERDICT: PASS
```

════════════════════════════════════════════════════════════════════════════════
## הצעה נגזרת מה-recon — **אינה חלק מההכרעה** ⇒ TASK-280

‏**~45 שניות מכל ריצה הן `pip install` של requirements.txt המלא**, מאפס, בכל
דקה — כולל `streamlit`, `plotly`, `altair`, `pyarrow` לסוכן שאינו מציג UI.
מתוך חציון-ריצה של 48ש, העבודה עצמה היא ~2-5ש
(`Sheets API reads this run (cache misses): total=4`).

‏cache של pip או פיצול requirements יוריד ריצה מ-~50ש ל-~10ש — וזה, לא התקרה,
הוא מקור-האיטיות האמיתי; הוא גם מקטין ישירות את החפיפה של TASK-259.

⚠️ **שינוי ב-`.github/workflows/` = נתיב מוגן + שינוי משטר-ריצות ⇒ אסור בחלון
10/8–4/9.** מועמד לאחרי 4/9. נפתח כתיק נפרד: **TASK-280**.
