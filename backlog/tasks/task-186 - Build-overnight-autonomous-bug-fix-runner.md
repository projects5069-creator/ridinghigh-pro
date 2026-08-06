---
id: TASK-186
title: Build overnight autonomous bug-fix runner
status: In Progress
assignee: []
created_date: '2026-06-19 02:09'
updated_date: '2026-08-05 18:18'
labels: []
dependencies: []
priority: high
ordinal: 192000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
launchd + claude -p (Max subscription) overnight runner on feature/overnight-runner. Strict auto-safe filter, worktree-isolated draft PRs, secret+CORE_UNSAFE PreToolUse hooks, token/time circuit breaker. Code+tests DONE & GREEN; schedule-enable gated behind §11 supervised gates.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RULING 2026-08-05 (עמיחי)

הכרעה: מוקפא רשמית עד אחרי הוורדיקט של HYP-002 (תחילת אוקטובר, HYPOTHESES.md:257 —
"45 trading days from 2026-08-03 reaches early October").

הנימוק אינו הבאגים. הנימוק הוא שסוכן שמתקן קוד לבד בזמן שרצה השערה רשומה עלול לגעת
במשהו שיפסול אותה. HYP-002 כבר נפסלה פעם אחת ב-3/8 ונרשמה מחדש בלי carry-forward;
פסילה שנייה מתחילה את 45 הימים מאפס בפעם השלישית.

עובדה מאומתת 2026-08-05 (הרצה חיה):
  launchctl list | grep -i overnight  ->  ריק
  ls ~/Library/LaunchAgents/          ->  com.rh.overnight.plist.disabled
                                          com.rh.overnight.plist.bak_20260702
אין com.rh.overnight.plist חשוף. launchd סורק רק *.plist, ולכן login אינו יכול לטעון.
המנגנון שגרם ל-9 הלילות (launchctl unload שהשאיר את ה-plist על הדיסק, POSTMORTEM
docs/POSTMORTEM_overnight_ARMED_2026-07-02.md:42-49) אינו קיים היום. ההקפאה היא תיעוד
של מצב קיים, לא שינוי מצב.

החוסם שהיה בלתי נראה עד עכשיו:
TASK-234 מצהיר בגופו במפורש "Blocks TASK-186." ארבעת התיקים 234, 235, 236, 237 מתארים
בדיוק למה execute-proof תקוע, והם ישבו על ענף fix/auto-dancer-planmd בלבד ולא הופיעו
ב-backlog task list. הועברו ל-main ב-2026-08-05 באמצעות git checkout עם ארבעה נתיבים
מפורשים בלבד. cherry-pick נשלל בכוונה: הענף נושא גם task-238 ו-task-239 שכבר Done
ב-main, וקומיט שלם היה מחזיר אותם ל-To Do.

השפעה על הספירה: לפני ההעברה 53 תיקים פתוחים. אחריה 57 (234-237), ועם TASK-255/256/257
שנפתחו באותה הכרעה 60, ובניכוי TASK-10 שנסגר — 59. כל דוח או תוכנית שמניחים 53 התיישנו
ברגע הזה.

תיעוד שנותר פתוח (POSTMORTEM §7): שמונה מקורות עדיין מתעדים DISARMED-שגוי מ-6/20
("launchctl unload"), ביניהם שבעה קבצי handoff/plan/backlog ורשומת זיכרון אחת.
<!-- SECTION:NOTES:END -->
