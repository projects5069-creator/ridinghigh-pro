# RidingHigh Pro - Open Issues Log
*Last updated: 2026-04-25*

---

## ✅ CLOSED (2026-04-25) - Session "Cleanup + PROJECT_STATE"

### #14: Cleanup backup files
- 38 `*_BEFORE_*.py` files moved to `גיבוי זמני/2026-04-25/`
- `.gitignore` updated with patterns: `*_BEFORE_*`, `*.BEFORE_*`, `גיבוי זמני/`
- **Status:** Closed
- Commit: 2ba5ce7

### #16: PROJECT_STATE.md auto-update system
- Created `generate_project_state.py` (live snapshot generator)
- Reads: git log, GitHub Actions API, Google Sheets stats, OPEN_ISSUES.md
- Auto-runs after every commit via `.git/hooks/post-commit`
- v2 includes smart month selection (prefers current Peru month with data)
- **Status:** Closed
- Commits: dbc5424 (initial), 2ba5ce7 (v2 + cleanup)

---

## ✅ CLOSED (2026-04-24) - Session "Schema Migration + OAuth"

### #41: Schema migration timeline_live → 28 cols
- 218,522 rows migrated successfully
- daily_summary restored to 13 days, 890 rows
- **Status:** Closed
- Commits: 4c91c4a, 5517989

### #42: ScanTime sort bug
- HH:MM strings sorted lexicographically incorrectly
- Fixed: zfill HH:MM in dashboard cached loaders
- **Status:** Closed
- Commit: ff7b0a9

### #43: Drive folder migration ⚠️ ABANDONED
- Investigation showed quota is on the creator account, not folder
- **Status:** Abandoned (not a fix path)
- See #44 for actual solution

### #44: OAuth-based sheet creation (quota fix)
- Service account: continues all reads/writes
- User OAuth (projects5069@gmail.com): used only for new sheet creation
- GitHub Secret `GOOGLE_OAUTH_TOKEN_JSON` configured
- ticker_follow_up sheet created: 1mlYjdKCfKew1gRt7h7DiMwSGGJP_hRFHI2yAg04gl0k
- **Status:** Closed
- Commits: bf4f6fc, 55ac6a4

---

## ✅ CLOSED (2026-04-17) - Session "Critical Fixes"

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

### Auto-closed during cleanup (2026-04-25)

- ✅ **#3: ~13K broken Score VARIANTS in timeline_live**
  - Decision: leave as-is, variants are informational only
  - Use only 'Score' column for analysis

- ✅ **#4: live_trades with broken Score_D**
  - Verified: live_trades has 14 rows, Score 70-100 CLEAN, no Score_D column
  - Was confusion with timeline_live variants

- ✅ **#10: Hardcoded cutoff 2026-04-10 in page 7**
  - Verified 2026-04-25: no occurrence in dashboard.py
  - Likely removed in a previous edit

- ✅ **#11: VWAP misnamed (Typical Price)**
  - formulas.py:145-147 documents this explicitly with NOTE
  - Decision: keep name for backward compat, doc is sufficient

---

## 🔴 STILL OPEN - Critical

### #1: 3 different SL definitions across dashboard pages
- Portfolio Tracker (page 3): uses `SL_THRESHOLD_FRAC` (7%), within 5 days
- Live Trades (page 4): SL=10% hardcoded, within 5 days
- Score Comparison (page 9): SL=7%, ONLY D1 (SL7_Hit_D1)
- **Verified 2026-04-25:** only one usage of SL_THRESHOLD_FRAC in dashboard (line 2824)
- **Impact:** Win rate inconsistency across pages
- **Effort:** 45 min (strategic decision + implementation)

### #2: Min Score threshold inconsistent across pages
- `MIN_SCORE_DISPLAY` exists in config but not enforced everywhere
- Hardcoded `>= 60` in lines: 1203, 1480, 3198, 3243, 3347, 3396
- Hardcoded `>= 70` in lines: 3411, 3545
- **Impact:** Inconsistent filtering across dashboard pages
- **Effort:** 15 min (replace hardcoded with MIN_SCORE_DISPLAY)

### #5: DynamicScore - unclear if saved anywhere
- Calculated on-the-fly in dashboard page 8 only
- Not saved to any sheet
- **Impact:** Can't backtest historically
- **Effort:** 15 min (investigation + decision)

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
- 3 BROKEN rows, 21 NO_DATA in post_analysis
- Pre-split prices, partial intraday issues
- **Alternatives:** Polygon.io ($29/mo), FMP ($14/mo)
- **Decision needed:** switch providers?

---

## 🟡 STILL OPEN - Medium

### #12: Score_v2 duplicate in page 8
- After recalc, Score and Score_v2 are identical
- **Effort:** 10 min cleanup

---

## 🟢 STILL OPEN - Low

### #13: Update documentation
- PROJECT_DOCUMENTATION.md marked OUTDATED - needs rewrite
- CONVERSATION_SUMMARY.md marked OUTDATED
- README.md last touched in v1 era

### #15: config.py v1 legacy weights
- Kept for reference - eventually can remove

### #17: DropsLab schema migration pending
- Same migration as #41 needs to apply to DropsLab
- Currently on old schema

---

## 📊 Observed Stats (2026-04-17)

### Live Trades Performance (14 trades total)
- TP10 Wins: 2 (14.3%)
- SL Hits: 12 (85.7%)
- Open: 0
- **Note:** Small sample. Real confirmation requires more trades + post_analysis 124-row data (r=-0.336).

### Post Analysis Correlations (Apr 2026, 124 rows)
- Score ↔ MaxDrop: r = -0.336 (strong)
- ScanChange ↔ MaxDrop: r = -0.348
- MxV ↔ MaxDrop: r = +0.053 (noise, despite 25% weight)

---

## 📅 Daily Maintenance

### Daily Audit (when email setup complete)
- 06:00 Peru: daily_audit.py pre-market check
- 19:00 Peru: daily_audit.py post-market check (after post_analysis)

---

## 🎯 Next Session Checklist (open Mon 2026-04-27)

- [ ] Dashboard: Daily Summary 2026-04-27, Score 0-100, last scan HH:MM
- [ ] ticker_follow_up: new rows with FollowDay=1 (~119 tickers from 23/4 + 24/4)
- [ ] GitHub Actions: auto_scan.yml runs every minute, no OAuth errors

---

## Legend
- 🔴 Critical - affects data accuracy or trading decisions
- 🟠 Important - system works but suboptimal
- 🟡 Medium - nice to fix
- 🟢 Low - cosmetic/documentation
