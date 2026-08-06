---
id: TASK-248
title: requirements.txt pins finvizfinance 0.14.6 which cannot parse finviz today
status: To Do
assignee: []
created_date: '2026-07-29 10:11'
updated_date: '2026-08-05 18:16'
labels:
  - bug
  - ci
dependencies: []
priority: high
ordinal: 246000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verified live 2026-07-29. requirements.txt line 4 pins finvizfinance==0.14.6. That version looks for a table with class table-light, and the live finviz screener page no longer contains it, only screener_table and styled-table-new. A real fetch under 0.14.6 raises AttributeError NoneType has no attribute findAll. The pin is not merely stale, it is poisonous.

The scanner survives only because all three workflows install finvizfinance unpinned and get 1.3.0, so they ignore the pin entirely. Anyone running pip install -r requirements.txt gets a dead scanner, and the local development environment does not reflect production for this dependency.

DECISION NEEDED: pin to the version CI actually resolves, or drop the pin and let it float. Pinning is safer for reproducibility but must be to a version that parses the current page. Note that the TASK-238 fix subclasses _get_table, so any version change must be checked against that hook.

Do not change the pin without a live fetch proving the chosen version parses. Also decide whether the workflows should install via -r requirements.txt instead of listing packages inline, which is the reason the pin was silently bypassed.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RULING 2026-08-05 (עמיחי)

הכרעה: להצמיד finvizfinance ל-1.3.0, ואז לאחד את ההתקנה ב-workflows דרך -r requirements.txt.

סדר מחייב: שינוי הפין קודם לאיחוד, או באותו commit. איחוד לפני שינוי הפין מוריד את
auto_scan.yml ל-0.14.6 והסורק מת בשעות מסחר (AttributeError NoneType has no attribute findAll).

תנאי מוקדם לפני כל שינוי: fetch חי שמוכיח ש-1.3.0 מפרסרת את הדף הנוכחי, ואימות שה-hook
של SanitizedOverview (_get_table override, utils.py:884) עדיין תופס תחת אותה גרסה.

תיקון עובדתי לגוף התיק (ביקורת 2026-08-05): הגוף אומר "all three workflows install
finvizfinance unpinned". זה לא מדויק. 12 workflows מתקינים -r requirements.txt ולכן
כבר מקבלים 0.14.6 היום: agent_minute, agent_critic, agent_critic_weekly,
agent_critic_monthly, agent_email_daily, agent_email_morning, agent_market_context,
agent_eod, health_audit, overnight_report_email, prepare_next_month, warm_oauth_token.
הם שורדים רק כי אף אחד מהם לא נוגע ב-finviz: utils.SanitizedOverview הוא proxy עצל
(utils.py:918-925) שמייבא את הספרייה רק כשקוראים לו. רק 3 workflows מתקינים finviz
inline ללא pin ולכן מקבלים 1.3.0: auto_scan.yml:24, post_analysis.yml:30, backfill_ohlc.yml:29.

לתעד לפני האיחוד: מעבר של auto_scan.yml ל--r requirements.txt מוסיף streamlit, plotly
ו-openpyxl (אף אחד מהם אינו מיובא בנתיב הסורק) ומוריד google-auth-oauthlib (אפס מייבאים
בקוד החי; _get_oauth_creds ב-sheets_manager.py:186 משתמש ב-google.oauth2.credentials
מ-google-auth). auto_scan.yml רץ כל דקה עם timeout-minutes: 8 — נדרשת מדידת זמן התקנה
לפני ואחרי לפני שמאחדים.

אזהרה נוספת: auto_scan.yml הוא הקובץ היחיד שמזריק GOOGLE_CREDENTIALS_JSON_AS (TASK-215).
כל עריכה שלו חייבת לשמר את ההזרקה.

קשור: תיק חדש שנפתח באותו יום על פער ה-CI signature guard (0.14.6 ב-CI מול 1.3.0 בפרודקשן).
<!-- SECTION:NOTES:END -->
