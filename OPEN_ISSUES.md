# RidingHigh Pro - Open Issues Log
*Last updated: 2026-04-30 17:00 Peru*

---

## ✅ CLOSED (2026-05-02) - Session "Score v1/v2 tagging (#N10 + #6)"

### ✅ #N10 — Score v1/v2 validation (closed 2026-05-02)
- **Decision:** Tag instead of recompute (Option C — minimal risk, ~30 min vs 4-6h)
- **Investigation:** 104/156 April records (67%) computed with Score v1 (before commit f3d96ca, 11/4/2026)
- **Resolution:** Added `score_version` column to post_analysis & daily_snapshots
  - post_analysis: v1=104, v2=50
  - daily_snapshots: v1=0, v2=343 (sheet started 2026-04-23, all post-cutoff)
- **Why tagging not recompute:** r=-0.07 (Score barely predicts wins) → not worth touching 5 sheets and risking inconsistency. Raw metrics (MxV, ATRX, RunUp) unchanged → still usable for primary analyses.
- **Implementation:** `mark_score_version.py` (idempotent, with backups + audit log)
- **Commit:** bf2892b
- **Backups:** `~/RidingHighPro/backups/{post_analysis,daily_snapshots}_2026-04_pre_mark_*.csv`
- **Next action:** Filter `score_version == 'v2'` in dashboard pages that use Score

### ✅ #6 — Gap removed from Score v2 (closed 2026-05-02)
- **Status:** Deferred to Score v3 design phase
- **Original concern:** Gap removed 11/4 (commit f3d96ca) despite r=-0.256 (strong correlation with wins)
- **Decision:** Not re-adding to current Score v2. When Score v3 is designed (after Phase 1 data accumulation), Gap will be reconsidered with fresh data.
- **Why defer not fix:** v2 is producing data; mid-flight re-introduction would cause yet another version drift like #N10.
- **Reference:** Closed alongside #N10 since both relate to Score v2 formula stability.

## ✅ CLOSED (2026-04-30) - Session "Stale Issue Audit + #N9 Workaround + #N8 fix"

