# Master Task List - RidingHigh Pro
**Source session:** 2026-05-25 layers paradigm shift
**Created:** 2026-05-26
**Status:** Active roadmap - ~3 months
**Total:** 15 stages, ~65 tasks, **17 completed (26%)**

> **Filter numbering:** Filters in decision_logic.py use sequential numbering with letter
> suffixes for inserts (e.g., Filter 4b for L6). Preserves historical ROCKET_GUARD (11).

---

## Stage 0 - Quick Wins ✅ COMPLETE

- [x] **0.1** AGENT_RUNUP_MIN = 0 - הושלם
- [x] **0.2** שיתוף DropsLab עם service account - הושלם
- [x] **0.3** SESSION_HANDOFF נשמר ב-docs/ - הושלם
- [x] **0.4** בדיקת DropsLab - root cause: drops_collect timeout (organic growth) - הושלם 26/5

---

## Stage 1 - L6 Active ✅ COMPLETE
**Sub-\$3 ban | commits: e4687e0 (code) + 1adf3b8 (PK)**

- [x] **1.1** AGENT_MIN_SCANPRICE_USD = 3.0
- [x] **1.2** Filter 4b PRICE_TOO_LOW
- [x] **1.3** 5 tests, all pass
- [x] **1.4** verification - tests, syntax, diff
- [x] **1.5** commit + push
- [x] **1.6** monitor production — הושלם 26/5. 67 runs, 902 decisions, L6 fired on AEMD @$2.58. 0 ENTERs (calm market).

---

## Stage 2 - Toxic Tickers Blacklist ✅ COMPLETE
**AEHL + TDIC = chronic droppers (DropsLab cross-reference)**

- [x] **2.1** CHRONIC_DROPPER_BLACKLIST = ["AEHL","TDIC"] ל-config.py
- [x] **2.2** Filter 4c BLACKLISTED_TICKER (after Filter 4b)
- [x] **2.3** tests + commit
- [x] **2.4** תיעוד + PK update v2.38

---

## Stage 3 - Full Metrics Logging
**SKIPs לא נכתבים ל-decision_log (Route B b1a4e4f) - צריך טבלה חדשה**

- [ ] **3.1** scanner_metrics_log כטבלה חדשה, batch write יומי
- [ ] **3.2** sheet חדש (18 עמודות) ב-prepare_next_month.py
- [ ] **3.3** scanner_metrics_logger.py - מודול חדש
- [ ] **3.4** אינטגרציה ב-auto_scanner.run_eod()
- [ ] **3.5** tests + verification

**18 עמודות:** date, ticker, scan_time, Score, MxV, RunUp, ATRX, RSI, TypicalPriceDist, ScanChange, REL_VOL, ScanPrice, Volume, MarketCap, Float, Price_vs_SMA20, DaysSinceIPO, Sector

---

## Stage 4 - Watch Threshold 15%

- [ ] **4.1** בדיקה: איפה 25% threshold היום
- [ ] **4.2** WATCH_THRESHOLD_PCT = 15 (מעקב בלבד)
- [ ] **4.3** TRADE_THRESHOLD_PCT = 25 נשאר
- [ ] **4.4** scanner_metrics_log יקבל 15-25%

---

## Stage 5 - score_analytics Workflow

- [ ] **5.1** agent_score_analytics.yml ב-.github/workflows/
- [ ] **5.2** cron 21:30 UTC (16:30 Peru) Mon-Fri - daily
- [ ] **5.3** Saturday 23:00 UTC (18:00 Peru) - weekly
- [ ] **5.4** verification

---

## Stage 6 - Minute Tracker
**מחליף score_tracker | בסיס ל-Entry Timing Score**

- [ ] **6.1** דיזיין: 25 שדות
- [ ] **6.2** minute_tracker sheet
- [ ] **6.3** minute_tracker.py
- [ ] **6.4** running stats: high_since_watch, low, drop_from_high
- [ ] **6.5** migration

---

## Stage 7 - L3 Active ✅ / L4 + L5 NEXT
**אחרי 30 ימי נתונים מ-L6**

- [ ] **7.1** re-validate plateau backtest
- [ ] **7.2** L4: Filter 9 REENTRY_LIMIT verify
- [ ] **7.3** L5: Time<13:00 new filter
- [x] **7.4** L3: Toxic Profile (RSI>88 AND Price/SMA20>250%) — Filter 4d, commit 14452a2 (26/5)
- [ ] **7.5** monitor 2 שבועות

---

