---
id: TASK-300
title: >-
  Six repos carry commits that exist on no remote; local main is diverged and
  misleading
status: To Do
assignee: []
created_date: '2026-08-10 04:13'
updated_date: '2026-08-10 04:40'
labels: []
dependencies: []
priority: high
ordinal: 298000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמצא 9/8, ותוקן באותו יום אחרי מדידה רחבה יותר.

הממצא הראשון היה שגוי בחלקו. נקבע שם ש-29 קומיטים של auto-dancer אינם באף remote; המדידה הנכונה - git rev-list --count main --not --remotes - מחזירה אפס, ו-git branch -r --contains מראה שהם יושבים ב-origin/fix/auto-dancer-planmd. הטעות היתה להשוות מול origin/main בלבד. זו אותה מחלקת-שגיאה של כלי שבודק משהו צר יותר ממה שנראה.

מה שנכון ונשאר: ה-main המקומי מסועף - 92 קומיטים מאחור ו-29 קדימה - ולכן git checkout main נותן את תוכן ענף-ה-auto-dancer ולא את main. מלכודת אמיתית, אך לא סיכון-אובדן.

הסריקה הרחבה מצאה שישה ריפואים עם קוד שאינו אצל אף remote:
ReboundPro 33 קומיטים ב-11 ענפים (יש remote, ובכל זאת) · biotech-screener 9 · RidingHighPro 1 בענף fix/96-check06-robustness · projects/vardan-tracker 26 (אין remote) · smallcap-median-study 4 (אין remote) · trade-tracker 71 (אין remote).

הוקטן 9/8: bundles מלאים (--all) נוצרו ואומתו לכולם תחת ClaudeWork/_machine/repo_bundles ומגובים ל-Drive. מדיניות-הגיבוי עודכנה - ההנחה 'יש remote ⇒ מגובה' הוחלפה בקריטריון הנמדד 'אפס קומיטים שאינם באף remote, בכל ענף'.

נכלל גם docs/auto-dancer/: ארבעה קבצים untracked, שניים .bak ושניים תורי-הרצה מאותו מאמץ.

שער-קבלה: לכל אחד מששת הריפואים הוכרע - נדחף, נזרק, או נשאר מקומי במודע עם bundle; ה-main המקומי יושר או סומן; והוכרע מה קורה ל-docs/auto-dancer.
<!-- SECTION:DESCRIPTION:END -->
