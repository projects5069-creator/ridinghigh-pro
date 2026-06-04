---
id: TASK-101
title: התקנת security-guidance plugin + אימות אי-התנגשות עם skill-gate hook
status: To Do
assignee: []
created_date: '2026-06-02 17:34'
updated_date: '2026-06-04 19:10'
labels:
  - infra
  - security
  - plugin
  - claude-code
  - auto-mode
dependencies: []
priority: medium
ordinal: 101000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
פלאגין אבטחה רשמי של Anthropic ל-Claude Code — security-guidance v2.0.2 (מאת David Dworken/Anthropic; מאומת מול plugin.json+README ב-anthropics/claude-plugins-official, 2/6/2026). 3 שכבות: (1) per-edit — אזהרות regex על ~25 דפוסים מסוכנים (yaml.load, torch.load weights_only=False, pickle.load על קלט לא-מהימן, innerHTML גולמי, hardcoded-secrets), אפס עלות מודל, hook על Edit/Write. (2) Stop — קריאת LLM (Opus 4.7 ברירת מחדל; ENV SECURITY_REVIEW_MODEL) סוקרת את ה-diff בסוף תור ומחזירה ממצאי high-severity לתיקון לפני שהמשתמש רואה. (3) commit — reviewer agentic מבוסס-SDK שקורא קבצים קשורים (Read/Grep/Glob) לאיתור פגיעויות חוצות-קבצים (IDOR, auth-bypass, SSRF חוצה-קבצים). מחלקות: injection/SQLi, XSS, SSRF, hardcoded-secrets, IDOR, auth-bypass, unsafe-deserialization, path-traversal. רלוונטיות ל-rhpro: רוב מחלקות ה-web לא חלות (Python+Sheets+Alpaca, בלי שרת/DB/auth), אבל hardcoded-secrets (google_credentials/Alpaca/OAuth/SMTP) + unsafe-loading (pickle/yaml.load) כן רלוונטיים, ובעיקר = שכבת הגנה נוספת ל-batch הלילי האוטונומי (auto mode). משלים את Agent #8 (TASK-94), לא כופל: #8=נכונות/QA, זה=אבטחה. SCOPE: (1) /plugin install security-guidance@claude-plugins-official + reload (user scope). דרישות סף מאומתות: CLI Claude Code >= v2.1.144 (אצלנו 2.1.156 OK) + Python 3.8+ (אצלנו 3.9.6 OK). (2) קונפליקט עם skill-gate hook (RULE #11): סיכון נמוך — layer1 הוא PreToolUse על Edit/Write, ו-Claude Code מריץ את כל ה-hooks התואמים (additive, לא בלעדי), כך ששני PreToolUse לא דורסים זה את זה. בנוסף יש kill-switches: SECURITY_GUIDANCE_DISABLE=1 (כיבוי מלא), ENABLE_PATTERN_RULES=0 (כיבוי layer1), ENABLE_STOP_REVIEW=0 (שימושי ל-multi-agent/shared-worktree — רלוונטי ל-auto-mode). עדיין לאמת בפועל שה-gate ממשיך לחסום אחרי ההתקנה. (3) לוודא שאין האטה מהותית על כל edit. (4) אופציונלי SG_DUAL_OR=on = +כמה אחוזי recall ב-2x עלות API. תזמון: להתקין כשמגדירים את ה-batch הלילי (יחד עם TASK-93/auto-mode), לא לפני — הערך מתממש כשהסוכן כותב קוד לבד; עד אז attended=המשתמש הוא הביקורת. הערה: מהטקסט המקורי הוסרו 'הושק 27/5/2026' ו-'30-40% פחות הערות PR בבדיקות פנימיות' — לא נמצאו במסמכי הפלאגין v2.0.2; אם יש מקור, להוסיף בחזרה.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verified 2026-06-04 (Iron Rule — live mechanism, not task text): (1) claude plugin CLI works; (2) marketplace claude-plugins-official EXISTS (GitHub anthropics/claude-plugins-official); (3) plugin security-guidance@claude-plugins-official EXISTS in catalog cache (source ./plugins/security-guidance) — so /plugin install security-guidance@claude-plugins-official is a VALID verified one-liner; (4) conflict with skill-gate LOW: both are additive PreToolUse hooks (CC runs all matching, no override), skill-gate is fail-OPEN, kill-switches exist (SECURITY_GUIDANCE_DISABLE=1 / ENABLE_PATTERN_RULES=0 / ENABLE_STOP_REVIEW=0). NOT installed now — gated on TASK-93/94 auto-mode (attended until then = user is the review). Future install is known-safe.
<!-- SECTION:NOTES:END -->
