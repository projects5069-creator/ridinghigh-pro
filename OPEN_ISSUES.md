# RidingHigh Pro - Open Issues Log
*Last updated: 2026-04-29 19:55 Peru*

---

## ✅ CLOSED (2026-04-29) - Session "Quick Wins + Health Audit Fixes"

### ✅ #N4: Health Audit workflow missing pandas + yfinance
- **Root cause:** `.github/workflows/health_audit.yml` installed only `gspread google-auth pytz`,
  causing checks 17 + 18 to crash with `ModuleNotFoundError: No module named 'pandas'`.
  After fixing pandas, exposed missing yfinance (FundamentalsProvider always uses yfinance).
- **Fix:** Switched to `pip install -r requirements.txt` (single source of truth).
  Other 5 workflows still on manual install — tracked as new Task #N7 (LT).
- **Verification:** Health Audit Run #17 — 0 CRITICAL (was 2), Status Success.
- **Status:** Closed
- **Commits:** 4959ecc (initial pandas/alpaca-py), ecbaf2c (final requirements.txt)

### ✅ #19: post_analysis_collector selection logic — documented
- **Decision:** Verified working as designed. Collector selects peak Score row per
  (ticker, scan_date) — see `day.loc[day["Score"].idxmax()]`.
- **Documentation:** PROJECT_KB.md §8 + §9 issue #16.
- **Status:** Closed
- **Commits:** f68b5b3 (PROJECT_KB doc), c47e874 (OPEN_ISSUES closure)

### ✅ #N5: PROJECT_STATE "YAAS" bug — last_date showing ticker instead of date
- **Root cause:** `generate_project_state.py` used `values[-1][0][:10]` — assumed col 0
  is always Date AND last row is latest date. Both wrong for post_analysis (col 0=Ticker,
  sorted alphabetically → "YAAS"), portfolio (col 0=PositionKey → "SBLX_2026-"),
  portfolio_live (col 0=Ticker → "AKAN").
- **Fix:** New `_last_date(headers, values)` helper finds date column dynamically by
  header name (Date / ScanDate / scan_date), returns max() of valid YYYY-MM-DD values.
- **Side effect:** Exposed real D2 issue — post_analysis missing 2026-04-28 (was masked
  by bogus YAAS display). Fixed via N6 backfill.
- **Status:** Closed
- **Commit:** 04447c9

### ✅ #2: MIN_SCORE_DISPLAY hardcoded — replaced with config imports (partial)
- **Scope:** 6 occurrences of `>= 60` + 1 of `>= 70` in dashboard.py and post_analysis_collector.py
- **Fix:** All replaced with MIN_SCORE_DISPLAY (60) and TRADE_ENTRY_MIN_SCORE (70) from config.py.
  Imports already existed in both files.
