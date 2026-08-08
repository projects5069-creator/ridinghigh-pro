# שכבת התלויות של 53 התיקים — קובץ ב'

**מה בקובץ הזה:** §3 הגרף המאוחד · §4 חסימה בפועל מול מוצהרת · §5 פרמיסות שהתיישנו.
**קובץ א' מכיל:** §0 ממצא על מנגנון ה-CLI · §1 סטטוס כל תיק-תלות · §2 השדות מ-MASTER.

נכתב 2026-08-05 11:31 Lima. **תיאור וחילוץ בלבד.** אין תוכנית, אין דירוג, אין סדר-ביצוע, אין הצעת תיקון.
**⚠️ לא שיניתי סטטוס של אף תיק.**

---

## 3. הגרף המאוחד

מיזוג של שני מקורות: **גוף התיק** (`backlog task <N> --plain`) ו-**MASTER** (`docs/MASTER_TASK_LIST_2026-08-03.md`, שדה `תלוי ב / חוסם את`).
עמודת המקור: `גוף` · `MASTER` · `שניהם`.
סטטוס התלות בסוגריים לפי §1 של קובץ א'.

### 3.1 — הטבלה המלאה

| תיק | מי חוסם אותו | את מי הוא חוסם | מקור |
|---|---|---|---|
| **9** | — | — (MASTER: "עצמאי. משיק ל-TASK-66") | שניהם |
| **10** | — | — (MASTER: "עצמאי") | שניהם |
| **39** | — | — | שניהם |
| **49** | — (106 Done, מרחיב אותו) | — | שניהם |
| **54** | — (53 Done = תקדים-סיכון בלבד) | — | שניהם |
| **65** | 109 (To Do) · 215 (To Do) | — | **MASTER** (הגוף מונה 105/106/109/215 כ"קשור", MASTER מדייק ש-109+215 הם השארית) |
| **66** | — (62/28/96 Done) | **מעבר SENTINEL ל-active** (לא תיק) | שניהם |
| **71** | **74 (To Do)** | — | **MASTER** (`תלוי בפועל ב-TASK-74`) — הגוף מזכיר רק את 62 |
| **73** | 65 (To Do) | — | שניהם (48/62 Done) |
| **74** | — | **71** | **MASTER** (הגוף אומר `חוסם ניתוח 'הצד השני' המלא (TASK-71)`) — שניהם למעשה |
| **82** | — (80/139/172 Done) · מקור-נתונים בתשלום | — | שניהם |
| **83** | — (80 Done) · זמן/n | — | שניהם |
| **88** | — (48 Done) | — | שניהם |
| **92** | — (58 Done) | — | שניהם |
| **101** | **186 (In Progress)** | — | **MASTER** (`ובפועל על TASK-186 שתקוע`) — הגוף מציין רק 93/94 שהם Done |
| **109** | — (108/106 Done) · שער track-record | — | שניהם |
| **126** | — (125 Done) | — | שניהם |
| **128** | **HYP-002** (VOIDED+re-registered) · 194 · 202 · 205 · 206 | **194** (AC#4 `via TASK-194`) | שניהם — **מעגל עם 194** |
| **145** | — (139/60 Done) | — | שניהם |
| **153** | — (139/156/27 Done) | — | שניהם |
| **176** | — (171/136 Done, 67 בארכיון) | — | שניהם |
| **179** | ⚠️ **אף אחד** (172/177/178 כולם Done) | — | **MASTER** מתקן את הגוף |
| **186** | **234–237** (To Do, ענף אחר) · אישור | **101** | **חדש** — TASK-234 בגופו: `Blocks TASK-186`. אינו ב-MASTER ואינו בגוף 186 |
| **194** | **HYP-002** · 128 | **128** · 208 · 209 | שניהם — **מעגל עם 128** |
| **202** | — (200 Done) | — | שניהם |
| **205** | — | — | שניהם |
| **206** | 230 (To Do) | — | שניהם (201/203/149/168 Done) |
| **208** | **209** (To Do) · הכרעה | **209** | שניהם — **מעגל עם 209** |
| **209** | **208** (To Do) · הכרעה | **208** | שניהם — **מעגל עם 208** |
| **215** | — (58/214/213 Done) · שני צעדים תפעוליים | **244** · מקל על 65, 109 | **MASTER** (`חוסם בפועל את 244`) — הגוף לא אומר זאת |
| **216** | — (91 Done) | — | שניהם (MASTER: קשור ל-243, 219) |
| **217** | **219** (To Do) | **219** | שניהם — **מעגל עם 219** |
| **218** | — (176 To Do אך AC#1 בוצע; 213 Done) | — | שניהם |
| **219** | **217** (In Progress) · **תאריך 1/9** | **217** | שניהם — **מעגל עם 217** |
| **222** | — (211 Done) | — | שניהם |
| **224** | — · אישור מפורש | — | שניהם |
| **225** | **HYP-002** (עד תחילת אוקטובר) | — | שניהם |
| **226** | — (**166 Done**) | — | שניהם — ⚠️ הגוף אומר `unify with TASK-166`, ו-166 **Done** |
| **229** | **HYP-002** · §G תפוס | — | שניהם |
| **230** | — (182 Done) · blocked-by-data (IEX) · הכרעת-עלות | — | שניהם |
| **240** | ⚠️ **אף אחד** (238 Done) | — | **MASTER** מתקן את הגוף |
| **241** | **246** (To Do) | — | **MASTER** (`תלוי ב-246 בלבד`) — הגוף מזכיר רק את HYP-002 |
| **243** | — (242 Done) · **תאריך 1/9** | **251** (חלק §10) · 216, 219 | **MASTER** (`חוסם את החלק של §10 ב-251`) |
| **244** | **215** (To Do) | — | **MASTER** (הגוף אומר HYP-002; MASTER: `תלוי ב-215`) |
| **245** | ⚠️ **אף אחד** (238 Done) | — | **MASTER** מתקן את הגוף |
| **246** | ⚠️ **אף אחד** (238 Done) · אישור-כתיבה | **241** | **MASTER** (`חוסם את 241`) |
| **248** | — (238 Done) · הכרעה | — | שניהם |
| **249** | — (239 Done) | **מחליף את 239** | שניהם |
| **250** | — (55/228 Done) | — | שניהם |
| **251** | **243** (To Do) | — | שניהם |
| **252** | 245 (To Do — רק כמוטיבציה) | — | שניהם (MASTER: `עצמאי`) |
| **253** | — · סדר עצמי (גלאי לפני תיקון) | — | שניהם |
| **254** | 208 · 209 (שניהם To Do) | — | שניהם (MASTER: `עצמאי. קשור ל-65, 73, 208, 209`) |

### 3.2 — קשרים שקיימים ב-MASTER ואינם בגוף התיק (8)

| קשר | הציטוט מ-MASTER | מה הגוף אומר |
|---|---|---|
| **71 ← 74** | `תלוי בפועל ב-TASK-74` (§71 DEPS) | הגוף של 71 מזכיר רק את TASK-62 |
| **101 ← 186** | `ובפועל על TASK-186 שתקוע` (§101 BLK) | הגוף של 101 מזכיר רק 93/94 |
| **215 → 244** | `חוסם בפועל את 244, ומקל על 65, 105, 109` (§215 DEPS) | הגוף של 215 לא מזכיר את 244 כלל (244 נוצר חודש אחריו) |
| **244 ← 215** | `תלוי ב-215` (§244 DEPS) | הגוף של 244 מזכיר את HYP-002 ואת "the finviz ticker corruption", לא את 215 |
| **241 ← 246** | `תלוי ב-246 בלבד` (§241 DEPS) | הגוף של 241 מזכיר רק את HYP-002 |
| **246 → 241** | `**חוסם את 241**` (§246 DEPS) | הגוף של 246 לא מזכיר את 241 |
| **243 → 251** | `חוסם את החלק של §10 ב-251` (§243 DEPS) | הגוף של 243 לא מזכיר את 251 |
| **65 ← 109, 215** | `השארית האמיתית היא TASK-109 ... ו-TASK-215` (§65 PREMISE) | הגוף מונה 105/106/109/215 כרשימת-"קשור" בלי לומר מי החוסם |

### 3.3 — קשרים שקיימים בגוף ואינם ב-MASTER (5)

| קשר | הציטוט מהגוף | מה MASTER אומר |
|---|---|---|
| **179 ← 172, 177, pre-registration** | `BLOCKED ON: TASK-172 + TASK-177 + pre-registration task` | MASTER מבטל אותו: `⚠️ לא מה שכתוב ... שלושתם Done` |
| **240 ← ticker corruption scope** | `Blocked on the ticker corruption scope` | MASTER מבטל: `TASK-238 Done` |
| **245 ← ticker corruption scope** | `Blocked in practice on the ticker corruption scope` | MASTER מבטל: `TASK-238 Done` |
| **246 ← the finviz ticker fix** | `BLOCKED ON: the finviz ticker fix` | MASTER מבטל: `TASK-238 Done ומאומת` |
| **250 ← TASK-55** | `a direct contribution to TASK-55` | MASTER מחליף ל-215: `תורם ל-215` (ו-55 Done) |

### 3.4 — קשר שאינו באף אחד משני המקורות (1)

| קשר | המקור |
|---|---|
| **186 ← 234, 235, 236, 237** | גוף TASK-234 (על ענף `fix/auto-dancer-planmd`): `"Blocks TASK-186."` · TASK-235: `"blocks --manual execute"` · TASK-236: `"execute-proof final stage"` |

ארבעת התיקים האלה **אינם** ב-53, אינם ב-MASTER, ואינם מוזכרים בגוף TASK-186. הם היחידים בכל המיפוי שהם **To Do** ומופיעים כחוסמים.

### 3.5 — מעגלים

**שלושה מעגלים דו-כיווניים:**

| מעגל | הראיה משני הצדדים |
|---|---|
| **208 ↔ 209** | 208 (Notes): `נדחה עם TASK-209` · 208 (MASTER DEPS): `נדחה יחד עם 209` — 209 (MASTER DEPS): `צמוד ל-208` |
| **217 ↔ 219** | 217 (Notes): `WIRING = TASK-219` · 217 (MASTER BLK): `השארית היא 219` — 219 (גוף): `Follow-up of TASK-217` · 219 (MASTER DEPS): `Follow-up ל-217` |
| **128 ↔ 194** | 128 (AC#4): `promote shadow to active only after ... via TASK-194` — 194 (גוף): `BLOCKED until >=2 weeks of multi-regime shadow_gate_events data (TASK-128)` · 194 (MASTER DEPS): `תלוי ב-HYP-002` |

⚠️ **המעגל השלישי (128↔194) נשבר בפועל:** MASTER קובע ששניהם תלויים ב-HYP-002 ולא זה בזה, ובפועל ה-flip כבר בוצע ב-29/6 — כלומר AC#4 של 128 ("promote via 194") הוקדם ובוצע לפני שהתנאי שלו התקיים.

**אין מעגלים באורך 3 ומעלה** שזיהיתי.

---

## 4. חסימה בפועל מול חסימה מוצהרת

⚠️ **ארבע הקטגוריות שהגדרת אינן מכסות את כל 53.** 11 תיקים אינם מנוסחים כחסומים כלל, אין להם תלות באף תיק, ו-MASTER כותב עליהם `מה חוסם: כלום`. הוספתי להם קטגוריה חמישית: **NOT-BLOCKED**. זה תיאור עובדתי, לא הערכה.

### 4.1 — BLOCKED-REAL (2) — כל התלויות שלו פתוחות

| תיק | החוסם | הראיה |
|---|---|---|
| **71** | TASK-74 (To Do) | MASTER §71 BLK: `בפועל TASK-74, שכן 94% מהמניות שנסרקו אין להן תוצאה ידועה` · MASTER §74 CONTRIB: `חוסם את TASK-71 ברמת n משמעותי` · `backlog task 74 --plain → Status: ○ To Do` |
| **244** | TASK-215 (To Do) | MASTER §244 BLK: `TASK-215. הפילטר עוצר את הנזק, לא את ה-429 עצמו` · MASTER §215 DEPS: `חוסם בפועל את 244` · `backlog task 215 --plain → Status: ○ To Do` |

### 4.2 — UNBLOCKED (13) — כל התלויות Done, אך התיק עדיין מנוסח כחסום

| תיק | מה כתוב | מצב התלויות | הראיה |
|---|---|---|---|
| **66** | `לחקור לפני כל מעבר ל-active` | 62 Done · 28 Done · 96 Done | MASTER: `מה חוסם: כלום לחקירה` |
| **145** | `next scheduled run 1/7 must be watched` | 139 Done · 60 Done | MASTER: `מה חוסם: כלום`. הריצה של 1/7 **ושל 1/8** עברו |
| **153** | `Review with Amihay, then adopt` | 139 Done · 156 Done · 27 Done | MASTER: `מה חוסם: כלום` |
| **176** | AC#2 `Quota savings measured` | 171 Done · 136 Done · 67 בארכיון | MASTER: `מה חוסם: כלום`. AC#1 בוצע (`config.py:364`) |
| **179** | `BLOCKED ON: TASK-172 + TASK-177 + pre-registration task` | **172 Done · 177 Done · 178 Done** | MASTER: `⚠️ לא מה שכתוב ... החוסם האמיתי הוא כוח סטטיסטי בלבד`. `HYPOTHESES.md:167-171`: `TASK-172 ✅ DONE · TASK-177 ✅ DONE` |
| **202** | (לא מנוסח כחסום) `Documented debt; not started` | 200 Done | MASTER: `מה חוסם: כלום` |
| **222** | (לא מנוסח כחסום) | 211 Done | MASTER: `מה חוסם: כלום` |
| **226** | `Natural home: unify with TASK-166` | **166 Done** (2026-06-23) | `backlog task 166 --plain → ✔ Done`. MASTER §166: `הבדיקה כבר קיימת חלקית, check_30_lineage_sentinel ב-health_audit.py:1339, ואומתה PASSED ב-3/8` |
| **240** | `Blocked on the ticker corruption scope` | **238 Done** (2026-07-30) | MASTER: `⚠️ התיאור אומר Blocked on the ticker corruption scope, ו-TASK-238 Done` |
| **245** | `Blocked in practice on the ticker corruption scope` | **238 Done** | MASTER: `התיק אומר "חסום בפועל על היקף שחיתות הטיקרים", ו-TASK-238 Done` |
| **246** | `BLOCKED ON: the finviz ticker fix` | **238 Done** | MASTER: `⚠️ התיאור אומר BLOCKED ON: the finviz ticker fix, ו-TASK-238 Done ומאומת` |
| **249** | (לא מנוסח כחסום) | 239 Done | MASTER: `מה חוסם: כלום` |
| **250** | `a direct contribution to TASK-55` | **55 Done** (2026-05-29) · 228 Done | MASTER: `מה חוסם: כלום` |

### 4.3 — PARTIAL (7) — חלק Done וחלק פתוח

| תיק | Done | עדיין פתוח |
|---|---|---|
| **65** | 105 · 106 · 62 · 198 (ארכיון) | **109** · **215** — MASTER §65 PREMISE: `השארית האמיתית היא TASK-109 (auto-repair כבוי) ו-TASK-215` |
| **73** | 48 · 62 | **65** — MASTER §73 EVID: `score_analytics באפס שורות הוא downstream של MetricsAtEntry הריק (TASK-65)` |
| **101** | 93 · 94 | **186** (In Progress) — MASTER §101 BLK: `ובפועל על TASK-186 שתקוע` |
| **216** | 91 | **243** · **219** — MASTER §216 DEPS: `קשור ל-91, 243, 219` |
| **217** | 105 · 216-חלקי · 91 | **219** — MASTER §217 BLK: `כלום. השארית היא 219` |
| **241** | **238** · **247** | **246** — MASTER §241 BLK: `שלושה חוסמים רשומים, שניים מהם כבר Done: 238 (Done) ו-247 (Done)` |
| **251** | 143 · 242 | **243** — MASTER §251 BLK: `החלק של §10 שייך ל-TASK-243` |

### 4.4 — SELF-BLOCKED (20) — חסום על תאריך, מדידה, או הכרעת עמיחי

| תיק | סוג החסימה | הראיה |
|---|---|---|
| **10** | נתיב מסחר חי | MASTER: `לא מתועד בתיק. בפועל נוגע בנתיב הכניסה החי` |
| **49** | שער עצמי — חקירה לפני תיקון | גוף: `חקירה לפני תיקון — אסור לגעת ב-order_manager עד שהשורש ברור` |
| **82** | מקור-נתונים בתשלום (3 מ-5) | MASTER: `שלושה מהחמישה דורשים מקור נתונים בתשלום` |
| **83** | **זמן** — צבירת n · ריפו חיצוני | MASTER: `זמן. מניות חדשות לא ישלימו 15 יום מיד` |
| **92** | **הכרעת עמיחי** | MASTER: `החלטה שלך. אסור לבצע בלי הכרעה מפורשת`. AC#3: `עמיחי החליט במפורש איזו רמה` |
| **109** | **מדידה** — שער track-record | MASTER: `השער לא נפתח. recon 2/7: יש רק יום הוכחה אחד` |
| **128** | **HYP-002** → תחילת אוקטובר | MASTER: `מה חוסם: HYP-002` · `HYPOTHESES.md:257`: `45 trading days from 2026-08-03 reaches early October` |
| **186** | **אישור עמיחי** + 234-237 | MASTER: `אישור שלך`. + TASK-234: `Blocks TASK-186` |
| **194** | **HYP-002** | MASTER: `מה חוסם: HYP-002` |
| **208** | **הכרעת עמיחי** | MASTER: `החלטה שלך. ההכרעה מ-30/6 היא שכל עבודת Score נדחית להמשך, כמכלול` |
| **209** | **הכרעת עמיחי** | MASTER: `החלטה שלך. blast-radius גבוה` |
| **215** | **שני צעדים תפעוליים** (secret + push) | MASTER: `הסוד GOOGLE_CREDENTIALS_JSON_AS טרם הוגדר ב-GitHub, וה-push דורש זהירות`. **כל תלויות-התיקים שלו Done** (58, 213, 214) |
| **219** | **תאריך/אירוע — 1/9** | MASTER: `⚠️ זמן ואירוע. ה-raise יורה רק ברוטציה ... הרוטציה הבאה היא 1/9, כלומר 29 יום מהיום` |
| **224** | **אישור מפורש** — נתיב כניסה חי | גוף: `LIVE ENTRY PATH — implement only on a separate explicit go` |
| **225** | **HYP-002** → תחילת אוקטובר | MASTER: `⚠️ שער קשיח שהוארך ... הפסילה של 3/8 האריכה את זה לתחילת אוקטובר` |
| **229** | **HYP-002** + §G תפוס | MASTER: `HYP-002. וגם §G ב-HYPOTHESES.md תפוס על ידי HYP-003` |
| **230** | **blocked-by-data** (feed IEX) + הכרעת-עלות | MASTER: `⚠️ AC#3 מסומן כבר כבוצע, והתשובה היא blocked-by-data ... חתימת פתילים ונפח אינה ניתנת לבדיקה על ה-feed הנוכחי` |
| **243** | **תאריך — 1/9** | MASTER: `⚠️ זמן. הרוטציה הבאה היא 1/9, כלומר 29 יום` |
| **248** | **הכרעת עמיחי** | MASTER: `החלטה שלך`. גוף: `DECISION NEEDED: pin to the version CI actually resolves, or drop the pin` |
| **253** | **סדר עצמי** — גלאי לפני תיקון | גוף: `DO NOT FIX BLIND ... Build a detector first ... get a baseline over several days, and only then touch the write` |

### 4.5 — NOT-BLOCKED (11) — קטגוריה חמישית שהוספתי

אין להם תלות בתיק פתוח, ו-MASTER כותב עליהם `מה חוסם: כלום`. הם אינם מנוסחים כחסומים, ולכן `UNBLOCKED` (שמשמעו "כתוב שחסום אך אינו") לא חל.

| תיק | MASTER `מה חוסם` | הערה |
|---|---|---|
| **9** | `כלום` | MASTER: `TASK-66 מראה שהמעבר shadow→active חסום ממילא` — הערת-הקשר, לא תלות |
| **39** | `כלום` | — |
| **54** | `כלום, אבל התיק מזהיר: hook שגוי יכול לחסום את כל פעולות Claude Code` | אזהרת-סיכון, לא חוסם |
| **74** | `כלום, אבל התיק מסמן שזו עבודה כבדה מול Alpaca` | הוא-עצמו חוסם את 71 |
| **88** | `כלום` | — |
| **126** | `כלום. הליבה כבר בוצעה` | ⏰ **AC#3 נושא תאריך: ~9/8, בעוד 4 ימים** |
| **205** | `כלום` | — |
| **206** | `כלום` | MASTER מציין `קשור ל-230` שפתוח |
| **218** | `כלום. התיק מסמן את זה כ-MARKET-SAFE` | — |
| **252** | `כלום` | 245 מוזכר כמוטיבציה, לא כתלות |
| **254** | `כלום` | MASTER: `עצמאי` |

### 4.6 — הספירה

| קטגוריה | # |
|---|---|
| BLOCKED-REAL | **2** |
| UNBLOCKED | **13** |
| PARTIAL | **7** |
| SELF-BLOCKED | **20** |
| NOT-BLOCKED (קטגוריה חמישית) | **11** |
| **סה"כ** | **53** |

**עובדה מדודה:** מתוך 118 תיקי-התלות שנבדקו ב-§1, **108 הם Done**, 5 בארכיון, ו-**4 בלבד הם To Do** — וארבעת אלה (234-237) יושבים על ענף אחר ואינם ב-53. בתוך ה-53 עצמם, רק **6 תיקים** מופיעים כתלות של אחר: 74, 215, 246, 243, 219, 209 (ו-208, 217, 186, 65, 109, 230 בכיוונים משניים).

---

## 5. פרמיסות שהתיישנו

**24 פריטים.** מחולקים לפי סוג. כל פריט: הציטוט מהתיק, מול העובדה היום.

### 5.1 — חוסם שנסגר (6)

| # | תיק | הציטוט מהתיק | העובדה היום |
|---|---|---|---|
| 1 | **179** | `BLOCKED ON: TASK-172 + TASK-177 + pre-registration task` | `backlog task 172 → ✔ Done (2026-06-23)` · `177 → ✔ Done (2026-06-23)` · `178 → ✔ Done (2026-06-23)`. `docs/HYPOTHESES.md:167-171`: `TASK-172 ✅ DONE ... TASK-177 ✅ DONE ... PHASE 0 data-integrity ✅` |
| 2 | **240** | `Blocked on the ticker corruption scope` | `backlog task 238 → ✔ Done (2026-07-30)` |
| 3 | **245** | `Blocked in practice on the ticker corruption scope` | `backlog task 238 → ✔ Done` |
| 4 | **246** | `BLOCKED ON: the finviz ticker fix, so that the cleanup rule can distinguish a phantom from a real symbol` | `backlog task 238 → ✔ Done`. הפונקציה קיימת: `formulas.classify_phantom_tier` (`formulas.py:441`) |
| 5 | **250** | `That is a direct contribution to TASK-55` | `backlog task 55 → ✔ Done (2026-05-29)` |
| 6 | **226** | `Natural home: unify with TASK-166 (daily lineage sentinel)` | `backlog task 166 → ✔ Done (2026-06-23)`. הבדיקה חיה: `check_30_lineage_sentinel` — `health_audit.py:1339` |

### 5.2 — תאריך שעבר (6)

| # | תיק | הציטוט | היום |
|---|---|---|---|
| 7 | **128** | AC#4: `promote shadow to active only after multi-regime and shadow-benign **about 2026-07-27**` | עברו 9 ימים. ה-promote בוצע ב-29/6, **חודש לפני** התאריך |
| 8 | **194** | `checkpoint **2026-07-27** = החלטת-promote נפרדת` | עבר. ההרצה נפסלה ב-3/8 |
| 9 | **145** | `next scheduled run **1/7** must be watched` | עברו 1/7 **וגם 1/8** |
| 10 | **176** | `AC#2 ... measure via scripts/measure_429_by_workflow_v1.py **over 1-3/7**` | עבר חודש |
| 11 | **215** | `step-3 אימות-429 ... מתחבר ל-TASK-213 (**דדליין 6/7**)` | `backlog task 213 → ✔ Done (2026-07-03)` — התיק שהדדליין שלו צוין נסגר, 215 עדיין פתוח |
| 12 | **219** | `PREREQ: audit ... avoid halting **1/8** rotation` · `raise fires only at rotation **1/8**` | הרוטציה של 1/8 **רצה** (`commit 33ea4dd`, 2026-08-01, `Auto: Add sheets_config for new month`). האירוע שהתיק המתין לו קרה, ולא אומת |

### 5.3 — דגל קונפיג שהתהפך (2)

| # | תיק | הציטוט | העובדה בקוד |
|---|---|---|---|
| 13 | **128** | הכותרת: `Gate כניסה מבוסס-מדדים בא **shadow mode**` · הגוף: `Build as shadow layer ... for 2+ weeks multi-regime **before any active gating**` | `EXPLICIT_GATE_MODE = "active"` — `config.py:374` · `ENTRY_GATE_MINIMAL = True` — `config.py:378`. הגייט חי מ-29/6 |
| 14 | **194** | `BLOCKED until >=2 weeks of multi-regime shadow_gate_events data (TASK-128) show the SCORE_TOO_LOW->would-ALLOW divergence is benign. **Then** either flip EXPLICIT_GATE_MODE to active` | ה-flip בוצע. `config.py:372-373` (הערת-inline): `"TASK-194 stage-2 flip 2026-06-29 ... Flipped without >=2wk shadow-accumulation (owner decision, DRY_RUN)"` |

### 5.4 — מספר שורות/מדידה שהשתנו (5)

| # | תיק | הציטוט | העובדה היום |
|---|---|---|---|
| 15 | **73** | `CRITIC (critic_v1.py, **835 שורות**)` | `wc -l agent/critic/critic_v1.py` → **942** |
| 16 | **245** | `From 2026-07-15 onward it runs 23, 14, 12, 20, 38, 20, 18, 14, 22, 28. Median falls from roughly 46 to roughly **20**` | MASTER §245 PREMISE: `אומת 3/8: 29/7 היה 57, 30/7 היה 145, 31/7 היה 57, ו-3/8 היה **85**. הנפח מעל רמת סוף יולי` |
| 17 | **246** | `DRY_RUN_OPEN **83** ... 64 are on confirmed phantom tickers, 19 are on doubled letter candidates ... and **zero are on a clean ticker**` | MASTER: `נמדד 3/8: **84 פתוחות, 82 CONFIRMED, אחת SUSPECT ואחת CLEAN**. כלומר יש אחת CLEAN, בניגוד לטענה` |
| 18 | **252** | `by then 71 rows and **83 positions** were affected` | MASTER §252: `המספר "83 positions" בגוף התיק הוא **84** נכון ל-3/8` |
| 19 | **82** | AC#4: `borrow_data tabs **empty** (verified live)` | MASTER §82: `**הערה:** borrow_data כבר לא ריק. אומת 3/8: 63 שורות ביולי, 4 באוגוסט` |

### 5.5 — מספר-שורה בקוד שזז (6)

כולם מאומתים על ידי בסשן הזה מול הקוד החי.

| # | תיק | הציטוט | השורה היום |
|---|---|---|---|
| 20 | **194** | `Filter 1 Score gate (**decision_logic.py:277** d.score<AGENT_MIN_SCORE)` | `agent/trader/decision_logic.py:372` — `if include_score_gate and d.score < AGENT_MIN_SCORE` |
| 21 | **194** | `Score ranking (**auto_scanner.py:578/1338** idxmax / TRADE_ENTRY_MIN_SCORE>=70)` | `auto_scanner.py:504` · `:1349` · `:1352` |
| 22 | **208** | `Score (TRADE_ENTRY_MIN_SCORE>=70, idxmax/sort) at **:490/578/1335/1338**` · Notes: `update_live_trades ENTRY_MIN_SCORE (**:994**)` | `:504` · `:1008` · `:1349` · `:1352`. ⚠️ ה-Notes מ-3/7 כבר תיקן חלק, וגם הוא זז |
| 23 | **209** | `normalize_mxv/normalize_atrx (**formulas.py:457/468**)` · `calculate_vwap_dist (deprecated alias, **formulas.py:596**)` · `dashboard.py:**63**` · `decision_logic.py:**266**` | `formulas.py:556` · `:567` · `:168` · `dashboard.py:62` · `decision_logic.py:270`. ⚠️ `health_audit.py:738` ו-`:1008` **נכונים** |
| 24 | **226** | `auto_scanner.py:**65** 'No results' path` · `sentinel scan_freshness (**WARN>=3m/BLOCK>=5m**, checks/scan_freshness.py:8-9)` | המסלול: `auto_scanner.py:418-427`. הספים: `SENTINEL_SCAN_MAX_AGE_MINUTES = 5` / `SENTINEL_SCAN_MAX_AGE_BLOCK_MINUTES = 10` — `config.py:395-396`, עם הערה: `"was 3 — too tight vs ~1.6min scan cadence"` |
| 25 | **252** | `**_HA_SHEET_CACHE** at line **1088** memoises reads` | השם בקוד: `_HA_CACHE_TTL_SEC = 600` — `health_audit.py:1089`; הפונקציה: `_ha_cached_read` — `:1092`. **שם שגוי ושורה זזה באחת** |
| 26 | **230** | `feed=IEX-בלבד (paper-plan, **alpaca_provider:365**)` | `providers/alpaca_provider.py:215` (`get_daily_bars`) ו-`:290` (`get_latest_quote`) |

### 5.6 — תיק שמוזג או נסגר (4)

| # | תיק | הציטוט | העובדה |
|---|---|---|---|
| 27 | **65** | `MERGED **TASK-198** (30/6)` | `backlog task 198 --plain → not found`. הקובץ ב-`backlog/archive/tasks/task-198 - 20-ENTERs-in-decision_log-...md` |
| 28 | **128** | `קלט-מדדים מאומת (**מחקר 199**, צ'אט 2026-06-28)` | `backlog task 199 --plain → not found`. הקובץ בארכיון |
| 29 | **176** | `no WIN/LOSS discrimination (WITH news WR 60% vs WITHOUT 62%, EDGAR r=-0.156, **TASK-67**)` | `backlog task 67 --plain → not found`. הקובץ בארכיון |
| 30 | **239** (מוזכר ב-249) | 249: `This is the cause behind **TASK-239**, which two ceiling raises only masked` | `backlog task 239 → ✔ Done (2026-08-04)` — נסגר **יום אחרי** ש-MASTER נכתב, ו-MASTER עצמו כתב `מועמד לסגירה` |

### 5.7 — פרמיסה שהתיישנה מחוץ לכל הקטגוריות (2)

| # | תיק | מה |
|---|---|---|
| 31 | **186** | הסטטוס הוא **In Progress**, והגוף אומר `Code+tests DONE & GREEN; schedule-enable gated behind §11 supervised gates`. אבל `docs/POSTMORTEM_overnight_ARMED_2026-07-02.md` (131 שורות) מתעד ניטרול ב-2/7 אחרי 9 לילות שירה. MASTER §186 EVID מוסיף: `**מחוץ לתיק:** ... 29 קומיטים של auto-dancer יושבים ב-main המקומי ולא נדחפו מעולם`. אף אחד מהשניים אינו בגוף התיק |
| 32 | **251** | הגוף: `Not broken today. The auto_scan log of 2026-08-03 shows live_trades updated: 0 rows, 0 pending`. MASTER §251 EVID מסביר למה, וזה **לא** מה שהתיק חושב: `הסיבה אינה מזהה הגיליון אלא קריטריון הכניסה: update_live_trades כותב רק כשציון סורק מגיע ל-70, והציון הגבוה ביותר בריצה החיה של 3/8 היה 60.86`. מאומת בקוד: `ENTRY_MIN_SCORE = TRADE_ENTRY_MIN_SCORE` (`auto_scanner.py:1008`), `TRADE_ENTRY_MIN_SCORE = 70` (`config.py:106`) |

### 5.8 — הפער בין שני המקורות עצמו

MASTER נכתב ב-2026-08-03 בלילה, ו-**12 מ-65 התיקים שהוא מכסה נסגרו ב-2026-08-04**, יום אחריו: 11, 72, 75, 89, 154, 196, 227, 228, 232, 233, 239 (+166 שנסגר קודם). כלומר MASTER עצמו התיישן ב-18% תוך יממה — בדיוק כפי שהוא מזהיר בכותרת:
> `קובץ זה מתיישן מהרגע שנכתב.`

---

## אימות

```
git status --porcelain
?? docs/auto-dancer/
?? reports/

git diff --stat
(ריק)
```

לא נגעתי בקוד, לא הרצתי pytest, לא נגעתי ב-Sheets/Drive/FINVIZ, לא commit, לא push, **לא שיניתי סטטוס של אף תיק**.
הכתיבות היחידות: שני קבצי הדוח ו-`reports/INDEX.md`.
