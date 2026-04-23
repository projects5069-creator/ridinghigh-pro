# RidingHigh Pro - Open Issues Log
*Last updated: 2026-04-22 23:00 Peru*
*Single source of truth for open issues and fix history.*

---

## ✅ CLOSED — 2026-04-23

- ✅ **#29 Revert SCANNER_MIN_SCORE 60→70** — Commit `df589a6`
  - Partial revert of #28 based on E1c research (N=26)
  - Score 60-69 entries dilute expectancy by ~$40/trade
  - Issue #28 gate + RSI changes retained
- ✅ **#30 Rename SCANNER_MIN_SCORE + fix portfolio hardcoded 60** — Commit `02afdf7`
  - Renamed SCANNER_MIN_SCORE → TRADE_ENTRY_MIN_SCORE (more accurate name)
  - Legacy alias retained
  - Fixed portfolio bug: was using MIN_SCORE_DISPLAY (60) instead of trade entry threshold
  - Now portfolio and live_trades use the same threshold (70)
  - Original split plan cancelled — timeline_live already captures everything
- ✅ **#31 TASK E.3 — Block new entries after 13:00 Peru** — Commit `8a54053`
  - Added ENTRY_CUTOFF_HOUR_PERU = 13 constant
  - update_live_trades blocks new entries at/after hour 13
  - Existing Pending positions unaffected
  - Rationale: 0/11 historical wins for trades opened after 13:00
- ✅ **#33 Revert Issue #31 — remove 13:00 entry cutoff** — Commit `2ab85a2`
  - System moving to pure research mode, trading-mode cutoff removed
- ✅ **#34 Remove multi-score code + DynamicScore** — Commit `ecfc4e5`
  - Removed Score_B..I, EntryScore, DynamicScore functions (10 functions, ~270 lines)
  - Simplified live_trades to 1 trade per ticker via primary Score
  - Pages live_trades + Score Comparison flagged for removal in #35
  - Net: -424 lines across 6 files, 107/107 tests passing

---

## ✅ CLOSED — 2026-04-22 Session (Deep Audit + Research + Fixes)

- ✅ **#15 Remove DataLogger, LiveTracker, PortfolioTracker** — Commit `d685747`
- ✅ **#18 Score Comparison scale bias fix** — Commit `24de7ec`
- ✅ **#19 yfinance validation layer + retry logic** — Commit `a0d4e5b`
- ✅ **#26 Remove calc_score_v2 — duplicate Score with wrong inputs** — Commit `0a34b8e`
  - dashboard.py had a duplicate Score that read from *_calc columns (yfinance)
    instead of stored values (FINVIZ). Removed function + Score_v2 column.
- ✅ **#27 REL_VOL historical capping** — Data-only fix (no code change)
  - 30 rows in post_analysis had REL_VOL > 100 (max 26,794). Capped to 100.
  - Original values preserved in audit_flag (e.g., `CLEAN | REL_VOL_CAPPED_from_26794.01`).
- ✅ **#28 Entry logic overhaul** — Commit `cbcc954`
  - Entry gate: max(Score_B..I) -> Score only (Score_I was 0/11 wins in live)
  - SCANNER_MIN_SCORE: 70 -> 60 (86.2% TP10, 2x more candidates)
  - RSI formula: bell curve 50-70 -> extreme-only 80+ (RSI 90+ = 100% TP20)
  - Dashboard sort: EntryScore desc -> Score desc
- ✅ **Deep Data Audit completed** — Phases 1-4
  - Score formula: 110/110 rows perfect match (all 9 variants verified)
  - TP cascade logic: 0 violations
  - MaxDrop% vs D1-D5 lows: 0/124 mismatches
  - OHLC High >= Low: 0 violations across D1-D5
  - 1 D0_Drop% outlier (RDGT, correctly flagged BROKEN)
  - timeline_live: 2,351 duplicate scans (1.2%, cosmetic)
  - post_analysis backfilled: 138 rows total (was 129), all D1+TP filled
