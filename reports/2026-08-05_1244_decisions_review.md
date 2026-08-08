# ביקורת תשע ההחלטות

**נכתב 2026-08-05 12:44 Lima (13:44 EDT NY).** אני מבקר, לא מבצע. לא בוצע דבר.
לכל שאלה: (א) הראיה · (ב) האם ההמלצה עומדת · (ג) דעה עצמאית · (ד) מה עלול להישבר.

**סקילים שנטענו לפי intent:**
| סקיל | path | wc -l |
|---|---|---|
| rhpro-live | `~/.claude/skills/rhpro-live/SKILL.md` | 180 |
| systematic-debugging | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/systematic-debugging/SKILL.md` | 296 |
| data-quality-checker | `~/.claude/skills/data-quality-checker/SKILL.md` | 161 |
| trader-memory-core | `~/.claude/skills/trader-memory-core/SKILL.md` | 273 |
| verification-before-completion | `~/.claude/plugins/cache/superpowers-marketplace/superpowers/5.1.0/skills/verification-before-completion/SKILL.md` | 139 |

⚠️ **הערה כנה על שניים מהם:** `data-quality-checker` הוא linter למסמכי-markdown (scale-של-מחיר, התאמת יום-בשבוע, סכומי-הקצאה) — הוא **לא** כלי לבדיקת זמינות מקורות-דאטה, ולכן לא תרם ל-Q5/Q6 מעבר לעיקרון "advisory, לא חוסם". `trader-memory-core` הוא CLI לניהול תזות בריפו אחר (`claude-trading-skills`) — לא חל על Q7/Q8. טענתי את שניהם כפי שביקשת; התוכן שלהם לא ענה על השאלות. הראיות ב-Q5–Q8 הן מהקוד.

**מלאי superpowers (14):** brainstorming · dispatching-parallel-agents · executing-plans · finishing-a-development-branch · receiving-code-review · requesting-code-review · subagent-driven-development · systematic-debugging · test-driven-development · using-git-worktrees · using-superpowers · verification-before-completion · writing-plans · writing-skills.

---

## Q1 · finvizfinance — להצמיד ל-1.3.0 + לאחד התקנה

### (א) הראיה

**`requirements.txt` — 13 חבילות:**
```
1  streamlit>=1.40.0        7  gspread>=6.0.0
2  pandas>=2.2.0            8  google-auth>=2.0.0
3  plotly>=5.18.0           9  google-api-python-client>=2.0.0
4  finvizfinance==0.14.6   10  pytz>=2023.3
5  yfinance>=0.2.50        11  openpyxl
6  ta==0.11.0              12  pandas-market-calendars
                           15  alpaca-py>=0.25.0
