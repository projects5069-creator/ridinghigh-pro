# RidingHigh Pro - Open Issues Log
*Last updated: 2026-04-21*
*Single source of truth for open issues and fix history.*

---

## ✅ CLOSED — 2026-04-21 Session

- ✅ **#17 post_analysis 29 rows recalc + collector computes scores** — Commit `235f4fc`
  - Recalculated 29 rows with Score_recalc_date=empty/nan using current formulas
  - Fixed: Score_B-H stored as 0 (never computed), broken values (Score_I=-1290, Score_C=3539)
  - Root cause fix: post_analysis_collector now COMPUTES Score_B-I + EntryScore via formulas.py
    instead of copying stale values from timeline_live/daily_snapshots
  - All 129 post_analysis rows now have consistent Score_recalc_date timestamps

- ✅ **#23 timeline_live expanded with 8 dynamic metric columns** — Commit `d21911a`
  - Added: Change, RSI, ATRX, Gap, TypicalPriceDist, PriceToHigh, PriceTo52WHigh, Float%
  - TIMELINE_LIVE_COLS expanded from 17 to 25 entries in sheets_manager.py
  - Migration script added 8 header columns (R-Y) to timeline_live Sheet
  - Historical rows retain 17 values (new columns empty — not backfilled)

- ✅ **#24 VWAP_price/_raw/_calc renamed to TypicalPrice/_raw/Dist_calc** — Commit `d3b1cb6`
  - Renamed across: formulas.py, auto_scanner.py, post_analysis_collector.py, dashboard.py
  - Migration script renamed column headers in daily_snapshots + post_analysis Sheets
  - Also resolves #11 (VWAP column naming confusion)

- ✅ **#11 VWAP column name is actually Typical Price** — Resolved via #24 above

---

## ✅ CLOSED — 2026-04-19 Architecture Cleanup Session

### 🔴 Critical Fixes

- ✅ **#2 Min Score threshold hardcoded (60/70/85)** — Commit `6bf67a5`
  - 9 locations in auto_scanner.py + dashboard.py replaced with config constants
  - Now reads from: `MIN_SCORE_DISPLAY`, `SCANNER_MIN_SCORE`, `CRITICAL_SCORE`
  - No behavior change

- ✅ **#4 TP15/TP20 stretch targets hardcoded** — Commit `8657cad`
  - Added `TP15_THRESHOLD_PCT=15` + `TP20_THRESHOLD_PCT=20` + FRAC variants to config.py
  - utils.calculate_ohlc_stats + dashboard._simulate_short_trades now read from config
  - Main TP10/SL7 were already centralized

- ✅ **#5 DynamicScore location unclear** — Verified, no bug
  - Confirmed: computed on-the-fly in dashboard page 8 only
  - Never saved to Sheets, so no stale ATRX risk
  - Uses current formulas.py at every page load

- ✅ **#6 MxV missing *100 multiplier** — Verified on 85K+ rows, no bug
  - formulas.calculate_mxv line 89 has `*100` included
  - All 4 sheets (timeline_live, daily_snapshots, score_tracker, post_analysis) show values in percentage range
  - Cross-check between timeline_live ↔ score_tracker: ratio median = 0.9994 (consistent)

- ✅ **#3 score_tracker_sync.py replace + #10 REL_VOL cap** — Commit `afde95e`
  - File score_tracker_sync.py does not exist (stale reference in code_auditor.py — removed)
  - Active function is `sync_score_tracker` in auto_scanner.py (works correctly)
  - REL_VOL_CAP centralized to config.py (was hardcoded in formulas.py)
  - 2 duplicate `if rel_vol > 100` blocks removed from auto_scanner.py
  - formulas.calculate_rel_vol already caps via config.REL_VOL_CAP

### 🟠 Architecture Refactoring

- ✅ **#7.1 9 score functions + entry score migrated to formulas.py** — Commit `acbf0ad`
  - calculate_score, calculate_score_b..i, calculate_entry_score
  - ~300 lines moved from auto_scanner.py → formulas.py
  - Verified via baseline JSON: 3 inputs × 9 variants + 3 entry_scores IDENTICAL output

- ✅ **#7.2 calculate_score reads weights from config** — Commit `0fb1484`
  - SCORE_WEIGHTS_V2 + SCORE_CAPS_V2 + SCORE_RSI_PARAMS now source of truth
  - Verified: changing weight in config propagates to score (smoke test)
  - 8 score variants (B-I) intentionally left with hardcoded weights — they are research experiments

---