- **False positives confirmed:** dashboard.py:1313, 1364 are `total_seconds() >= 60` (seconds, not Score).
- **Health audit C2:** 6 → 5 thresholds.
- **Note:** This task closed the dashboard.py + post_analysis_collector.py portion only.
  The broader issue ("Min Score threshold inconsistent across pages" — original #2)
  was renumbered to **#22** since other thresholds remain in score_distribution.py,
  auto_scanner.py, and health_check.py (tracked as #N8).
- **Status:** Closed
- **Commit:** c1328d1
- **Related (still open):** #22, #N8

### ✅ #N6: post_analysis missing 2026-04-28 (D2 health alert) — backfilled
- **Detected by:** Health audit D2 — "Missing 1/3 recent days: ['2026-04-28']"
- **Investigation:** daily_snapshots had 2 candidates with Score≥60 (AKAN 86.21, SBLX 65.68)
  but post_analysis had 0 rows for that date. Collector ran but didn't persist results.
- **Fix:** Manual backfill: `python3 post_analysis_collector.py --date 2026-04-28`
- **Result:** 2 rows added (AKAN, SBLX). post_analysis: 148 → 150 rows. D2 → PASSED. D3 → PASSED.
- **Status:** Closed (manual operation, no commit)

### ✅ #18: Document MxV positive values are normal
- **Decision:** Added full value range explanation to PROJECT_KB.md §4.5:
  +98 to +100 = no pump, 0 = boundary, negative = pump.
  Explicitly noted: positive values are NOT a bug.
- **Status:** Closed
- **Commit:** [this commit]

### ✅ #N3: Project Knowledge "missing files" — investigation result
- **Concern raised:** UI showed only 1 file ("ridinghigh-pro" GitHub connector card),
  user feared sync issues.
- **Investigation:** Clicking the connector card opened full file list — 64 files all
  selected, 14% capacity. `git ls-files | wc -l` confirmed 64 files locally.
- **Conclusion:** NOT a bug. The connector card is a collapsed view; clicking expands
  to all files. Search index is fully synced and finds all files correctly.
- **Related:** Web search confirmed Issue #25759 (anthropics/claude-code, 14-Feb-2026)
  about RAG mode at 2% capacity threshold — relevant context but not the issue here.
- **Status:** Closed (no action needed)
- **Verified:** 2026-04-29 by user screenshot inspection

---

## ✅ CLOSED (2026-04-28) - Session "UnboundLocalError + Email Alerts"

### 🔴 Critical: UnboundLocalError in analyze_ticker (silent 24h+ outage)
- **Root cause:** Duplicate `from data_provider import get_fundamentals_provider` at line 264 inside analyze_ticker. Python treated the name as local for entire function, breaking earlier use at line 164. The `except: pass` swallowed the UnboundLocalError silently.
- **Symptoms:**
  - REL_VOL stuck at 1.0 in 100% of rows since Phase 2 deploy (26/4)
  - Float% stuck at 0.0
  - MxV using only FINVIZ market_cap (degraded values)
  - All 3 metrics defaulted because `fund={}` after the silent exception
- **Detection:** Manual inspection 28/4 morning when scanner data looked off
- **Fix:** Removed duplicate import + reuse `fund` already fetched at line 164. Avoids double API call AND fixes UnboundLocalError.
- **Verification:** Local run shows REL_VOL=0.03/0.8/13.26/1.58 (varied), Float%=77.75/11.86/92.17/12.65 (varied)
- **Status:** Closed
- **Commit:** 59ebc33

### 🟠 check_05 false positive — Post-analysis completeness
- **Root cause:** Read `col_values(1)` (Ticker column) and tried to parse as date. All parses failed silently, check always returned "Missing X/X recent days" even when data was complete.
- **Fix:** Read `col_values(2)` (ScanDate column) instead.
- **Impact:** Misled today's investigation into post_analysis_collector — collector was healthy all along.
- **Status:** Closed
- **Commit:** e832d89

### 🟢 health_audit improvements (Phase 3 monitoring)
- **check_16 — Metric Sanity:** detects stuck REL_VOL=1.0, Float%=0, Gap outliers >100% in last 200 timeline_live rows. Born from today's incident.
- **check_17 — Fundamentals provider:** calls `get_fundamentals('AAPL')`, validates required fields. Would have caught UnboundLocalError at next 06:00 cycle.
- **check_18 — Daily bars provider:** calls `get_daily_bars('AAPL', days=10)`, validates OHLCV columns.
- **Email alerts:** Gmail SMTP SSL via 3 GitHub Secrets (GMAIL_USER, GMAIL_APP_PASS, REPORT_TO). Sends only on CRITICAL with full report (summary, all CRITICAL details, all WARNINGs, PASSED list).
- **Status:** Closed
- **Commits:** a0b5fc4 (check_16), 02de227 (check_17+18), 40a25dc (email basic), 241074f (email full report)

### 🟢 Backfill 3 missing post_analysis days
- Manually ran `post_analysis_collector.run(target_date='YYYY-MM-DD')` for 23/4, 24/4, 27/4
- Added 5+3+2 = 10 rows
- post_analysis: 138 → 148 rows
- **Status:** Closed (manual operation, no commit)

### 🟢 Cleanup: 12 DEBUG prints
- 9 `[DEBUG-T*]` and 3 `[DEBUG-FUND-*]` added during root cause investigation
- Replaced with minimal `print(f"⚠ {ticker}: {type(e).__name__}")` after fix verified
- Preserves visibility of future silent failures without DEBUG-tag clutter
- **Status:** Closed
- **Commit:** cf531fd

### ✅ #19: post_analysis_collector selection logic — documented (closed 2026-04-29)
- **Decision:** Verified working as designed. Collector selects peak Score row per
  (ticker, scan_date) — see `day.loc[day["Score"].idxmax()]` in post_analysis_collector.py.
- **Why volume drops:** 992 timeline_live rows ≥60 on 22/4 → 5 rows in post_analysis.
  Collector picks one row per ticker, so volume reduces from "rows" to "unique tickers".
- **Documentation:** PROJECT_KB.md §8 (collector row in critical files table) + §9 issue #16
  ("post_analysis << timeline_live row count — Not a bug").
- **Status:** Closed
- **Commits:** f68b5b3 (PROJECT_KB §8 documentation), this commit (OPEN_ISSUES closure)
- **Verified:** 2026-04-29 by code audit + grep cross-check between OPEN_ISSUES.md and PROJECT_KB.md

---

## ✅ CLOSED (2026-04-25) - Session "Cleanup + PROJECT_STATE"

### ✅ #1 — SL Unification (closed 2026-04-25)
- **Decision:** TP=-10%, SL=+10%, 5-day window, unified across all 3 dashboard pages
- **Implementation:** all SL/TP reads from `config.py` (`TP_THRESHOLD_PCT`, `SL_THRESHOLD_PCT`, `MAX_HOLDING_DAYS`)
- **Schema change:** `SL7_Hit_D1` → `SL_Hit_D5` (renamed in utils.py:396-401)
- **Migration script:** `migrate_sl_hit_d5.py`
- **Commit:** d36714d
- **Verified:** 2026-04-28 by code audit — all 3 dashboard pages + auto_scanner + utils consistent

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

### #22: Min Score threshold inconsistent across pages (broader scope, see #N8)
- `MIN_SCORE_DISPLAY` exists in config but not enforced everywhere
- **Closed (2026-04-29 commit c1328d1):** dashboard.py + post_analysis_collector.py
  (8 hardcoded thresholds → 0). See ✅ #2 in CLOSED 2026-04-29.
- **Still open:** thresholds in other files (tracked as #N8):
    - `score_distribution.py:[205, 240]` → TP_THRESHOLD_FRAC (0.10)
    - `auto_scanner.py:[933, 935]` → MIN_SCORE threshold (70)
    - `health_check.py:[169]` → MIN_SCORE
- **Health audit C2 status:** 5 thresholds remaining (down from 6 before #2 closure)
- **Renumbered:** This issue was originally #2; renumbered to #22 to avoid collision
  with closed #2 (partial fix). The broader scope continues here.
- **Effort:** 30 min to close fully via #N8

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

## 🆕 DISCOVERED 2026-04-29

### #N7: Migrate 5 workflows to `pip install -r requirements.txt`
- **Background:** Today's #N4 fix migrated `health_audit.yml` to use `requirements.txt`.
  5 other workflows still install dependencies manually:
    - `auto_scan.yml`
    - `post_analysis.yml`
    - `backup.yml`
    - `monthly_rotation.yml`
    - `prepare_next_month.yml`
- **Risk if left unfixed:** Adding a new dependency to `requirements.txt` won't propagate
  to those workflows. Future drift potential — same root cause as N4.
- **Effort:** 45 min (need to verify each workflow gets all deps it actually uses, not
  just blindly switch to `-r requirements.txt`)
- **Priority:** LT (long-term refactoring)
- **Discovered:** 2026-04-29 during N4 investigation

### #N8: 4 hardcoded thresholds outside #2/#22 scope
- **Background:** #2 closure on 2026-04-29 (commit c1328d1) reduced health_audit C2
  from 6 → 5 thresholds — not 6 → 0 as initially expected. The remaining 5 are in
  files outside the original #2 scope:
    - `score_distribution.py:[205, 240]` → `TP_THRESHOLD_FRAC` (0.10)
    - `auto_scanner.py:[933, 935]` → `MIN_SCORE` (70)
    - `health_check.py:[169]` → `MIN_SCORE`
    - `dashboard.py:[1313, 1364]` — **false positives** (seconds, not Score) — already
      verified during #2; would need check_C2 logic improvement to suppress
- **Effort:** 30 min (4 str_replace + verify check_C2 result)
- **Priority:** P2
- **Discovered:** 2026-04-29 by health_audit C2 analysis after #2 closure

### #N9: check_19 false positive — fails to catch issues marked Verified in body without title markers
- **Background:** #19 (post_analysis_collector selection logic) was marked "Verified
  working as designed" on 2026-04-28 but stayed in DISCOVERED section. check_19 didn't
  flag this drift because it scans only for `~~` (strikethrough) or `✅` markers in
  issue titles — not body text.
- **Suggested fix:** Extend check_19 to detect issues where body contains "Verified",
  "Closed", "Confirmed working", or similar wording without title markers.
- **Effort:** 20 min (regex update + test)
- **Priority:** P3 (nice-to-have)
- **Discovered:** 2026-04-29 during #19 closure investigation

---

## 🆕 DISCOVERED 2026-04-28

### #20: Streamlit Cloud dashboard.py ImportError (deferred from 25/4)
- Error: `from formulas import (...)` at dashboard.py line 27
- Status pre-incident, not caused by today's fixes
- **Effort:** 20 min (fix import or update formulas exports)

### #21: GitHub Actions runner queue resilience
- Today's GitHub outage (08:30–10:30 Peru) caused 12 consecutive scanner failures + 17 queued runs
- No auto-retry or backoff strategy in place
- **Effort:** 30 min (add retry logic or alert on stuck queue)

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