### ✅ #22 + #N8: Min Score threshold consistency — fully resolved
- **Original concern (#22, was #2):** MIN_SCORE_DISPLAY exists in config but hardcoded
  `>= 60` and `>= 70` thresholds appear throughout the codebase.
- **Phase 1 (closed 2026-04-29 commit c1328d1):** dashboard.py + post_analysis_collector.py
  — 8 hardcoded thresholds replaced with config imports (MIN_SCORE_DISPLAY, TRADE_ENTRY_MIN_SCORE).
- **Phase 2 (this commit):** Investigation of remaining 5 health_audit C2 entries revealed:
    - **1 real hardcoded** (now fixed): `health_check.py:169` — `Score >= 70` →
      `Score >= TRADE_ENTRY_MIN_SCORE`. Added `from config import TRADE_ENTRY_MIN_SCORE`.
      Also updated f-string at line 174 to use the variable.
    - **4 false positives** (no fix needed):
        - `score_distribution.py:[205, 240]` — `quantile(0.10)` is statistical (p10), not threshold.
          The 0.10 value coincidentally matches TP_THRESHOLD_FRAC.
        - `auto_scanner.py:[933, 935]` — Hebrew docstring/comment, not code.
        - `dashboard.py:[1313, 1364]` — `total_seconds() >= 60` (seconds, not Score).
- **Result:** All actual hardcoded MIN_SCORE thresholds now use config. C2 dropped 5 → 4,
  and the 4 remaining are confirmed false positives.
- **Status:** Closed (#22 fully resolved, #N8 fully resolved)
- **Commit:** [this commit]
- **Discovered new task:** #N11 — improve check_C2 to suppress false positives

### ✅ #N9 (workaround): check_19 false positive — title markers removed
- **Background:** #N9 title contained literal `~~` and `✅` characters as descriptive
  text, which check_19 interprets as "fixed marker" indicators. Result: false-positive
  WARNING on every check_sync run, displaying `#?` because the regex `\d+` couldn't
  extract numeric ID from "N9".
- **Workaround applied:** Renamed #N9 title to remove the trigger characters.
  Body still explains the markers check_19 scans for. The proper fix (extending
  check_19 to detect 'Verified'/'Closed' wording in body text) remains tracked as #N9.
- **Status:** Workaround closed. #N9 itself still open as P3.
- **Commit:** 1293525
- **Verified:** check_sync.py [19] ✅ PASSED after workaround

### ✅ #5: DynamicScore — investigation revealed already removed
- **Original concern:** "Calculated on-the-fly in dashboard page 8 only, not saved, can't backtest"
- **Investigation result:** DynamicScore was REMOVED entirely in Issue #34 (commit ecfc4e5).
  Only stale comments remain:
    - `formulas.py:377` — "# Score_B..I, EntryScore, DynamicScore removed in Issue #34"
    - `dashboard.py:2439` — "# Dynamic Score section removed (Issue #34)"
- **Why this issue stayed open:** Drift — code was fixed but tracker wasn't updated.
  Same pattern as closed #19 yesterday.
- **Status:** Closed (no action needed)
- **Verified:** 2026-04-30 by stale issue audit

### ✅ #7: post_analysis recalc — context shifted, no longer applicable
- **Original concern:** "124 rows might need recalc with new formulas after formulas.py fixes"
- **Investigation result:** post_analysis now has 150 rows (was 124 when issue opened).
  Daily collector running consistently, new rows use current formulas.
- **What's left:** Validating that the original 124 historical rows match new formulas
  (a narrower question). Tracked separately as #N10 in DISCOVERED 2026-04-30.
- **Status:** Closed (superseded by #N10)
- **Verified:** 2026-04-30 by stale issue audit

### ✅ #15: config.py WEIGHTS_V1_LEGACY removed (dead code cleanup)
- **Background:** config.py contained `WEIGHTS_V1_LEGACY` dict with comment
  "DEPRECATED: DO NOT USE", kept for reference since Score v1 → v2 migration
  on 2026-04-11.
- **Investigation:** No active code imports or references `WEIGHTS_V1_LEGACY`.
  Only mentions were:
    - `config.py:33` — migration note in module docstring
    - `config.py:220` — the dict definition itself
    - archive/backup copies (not active)
- **Fix:**
    - Removed `WEIGHTS_V1_LEGACY` dict and its docstring (20 lines)
    - Removed migration note from module docstring (5 lines), replaced with
      single-line summary: "Score v2 (current) replaces Score v1 (deprecated 2026-04-11)."
    - Cosmetic: trimmed 4 blank lines → 2 between DASHBOARD_COLORS and Module self-test.
- **Verification:**
    - `grep -c WEIGHTS_V1_LEGACY config.py` → 0
    - `python3 -c "import config"` → OK, SCORE_WEIGHTS_V2 loads with 7 keys
    - `python3 -c "import ast; ast.parse(open('config.py').read())"` → syntax OK
- **Why now:** "שלמות > מהירות" — dead code cleanup; git history preserves
  the legacy weights if anyone needs them for reference.
- **Status:** Closed
- **Commit:** [this commit]

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


---

## 🟠 STILL OPEN - Important

### #8: Section 5 on page 9 is biased
- Score tends to high values, "wins" without normalization
- **Effort:** 25 min

### #9: yfinance reliability for fundamentals (post Phase 2 Alpaca migration)
- **Current state (2026-04-30 audit):**
    - Main bars data → Alpaca (post Phase 2 migration, working)
    - **Fundamentals → yfinance** (still required: Alpaca Basic doesn't expose shares/float/marketcap)
    - Active code path: `providers/yfinance_provider.py:32` (fundamentals only)
    - Direct `import yfinance` only in archive/old sync copies
- **Original concern:** 3 BROKEN rows, 21 NO_DATA in post_analysis (pre-split prices, partial intraday)
- **Reduced scope after Phase 2:** Reliability concern now narrows to fundamentals fetch only.
  Bars data is on Alpaca and stable.
- **Alternatives for fundamentals:** Polygon.io ($29/mo), FMP ($14/mo)
- **Decision needed:** Is fundamentals reliability sufficient with yfinance, or worth $14-29/mo upgrade?
- **Updated:** 2026-04-30 — narrowed scope after architecture audit

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


### #17: DropsLab schema migration pending
- Same migration as #41 needs to apply to DropsLab
- Currently on old schema

## 🆕 DISCOVERED 2026-05-01

### #N21: Health Audit מורחב + Live Write Verification
- **Priority:** 🟠 P1 (חשוב, לא דחוף — אחרי משימות 2/3/4)
- **Background:** On 2026-05-01 at 09:00 Peru, 3 sheets (score_tracker, live_trades,
  portfolio_live) showed 0 rows. Investigation revealed all 3 are working correctly:
  score_tracker writes every 5 min, live_trades waits for entries ≥70 after market open
  (09:30), portfolio_live is empty because it's the first day of the month with no open
  positions. But the Health Audit didn't flag this — and when everything passes, it sends
  no email, creating an illusion of a dead system.
- **What to build:**
    1. Add cron `0 14 * * 1-5` (08:40 Peru, Mon-Fri) to `health_audit.yml` — smoke test
       10 min after market open verifying scanner is writing.
    2. New `check_live_writes()` in `health_audit.py`:
       - Distinguish EXPECTED_LIVE vs EXPECTED_EOD by time of day
       - LIVE sheet with no data in last 15 min during market hours → CRITICAL
       - EOD sheet with no data after EOD window → CRITICAL
    3. **Decision needed — heartbeat email strategy:**
       - Option A: Always send email after every check (simple)
       - Option B: CRITICAL/WARNING only, add Slack/Discord heartbeat (cleaner)
       - Option C: Daily heartbeat at 06:00 Peru only, silent otherwise unless CRITICAL
    4. Minor fix: `auto_scanner.py:565` — add `print("📊 portfolio sheet empty, skipping
       portfolio_live")` so logs distinguish "empty" from "crashed"
- **Effort:** 2-3 hours
- **Blockers:** Requires decision on heartbeat option (A/B/C)
- **Files:** `.github/workflows/health_audit.yml`, `health_audit.py`, `auto_scanner.py`
- **Discovered:** 2026-05-01 during investigation of "missing writes" false alarm

### #N22: sheets_manager._get_root_folder_id falls back to wrong folder when run locally
- **Priority:** 🟡 P2
- **Background:** When `ensure_monthly_setup` runs locally with OAuth credentials,
  `_get_root_folder_id()` can't reach ROOT_FOLDER_ID (`1mHSdsTENVuMTtlv4XM54SrbadCEF_HHh`)
  and falls back to creating/using a `RidingHigh-Data` folder. This caused
  ticker_follow_up sheets for 2026-05 and 2026-06 to be created in the wrong
  parent folder on 2026-05-01 (manually fixed via Drive API move).
- **Why:** SA may not have access to ROOT_FOLDER_ID, or there's a permission issue
  with the OAuth user's view of that folder via the SA `_get_drive_service()` path.
- **Fix needed:** Investigate why ROOT_FOLDER_ID isn't accessible from local SA,
  add explicit error if fallback would create different folder structure.
- **Impact:** Confusion when running `ensure_monthly_setup` locally for repair.
  Does not affect CI runs (which use both SA and OAuth credentials correctly).
- **Files:** `sheets_manager.py:219-249`, `_get_root_folder_id()`
- **Discovered:** 2026-05-01 during ticker_follow_up backfill
- **Cleanup status:** All misplaced folders moved to RidingHighPro/. RidingHigh-Data deleted (2026-05-01 evening).

### #N23: pandas_market_calendars Python 3.9 incompatibility (LOCAL ONLY)
- **Priority:** 🟢 P3 (cosmetic, local-only — production unaffected)
- **Background:** `mcal.get_calendar('NASDAQ')` throws `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` on Python 3.9 due to PEP 604 union types (`X | None` syntax) which requires Python 3.10+.
- **Impact:**
  - Local runs of `utils.is_trading_day` fall back to weekday-only check (no holiday detection — Memorial Day, Christmas, etc. tagged as trading days locally).
  - GitHub Actions (Python 3.11.15) works correctly — `mcal` loads NYSE calendar and detects holidays. **Production unaffected.**
- **Verified locally:**
  - 2026-05-25 (Memorial Day, Mon) → `True` locally (wrong), `False` on 3.11
  - 2026-12-25 (Christmas, Fri)    → `True` locally (wrong), `False` on 3.11
- **Workaround in place:** try/except in `utils.is_trading_day` catches `TypeError` and falls through to `weekday() < 5` check.
- **Fix options:**
  1. Upgrade local Python to 3.10+
  2. Pin `pandas_market_calendars` to 3.9-compatible version (e.g., 4.x)
  3. Hard-code NYSE holidays as static fallback list when `mcal` fails
- **Files:** `utils.py:75` (is_trading_day), `requirements.txt` (mcal version)
- **Discovered:** 2026-05-01 evening (during is_trading_day duplicate cleanup, commit 8ae2c88)

---

## 🆕 DISCOVERED 2026-04-30

### #N11: Improve check_C2 to suppress false positive thresholds
- **Background:** #N8 closure (this morning) revealed 4 of 5 detected thresholds
  were false positives:
    - `quantile(0.10)` — statistical, not threshold
    - Hebrew docstrings/comments
    - `total_seconds() >= 60` — time, not Score
    - String constants in f-strings (already fixed but worth detecting)
- **Suggested improvements:**
    1. Skip lines inside docstrings/comments (parse via `ast` instead of regex)
    2. Distinguish `>=` in `Score`/`MIN_SCORE` context vs `total_seconds`/`quantile`
    3. Skip f-string literals or treat them as cosmetic (lower severity)
    4. Allow whitelist of known-safe values (0.10 in quantile context)
- **Why this matters:** Currently health_audit C2 always reports WARNING with 4-5
  false positives, dulling alert fatigue and hiding real hardcoded values.
- **Suggested approach:** Use `ast.parse()` to walk the AST and only flag actual
  numeric comparisons in code paths, not strings/comments/docstrings.
- **Effort:** 1-2 hours (proper AST-based analysis)
- **Priority:** P3 (nice-to-have, doesn't break anything)
- **Discovered:** 2026-04-30 by #N8 closure investigation

---

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
