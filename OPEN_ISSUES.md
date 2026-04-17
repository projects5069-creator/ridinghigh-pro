# RidingHigh Pro - Open Issues Log
*Last updated: 2026-04-17*

## ✅ CLOSED (2026-04-17) - תוקנו היום

### 🔴 Critical Fixes
- ✅ **ATRX formula mismatch** - dashboard had (atr/price)*100, auto_scanner had (high-low)/atr
  - Fixed in: formulas.py calculate_atrx() - now used everywhere
  - Commit: 4b11686
  
- ✅ **Float% measured Turnover, not Float** - dashboard used volume/shares instead of float_shares/shares
  - Fixed in: formulas.py calculate_float_pct() + added floatShares lookup
  - Commit: 4b11686

- ✅ **Score v1 still in dashboard** - local runs used old scoring
  - Fixed: dashboard imports calculate_score from auto_scanner (v2)
  - Commit: 4b11686

- ✅ **REL_VOL no cap in dashboard** - could reach 26,000+ from yfinance outliers
  - Fixed in: formulas.py calculate_rel_vol() with cap=100
  - Commit: 4b11686

### 🟠 Code Quality
- ✅ **calculate_mxv duplicate** - was in 3 places, now centralized
- ✅ **14 duplicate functions removed** - parse_market_cap, parse_volume, 
  is_trading_day, is_day_complete, get_trading_days_after, calculate_stats
  - Fixed: moved to utils.py
  - Commit: 55adc6e

- ✅ **Hardcoded values scattered** - moved to config.py v2.0
  - POSITION_SIZE_USD, TP/SL thresholds, SCORE_WEIGHTS_V2
  - Commit: 55adc6e

---

## 🔴 STILL OPEN - Critical

### #1: 3 different SL definitions across dashboard pages
- Portfolio Tracker (page 3): SL=7%, within 5 days
- Live Trades (page 4): SL=10%, within 5 days
- Score Comparison (page 9): SL=7%, ONLY D1 (SL7_Hit_D1)
- **Impact:** Win rate inconsistency across pages
- **Effort:** 45 min (strategic decision + implementation)

### #2: Min Score threshold different across pages
- Page 3: >=60 | Page 4: >=70 | Page 9: >=60
- **Impact:** Inconsistent filtering
- **Effort:** 15 min

### #3: ~13K broken Score VARIANTS in timeline_live (NOT critical)
- Investigated 2026-04-17: Score (main) is CLEAN (0 broken rows out of 125K)
- Only Score_B (7002), Score_I (4475), Score_C (1563) are broken
- Variants are INFORMATIONAL only - not used for trading decisions
- All from before today's formulas.py fixes
- **Impact:** NONE on trading. Ignore variants in analysis.
- **Decision:** Leave as-is. Use only 'Score' column for analysis.

### ~~#4: live_trades with broken Score_D~~ - CLOSED 2026-04-17
- Investigated: live_trades has only 14 rows
- Score column is CLEAN (70-100)
- No Score_D column exists at all
- Was confusion - Score_D=19,000 was in timeline_live variants (not trades)
- **Status:** Nothing to fix

### #5: DynamicScore - unclear if saved anywhere
- Calculated on-the-fly in dashboard page 8
- If saved somewhere with old ATRX - needs recalc
- **Effort:** 15 min (investigation)

---

## 🟠 STILL OPEN - Important

### #6: Gap removed from Score v2 despite r=-0.256 (strong correlation)
- Removed 11/4 (commit f3d96ca) without documented reason
- **Impact:** Score weaker than possible
- **Decision needed:** Add back to Score v3?

### #7: 124 rows in post_analysis - run again with new formulas?
- After formulas.py fixes, some calculated values may differ
- **Effort:** 20 min recalc

### #8: Section 5 on page 9 is biased
- Score tends to high values, "wins" without normalization
- **Effort:** 25 min

### #9: yfinance data reliability
- 3 BROKEN rows, 21 NO_DATA
- **Alternatives:** Polygon.io (\$29/mo), FMP (\$14/mo)
- **Decision needed:** switch providers?

---

## 🟡 STILL OPEN - Medium

### #10: Hardcoded cutoff 2026-04-10 in page 7
- dashboard.py:2854
- **Effort:** 10 min (move to config.py)

### #11: VWAP is actually Typical Price (H+L+C)/3
- Misleading name, not real volume-weighted VWAP
- **Effort:** 15 min rename

### #12: Score_v2 duplicate in page 8
- After recalc, Score and Score_v2 are identical
- **Effort:** 10 min cleanup

---

## 🟢 STILL OPEN - Low

### #13: Update documentation
- PROJECT_DOCUMENTATION.md marked OUTDATED - needs rewrite
- CONVERSATION_SUMMARY.md marked OUTDATED

### #14: Cleanup backup files  
- 12 *_BEFORE_*.py files in project dir
- Should move to גיבוי זמני/

### #15: config.py v1 legacy weights
- Kept for reference - eventually can remove

---


## 📊 Observed Stats (2026-04-17)

### Live Trades Performance (14 trades total)
- TP10 Wins: 2 (14.3%)
- SL Hits: 12 (85.7%)
- Open: 0
- **Note:** Small sample. This is simulated data. Real confirmation
  of system requires more trades + post_analysis 124-row data (r=-0.336).

## 📅 Daily Maintenance

### Daily Audit (when email setup complete)
- 06:00 Peru: daily_audit.py pre-market check
- 19:00 Peru: daily_audit.py post-market check (after post_analysis)

---

## Legend
- 🔴 Critical - affects data accuracy or trading decisions
- 🟠 Important - system works but suboptimal
- 🟡 Medium - nice to fix
- 🟢 Low - cosmetic/documentation