## Stage 8 - Position Sizing דינמי

- [ ] **8.1** דיזיין: גודל לפי layers passed
- [ ] **8.2** All 6 layers -> \$1,500
- [ ] **8.3** 5 layers -> \$1,000 default
- [ ] **8.4** 4 layers -> \$500
- [ ] **8.5** tests + walk-forward

---

## Stage 9 - Time-based Exits

- [ ] **9.1** 2h breakeven check
- [ ] **9.2** Trail stop after -5%
- [ ] **9.3** tests + monitor 2 שבועות

---

## Stage 10 - Anti-Squeeze Filter

- [ ] **10.1** agent/enrichment/yfinance_metrics.py
- [ ] **10.2** get_short_interest, days_to_cover, insider_activity
- [ ] **10.3** cache 24h
- [ ] **10.4** אינטגרציה ב-scanner
- [ ] **10.5** Filter ANTI_SQUEEZE
- [ ] **10.6** backtest

---

## Stage 11 - SEC EDGAR Enhancement

- [ ] **11.1** הרחבת news_detective_v1.py
- [ ] **11.2** s3_filings_last_90d
- [ ] **11.3** form_4_insider_sells_30d
- [ ] **11.4** 8k_halts_history
- [ ] **11.5** reverse_merger_flag

---

## Stage 12 - Sector Heat Module

- [ ] **12.1** agent/market_context/sector_heat.py
- [ ] **12.2** סקר FINVIZ sector pumps
- [ ] **12.3** sector_heat_score
- [ ] **12.4** Filter SECTOR_TOO_HOT

---

## Stage 13 - DropsLab Bridge

- [ ] **13.1** תיקון DropsLab (חוזר ל-0.4)
- [ ] **13.2** דיזיין bridge
- [ ] **13.3** dropslab_bridge.py
- [ ] **13.4** dropslab_daily sheet
- [ ] **13.5** auto-update blacklist
- [ ] **13.6** drops_collect optimization (skip processed rows / --date flag) — root cause of May 19 timeout. Quick fix applied 26/5 (timeout 10->20)

---

## Stage 14 - Entry Timing Score

- [ ] **14.1** דיזיין
- [ ] **14.2** drop_from_high
- [ ] **14.3** volume_decay
- [ ] **14.4** MACD bearish crossover
- [ ] **14.5** תיעוד ב-minute_tracker
- [ ] **14.6** backtest

---

## Stage 15 - Infrastructure & Quality

- [ ] **15.1** MFE/MAE עם yfinance intraday (2h)
- [ ] **15.2** A/B testing framework
- [ ] **15.3** dashboard.py refactor (5,193 שורות)
- [ ] **15.4** PK update - Score weights actual vs documented

---

## Tech Debt (זוהה בסשן L6)

- [x] **TD.1** test_decision_has_41_fields -> 43 — commit fd450c9 + 14452a2 (26/5)
- [x] **TD.2** price_vs_sma20 added to FIELD_MAPPING (41->42). reentries_used_today stays internal. commit 5b20cbf (26/5)
- [ ] **TD.3** ניקוי ~95 .bak files
- [ ] **TD.4** ניקוי 22 research/ dirs
- [ ] **TD.5** TASK-41 filter order distribution
- [ ] **TD.6** WHIPSAW + NO_TOUCH investigation
- [ ] **TD.7** re-run win-rate analysis end-May (n>91)
- [ ] **TD.8** health_audit market calendar awareness (false positive 26/5)

---

## Strategic Questions (לא משימה - דיון)

- [ ] **STRAT.1** 🔴 Real WR 49.4% - מה זה אומר?
- [ ] **STRAT.2** 🔴 Phase 2 gate (WR>=60%) - איך לסגור פער?

---

## סדר עדיפויות

### שבועיים ראשונים
Stage 0.4 -> Stage 2 -> Stage 5

### חודש שני
Stage 3 -> Stage 4 -> Stage 6 -> המתנה 30 ימים

### חודש שלישי
Stage 7 -> Stage 8 -> Stage 9

### חודש רביעי+
Stage 10 -> 11 -> 12 -> 13 -> 14 -> 15

---

## הצעד הבא הקונקרטי

**26/5 08:30 Peru:** ניטור L6 (Stage 1.6)
**אחרי ניטור:** Stage 0.4 + Stage 2

---

*Last updated: 2026-05-26*
*Reference: docs/SESSION_HANDOFF_2026-05-25_layers_paradigm.md*
*L6 commit: e4687e0 | PK update: 1adf3b8*