```

**⚠️ הטענה בתיק שגויה. לא "שלושת ה-workflows" — אלא 3 מתוך 17.**
`grep -rn "pip install" .github/workflows/*.yml`:

| מתקין `-r requirements.txt` (⇒ **מקבל 0.14.6**) | מתקין inline |
|---|---|
| `agent_minute.yml:20` · `agent_critic.yml:23` · `agent_critic_weekly.yml:26` · `agent_critic_monthly.yml:26` · `agent_email_daily.yml:17` · `agent_email_morning.yml:17` · `agent_market_context.yml:24` · `agent_eod.yml:22` · `health_audit.yml:32` · `overnight_report_email.yml:26` · `prepare_next_month.yml:25` · `warm_oauth_token.yml:30` — **12** | `auto_scan.yml:24` · `post_analysis.yml:30` · `backfill_ohlc.yml:29` · `backup.yml:24` · `monthly_rotation.yml:27` — **5** (רק 3 הראשונים מתקינים finviz) |

**הממצא המכריע — שומר-החתימה מאמת את הגרסה הלא-נכונה.**
קיים טסט-שומר: `tests/test_ticker_sanitizer_v1.py:155-167`
```python
LIBRARY_GET_TABLE_SIGNATURE = "(self, rows, df, num_col_index, table_header, limit=-1)"

def test_library_get_table_signature_is_what_the_override_expects():
    """0.14.6 defines it on Overview, 1.3.0 on Base, both with this signature."""
    pytest.importorskip("finvizfinance")
    from finvizfinance.screener.overview import Overview
    actual = str(inspect.signature(Overview._get_table))
    assert actual == LIBRARY_GET_TABLE_SIGNATURE, (...)
```
ו-`tests.yml:31`:
```yaml
run: uv run --with-requirements requirements.txt --with pytest pytest -m "not integration" -q
```
⇒ **CI מתקין 0.14.6 ומאמת את החתימה של 0.14.6.** הפרודקשן (`auto_scan.yml`) רץ על 1.3.0. **השומר שנועד להגן על גרסת-הפרודקשן מעולם לא ראה אותה.**

**מקור הקביעה על זהות-החתימה:** `utils.py:824` (הערה) ו-`tests/test_ticker_sanitizer_v1.py:7-9` (docstring) — שניהם מצטטים `0.14.6 overview.py:199` ו-`1.3.0 base.py:127`. זו קביעה עם file:line בשתי הגרסאות, כלומר מישהו כן הסתכל. **אבל היא לא נאכפת אוטומטית על 1.3.0** — הטסט שיכול לאכוף אותה רץ רק על 0.14.6. לא הרצתי pip ולא fetch, ולכן **לא אימתתי בעצמי** את החתימה ב-1.3.0.

**דיף החבילות אם `auto_scan.yml` יעבור ל-`-r requirements.txt`:**
- **נוסף:** `streamlit` · `plotly` · `openpyxl` — אף אחד מהם לא מיובא בנתיב-הסורק (אימות: grep על `auto_scanner.py`, `utils.py`, `sheets_manager.py`, `formulas.py`, `config.py`, `data_provider.py` → אפס).
- **יורד:** `google-auth-oauthlib` — **אפס מייבאים בכל הקוד החי**. `_get_oauth_creds` (`sheets_manager.py:186`) משתמש ב-`google.oauth2.credentials` ו-`google.auth.transport.requests`, שניהם מ-`google-auth`. הורדתו בטוחה.
- **`bs4` אינו ב-requirements.txt כלל** — הוא מגיע כתלות טרנזיטיבית של finvizfinance. הטסט פותח ב-`pytest.importorskip("bs4")` (`:35`), כלומר שינוי בגרסת finviz שמשמיט את bs4 יגרום לקובץ-הטסט כולו **לדלג בשקט**.

### (ב) האם ההמלצה עומדת
**כן על התוכן. לא על הסדר, ולא על ההנמקה.**

### (ג) דעתי
מסכים שצריך להצמיד ל-1.3.0 ולאחד — אבל **הנימוק החזק ביותר אינו זה שכתבת.** הנימוק הוא שהאיחוד הוא מה שיגרום לשומר-החתימה לאמת, בפעם הראשונה, את הגרסה שהפרודקשן באמת מריץ. היום יש שתי מערכות: אחת שנבדקת ואחת שרצה, והן אינן אותה גרסה.

**חולק על סדר-הפעולות.** אם מאחדים קודם והפין נשאר `==0.14.6`, `auto_scan.yml` יקבל 0.14.6 → `AttributeError: NoneType has no attribute findAll` → **הסורק מת בדקה הראשונה בשעות-מסחר.** הפין חייב להשתנות באותו commit או לפניו.

**חולק גם על ניסוח התיק:** "The scanner survives only because all three workflows install unpinned" מרמז שרק 3 workflows נוגעים בפין. בפועל **12 workflows כבר מקבלים 0.14.6 היום** — כולל `agent_minute.yml` שרץ כל דקה. הם שורדים רק כי אף אחד מהם לא נוגע ב-finviz: `SanitizedOverview` הוא proxy עצל (`utils.py:918-925`) שמייבא את הספרייה רק כשקוראים לו.

### (ד) מה עלול להישבר
| מה | סבירות | הסבר |
|---|---|---|
| **הסורק מת** | ודאי אם מאחדים לפני שמשנים את הפין | 0.14.6 לא מפרסר את הדף החי |
| זמן-התקנה ב-`auto_scan.yml` | גבוהה | +streamlit +plotly +openpyxl על workflow עם `timeout-minutes: 8` שרץ כל דקה |
| `test_ticker_sanitizer_v1.py` נהיה **אדום** | בינונית | זו התוצאה **הרצויה** אם החתימה באמת שונה ב-1.3.0. אבל אם היא זהה — הוא נשאר ירוק, ורק אז נדע |
| דליפת `_AS` | נמוכה | לא קשור, אבל `auto_scan.yml` הוא הקובץ היחיד שמזריק `GOOGLE_CREDENTIALS_JSON_AS` (TASK-215) — כל עריכה שלו צריכה לשמר את זה |

---

## Q2 · DropsLab — לאמץ PK, לא לחווט אינטגרציה

### (א) הראיה

`ls docs/ | grep -i drops` → **אין `DropsLab_PK.md`**. הטיוטה קיימת רק ב-`docs/research/INVESTIGATION_2026-06-10/DROPSLAB_PK_DRAFT.md`.

**מה נספג ל-153** (Implementation Notes):
> TASK-156 merge: absorbs TASK-27 (DropsLab integration #N25 — **integrate DropsLab signals as Trader input**; unblocked 3/6).

**HYP-001** (`docs/HYPOTHESES.md:125-129`):
> **Entry.** SHORT at **d1_close of the drop-event day**
> **Exit (LOCKED by TASK-178).** Cover at **D5_Close — exactly 5 trading days after the d1_close entry; time-only, zero-discretion, NO TP/SL.**

**הסוכן החי:** `AGENT_FORCE_EOD_CLOSE = False` (`config.py:315`) ⇒ `is_eod_window` מחזיר `False` תמיד (`agent/orchestrator.py:117-124`). `MAX_HOLDING_DAYS` הוא display-only (`config.py:146`). **לסוכן אין שום יציאה מבוססת-זמן.** יציאתו היחידה היא TP/SL (`position_manager.py:244-251`).

**HYP-002 Universe** (`HYPOTHESES.md:193-194`):
> - Universe: **FINVIZ screener (Price>$2 ∧ Today+15%)** → tickers passing the LIVE ENTRY_GATE_MINIMAL gate (MxV<=-100 ∧ price>=$3 ∧ data-quality ∧ exposure-safety).

**היתכנות טכנית:** `grep -i "dropslab\|drops_raw\|drops_post"` על כל הקוד החי → שלוש תוצאות בלבד, כולן **הערות**: `formulas.py:353`, `config.py:301` (רשימת `CHRONIC_DROPPER_BLACKLIST` ידנית), `decision_logic.py:396`. `sheets_config.json` → **אפס מפתחות DropsLab**. אין reader, אין sheet-id, אין קובץ-ביניים.

### (ב) האם ההמלצה עומדת
**כן, ובנימוק חזק יותר משנתת.**

### (ג) דעתי
**מסכים — אבל לא כי החיווט "מוקדם מדי". כי הסוכן החי לא מסוגל לבצע את HYP-001 בכלל.**
HYP-001 דורש יציאה **בזמן** (D5_Close, ללא TP/SL). לסוכן אין מנגנון כזה — אין forced-exit ואין time-check. חיווט DropsLab לתוך ה-Trader לא ייצר את HYP-001; הוא ייצר **אסטרטגיה שלישית** — סיגנל DropsLab → שער MxV → יציאת TP10/SL10 — שאינה לא HYP-001 ולא HYP-002.

**על סתירת הרישום-המקדים — אני מדייק את הטענה שלך.** סעיף ה-freeze (`HYPOTHESES.md:210-215`) מונה במפורש **ארבעה** פרמטרים בלבד: `AGENT_TP_PCT · AGENT_SL_PCT · HOLD<=5 · reentry<=1`. Universe **אינו ברשימה**. לכן, **לפי האות**, שינוי-יקום לא פוסל אוטומטית.
**לפי המהות — כן.** שדה `Universe` הוא חלק מהרישום, והוא אומר `FINVIZ screener`. אם DropsLab מתחיל להזין את ה-Trader, המדגם שנאסף מ-3/8 הוא תערובת של שני יקומים, וההרצה כבר לא מודדת את מה שנרשם. §A.4 (`Out-of-sample mandatory`) ו-§A.6 (`Discovery sample is locked`) מניחים יקום יציב.

**היתכנות: זה לא "חיווט", זה בניית נתיב-דאטה מאפס.** DropsLab הוא ריפו נפרד (TASK-83: `repo Ambroseius/DropsLab`), אין לו sheet-id בקונפיג, ואין שום קוד קורא. הבחירה בין קריאה חוצת-ריפו / גיליון משותף / קובץ-ביניים **לא נעשתה בשום מקום**.

### (ד) מה עלול להישבר
- **אימוץ ה-PK בלבד:** כלום. זו העברת קובץ md מ-`research/` (gitignored) ל-`docs/`. הסיכון היחיד הוא שהוא ייכנס ל-Anti-Drift ויידרש לעדכון בכל שינוי DropsLab.
- **אילו כן היו מחווטים:** פסילת ההרצה של HYP-002 שנרשמה-מחדש ב-3/8 → 45 ימי-מסחר מתחילים מאפס בשלישית.
- ⚠️ **לא אומת:** האם DropsLab עצמו עדיין חי. MASTER §153: `לא אומת האם DropsLab עצמו עדיין חי; הזיכרון מציין קולקטור מת מ-5/6, וזה TASK-144` — ו-`backlog task 144` מחזיר `✔ Done (2026-06-15)`.

---

## Q3 · רץ הלילה — להקפיא רשמית + להעביר 234-237

### (א) הראיה

**המנגנון** (`docs/POSTMORTEM_overnight_ARMED_2026-07-02.md:42-49`):
> **`launchctl unload` ≠ disable.** ב-6/20 השבתנו את הרנר ב-`launchctl unload` בלבד. זה מסיר את ה-job מה-session הנוכחי של launchd, אבל **משאיר את קובץ ה-plist במקומו**... macOS טוען אוטומטית כל plist בתיקייה הזו ב-login / הפעלה-מחדש של user session.
> האימות ב-6/20 ("לא ב-`launchctl list`") היה **נכון לרגע-הבדיקה בלבד**.

**למה לא היה נזק** (`:55-64`): שני שומרים עצמאיים עצרו כל אחד מ-9 הלילות — `auth-smoke` ב-7 מהם, `base-RED` ב-2. **"אין ולו לילה אחד ששני השומרים עברו בו."**

**האם המנגנון קיים היום — אימות שהרצתי עכשיו:**
```
$ launchctl list | grep -i "overnight|dancer|ridinghigh|rhpro"
(nothing matching overnight/dancer/ridinghigh loaded)

$ ls -la ~/Library/LaunchAgents/ | grep -i "overnight|dancer|rh"
-rw-r--r--  1 adilevy  staff  1603 Jul  2 11:15 com.rh.overnight.plist.bak_20260702
-rw-r--r--  1 adilevy  staff  1603 Jun 19 18:05 com.rh.overnight.plist.disabled
```
**אין `com.rh.overnight.plist` חשוף.** launchd סורק רק `*.plist` (`:84-85`), ולכן login לא יכול לטעון אף אחד מהשניים. **המנגנון שגרם ל-9 הלילות אינו קיים היום.**

**הענף:**
```
$ git log --oneline -5 fix/auto-dancer-planmd
131a88a docs(backlog): add TASK-238/239/240/241 - finviz pin, collector timeout, data and agent audits
d25493a docs(backlog): add TASK-235/236/237 and session handoff 2026-07-05
f69f643 fix(auto-dancer): TASK-234 — grant tools via --allowedTools (real execute-proof unblock)
8ce1fef fix(auto-dancer): TASK-234 — plan doc to .dancer/plan.md (unblock execute-proof)
69c0c21 feat(auto-dancer): PLANNER STEP 0 grounding — load rhpro-live + systematic-debugging...
```

⚠️ **מלכודת שלא הזכרת.** `git ls-tree` על אותו ענף מחזיר גם:
```
backlog/tasks/task-238 - Pin-finvizfinance-in-CI-and-sanitize-doubled-letter-tickers.md
backlog/tasks/task-239 - Fix-post_analysis-collector-15min-GHA-timeout.md
backlog/tasks/task-230 - Data-gap-audit...
backlog/tasks/task-231 - DST-fix-enrich_post_analysis...
```
**238 ו-239 כבר `✔ Done` ב-main** (30/7 ו-4/8 בהתאמה). cherry-pick של הקומיט `131a88a` או `d25493a` יחזיר גרסאות **ישנות** של קבצי-התיק האלה ויהפוך אותם חזרה ל-To Do.

### (ב) האם ההמלצה עומדת
**כן על ההקפאה. כן על ההעברה, אבל לא בשיטה שהיא מרמזת.**

### (ג) דעתי
**מסכים על ההקפאה, ואוסיף שהיא כבר עובדה — לא החלטה.** הריצה מנוטרלת מ-2/7 והאימות שהרצתי עכשיו מאשר זאת. מה ש"הקפאה רשמית" מוסיף הוא רק תיעוד: הפוסטמורטם §7 מונה **8 מקורות** שעדיין מתעדים DISARMED-שגוי (7 קבצי handoff/plan/backlog + רשומת-זיכרון), וכולם עדיין אומרים "unload 6/20".

**חולק על השיטה להעברה.** `git mv` לא רלוונטי (הקבצים בענף אחר). `cherry-pick` של הקומיטים מסוכן כי הם מערבבים 4 תיקים חדשים עם 4 שכבר Done. הדרך הבטוחה היחידה היא **בחירה ברמת-הקובץ**: `git checkout fix/auto-dancer-planmd -- "backlog/tasks/task-234 *" "...task-235 *" "...task-236 *" "...task-237 *"` — ארבעה נתיבים מפורשים, אפס נגיעה בשאר.

**מה שאני חושב שחשוב יותר מההעברה עצמה:** ארבעת התיקים האלה מתארים **למה** TASK-186 תקוע, ו-TASK-234 אומר במפורש `Blocks TASK-186.` היום 186 הוא `In Progress / HIGH` בלי שום תיעוד של החוסם. ההעברה לא "מסדרת בקלוג" — היא הופכת חוסם בלתי-נראה לנראה.

### (ד) מה עלול להישבר
- **cherry-pick נאיבי:** מחזיר 238/239 ל-To Do, ומחזיר גרסאות ישנות של 230/231.
- **הענף עצמו:** מכיל גם קוד (`f69f643`, `8ce1fef`, `69c0c21` — שינויי auto-dancer). בחירה ברמת-קובץ על `backlog/tasks/` בלבד לא נוגעת בו.
- ⚠️ **תופעת-לוואי לא מוזכרת:** אחרי ההעברה, `backlog task list --plain` יעלה מ-53 ל-57. כל דוח, ספירה, או תוכנית שמניחה 53 תתיישן באותו רגע.

---

## Q4 · qty guard — להמתין לאוקטובר

### (א) הראיה

**אין שום בדיקת quantity על נתיב-הביצוע.** grep על ארבעת הקבצים:
```
decision_logic.py:145   qty = int(AGENT_POSITION_SIZE_USD / price)
decision_logic.py:333   d.quantity = position["quantity"]
order_manager.py:183    qty=decision.quantity,        ← ישירות ל-broker
order_manager.py:273    "Quantity": decision.quantity,
alpaca_broker.py:171    qty=qty,
```
**אפס השוואות** `quantity </>/== 1`. הטענה שלך מאומתת.

`AGENT_POSITION_SIZE_USD = 1000` (`config.py:320`) ⇒ `qty = 0` כאשר `price > 1000`.
**אין תקרת-מחיר בשום מקום** — רק רצפה: `AGENT_MIN_SCANPRICE_USD = 3.0` (`config.py:300`, נאכף ב-`decision_logic.py:391`). `AGENT_MARKET_CAP_MAX` כבוי תחת `ENTRY_GATE_MINIMAL`.

**⚠️ ההתנהגות בפועל הפוכה ממה שההמלצה מניחה:**

| מצב | מה קורה עם qty=0 |
|---|---|
| **DRY_RUN (המצב היום)** | `_sim_bracket_order` (`alpaca_broker.py:154`) לא בודק qty → מחזיר `SimulatedOrder(qty="0")` → `_write_to_portfolio` כותב `Quantity: 0` → `position_manager:254` `qty = int(...) = 0` → `unrealized_pnl = (entry−current) × 0 = 0`. **אבל בדיקת ה-TP/SL ב-DRY_RUN (`:244-251`) בודקת מחיר בלבד ולא qty** ⇒ הפוזיציה **תיסגר** על TP או SL עם `RealizedPnL = 0`. |
| **LIVE_PAPER** | `submit_bracket_order` בונה `LimitOrderRequest(qty=0)` ושולח ל-Alpaca → ה-API דוחה → `_submit_with_retry` מנסה 3× ומחזיר `None` → `order_status = REJECTED`, **אין שורת paper_portfolio**. |

**כלומר: ה-broker אוכף את מה שהקוד לא. המצב שבו אנחנו נמצאים היום — DRY_RUN — הוא היחיד שבו הבאג מייצר רשומה.**

⚠️ **קובץ-הראיה שהתיק מצטט אינו קיים.** TASK-224 מפנה ל-`plans/stateless-seeking-sifakis.md S2`.
```
$ ls -d plans     → No such file or directory
$ find . -name "*sifakis*" -not -path './.git/*'   → (nothing)
```
**שישה תיקים מצטטים אותו:** 208, 209, 223, 224, 226, 229.

### (ב) האם ההמלצה עומדת
**חולקת — בחלק הסיכון. עומדת בחלק המשמעת.**

### (ג) דעתי
**חולק על הערכת הסיכון.** הסיכון אינו "פקודה לא-חוקית מגיעה לברוקר" — תחת LIVE זה ייחסם. הסיכון האמיתי הוא ש**תחת DRY_RUN נוצרת עסקת-רפאים עם PnL בדיוק 0 שנכנסת למדגם של HYP-002**. היא נספרת ב-n, היא נסגרת ב-TP או SL, והיא תורמת תצפית של אפס ל-expectancy. זה בדיוק סוג הזיהום ש-3/8 פסל בגללו את ההרצה הקודמת.

**ועל השאלה המכריעה ששאלת — האם הפילטר ניטרלי למדידה: הוא לא ניטרלי, הוא מגן עליה.**
פילטר `qty<1 → SKIP` יכול לעשות דבר אחד בלבד: להסיר תצפיות מנוונות. הוא **לא יכול** להוסיף תצפית, לא יכול לשנות מחיר-כניסה, ולא יכול להזיז TP/SL. ההשפעה שלו על ה-expectancy היא חד-כיוונית: הוצאת אפסים. אין תרחיש שבו הוא מטה את התוצאה לטובה.
בנוסף: סעיף ה-freeze (`HYPOTHESES.md:210-215`) מונה 4 פרמטרים, ו-qty guard אינו אחד מהם. התיק עצמו כותב `Not a HYP-002 frozen param (guard, not threshold)`.

**הצד השני, בכנות:** שדה ה-Universe ברישום מתאר את השער כ-`MxV<=-100 ∧ price>=$3 ∧ data-quality ∧ exposure-safety`. תנאי חמישי הופך את התיאור הזה לבלתי-מדויק. מי שקורא את הרישום בעוד חודשיים יראה שער שאינו מה שרץ.

**המסקנה שלי:** ההמתנה מוצדקת על משמעת-רישום, לא על סיכון. אבל צריך להיות מודע שהמחיר של ההמתנה הוא בדיוק הסיכון שההמתנה אמורה למנוע — כל תצפית qty=0 שתיווצר עד אוקטובר תזהם את ההרצה שנרשמה-מחדש. **שאלה שלא נשאלה: כמה סיגנלים במחיר >$1000 היו בפועל?** לא יכולתי למדוד — זה דורש קריאת Sheets, והשוק פתוח.

### (ד) מה עלול להישבר
| החלטה | מה עלול להישבר |
|---|---|
| **להמתין** | כל סיגנל >$1000 עד אוקטובר ייצר עסקת-רפאים ב-PnL 0 בתוך המדגם הרשום |
| **לממש עכשיו** | תיאור ה-Universe ברישום נהיה לא-מדויק; מי שיבקר את ההרצה יצטרך את ה-diff הזה |
| **בכל מקרה** | `plans/stateless-seeking-sifakis.md` חסר — ה-RULING של 3/7 שהתיק מסתמך עליו אינו ניתן לאימות מהריפו |

---

## Q5 · שני מדדי שורט חינמיים — VWAP + sigma-bands

### (א) הראיה

**אין VWAP אמיתי בשום מקום.** `formulas.py:147-166`:
```python
def calculate_typical_price_dist(price, high, low):
    """TypicalPriceDist - Distance (%) from Typical Price = (H+L+C)/3.
    This was previously (incorrectly) named 'VWAP distance'. True VWAP
    requires intraday tick-by-tick volume data, which we don't have.
    Typical Price is a standard TA indicator used as a VWAP proxy for daily bars."""
    typical_price = (high + low + price) / 3
    return float((price / typical_price - 1) * 100)
```
**ההבדל:** Typical Price הוא ממוצע פשוט של שלושה מספרים מהמוט היומי. **אין בו נפח בכלל.** VWAP הוא `Σ(price×volume)/Σ(volume)` על כל העסקאות התוך-יומיות.

**האם הנתונים קיימים?**
- `intraday_cache.py:25` — `_COLS = ["open", "high", "low", "close", "volume"]` ✅ **המוטות כן נושאים נפח.**
- `intraday_cache.py:49` — `get_intraday_bars_cached(ticker, date, timeframe="1Min", ...)`, עם קאש-דיסק ב-`data/` (gitignored).
- `providers/alpaca_provider.py:364` — `feed=self._sdk["DataFeed"].IEX` · תמיכה ב-`1Min/5Min/15Min/1H`.

**⚠️ אבל — TASK-230 AC#3, verdict שכבר סגור:**
> `verdict 4/7 = blocked-by-data` — feed=IEX-בלבד, **median 28/390 נרות ליום למיקרו-קאפ** (n=168 מדגם-מרובד, 33 שמישים-מזווגים).

**sigma-bands — ראיה נפרדת לגמרי.** `agent/enrichment/sma20_cache.py:78-88`:
```python
closes = bars["close"].dropna().tolist()
if len(closes) < 15: return None
sma20 = sum(closes[-20:]) / min(len(closes), 20)
cache[cache_key] = {"sma20": round(sma20, 4), "computed_at": today_str}
```
**רק ממוצע. אין std.** הקאש שומר שדה אחד. ה-`.std()` היחיד בכל הקוד החי הוא `score_analytics.py:357`.
**אבל:** `closes` כבר בזיכרון באותה פונקציה, מ-`get_daily_bars(ticker, days=25)` שכבר נקרא. חישוב std ממנו דורש **אפס קריאות-ספק נוספות**.

### (ב) האם ההמלצה עומדת
**חצי. sigma-bands — כן. VWAP — לא.**

### (ג) דעתי
**חולק על ה"שניים". זה מדד אחד חינמי, לא שניים.**

**sigma-bands ישימים היום, בעלות אפס.** הנתונים כבר נשלפים (`days=25`), כבר בזיכרון (`closes`), וכבר יש קאש-דיסק שמונע קריאה חוזרת. התוספת היא שורה אחת של חישוב ושדה אחד בקאש.

**VWAP אינו ישים, וזו לא שאלת-מאמץ אלא שאלת-תקפות.** VWAP על 28 מתוך 390 דקות הוא ממוצע-משוקלל של **7% מהזמן**, והנפח הזה מגיע מבורסה **אחת** (IEX). VWAP שסוחר-שורט מקצועי מתייחס אליו הוא ה-consolidated — כל הבורסות. מספר שנקרא "VWAP" ומחושב על IEX-בלבד יהיה **גרוע יותר** מ-Typical Price הנוכחי, כי הוא נושא שם שמרמז על סמכות שאין לו. TASK-230 כבר הכריע בדיוק את השאלה הזו עבור חתימת-פתילים ונפח, ואותה ראיה חלה כאן.

זו בדיוק הנקודה ש-TASK-82 עצמו מנסח: `עוקף הנחות — לאמת זמינות לפני מימוש`. הזמינות אומתה ב-TASK-230, והתשובה הייתה לא.

### (ד) מה עלול להישבר
- **sigma-bands:** כמעט כלום. `sma20_cache` נקרא רק מ-`_signal_from_timeline_row` (`orchestrator.py:86-90`) עבור פילטר 4d, שכבוי היום (`ENTRY_GATE_MINIMAL`). שינוי בו לא נוגע בשער החי. הסיכון היחיד: פורמט-הקאש משתנה, וקבצים ישנים ב-`data/sma20_cache.json` צריכים להיקרא בסובלנות.
- **VWAP:** אם ייבנה בכל זאת — מדד שנראה סמכותי ומחושב על 7% מהנתונים, שייכנס ל-Score או לשער ויטה החלטות בלי שאיש יידע.
- ⚠️ **אזהרה נפרדת:** אם מוסיפים מדד חדש ל-`timeline_live`, זה שינוי-סכמה. `SCHEMA.json` הוא חוזה שנאכף ב-`check_08_required_columns` (`health_audit.py:834`).

---

## Q6 · IBKR recon

### (א) הראיה

**TASK-230 שלב-4ג, כלשונו:**
> · מנויי-market-data פעילים בחשבון-ה-IBKR של עמיחי — לאמת בחשבון בפועל, לא להניח.
> · בדיקת-כיסוי אמפירית: נרות-דקה היסטוריים מ-IBKR על אותו מדגם-מרובד של 168 ימי-השיא (אותו seed=42) — bars-per-day מול ה-28/390 של IEX.
> · זמינות borrow/shortable + fee ... וסטטוס-halts.
> · **תפעול: IBKR API הוא session-based (דורש Gateway/TWS רץ, לא REST)** — השלכות על אוטומציה/GHA; מגבלות-pacing.
> · Verdict: כיסוי-נרות טוב ⇒ IBKR מחליף את אופציית-SIP-בתשלום כמסלול-ה-backfill המרכזי.

**ארבעת מקומות "עמלת ההשאלה" — כולם מאומתים כלא-נתון:**

| # | מיקום | הערך | הראיה |
|---|---|---|---|
| 1 | `agent/perception/tradability.py:30` | `"borrow_fee_pct": 12.5` | קבוע ב-`MOCK_DEFAULTS`. נבחר תחת `if broker is None or AGENT_DRY_RUN` (`:62`) — **תמיד היום** |
| 2 | `agent/perception/tradability.py:89` | `"borrow_fee_pct": 0.0` | הערה בקוד: `# Alpaca paper doesn't expose real fees` |
| 3 | `agent/perception/borrow_collector.py:119` | `""` | `# BorrowFeePct — NULL` |
| 4 | `config.py:165` | `BORROW_SCENARIOS = [0.50, 2.00, 5.00]` | `# assumed annual borrow rates (fee=NULL from TASK-139 — assumptions flagged)` |

**מה `calculate_net_pnl` משתמש בו בפועל — כל הקוראים:**
```
utils.py:495   net_borrow = [calculate_net_pnl(scan_price, cls, day, r, slip=SLIP) for r in BORROW_SCENARIOS]
utils.py:506   "NetPnL_SlipOnly": calculate_net_pnl(scan_price, cls, day, 0.0, slip=SLIP)
dashboard.py:2423/2424/2432  calculate_net_pnl(sp, c, d, _b, slip=SLIP)   # _b = לולאה על BORROW_SCENARIOS
```
**רק #4.** שלושת האחרים לא מגיעים לשום חישוב.

**⚠️ ממצא נוסף: `decision_log.BorrowFee` הוא write-only.** הוא נכתב (`decision_logger.py:83` mapping · `decision_logic.py:327`), הכותרת קיימת (`create_agent_sheets.py:72`), ו-**אף קוד חי אינו קורא אותו בחזרה.** הקוראים היחידים הם טסטים (`test_tradability.py:28,56,61` · `test_decision_logger_writes.py:71`).

### (ב) האם ההמלצה עומדת
**כן על ה-recon. לא על התיאור "מסלול backfill מרכזי".**

### (ג) דעתי
**מסכים שה-recon שווה — ואוסיף שהתשובה התפעולית כבר ידועה מהתיק עצמו, ואינה דורשת recon כדי להכריע.**

`IBKR API הוא session-based (דורש Gateway/TWS רץ, לא REST)` ⇒ **הוא לא יכול לרוץ ב-GitHub Actions.** ה-runner הוא container חולף ללא תצוגה, בלי אפשרות להריץ TWS ולעבור אימות דו-שלבי. כל 17 ה-workflows של המערכת רצים ב-Actions. משמע: IBKR יכול להיות **רק** משימה מקומית על המק של עמיחי, מחוץ-לשעות — שזה בדיוק המבנה שכבר נכשל פעם אחת (רץ-הלילה, Q3).

לכן ה-verdict שהתיק מציע — `כיסוי-נרות טוב ⇒ IBKR מחליף את SIP כמסלול-ה-backfill המרכזי` — **אינו זמין כניסוח.** האפשרויות האמיתיות הן: משימה מקומית ידנית, או SIP בתשלום שכן עובד מ-Actions. ה-recon עדיין שווה בשביל שני הפערים האחרים (borrow fee, halts), אבל לא בשביל "מסלול מרכזי".

**על ארבעת מקומות ה-borrow — הטענה שלך מאומתת ואני מוסיף עליה.** לא רק שאף אחד מהם אינו נתון: **שלושה מהם אינם מחוברים לשום חישוב.** אפילו אם IBKR יחזיר עמלה אמיתית מחר, היא לא תשנה אף מספר במערכת עד שמישהו יחווט אותה ל-`BORROW_SCENARIOS` או ל-`calculate_net_pnl`. סגירת "פער ה-borrow" היא שתי עבודות, לא אחת: להשיג את הנתון, **ואז** לחווט אותו.

### (ד) מה עלול להישבר
- **ה-recon עצמו:** כלום — קריאה-בלבד.
- **אילו כן היו מחווטים עמלה אמיתית:** `HYPOTHESES.md:198-200` נועל את ה-fitness על `borrow 500%/yr`. החלפת הקבוע בנתון-אמיתי היא **שינוי ב-locked fitness** → פוסלת את HYP-001 ואת HYP-002 שתיהן ודורשת רישום-מחדש.
- **`12.5` שממשיך להיכתב:** כל ניתוח עתידי שיקרא את `decision_log.BorrowFee` יקבל קבוע ויחשוב שזה נתון.

---

## Q7 · Filter 12 — לסגור כ-WON'T-DO

### (א) הראיה

**TASK-10 בגופו, במלואו:**
> Add Filter 12 to Trader: ticker_reputation score based on historical performance. Skip tickers with bad track record (e.g., HCWB-style chronic whipsaws).

אין AC. אין DoD. אין ראיה מדודה (MASTER §10: `אין ראיה מדודה`).

**§H null result** (`HYPOTHESES.md:296-299`):
> **(a) MxV/ATRX per-trade outcome (TASK-62)** — no separation, n=229. MxV WIN med −698 vs LOSS med −559 (inverted); ATRX WIN 5.00 vs LOSS 4.90. Consistent with research-199: **MxV is a candidate-selection engine, not a per-trade predictor**; ATRX ≈ noise.

**מה כבר קיים במערכת:**
- `CHRONIC_DROPPER_BLACKLIST = ["AEHL", "TDIC"]` — `config.py:301`, עם ההערה: `chronic droppers from DropsLab x-ref (3+ drops in 30d in Apr 2026), accounted for major DRY_RUN losses`
- נאכף כ-Filter 4c: `decision_logic.py:398` — `if not _minimal and d.ticker in CHRONIC_DROPPER_BLACKLIST`
- **כבוי היום** — `ENTRY_GATE_MINIMAL = True` (`config.py:378`)
- אגרגציה פר-טיקר כבר קיימת: `trade_history_page.py:463` `_render_win_rate_by_ticker` · `:476` `df.groupby("Ticker")`

### (ב) האם ההמלצה עומדת
**המסקנה עומדת. הנימוק לא.**

### (ג) דעתי
**חולק על ההקבלה — היא שגויה מתודולוגית.**

ממצא §H(a) הוא על **מדד רציף ברמת-הסיגנל**: האם ערך MxV של עסקה בודדת מנבא את התוצאה שלה. `ticker_reputation` הוא אובייקט אחר לגמרי — **prior קטגורי ברמת-הישות**: האם היסטוריית הטיקר מנבאת את התוצאה הבאה שלו. אלה שתי שאלות סטטיסטיות נפרדות. העובדה ש-MxV לא מפריד פר-עסקה **אינה אומרת דבר** על האם AEHL כטיקר שונה מ-INOD כטיקר. אין ב-§H ולו מדידה אחת ברמת-טיקר.

**אבל המסקנה שלך נכונה משתי סיבות אחרות, חזקות יותר:**

1. **המערכת כבר בנתה פילטר-מוניטין וכיבתה אותו.** `CHRONIC_DROPPER_BLACKLIST` הוא בדיוק "skip tickers with bad track record", רק בגרסה ידנית. הוא הושבת ב-29/6 יחד עם 5 פילטרים אחרים כשעברו ל-`ENTRY_GATE_MINIMAL`. הנימוק שם (מה-Notes של TASK-128): `Source-trace proved protective filters were NOT part of the 2yr real-money method... re-validation deflated them: 129pp became 19.7pp; ROCKET_GUARD blocks 12 wins vs 7 losses`. **להוסיף Filter 12 זה להוסיף פילטר-הגנה בזמן שהמערכת בכוונה מריצה שער-מינימלי.** זו סתירה ישירה לכיוון שנבחר.

2. **הדוגמה בתיק אינה נתמכת.** התיק מצטט `HCWB-style chronic whipsaws`. HCWB מופיע בהיסטוריה כ-**באג**, לא כתופעת-שוק: TASK-4 = `P1.1 — HCWB×5 Filter 9 regression` (Done). כלומר 5 הכניסות ל-HCWB היו כשל בפילטר ה-re-entry, לא מוניטין גרוע של הטיקר.

**האם יש ראיה שמוניטין-טיקר הוא ממד נפרד?** לא מצאתי אף מדידה כזו בריפו. `_render_win_rate_by_ticker` מציג WR פר-טיקר בדשבורד, אבל אף מסמך לא בדק אם הוא יציב בין תקופות. **זו הראיה שחסרה — ובלעדיה, גם ה-WON'T-DO וגם ה-DO נשענים על הנחה.**

### (ד) מה עלול להישבר
- **סגירה כ-WON'T-DO:** מאבדים את הרישום של הרעיון. אם בעוד חצי שנה יימדד שמוניטין-טיקר כן יציב, התיק כבר לא שם.
- ⚠️ **מה שכן נשבר אם מממשים:** פילטר חדש ב-`_check_filters` תחת HYP-002 — אותה בעיה כמו Q4, אבל חמורה יותר: בניגוד ל-qty guard שמסיר תצפיות מנוונות, פילטר-מוניטין **מסיר תצפיות אמיתיות ומטה את המדגם באופן שאי-אפשר לכמת מראש**.

---

## Q8 · Score — לדחות, אבל למחוק קוד מת עכשיו

### (א) הראיה

`grep -rn "normalize_mxv\|normalize_atrx\|calculate_vwap_dist" --include="*.py" .` (ללא backups/project_sync/research):
```
formulas.py:47    calculate_vwap_dist,              ← docstring (רשימת usage)
formulas.py:168   def calculate_vwap_dist(...)      ← ההגדרה
formulas.py:556   def normalize_mxv(...)            ← ההגדרה
formulas.py:567   def normalize_atrx(...)           ← ההגדרה
formulas.py:695   print(f"calculate_vwap_dist ...   ← self-test של המודול
test_formulas.py:20    calculate_vwap_dist,         ← ייבוא
test_formulas.py:145-150                            ← 5 assertions
auto_scanner.py:33     calculate_vwap_dist,         ← ייבוא בלבד
dashboard.py:55        calculate_vwap_dist,         ← ייבוא
dashboard.py:58        normalize_mxv,               ← ייבוא
dashboard.py:59        normalize_atrx,              ← ייבוא
dashboard.py:380       vwap_dist = calculate_vwap_dist(price, current['high'], current['low'])   ← קריאה חיה
dashboard.py:560       vwap_dist = calculate_vwap_dist(price, current['high'], current['low'])   ← קריאה חיה
```

**ספירת אזכורים ב-`dashboard.py`:**
| פונקציה | אזכורים | פירוש |
|---|---|---|
| `normalize_mxv` | **1** | שורת הייבוא בלבד |
| `normalize_atrx` | **1** | שורת הייבוא בלבד |
| `calculate_vwap_dist` | **3** | ייבוא + **שתי קריאות** |
| `calculate_mxv` / `calculate_runup` / `calculate_atrx` / `validate_atrx` / `calculate_gap` / `calculate_float_pct` | 3 כל אחת | ייבוא + 2 קריאות |
| `calculate_rel_vol` | 5 | בשימוש |
| `fmt_rate_ci` | 12 | בשימוש כבד |
| `calculate_score` | 6 | בשימוש |

**האם יש טסט שיישבר:**
- `normalize_mxv` / `normalize_atrx` → `grep` על `test_formulas.py`, `test_utils.py`, כל `tests/` → **אפס אזכורים**. ✅
- `calculate_vwap_dist` → `test_formulas.py:20` (ייבוא) + `:146-150` (**5 assertions**).
- ו-`tests.yml:34`: `uv run --with-requirements requirements.txt python3 test_formulas.py` — **CI מריץ אותו כסקריפט.**

`auto_scanner.py` **מייבא** את `calculate_vwap_dist` (`:33`) אך **אינו קורא לו** — שלוש הקריאות שם הן ל-`calculate_typical_price_dist` (`:256`, `:936`, `:1246`).

### (ב) האם ההמלצה עומדת
**עומדת על שתיים מתוך שלוש. נופלת על השלישית.**

### (ג) דעתי
**חולק — `calculate_vwap_dist` אינו קוד מת.**

**מה כן מת ובטוח למחיקה:** `normalize_mxv` (`formulas.py:556`) ו-`normalize_atrx` (`:567`). אזכור אחד כל אחת ב-`dashboard.py` = שורת הייבוא. אפס קריאות בכל הריפו. אפס טסטים. שרשרת-הייבוא: `formulas` → `dashboard.py:58-59` → ולא הלאה. `calculate_score` (`formulas.py:584`) **לא נוגע בהן** — הוא קורא ל-`SCORE_WEIGHTS_V2` ו-`SCORE_CAPS_V2` בלבד (`:594-595`). מחיקה = מחיקת שתי ההגדרות + שתי שורות-הייבוא. אפס נגיעה ב-Score.

**מה לא מת:** `calculate_vwap_dist` הוא **alias חי** עם שתי קריאות בפרודקשן (`dashboard.py:380`, `:560`) ו-5 assertions ב-`test_formulas.py` שרצות ב-CI. מחיקתו:
- `dashboard.py` → `NameError` בשני מסלולי-סריקה של הדשבורד (שניהם בתוך `try/except:` עירום, כך שהוא ייבלע ויחזיר `vwap_dist = 0` — **כשל שקט**, לא קריסה)
- `test_formulas.py:20` → `ImportError` בשורת הייבוא → הסקריפט נופל → **`tests.yml` אדום**

**מה שנכון לעשות איתו הוא החלפה, לא מחיקה** — `calculate_vwap_dist(a,b,c)` → `calculate_typical_price_dist(a,b,c)` בשני האתרים ובטסט, כי הוא alias של שורה אחת (`formulas.py:176: return calculate_typical_price_dist(price, high, low)`). זו עבודה אחרת מ"מחיקת קוד מת", ובניגוד לשתי ה-normalize היא **נוגעת בקוד רץ**.

**על "לדחות את Score" — מסכים בלי הסתייגות.** `calculate_score` נקרא בנתיב הקריטי בכל החלטה (`decision_logic.py:270`), ו-`d.score` נכתב ל-`decision_log` בכל ENTER. blast-radius אמיתי.

### (ד) מה עלול להישבר
| פעולה | מה נשבר |
|---|---|
| מחיקת `normalize_mxv` + `normalize_atrx` | **כלום.** אפס call-sites, אפס טסטים |
| מחיקת `calculate_vwap_dist` | `test_formulas.py` → **CI אדום** · `dashboard.py:380/560` → כשל שקט (ה-`except:` העירום בולע) |
| ניקוי הייבואים ב-`dashboard.py:49-61` | הכל שם בשימוש חוץ מ-`normalize_mxv`/`normalize_atrx` |
| ⚠️ לא נשאלתי אבל רלוונטי | `formulas.py:47` הוא **docstring** שמונה את `calculate_vwap_dist` ברשימת ה-usage. הוא לא יישבר, אבל יתיישן |

---

## Q9 · iCloud מול GitHub Release

### (א) הראיה

```
$ gh repo view projects5069-creator/ridinghigh-pro --json visibility,isPrivate
{"isPrivate":false,"visibility":"PUBLIC"}
```
**הריפו ציבורי. חד-משמעית.**

**TASK-146 — `✔ Done`, אבל ה-AC היחיד שלו `[ ]` לא-מסומן:**
> DECISION 2026-06-10 (Amihay): repo **STAYS PUBLIC** for now, but research CSVs removed from tracking... NOTE: git **HISTORY still contains the CSVs** (commit 5b34304) — full scrub deferred

**TASK-154 — `✔ Done` (2026-08-04).** MASTER §154 מתעד את המסקנה:
> recon 2/7: אפס סודות דלופים ב-998 קומיטים. **החשיפה האמיתית היא ה-PK וקבצי ה-REPORT (verdicts של אסטרטגיה), לא 17 קבצי ה-CSV**... מקל: ה-verdicts ברובם שליליים, כלומר אין הרבה edge להגן עליו.

**TASK-196 — `✔ Done` (2026-08-04), וכל ארבעת ה-AC שלו `[ ]`:**
> - [ ] #1 להעריך מה בדיוק חשוף ב-5b34304
> - [ ] #2 להעריך חומרה
> - [ ] #3 להחליט מסלול: history-scrub מול private-migration
> - [ ] #4 **תיעוד-בלבד — אפס scrub מבוצע במשימה זו, רק הערכה + החלטה**

**מה הקובץ חושף:**
```
run_date,scan_time,decision_id,ticker,score,reason,run_id,run_created_at,run_skip_mismatch
rows: 138,915   ·   distinct tickers: 739
```

**iCloud:**
```
$ ls -ld ~/Library/Mobile\ Documents/com~apple~CloudDocs
drwx------  2 adilevy  staff  64 Aug  5 12:50 ...

$ echo "probe" > .../CloudDocs/.rhpro_write_probe_$$   →  WRITE OK
   sha256: 25be3235...  →  probe removed

$ defaults read MobileMeAccounts Accounts | grep -i "AccountID|Name"
   AccountID = "amihay.levy@icloud.com";
   Name = "MOBILE_DOCUMENTS";
```
החשבון מחובר, השירות MOBILE_DOCUMENTS פעיל, והכתיבה עובדת. **⚠️ אבל התיקייה ריקה לחלוטין** (`total 0`, גודל 64 = inode ריק), ותיקיות-אחיות תחת `Mobile Documents/` שייכות ל-WhatsApp/TextEdit/Preview בלבד. **iCloud Drive מעולם לא שימש לקבצים כאן.**

### (ב) האם ההמלצה עומדת
**כן, ובהפרש גדול יותר משחשבת.**

### (ג) דעתי
**מסכים — והראיה נגד GitHub Release חזקה ממה שניסחת.**

הריפו **ציבורי**, ולכן נכס ב-Release הוא **הורדה ציבורית לכל אדם**. אבל הנקודה החדה יותר היא שזה יהיה **חשיפה חדשה ומכוונת בזמן שהערכת החשיפה הקיימת מעולם לא בוצעה**. TASK-196 סגור כ-Done עם ארבעה AC לא-מסומנים, וה-AC הראשון הוא בדיוק `להעריך מה בדיוק חשוף`. פרסום 138,915 שורות על 739 טיקרים הוא הוספה לערימה שאיש עוד לא מדד.

**חולק על השוואה נפוצה אחת:** אפשר לטעון "ה-verdicts שליליים ממילא, אין edge להגן עליו" (MASTER §154). זה נכון לגבי **מסקנות המחקר**. ה-SKIP CSV אינו מסקנה — הוא **לוג-ההחלטות החי**: אילו טיקרים נסרקו, באיזו דקה, איזה ציון קיבלו, ולמה נדחו. זה מתאר את המנגנון, לא את התוצאה. שני דברים שונים.

**על iCloud — ישים, עם הסתייגות אחת שכן מדדתי ואחת שלא.**
מדדתי: הכתיבה עובדת, החשבון מחובר, ה-checksum של קובץ קטן שנכתב תקין. **לא מדדתי: מה קורה ל-checksum של 15MB אחרי סנכרון מלא.** זה דורש להמתין לסנכרון ולאמת מהצד השני, ולא עשיתי זאת.
מה שכן ידוע מהתנהגות iCloud: הוא עלול להוציא קבצים מהדיסק המקומי (Optimize Storage) ולהשאיר stub. `shasum` על stub **יוריד את הקובץ מחדש** ויחזיר את ה-hash הנכון — אבל רק אם יש רשת. גיבוי-DR שדורש רשת כדי לאמת את עצמו הוא גיבוי חלש יותר ממה שהוא נראה.

**מה שאני חושב שחסר בשתי האפשרויות:** שתיהן חד-יעדיות. ה-CSV הוא 15MB — הוא נכנס בנוחות גם ל-USB, גם ל-iCloud, וגם לשניהם. AC#3 מבקש `גיבוי מחוץ-למכונה`, בלשון יחיד, אבל שני עותקים בשני מדיומים עומדים באותו AC בעלות זהה כמעט.

### (ד) מה עלול להישבר
| מסלול | מה עלול להישבר |
|---|---|
| **GitHub Release** | חשיפה ציבורית של 739 טיקרים × 138,915 החלטות. בלתי-הפיך — מי שהוריד, הוריד. וזה קורה בזמן ש-TASK-196 AC#1 עדיין לא בוצע |
| **iCloud** | Optimize Storage הופך את הקובץ ל-stub; אימות-checksum ידרוש רשת. הסנכרון עצמו לא נבדק על 15MB |
| **בשניהם** | הקובץ נשען על `research/` שב-`.gitignore` (שורה `research/`) — כל תהליך-גיבוי שיסתמך על git לא יראה אותו לעולם |

---

## סיכום — טבלת הסכמה/מחלוקת

| # | ההמלצה | מסכים / חולק | הראיה המכריעה | מה עלול להישבר |
|---|---|---|---|---|
| **Q1** | להצמיד ל-1.3.0 + לאחד התקנה | **מסכים על התוכן · חולק על הסדר ועל ההנמקה** | `tests.yml:31` מתקין `-r requirements.txt` ⇒ שומר-החתימה (`test_ticker_sanitizer_v1.py:155`) מאמת **0.14.6**, בעוד הפרודקשן רץ 1.3.0. ו-12 workflows (לא 3) כבר מקבלים 0.14.6 | איחוד לפני שינוי-הפין = הסורק מת. +streamlit/plotly/openpyxl על workflow דקתי עם timeout 8 |
| **Q2** | לאמץ PK, לא לחווט | **מסכים · הנימוק שלי חזק יותר** | HYP-001 דורש יציאה בזמן (`HYPOTHESES.md:128`); לסוכן אין יציאה מבוססת-זמן כלל (`config.py:315`). חיווט ייצר אסטרטגיה **שלישית** | אימוץ PK: כלום. חיווט: פסילת ההרצה שנרשמה-מחדש ב-3/8 |
| **Q3** | להקפיא רשמית + להעביר 234-237 | **מסכים · חולק על שיטת ההעברה** | `launchctl list` ריק · רק `.disabled` + `.bak` על הדיסק ⇒ המנגנון מ-6/20 אינו קיים. אבל הענף נושא גם task-238/239 שכבר **Done ב-main** | cherry-pick נאיבי מחזיר 238/239 ל-To Do. הספירה 53→57 מיישנת כל דוח קודם |
| **Q4** | qty guard — להמתין לאוקטובר | **חולק בחלק הסיכון · מסכים בחלק המשמעת** | תחת **DRY_RUN** qty=0 מייצר עסקת-רפאים שנסגרת ב-TP/SL עם PnL=0 ונכנסת למדגם (`position_manager.py:244-262`); תחת LIVE הברוקר דוחה. **המצב שאנחנו בו הוא הלא-בטוח** | להמתין = כל סיגנל >$1000 מזהם את ההרצה. לממש = תיאור ה-Universe ברישום נהיה לא-מדויק |
| **Q5** | שני מדדי שורט חינמיים | **חולק — זה אחד, לא שניים** | sigma-bands: `closes` כבר בזיכרון (`sma20_cache.py:78`), אפס קריאות נוספות. VWAP: feed=IEX (`alpaca_provider.py:364`) + median **28/390** נרות (TASK-230 AC#3) | VWAP על 7% מהדקות ומבורסה אחת יהיה גרוע מ-Typical Price ויישא שם שמרמז על סמכות שאין לו |
| **Q6** | IBKR recon | **מסכים על ה-recon · חולק על "מסלול מרכזי"** | `IBKR API הוא session-based (דורש Gateway/TWS רץ, לא REST)` ⇒ **לא יכול לרוץ ב-Actions**, וכל 17 ה-workflows שם. ארבעת מקומות ה-borrow מאומתים כלא-נתון; **שלושה מהם לא מחוברים לשום חישוב** | חיווט עמלה אמיתית = שינוי ב-locked fitness ⇒ פוסל את HYP-001 **ואת** HYP-002 |
| **Q7** | Filter 12 — WON'T-DO | **המסקנה עומדת · ההקבלה שגויה** | §H(a) מדד **רציף ברמת-סיגנל**; reputation הוא **prior קטגורי ברמת-ישות** — שאלות שונות. אבל: `CHRONIC_DROPPER_BLACKLIST` כבר מממש מוניטין וכבוי בכוונה (`config.py:301` + `ENTRY_GATE_MINIMAL`), ו-HCWB היה **באג** (TASK-4) לא תופעת-שוק | סגירה: מאבדים את הרישום. מימוש: פילטר שמסיר תצפיות **אמיתיות** תחת HYP-002 — גרוע מ-Q4 |
| **Q8** | למחוק קוד מת עכשיו | **חולק על אחת מהשלוש** | `normalize_mxv`/`normalize_atrx`: אזכור **אחד** כל אחת ב-dashboard = ייבוא בלבד, אפס טסטים ✅. `calculate_vwap_dist`: **2 קריאות חיות** (`dashboard.py:380,560`) + **5 assertions** ב-`test_formulas.py` ש-CI מריץ (`tests.yml:34`) | מחיקת vwap_dist ⇒ CI אדום + כשל שקט בדשבורד (`except:` עירום בולע את ה-NameError) |
| **Q9** | iCloud, לא Release | **מסכים · בהפרש גדול יותר** | `isPrivate: false` — ריפו **ציבורי**. TASK-196 סגור כ-Done עם **ארבעה AC לא-מסומנים**, כולל `#1 להעריך מה בדיוק חשוף`. הקובץ: 739 טיקרים × 138,915 החלטות | Release: חשיפה בלתי-הפיכה בזמן שההערכה לא בוצעה. iCloud: Optimize Storage → stub; אימות-checksum ידרוש רשת |

---

## צעדים מקדימים שלא הזכרת

1. **Q1 — סדר-פעולות מחייב.** שינוי הפין ל-1.3.0 חייב לקדום לאיחוד ההתקנה, או להיות באותו commit. ההפך = סורק מת בשעות-מסחר.
2. **Q1 — `bs4` אינו ב-`requirements.txt`.** הוא מגיע טרנזיטיבית מ-finvizfinance. `test_ticker_sanitizer_v1.py:35` פותח ב-`pytest.importorskip("bs4")` — אם התלות תשתנה, **כל קובץ-הטסט ידלג בשקט** במקום להיכשל.
3. **Q3 — בחירה ברמת-קובץ, לא cherry-pick.** הענף מערבב 4 תיקים חדשים עם 4 שכבר Done ב-main.
4. **Q4 — קובץ-הראיה חסר.** `plans/stateless-seeking-sifakis.md` לא קיים בריפו, ו-**שישה תיקים מצטטים אותו** (208, 209, 223, 224, 226, 229). ה-RULING של 3/7 שעליו TASK-224 נשען אינו ניתן לאימות.
5. **Q5 — כל מדד חדש ב-`timeline_live` הוא שינוי-סכמה.** `SCHEMA.json` נאכף ב-`check_08_required_columns` (`health_audit.py:834`).
6. **Q6 — נתון-borrow אמיתי אינו "תוספת".** הוא שינוי ב-locked fitness של שתי היפותזות רשומות.
7. **Q8 — `calculate_vwap_dist` דורש החלפה בשלושה מקומות** לפני מחיקה, לא מחיקה.
8. **Q9 — AC#3 של TASK-126 מדבר על יעד אחד.** שני מדיומים (iCloud + USB) עומדים באותו AC בעלות כמעט זהה.

---

## מה גיליתי שלא שאלת עליו

1. **⚠️ שומר-החתימה של finviz מאמת את הגרסה הלא-נכונה.** `tests.yml` → 0.14.6; פרודקשן → 1.3.0. השומר שנועד למנוע חזרה של TASK-238 מעולם לא ראה את הגרסה שהוא אמור להגן עליה. **זה הממצא הכי משמעותי בכל התשעה.**

2. **`decision_log.BorrowFee` הוא write-only.** נכתב בכל ENTER עם הקבוע `12.5`, ואף קוד חי לא קורא אותו. הקוראים היחידים הם ארבעה טסטים.

3. **תחת DRY_RUN הברוקר לא מגן, ותחת LIVE הוא כן.** `_sim_bracket_order` (`alpaca_broker.py:322`) לא בודק qty; Alpaca כן. זו היפוך של האינטואיציה ש-DRY_RUN בטוח יותר.

4. **`google-auth-oauthlib` הוא תלות-רפאים ב-`auto_scan.yml`.** אפס מייבאים בכל הקוד החי. `_get_oauth_creds` משתמש ב-`google.oauth2.credentials` מ-`google-auth`.

5. **`calculate_vwap_dist` שורד בזכות שני `except:` עירומים.** `dashboard.py:381` ו-`:561` — אם היה נמחק, ה-`NameError` היה נבלע והמדד היה הופך שקטית ל-0. הטסט הוא מה שיתפוס, לא הפרודקשן.

6. **`plans/` לא קיים בריפו כלל.** שישה תיקים מפנים אליו כמקור-ראיה.

7. **iCloud Drive מחובר אך מעולם לא שימש.** התיקייה ריקה (`total 0`) והאחיות שלה שייכות ל-WhatsApp/TextEdit. זה יעד תקין, אבל לא יעד **מנוסה**.

8. **TASK-196 סגור כ-Done עם ארבעה AC לא-מסומנים**, כולל `#4 תיעוד-בלבד — אפס scrub מבוצע במשימה זו, רק הערכה + החלטה`. גם ההערכה וגם ההחלטה לא סומנו.

---

## אימות

```
$ git status --porcelain
?? docs/auto-dancer/
?? reports/

$ git diff --stat
(ריק)
```

לא נגעתי בקוד, לא הרצתי pytest, לא הרצתי pip, לא ביצעתי fetch ל-FINVIZ, לא נגעתי ב-Sheets/Drive, לא commit, לא push, **לא שיניתי סטטוס של אף תיק, לא פתחתי ואל סגרתי תיק.**
הכתיבה היחידה: הדוח הזה ו-`reports/INDEX.md`.

**מה שלא אימתתי, במפורש:**
- חתימת `_get_table` ב-finvizfinance **1.3.0** — דורש התקנה. הראיה היחידה היא הערת-קוד עם file:line.
- כמה סיגנלים במחיר >$1000 היו בפועל — דורש קריאת Sheets, השוק פתוח.
- checksum של 15MB אחרי סנכרון iCloud מלא — דורש המתנה לסנכרון ואימות מהצד השני.
- האם DropsLab עצמו עדיין חי — מחוץ לריפו.
