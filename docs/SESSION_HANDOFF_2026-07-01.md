# SESSION HANDOFF — 2026-07-01 (Wed)

*מצביע על מקורות חיים (PK v-live, Backlog). קרא את ה-PK החי לפני פעולה.*

## נדחף ל-main היום (6 commits, ahead 0, HEAD=ad95806)
| commit | מה |
|---|---|
| 5f0b288 | **TASK-176** — news_detective כובה מהנתיב-הדקתי (`NEWS_DETECTIVE_ENABLED=False`); מסיר ~46/91 מ-429 |
| 48580ca | **measure_429** — `scripts/measure_429_by_workflow_v1.py` (429/run/workflow/day; count_429 עמיד ל-3 מלכודות-לוג) |
| dd46470 | **TASK-217 Task1** — entry-write של paper_portfolio ל-by-name (`build_portfolio_row`) |
| 7c6f079 | **TASK-217 Task2** — repair helpers טהורים (`remap_row`+`mark_manual_cleanup`) |
| 0c441b7 | **TASK-217 Task3** — **migration חי של 2026-07 בוצע+אומת** (header canonical, 8 שורות→MANUAL_CLEANUP) |
| ad95806 | **TASK-217 Task4 (partial)** — header-guard functions (pure, 5/5); חיווט נדחה |
+ מוקדם היום: **_AM** (SA ייעודי ל-agent_minute, `GOOGLE_CREDENTIALS_JSON_AM`) + diagnostic (הוסר). PK v3.90→**v3.98**.

## 🎯 השרשור המרכזי שנסגר היום (מאומת חי — נתון+קוד)
- **חקירת "P&L% ריק"** → 7 השערות (2 הופרכו ביושר בראיה) → **שורש:** `paper_portfolio` 2026-07 tab נוצר עם **header ישן 23-col** (בלי TPPrice/SLPrice); ה-entry-append הפוזיציוני הזיז ערכים **+2** מ-CurrentPrice → Status נחת ב-ExitDate, נקרא ריק → **8 שורות מיותמות-מ-monitor_all**. הקוד עצמו תקין; 2026-05/06 תקינים. **תוקן end-to-end + verify PASS** (25 cols, 0 phantom, 8 MANUAL_CLEANUP).
- **429 root-cause** (מאומת רב-יומי, `measure_429`): agent_minute הוא המקור היחיד (mean 53/run); auto_scan(_AS) + health_audit(_HA) = **0×429**. פיצול: news_detective(46)+sentinel(45). 176 הסיר את חצי-news.

## 🔴 מעקב מחר בבוקר (08:30 פרו)
- **ריצת agent_minute ראשונה עם 176-חי:** האם 429 ירד ~91→~45? (`measure_429` על היום).
- **כניסות חדשות ל-2026-07:** עכשיו header קנוני + Task1 by-name → אמורות **להיישר נכון** (לא עוד +2). לוודא.

## פתוחים + דדליינים (מספרים מול הרשימה החיה — OPEN=45)
- **TASK-213** [HIGH, **דדליין 2026-07-06**] — מדידת ירידת-429 רב-יומית (הכלי `measure_429` מוכן; baseline 1/7 נתפס).
- **TASK-217** — הליבה (misalign) **פתורה+נדחפה**; **נשאר חיווט-guard** = TASK-219.
- **TASK-218** — sentinel worksheet-handle cache (45/91 הנותרים).
- **TASK-219** — חיווט header-guard ל-provisioning: **החלטה raise-vs-warn + audit 16 טאבים ×3 חודשים** לפני raise (לא לעצור רוטציית 1/8).
- **TASK-176** — AC#1 מסופק (לא-per-minute, נדחף); AC#2 (מדידת חיסכון) = אחרי ריצות מחר.

## דגלים שנמצאו היום (candidate-TASKs — לתריאז'):
- **ScanTime padding drift** ב-timeline_live ('08:45' מול '9:59' — שובר סדר-כרונולוגי; ממוסך ע"י workarounds).
- **2 eod_borrow tests שבורים** (`test_orchestrator_eod_borrow_wiring_v1`) — pre-existing, לא-217.
- **price-source divergence:** entry=FINVIZ (timeline) מול CurrentPrice=Alpaca (monitor) → הטיית-P&L למיקרו-קאפ.

## מצב-מערכת (קרא PK החי v3.98 לאישור)
- EXPLICIT_GATE_MODE=active (MxV≤−100), SENTINEL=shadow, DRY_RUN=True, ENTRY_GATE_MINIMAL=True, SCORE_WRITE_FROZEN=True.
- 3 SAs: מסחרי + _HA + _AS (נקיים). **_AM (agent_minute)** — secret קיים; agent_minute עדיין 429 (sentinel/news; 176 מסיר news).
- paper_portfolio: 2026-07 **מיושר** (backup: research/…231931.json). 8 שורות = MANUAL_CLEANUP.