- ✅ **Comprehensive research completed** — 6-phase study
  - Best predictor: ScanChange% (r=-0.429), Score (-0.378), RunUp (-0.367)
  - Score >= 70: 96.8% TP10, 80.6% TP20, EV=$94.52/trade
  - Best exit: ATRX>2 smart hold -> EV=$109.63/trade
  - Live vs post gap: 60% of SL trades were actually winners (entry timing)
  - EntryScore inverted: high ES = 0% wins, low ES = 87.5% wins

---

## ✅ CLOSED — 2026-04-21 Session

- ✅ **#17 post_analysis 29 rows recalc** — Commit `235f4fc`
- ✅ **#23 timeline_live expanded to 25 cols** — Commit `d21911a`
- ✅ **#24 VWAP renamed to TypicalPrice** — Commit `d3b1cb6`
- ✅ **#11 VWAP column naming** — Resolved via #24

---

## ✅ CLOSED — 2026-04-19 Session

- ✅ **#2** Min Score centralized — `6bf67a5`
- ✅ **#3** REL_VOL_CAP centralized — `afde95e`
- ✅ **#4** TP15/TP20 to config — `8657cad`
- ✅ **#5** DynamicScore verified — no bug
- ✅ **#6** MxV *100 verified — no bug
- ✅ **#7** Score functions to formulas.py + config — `acbf0ad`, `0fb1484`
- ✅ **#10** REL_VOL cap — `afde95e`

---

## 🔴 HIGH PRIORITY — 23/4/2026

### TASK A: Gmail notifications infrastructure (~2 hours)
A.1. Dedicated Gmail + 2FA + App Password
A.2. GitHub Secrets: GMAIL_USER, GMAIL_APP_PASS, REPORT_TO
A.3. notifier.py module with send_email()

### TASK B: Daily Audit Workflows (~1 hour)
B.1. Morning audit: 06:00 Peru (11:00 UTC)
B.2. Evening audit: 19:00 Peru (00:00 UTC)

### TASK C: 4 Daily Email Reports (~1 hour)
C.1. 09:00 Peru — market open check
C.2. 12:00 Peru — midday scan health
C.3. 15:00 Peru — market close summary
C.4. 16:30 Peru — post_analysis status

### TASK D: Verify Issue #28 results (~30 min)
D.1. Confirm Score-only gate active (no Score_I entries)
D.2. Check new entries with Score 60-69
D.3. Report initial win rate signal

---

## 🟡 MEDIUM PRIORITY — THIS WEEK

### TASK E: Strategy improvements (research 22/4)
E.1. **Dynamic SL by ATRX** (biggest expected win)
E.2. **Dynamic TP by metric**
E.3. **Block entry after 13:00 Peru** (0/11 afternoon wins)
E.4. **Position sizing by Score tier**
E.5. **Entry timing redesign**

### TASK F: May 2026 Simplification (target: before May 1)
F.1. Remove Score_B..I from formulas + scanner
F.2. Update TIMELINE_LIVE_COLS for May schema
F.3. Remove Score Comparison page

### #8: DATA_CUTOFF_DATE hardcoded — make dynamic (15 min)
### #9: Gap removed from Score v2 — decision needed (30 min)

---

## 🟢 LOW PRIORITY — FUTURE

### TASK G: Alpaca paper trading (~3 hours)
- Prerequisite: #28 validated, win rate improved
- Target: Friday 25/4 at earliest

### TASK H: Dashboard Win Rate tooltips (~30 min)

### TASK I: Historical data cleanup
- I.1. timeline_live duplicates (2,351 rows)
- I.2. Score variants > 100 (~13K rows)
- I.3. Old rows missing audit_flag

### #12-14, #16: Archive/cleanup (15 min total)
### #20: Broken Score variants in TL (leave as-is, removed in May)
### #21: Documentation outdated

### ⏸ #1: SL definitions (DEFERRED — user rebuilds pages)

---

## 📊 STATUS (22/4/2026 23:00)

| Sheet | Rows | Notes |
|-------|------|-------|
| post_analysis | 138 | All D1+TP filled (except today) |
| timeline_live | 188,762 | 25 cols, active |
| daily_snapshots | 583 | Active |
| portfolio | 166 | All Open |
| live_trades | 34 | 22 SL, 11 TP10, 1 Pending |

**Issues closed total: 18 | Open: ~14 (4 high, 4 medium, 6 low)**
