# SESSION HANDOFF — Layers Paradigm Shift
**Date:** 2026-05-25 (Memorial Day session, ~10 hours, 14 research folders)
**Next session goal:** Stage 0.4 + Stage 2 (DropsLab fix + Toxic Blacklist)
**Status:** Stage 1 (L6) deployed. Awaiting market open 26/5 for monitoring.

---

## TL;DR — מה קרה בסשן

המערכת לא נכשלת בבחירה — היא נכשלת בביצוע. ה-Score לא חוזה רווח (r=0.020) אבל **חייב להישאר** כי הוא חוסם 84% מההחלטות (volume control, לא predictor).

**הגילוי הגדול:** הציון בנוי הפוך. Toxic tickers מקבלים Score=92.44, Winners מקבלים Score=82.01. **ככל שהציון גבוה יותר — המניה מסוכנת יותר.**

**הפתרון:** 6 שכבות פילטר בינאריות שמחליפות paradigm של ציון 0-100. שלב 1 (L6) נפרס.

---

## מצב המערכת אחרי הסשן

### שינויים שנכנסו לפרודקשן
1. **AGENT_RUNUP_MIN: 30 -> 0** (לפני הסשן) - capture wider universe
2. **L6 PRICE_TOO_LOW filter** - commit e4687e0 (25/5)
3. **PK v2.36** - commit 1adf3b8 (25/5) - documents L6 + audit findings + changelog cleanup

### גישות חיצוניות
- **DropsLab** משותף עם service account. cross-reference הסתיים.

---

## 6 השכבות הסופיות

| # | שכבה | תנאי | סטטוס |
|---|------|------|-------|
| L1 | TypicalPriceDist | >= -5 | לא מיושם |
| L2 | REL_VOL | >= 5 | לא נכלל (0pp impact) |
| L3 | Toxic Profile | RSI <= 88 AND Price/SMA20 < 250 | לא מיושם |
| L4 | Concurrent | 1 entry/ticker/day | קיים כ-Filter 9 REENTRY_LIMIT |
| L5 | Time Cutoff | hour < 13:00 Peru | לא מיושם |
| **L6** | **ScanPrice** | **>= \$3** | **✅ פרודקשן 25/5** |

### תוצאות backtest סופי (L3+L6)
- n=13 (מ-77 baseline)
- PnL: +85.26% (מ--188.78% baseline)
- WR: 80% [CI 49-94%]
- Mean/trade: +6.56%
- Survives 3pp slippage
- **+274pp שיפור**

---

## Toxic Profile DNA

| מדד | Toxic | Winner | Z-score |
|-----|------:|-------:|--------:|
| MxV | -887.89 | -2507.91 | 0.83 |
| Score | 92.44 | 82.01 | 0.79 |
| RSI | 92.61 | 83.62 | 0.74 |
| Price/SMA20 | 305% | 194% | 0.72 |
| ScanPrice | \$3.61 | \$7.26 | 0.61 |

5 toxic tickers: PIII, QUCY, AEHL, STFS, TDIC (חשבון כל הפסדים DRY_RUN)

---

## DropsLab Cross-Reference

- DropsLab עצרה ב-Apr 17 (סיבה לא ידועה - דורש חקירה ב-Stage 0.4)
- 10/19 traded tickers שלנו = 53% גם ב-DropsLab
- **AEHL ו-TDIC = chronic droppers** (3x drops כל אחד באפריל)
- PIII, QUCY, STFS לא ב-DropsLab

---

## הסשן הבא - תכנית

### בוקר 26/5 (08:30 Peru) - L6 Monitoring
1. בדיקת GitHub Actions logs של agent_minute לחיפוש [SKIP] ... PRICE_TOO_LOW
2. ספירה - כמה PRICE_TOO_LOW skips בשעה הראשונה?
3. דיווח בצ'אט

### אחרי ניטור (45-60 דק') - Stage 0.4 + Stage 2
1. בדיקת DropsLab - למה עצרה Apr 17?
2. אם תקין: Toxic Blacklist (AEHL + TDIC) כ-Filter 4c
3. עדכון PK ל-v2.37

---

## False Positive Note (26/5)

ה-health audit של 26/5 01:51 הוציא CRITICAL על "timeline_live stale 4 days".
זה false positive: שישי 22/5 + סופ"ש + Memorial Day = שוק סגור 4 ימים.
Task עתידי: שלב market calendar awareness ב-health_audit.py.

---

## מספרים לזכור

- Baseline (enriched): n=77, PnL=-188.78%, WR=43.3%
- L3+L6 winner: n=13, PnL=+85.26%, WR=80%
- Mean per trade: +6.56% (vs -2.45% baseline)
- Real WR overall: 49.4% (Phase 2 blocker)
- Score filter blocks 84% (volume control)
- Hour 14+ WR: 30.8%
- AEHL median Score: 92.44 (DANGER ZONE)

---

*Generated: 2026-05-26*
*L6 commit: e4687e0 | PK update: 1adf3b8*
