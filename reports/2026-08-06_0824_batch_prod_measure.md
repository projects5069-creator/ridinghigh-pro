# מדידת ה-batch בייצור — 2026-08-06

**נכתב 2026-08-06 08:24 Lima.** קריאה בלבד מ-Actions. **לא נגעתי ב-Sheets/Drive/FINVIZ**,
לא הרצתי workflow/scanner/collector, לא נגעתי ב-`.github/workflows/`.
commit אחד — `task-262` בלבד. **אין push.**
`origin/main` = `9768c2c`.

**סקילים:**
| סקיל | path | wc -l |
|---|---|---|
| rhpro-live | `~/.claude/skills/rhpro-live/SKILL.md` | 180 |
| superpowers/verification-before-completion | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/verification-before-completion/SKILL.md` | 139 |

---

## 0. commit של TASK-262

```
$ git status --porcelain=v1 --untracked-files=all -- backlog/
?? "backlog/tasks/task-262 - ...-leaks-live-state.md"

$ git diff --cached --name-only | wc -l
1
$ git diff --cached --name-only | grep "\.github/workflows/"
CLEAN: no workflow staged
```

```
2090871  docs(backlog): open TASK-262 — borrow-wiring tests leak live state
         1 file changed, 76 insertions(+)
         create mode 100644 backlog/tasks/task-262 - ...
```
**קובץ אחד בדיוק, אפס workflows.** ה-index הודפס ואומת לפני ה-commit.
הודעת ה-commit נכתבה מקובץ (`-F`) — המקף-הארוך `—` שובר ציטוט ב-zsh.
**ללא `Co-Authored-By`, ללא "Generated with".** אין push.

---

## 1. שער הזמן

```
$ TZ='America/Lima'    date  →  2026-08-06 08:24 Thursday Lima
$ TZ='America/New_York' date →  09:24 EDT NY

$ now_et=09:24:50  open=09:30:00  diff_min=-5
```
**השוק טרם נפתח** ברגע תחילת התור — חמש דקות לפני הפתיחה.
15 ריצות כבר בוצעו היום, **אבל כולן לפני הפתיחה**: הן יוצאות ב-`is_market_hours`
(`orchestrator.py:549`) ואינן מגיעות ל-`read_latest_signals`, כלומר **אינן מפעילות את
נתיב ה-SMA20 כלל**. שקלול שלהן היה מטה את החציון כלפי מטה ומייצר מספר חסר-משמעות.

**המתנה עד 09:52 ET** — כ-20 דקות אחרי הפתיחה, כדי לצבור מדגם של ריצות
שבאמת מריצות את ההעשרה.

---

## 5. auto_scan — אימות מקדים (אינו דורש המתנה)

```
$ git show origin/main:auto_scanner.py | grep -c "prime_sma20_cache"
0
$ git show origin/main:auto_scanner.py | grep -n "sma20\|SMA20"
(ריק)

  agent/orchestrator.py            2      ← היחיד שקורא ל-prime_sma20_cache
  auto_scanner.py                  0
  post_analysis_collector.py       0
```
**מאומת: `auto_scanner` לא קיבל את ה-batch, ולמעשה אינו נוגע ב-SMA20 בכלל.**
ההעשרה הזו שייכת לנתיב הסוכן בלבד. לכן **הצפי הוא ש-`auto_scan` יישאר סביב 269 שניות
ללא שינוי** — וזה נכון וצפוי, לא רגרסיה.