## ✅ CLOSED — 2026-04-17 (Previous Session)

- ✅ ATRX formula mismatch dashboard vs auto_scanner — `4b11686`
- ✅ Float% was measuring Turnover not Float — `4b11686`
- ✅ Score v1 still in dashboard — `4b11686`
- ✅ REL_VOL no cap in dashboard (26K+ outliers) — `4b11686`
- ✅ calculate_mxv duplicate in 3 places → centralized — `55adc6e`
- ✅ 14 duplicate utility functions → utils.py — `55adc6e`
- ✅ Hardcoded values scattered → config.py v2.0 — `55adc6e`

---

## 🔴 STILL OPEN

### 🟠 High Priority

#### #15: DataLogger vs LiveTracker consistency
- **Description:** Inconsistency between DataLogger and LiveTracker components — different data showing on different pages
- **Status:** Not yet investigated
- **Impact:** Different numbers for the same metric across pages
- **Effort:** 1-2 hours investigation + fix

### 🟡 Medium Priority

#### #8: Hardcoded cutoff date 2026-04-10 in page 7
- **Location:** dashboard.py (Portfolio Score Tracker)
- **Value:** `DATA_CUTOFF_DATE = "2026-04-10"` in config.py
- **Impact:** From May 1st, page will show partial/wrong data
- **Effort:** 15 min — make dynamic (e.g., "last 60 days")

#### #9: Gap removed from Score v2 despite r=-0.256 correlation
- **Removed:** 2026-04-11 commit f3d96ca, without documented reason
- **Impact:** Score weaker than possible — strong signal lost
- **Decision needed:** Add Gap back to Score as v3?
- **Effort:** 30 min implementation + backtest


#### #18: Section 5 page 9 biased
- **Description:** Score tends to high values, "wins" without normalization
- **Effort:** 25 min investigation + fix

#### #19: yfinance data reliability
- **Current:** 3 BROKEN rows, 21 NO_DATA in post_analysis
- **Alternatives:** Polygon.io ($29/mo), FMP ($14/mo)
- **Decision needed:** switch providers?

### 🟢 Low Priority

#### #12: backfill_weeks13_14.py — one-time script still in project
- **Action:** Move to archive folder
- **Effort:** 2 min

#### #13: 4 old scripts to archive
- fix_atrx.py, recalculate_scores_v2.py, quick_audit.py, backfill_raw_fields_v1.py
- **Effort:** 5 min

#### #14: VWAP inline redundancy
- **Duplicate computation — formulas.py + inline**
- **Effort:** 10 min cleanup

#### #16: Score_v2 duplicate in page 8
- **After recalc, Score and Score_v2 are identical**
- **Effort:** 10 min cleanup

#### #20: ~13K broken Score variants in timeline_live
- **Only affects Score_B, Score_I, Score_C variants (informational)**
- **Impact:** NONE on trading. Main `Score` column clean.
- **Decision:** Leave as-is

#### #21: Documentation outdated
- PROJECT_DOCUMENTATION.md marked OUTDATED
- CONVERSATION_SUMMARY.md marked OUTDATED
- PROJECT_KB.md still mentions Score v1 in places

#### #22: 12 backup *_BEFORE_*.py files in project root (historical)
- **May have been resolved 2026-04-19 — verify clean**

### ⏸️ DEFERRED

#### #1: 3 different SL definitions across dashboard pages
- **Portfolio Tracker:** SL=7% within 5 days
- **Live Trades:** SL=7% intraday (but display text says 10%)
- **Score Comparison:** SL=7% D1 only (SL7_Hit_D1)
- **Status:** DEFERRED — user will rebuild pages from scratch
- **Actual finding from 2026-04-19:** All pages use 7% from config. Difference is in TIME WINDOW, not in value.
  Text "SL 10%" in live_trades_page caption (dashboard.py line 3002) is incorrect display text.

---

## 📊 Stats

- **Total issues tracked:** 24
- **Closed:** 12 (50%) — 4 new in 2026-04-21 (#11, #17, #23, #24) + 8 previously
- **Open critical:** 0 🎉
- **Open high:** 1 (#15)
- **Open medium:** 4 (#8, #9, #18, #19)
- **Open low:** 6 (#12, #13, #14, #16, #20, #21, #22)
- **Deferred:** 1 (#1)

---

## Legend
- 🔴 Critical — affects data accuracy or trading decisions
- 🟠 Important — system works but suboptimal
- 🟡 Medium — nice to fix
- 🟢 Low — cosmetic/documentation
- ⏸️ Deferred — intentionally postponed
