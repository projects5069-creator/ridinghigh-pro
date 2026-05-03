# 🚀 Claude Code Prompt v2.0 — Phase 1 Implementation

**For: Claude Code**
**Project: RidingHigh System (unified)**
**Phase: 1 — The Trader + Score Analytics**
**Replaces: v1.0 (2026-04-30)**

---

## 📋 Read This First

You are implementing **Phase 1** of the RidingHigh Agent for עמיחי.

Before writing any code:

1. **Read the State Update Summary:** `00_STATE-UPDATE-SUMMARY.md` — understand what changed
2. **Read the full spec:** `01_FINAL-SPEC_v2.0.md`
3. **Read the scanner reference:** `03_SCANNER-REFERENCE_v2.0.md`
4. **Read PK_v2 in the repo:** `docs/RidingHigh_Pro_PK_v2.md` — the authoritative system documentation
5. **Understand:** This is ONE system in TWO modules. The Scanner is MATURE and STABLE. You're adding the Agent module ALONGSIDE it.

---

## 🎯 The Mission

Extend the existing `projects5069-creator/ridinghigh-pro` repository with a new Agent module that:

- Reads signals from the existing Scanner's Google Sheets
- Makes entry/exit decisions based on עמיחי's MxV strategy
- Executes trades on Alpaca Paper Trading (already connected!)
- Logs every decision with full reasoning
- Provides continuous Score Analytics
- Sends daily/weekly emails
- Adds 2 new pages to existing Streamlit dashboard

**This is paper trading only.** No live trading in Phase 1.

---

## 🔒 Critical Boundaries — DO NOT VIOLATE

### ❌ Things You MUST NOT Do:

1. **DO NOT modify the scanner's behavior**
   - The scanner is in production. It works.
   - Do not change scanner logic, formulas, or output
   - If you find a bug — REPORT IT in OPEN_ISSUES.md, don't fix it
   - The Agent is purely ADDITIVE

2. **DO NOT move scanner files** (this was a mistake in v1.0 spec)
   - No `scanner/` migration
   - All existing files stay where they are
   - The Agent goes in NEW `agent/` directory alongside

3. **DO NOT use live trading credentials**
   - Use Alpaca PAPER API only
   - Verify base_url is `https://paper-api.alpaca.markets`
   - Already configured for the scanner; reuse same credentials

4. **DO NOT deploy without approval**
   - Build and test locally first
   - Ask user before pushing to Streamlit
   - Ask user before activating new GitHub Actions

5. **DO NOT skip Cold Start Mode**
   - First 30 days have specific limits
   - Critical safety measures

6. **DO NOT change scoring formula**
   - Use scanner's `formulas.calculate_score()` directly via IMPORT
   - Score Analytics OBSERVES, doesn't modify
   - Modifications come in Phase 2

7. **DO NOT skip writing tests**
   - Each milestone requires unit tests
   - The `test_agent_matches_scanner` test is critical

8. **DO NOT commit secrets**
   - All secrets in environment variables
   - Verify `.gitignore` covers sensitive files

9. **DO NOT add time limits on positions**
   - User decision: positions run until TP, SL, or EOD
   - No 48-hour, no 5-day, no any-time limit

10. **DO NOT use `MAX_HOLDING_DAYS`**
    - That's a scanner constant for simulation
    - Agent uses `AGENT_NO_TIME_LIMIT = True`

11. **DO NOT skip PK_v2 updates** (NEW IN V2.0)
    - PK_v2 has Anti-Drift Contract (§35)
    - EVERY milestone MUST end with PK_v2 update
    - Failure = system documentation drift = future Claude lies to user

12. **DO NOT call yfinance/Alpaca directly for market data**
    - Use existing `data_provider.py` abstraction
    - Agent's `alpaca_broker.py` is for ORDERS only

---

## ✅ How to Work — Process

### Step 1: Confirm Setup with User

Before writing any code, confirm with the user:

```
Hi עמיחי, I'm starting Phase 1 of RidingHigh System (Agent build).

Before I begin, please confirm:

1. ✅ Scanner stable?
   Run: python health_audit.py --local
   Expected: All CRITICAL checks pass (WARNINGs OK)

2. ✅ Alpaca paper credentials working?
   Run: python -c "from data_provider import test_connection; test_connection()"
   (assuming this exists; if not, check Alpaca dashboard manually)

3. ✅ EMERGENCY_CLEAR_PASSWORD added to GitHub Secrets?
   Repo: projects5069-creator/ridinghigh-pro
   Settings → Secrets → New repository secret

4. ✅ You understand:
   - Min Score 60 (Agent) ≠ 70 (Scanner) — by design
   - No time limit (Agent) ≠ 5 days (Scanner) — by design
   - 10 milestones, each gets your review before next
   - PK_v2 will be updated each milestone
   - Saturday 18:00 Peru weekly review

If yes to all 4, I'll start with Milestone 1.
If anything is missing, please address it first.
```

**Wait for explicit user confirmation before proceeding.**

### Step 2: Work Milestone-by-Milestone

10 milestones (full details in spec Section 13):

```
M1: Foundation & Configuration       ← agent/ skeleton + config additions
M2: Agent Sheets Setup                ← create 8 new sheets
M3: The Trader Core Logic             ← decision engine
M4: Decision Logger                   ← audit trail
M5: Alpaca Execution                  ← real paper trading
M6: Postmortem Engine                 ← position analysis
M7: Score Analytics System            ← continuous learning
M8: Email System                      ← notifications
M9: Streamlit Dashboard Pages 9-10    ← UI
M10: Critical Infrastructure & Production ← safety + go-live
```

For each milestone:

1. **Announce:** "🚀 Starting Milestone X: [name]"
2. **Plan:** Outline specific files to create/modify
3. **Implement:** Write the code
4. **Test:** Run unit tests
5. **Verify:** Check acceptance criteria from spec
6. **Update PK_v2:** Add new section reflecting changes (CRITICAL)
7. **Demo:** Show user what works
8. **Wait:** For approval before next milestone

### Step 3: Document as You Go

Update these continuously:

- `docs/RidingHigh_Pro_PK_v2.md` — MUST update each milestone (Anti-Drift Contract)
- `OPEN_ISSUES.md` — Add issues as discovered, close when fixed
- `README.md` — High-level project description
- Inline docstrings — Every function and class

---

## 🏗️ Phase 1 Implementation Order

Follow this exact order. Each milestone builds on the previous.

---

### Milestone 1: Foundation & Configuration

**Goal:** Add agent constants, create directory structure, validate setup.

**Tasks:**

1. **Verify scanner state:**
   ```bash
   cd ridinghigh-pro
   git status                    # clean
   git pull origin main
   python health_audit.py --local # all CRITICAL pass
   ```

2. **Create agent directory structure:**
   ```bash
   mkdir -p agent/{trader,perception,execution,analytics,monitoring,logging,notifications,utils,setup}
   touch agent/__init__.py
   touch agent/{trader,perception,execution,analytics,monitoring,logging,notifications,utils,setup}/__init__.py
   mkdir -p agent/notifications/templates
   mkdir -p tests/agent/unit
   mkdir -p tests/agent/integration
   ```

3. **Add agent constants to config.py (ADDITIVE only):**
   
   At the END of `config.py`, ADD a new section:
   
   ```python
   # ═══════════════════════════════════════════════════════════════════════
   # AGENT MODULE CONFIGURATION (Phase 1)
   # Added: 2026-MM-DD by Phase 1 implementation
   # See: agent/ directory, FINAL-SPEC v2.0
   # ═══════════════════════════════════════════════════════════════════════
   
   # Entry criteria — DIFFERENT from scanner (intentionally)
   AGENT_MIN_SCORE = 60               # Liberal threshold for learning
   AGENT_MXV_MAX = -100               # Must be very negative
   AGENT_RUNUP_MIN = 30               # %, intraday rise
   AGENT_VOLUME_MIN = 100_000         # Liquidity floor
   AGENT_MARKET_CAP_MIN = 5_000_000   # $5M minimum
   AGENT_MARKET_CAP_MAX = 2_000_000_000  # $2B maximum
   
   # Exit criteria — same as scanner except no time limit
   AGENT_TP_PCT = 10                  # Same as TP_THRESHOLD_PCT
   AGENT_SL_PCT = 10                  # Same as SL_THRESHOLD_PCT
   AGENT_NO_TIME_LIMIT = True         # ⚠️ DIFFERENT from MAX_HOLDING_DAYS
   AGENT_EOD_CLOSE_MIN_BEFORE = 5     # Close 5 min before market close
   
   # Position sizing
   AGENT_POSITION_SIZE_USD = 1000     # Same as POSITION_SIZE_USD
   
   # Cold Start Mode (first 30 days)
   AGENT_COLD_START_ENABLED = True
   AGENT_COLD_START_DAYS = 30
   AGENT_COLD_START_MAX_CONCURRENT = 5
   AGENT_COLD_START_MAX_DAILY = 10
   AGENT_COLD_START_DAILY_LOSS_ALERT_USD = 200
   
   # Modes
   AGENT_DRY_RUN = True               # Start in DRY_RUN; switch to False at M10
   AGENT_LIVE_PAPER = False           # Becomes True after M10 approval
   ```

4. **Create `agent/utils/sheets_cache.py`:**
   
   Implement per Spec Section 8.2.

5. **Verify imports work:**
   ```python
   # Test from project root:
   from agent.utils.sheets_cache import SheetsCache
   from formulas import calculate_score      # CRITICAL — must work
   from config import AGENT_MIN_SCORE, AGENT_MXV_MAX
   from data_provider import get_provider
   ```

6. **Update PK_v2 with new section §A1:**
   
   Add to `docs/RidingHigh_Pro_PK_v2.md`:
   
   ```markdown
   ## A1. 🤖 Agent Module Overview
   
   The Agent module is a Phase 1 addition that extends RidingHigh Pro
   with autonomous paper trading on Alpaca.
   
   **Status:** In development — Milestone 1 of 10 complete (YYYY-MM-DD)
   
   **Location:** `agent/` directory at repo root
   
   **Configuration:** All agent constants in `config.py` under
   "AGENT MODULE CONFIGURATION" section.
   
   **Key differences from scanner:**
   - `AGENT_MIN_SCORE = 60` (vs `TRADE_ENTRY_MIN_SCORE = 70`)
   - `AGENT_NO_TIME_LIMIT = True` (vs `MAX_HOLDING_DAYS = 5`)
   - Both intentional — Agent for learning, scanner for simulation research
   
   **Modules planned:**
   - trader/ (decision logic)
   - perception/ (data quality, tradability)
   - execution/ (Alpaca orders, position management)
   - analytics/ (Score Analytics, postmortems)
   - monitoring/ (health checks, self-test, emergency stop)
   - logging/ (decision logger)
   - notifications/ (email)
   ```
   
   Increment PK_v2 version: v2.0 → v2.1
   Add changelog entry.

7. **Commit:**
   ```bash
   git add agent/ config.py docs/RidingHigh_Pro_PK_v2.md
   git commit -m "feat(phase1-m1): foundation and configuration
   
   - Created agent/ directory structure
   - Added AGENT_* constants to config.py (additive)
   - Implemented sheets_cache utility
   - Updated PK_v2 with §A1 Agent Module Overview
   - Bumped PK_v2 to v2.1"
   ```

**Acceptance:**
- [ ] All scanner workflows still passing (health_audit green)
- [ ] `from agent.utils.sheets_cache import SheetsCache` works
- [ ] `from config import AGENT_MIN_SCORE` works
- [ ] PK_v2 has new §A1 section
- [ ] PK_v2 version bumped to v2.1
- [ ] No scanner files modified

**STOP HERE.** Show user the new directory structure and PK_v2 update. Wait for approval.

---

### Milestone 2: Agent Sheets Setup

**Goal:** Create 8 new sheets in current month's Drive folder.

**Tasks:**

1. **Create setup script `agent/setup/create_agent_sheets.py`:**
   
   Programmatic creation of all 8 sheets with correct headers.
   
   Reference Spec Section 11.2-11.9 for exact column lists.

2. **Run setup script for current month:**
   ```bash
   python -m agent.setup.create_agent_sheets --month current
   ```

3. **Update `sheets_config.json`:**
   
   Add agent sheet IDs to current month's config:
   ```json
   {
     "2026-05": {
       // ... existing 9 scanner sheets ...
       "decision_log": "<new_id>",
       "paper_portfolio": "<new_id>",
       "score_analytics": "<new_id>",
       "postmortems": "<new_id>",
       "system_events": "<new_id>",
       "pending_suggestions": "<new_id>",
       "config_history": "<new_id>",
       "borrow_data": "<new_id>"
     }
   }
   ```

4. **Update `monthly_rotation.yml` workflow:**
   
   Add agent sheets to monthly rotation logic (so May → June creates new agent sheets too).

5. **Update PK_v2 §15 (Schema Reference):**
   
   Add 8 new agent sheet schemas. Increment PK_v2 to v2.2.

**Acceptance:**
- [ ] All 8 agent sheets exist in current month folder
- [ ] Headers match spec exactly (40, 22, 25, 17, 7, 14, 10, 9 columns)
- [ ] sheets_config.json validates
- [ ] monthly_rotation tested in dry-run mode
- [ ] PK_v2 §15 updated
- [ ] PK_v2 version v2.2

**STOP HERE.** Show user the new sheets in Drive.

---

### Milestone 3: The Trader Core Logic

**Goal:** Trader can evaluate signals (without executing).

**Tasks:**

1. **Create `agent/trader/score_calculator.py`:**
   
   ```python
   # CRITICAL: Direct import from scanner's formulas
   from formulas import calculate_score
   
   def calculate_agent_score(metrics: dict) -> float:
       """
       Wrapper around formulas.calculate_score() for agent context.
       MUST return identical value to scanner's calculation.
       """
       return calculate_score(metrics)
   ```

2. **Create `agent/perception/data_quality.py`:**
   
   Implement per Spec Section 8.3.

3. **Create `agent/perception/tradability.py`:**
   
   Mock Alpaca for now (real integration in M5):
   ```python
   def check_tradability(ticker: str) -> dict:
       """Mock implementation — returns shortable=True for now."""
       return {
           "is_shortable": True,
           "is_etb": False,
           "is_htb": True,
           "borrow_fee_pct": 12.5,
           "locate_available": True,
       }
   ```

4. **Create `agent/trader/decision_logic.py`:**
   
   Implement decision tree from Spec Section 5.3.
   
   Key checks (in order):
   1. Pre-filter (Score >= 60, MxV <= -100, RunUp >= 30%, etc.)
   2. Tradability
   3. Safety (no duplicate, buying power, cold start limits)
   4. Calculate position size
   5. Return ENTER/SKIP with reason

5. **Create `agent/trader/trader.py`:**
   
   Main `Trader` class with `evaluate(signal) -> Decision` method.

6. **Write critical test `tests/agent/integration/test_scanner_agent_match.py`:**
   
   ```python
   def test_agent_matches_scanner():
       """
       CRITICAL: Read 100 random rows from scanner's timeline_live,
       compute score with agent's calculator,
       verify match within 0.01.
       
       If this test fails, STOP. Do not proceed to M5+.
       """
       from sheets_manager import get_sheet
       from agent.trader.score_calculator import calculate_agent_score
       
       # Get 100 random rows from current month timeline_live
       rows = get_random_timeline_rows(n=100)
       
       mismatches = []
       for row in rows:
           scanner_score = float(row["Score"])
           
           metrics = {
               "mxv": float(row["MxV"]),
               "run_up": float(row["RunUp"]),
               "atrx": float(row["ATRX"]),
               "rsi": float(row["RSI"]),
               "rel_vol": float(row["REL_VOL"]),
               "change": float(row["Change"]),
               "typical_price_dist": float(row["TypicalPriceDist"]),
           }
           agent_score = calculate_agent_score(metrics)
           
           if abs(scanner_score - agent_score) > 0.01:
               mismatches.append({
                   "ticker": row["Ticker"],
                   "scanner": scanner_score,
                   "agent": agent_score,
                   "diff": abs(scanner_score - agent_score)
               })
       
       assert len(mismatches) == 0, f"Score mismatches found: {mismatches[:5]}"
   ```

7. **Update PK_v2 with §A3: Agent Decision Logic.** Increment to v2.3.

**Acceptance:**
- [ ] All 28 metrics correctly read from scanner data
- [ ] **Score calculation matches scanner within 0.01 across 100 random rows**
- [ ] Decision logic returns ENTER/SKIP correctly
- [ ] Edge cases handled (None, zero, negative values)
- [ ] PK_v2 v2.3

**🚨 CRITICAL CHECK:** If `test_agent_matches_scanner` fails — STOP and investigate.

**STOP HERE.** Demo to user — show example decisions for various signals.

---

### Milestone 4: Decision Logger

**Goal:** Every decision logged to Sheets in real-time.

**Tasks:**

1. **Create `agent/logging/decision_id_generator.py`:**
   
   Format: `DEC-YYYY-MM-DD-NNNNN` where NNNNN is sequential per day.

2. **Create `agent/logging/decision_logger.py`:**
   
   Writes 40-column rows to `decision_log`, uses sheets cache for batched writes.
   
   ```python
   class DecisionLogger:
       def __init__(self):
           self.cache = SheetsCache()
           self.id_generator = DecisionIDGenerator()
       
       def log_decision(self, decision: Decision):
           """Write 40-column row to decision_log sheet."""
           row = self._build_row(decision)
           sheet_id = get_decision_log_sheet_id()
           self.cache.queue_write(sheet_id, row)
   ```

3. **Wire trader to logger:**
   
   Every `Trader.evaluate()` call ends with `logger.log_decision(decision)`.

4. **Update PK_v2 §A4: Decision Log Schema.** Increment to v2.4.

**Acceptance:**
- [ ] 100 test decisions write correctly
- [ ] All 40 columns populated
- [ ] No rate limit errors (cache works)
- [ ] Decisions appear in sheet within 5 seconds
- [ ] PK_v2 v2.4

**STOP HERE.** Show user the populated decision_log sheet.

---

### Milestone 5: Alpaca Execution

**Goal:** Trader actually submits orders to Alpaca Paper.

**Tasks:**

1. **Create `agent/execution/alpaca_broker.py`:**
   
   ⚠️ For ORDERS only. Market data goes through `data_provider.py`.
   
   Methods:
   - `submit_short_order(ticker, qty, limit_price)`
   - `submit_tp_order(ticker, qty, tp_price)`
   - `submit_sl_order(ticker, qty, sl_price)`
   - `cancel_order(order_id)`
   - `get_position(ticker)`
   - `list_positions()`
   - `get_account()`
   - `is_shortable(ticker)`
   - `get_borrow_info(ticker)`

2. **Create `agent/execution/order_manager.py`:**
   
   Implements retry logic from Spec Section 8.4.

3. **Create `agent/execution/position_manager.py`:**
   
   Monitor open positions every minute:
   - Update `paper_portfolio` sheet
   - Verify TP/SL still active
   - Handle EOD close (5 min before market close)
   - **NO TIME LIMIT check** — only TP/SL/EOD

4. **Create `agent/execution/reconciler.py`:**
   
   Daily reconciliation: Sheets vs Alpaca. Detect discrepancies.

5. **Wire trader to broker.**

6. **Update PK_v2 §A5: Order Execution Architecture.** Increment to v2.5.

**Acceptance:**
- [ ] Submit a test order, see in Alpaca dashboard
- [ ] TP/SL bracket orders register correctly
- [ ] Position appears in `paper_portfolio` sheet
- [ ] Can manually close position
- [ ] Reconciler detects mismatches
- [ ] PK_v2 v2.5

**⚠️ Critical:** Test with $1 positions FIRST. Verify everything works end-to-end. Only THEN test with $1,000.

**STOP HERE.** Show user a real (paper) trade execution lifecycle.

---

### Milestone 6: Postmortem Engine

**Goal:** Closed positions analyzed automatically.

**Tasks:**

1. **Create `agent/analytics/postmortem_engine.py`** (Spec Section 7.5)
2. **Detect position closes** every minute monitoring
3. **Compare predicted vs actual**
4. **Auto-generate lessons**
5. **Write to `postmortems` sheet**
6. **Update PK_v2 §A6: Postmortem Engine.** Increment to v2.6.

**Acceptance:**
- [ ] Position closes → postmortem appears within 1 minute
- [ ] Lessons reasonable (not generic)
- [ ] Predicted vs actual values logged
- [ ] PK_v2 v2.6

**STOP HERE.** Trigger 3 test exits. Verify postmortems make sense.

---

### Milestone 7: Score Analytics System

**Goal:** Daily + weekly analysis.

**Tasks:**

1. **Create `agent/analytics/score_analytics.py`** (Spec Section 6)
2. **Create `agent/analytics/correlation_finder.py`**
3. **Daily aggregation** writes to `score_analytics` sheet
4. **Weekly aggregation** writes to `pending_suggestions` sheet (Saturday 18:00 Peru)
5. **Generate reports for emails**
6. **Update PK_v2 §A7.** Increment to v2.7.

**🚨 IMPORTANT:** Phase 1 Score Analytics is **observational only**:
- ✅ Daily: writes to `score_analytics`
- ✅ Weekly: writes suggestions to `pending_suggestions`
- ❌ Does NOT modify scoring formula
- ❌ Does NOT change config automatically

User approves/rejects via dashboard or email.

**Schedule:**
- Daily: 16:30 Peru (after post_analysis at 16:05)
- **Weekly: SATURDAY 18:00 Peru** ⚠️ NOT Sunday

**Acceptance:**
- [ ] Daily report generated 16:30 Peru
- [ ] Weekly report generated **Saturday 18:00 Peru**
- [ ] 3-5 suggestions per weekly report
- [ ] Suggestions stored as PENDING
- [ ] PK_v2 v2.7

**STOP HERE.** Generate sample weekly report. Show user.

---

### Milestone 8: Email System

**Goal:** Reliable email delivery.

**Tasks:**

1. **Create `agent/notifications/email_sender.py`** (Spec Section 9)
2. **Build HTML templates:**
   - `daily_brief.html`
   - `weekly_review.html`
   - `urgent_alert.html`
3. **Reuse existing GMAIL_USER/GMAIL_APP_PASS/REPORT_TO secrets**
4. **Update PK_v2 §A8.** Increment to v2.8.

**Important:**
- HTML emails (with text fallback)
- Includes deep links to dashboard pages
- No new email credentials needed

**Schedules (will be set in M10 workflows):**
- Daily: 21:30 UTC = 16:30 Peru
- **Weekly: 23:00 UTC Saturday = 18:00 Peru Saturday**
- Urgent: immediate

**Acceptance:**
- [ ] Daily email arrives 16:30 Peru
- [ ] Weekly email arrives **Saturday** 18:00 Peru
- [ ] Urgent alert sends within 30 seconds
- [ ] Emails render correctly in Gmail and mobile
- [ ] PK_v2 v2.8

**STOP HERE.** Send sample emails. User confirms they look good.

---

### Milestone 9: Streamlit Dashboard Pages 9-10

**Goal:** New dashboard sections live.

**Tasks:**

1. **Add Agent pages to existing dashboard.py:**
   
   The current `dashboard.py` is single-file with conditional rendering. Add 2 new sections triggered by sidebar option:
   
   ```python
   # Existing pattern (in dashboard.py):
   page = st.sidebar.radio("Page", ["Home", "Daily Summary", ...])
   
   if page == "Home":
       render_home()
   elif page == "Daily Summary":
       render_daily_summary()
   # ... existing pages ...
   
   # NEW (added by Milestone 9):
   elif page == "🤖 Live Agent":
       render_agent_live()
   elif page == "🧠 Score Brain":
       render_score_brain()
   ```

2. **Implement `render_agent_live()`** (Spec Section 10.3)

3. **Implement `render_score_brain()`** (Spec Section 10.4)

4. **Implement Emergency Stop button:**
   
   ```python
   if st.button("🚨 EMERGENCY STOP", type="primary"):
       confirm = st.text_input("Type 'STOP' to confirm:")
       if confirm == "STOP":
           from agent.monitoring.emergency_stop import EmergencyStop
           EmergencyStop.trigger("manual_dashboard", triggered_by="user")
           st.success("Emergency stop triggered")
   ```

5. **Auto-refresh every 60 seconds.**

6. **Update PK_v2 §A9.** Increment to v2.9.

**Acceptance:**
- [ ] Both pages load in < 3 seconds
- [ ] Real-time data updates
- [ ] Emergency Stop tested (test mode first!)
- [ ] Suggestions can be approved/rejected from dashboard
- [ ] PK_v2 v2.9

**STOP HERE.** Demo to user, walk through both pages.

---

### Milestone 10: Critical Infrastructure & Production

**Goal:** All safety systems + first real paper trading.

**Tasks:**

1. **Create `agent/monitoring/agent_health.py`:**
   
   Adds checks to existing `health_audit.py`:
   
   ```python
   AGENT_HEALTH_CHECKS = [
       "alpaca_paper_account_responsive",
       "alpaca_buying_power_sufficient",
       "agent_decision_log_writable",
       "agent_no_stuck_positions",
       "agent_no_orphan_orders",
       "agent_score_calculator_matches_scanner",
       "agent_cold_start_within_limits",
       "agent_emergency_stop_status",
   ]
   ```

2. **Create `agent/monitoring/self_test.py`** (Spec Section 8.6)

3. **Create `agent/monitoring/emergency_stop.py`** (Spec Section 8.7)

4. **Create 5 new GitHub Actions workflows:**

   **`.github/workflows/agent_minute.yml`:**
   ```yaml
   name: Agent — Every Minute
   on:
     schedule:
       - cron: '*/1 13-20 * * 1-5'   # every min, market hours UTC
   jobs:
     run-agent:
       runs-on: ubuntu-latest
       timeout-minutes: 8
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - run: pip install -r requirements.txt
         - run: python -m agent.orchestrator
           env:
             GOOGLE_CREDENTIALS_JSON: ${{ secrets.GOOGLE_CREDENTIALS_JSON }}
             ALPACA_API_KEY_ID: ${{ secrets.ALPACA_API_KEY_ID }}
             ALPACA_SECRET_KEY: ${{ secrets.ALPACA_SECRET_KEY }}
             ALPACA_PAPER: 'true'
             EMERGENCY_CLEAR_PASSWORD: ${{ secrets.EMERGENCY_CLEAR_PASSWORD }}
   ```

   **`.github/workflows/agent_morning_test.yml`:**
   ```yaml
   on:
     schedule:
       - cron: '0 13 * * 1-5'        # 13:00 UTC = 08:00 Peru
   ```

   **`.github/workflows/agent_daily_email.yml`:**
   ```yaml
   on:
     schedule:
       - cron: '30 21 * * 1-5'       # 21:30 UTC = 16:30 Peru
   ```

   **`.github/workflows/agent_weekly_review.yml`:** ⚠️ SATURDAY!
   ```yaml
   on:
     schedule:
       - cron: '0 23 * * 6'          # 23:00 UTC Saturday = 18:00 Peru
   ```

   **`.github/workflows/agent_health_check.yml`:**
   ```yaml
   on:
     schedule:
       - cron: '*/5 13-20 * * 1-5'   # every 5 min, market hours
   ```

5. **Run final tests:**
   - All unit tests pass
   - Integration tests pass
   - `test_agent_matches_scanner` passes
   - Emergency Stop tested

6. **Verify all secrets configured.**

7. **Run DRY_RUN day:**
   - Set `AGENT_DRY_RUN = True` in config
   - Logs decisions but doesn't execute
   - Run for one full trading day
   - Review decisions in `decision_log`

8. **Review DRY_RUN with user.**

9. **Switch to LIVE_PAPER mode:**
   - Set `AGENT_DRY_RUN = False`
   - Set `AGENT_LIVE_PAPER = True`

10. **First real paper trading day.**

11. **Update PK_v2 §A10: Production Operations.** Increment to **v3.0** (major bump for Phase 1 complete).

12. **Update OPEN_ISSUES.md** to mark Phase 1 complete.

**Acceptance:**
- [ ] All milestones 1-9 complete
- [ ] All tests passing
- [ ] All GitHub secrets set
- [ ] All 5 GitHub Actions workflows running on schedule
- [ ] Email delivery confirmed
- [ ] Emergency Stop tested end-to-end
- [ ] Cold Start Mode active
- [ ] User has access to dashboard
- [ ] DRY_RUN day completed successfully
- [ ] User approved go-live
- [ ] First real paper trade executed
- [ ] All systems showing green
- [ ] PK_v2 v3.0 — Phase 1 fully reflected

🎉 **Phase 1 Complete!**

After this: **30-day Data-Only Phase begins automatically.**

---

## 🤔 What to Do When Things Go Wrong

### If a milestone is taking too long:
- Stop, ask user for clarification
- Don't push through if you're guessing
- It's OK to revise the plan

### If you find a bug in your own code:
- Fix it immediately
- Add a test that would have caught it
- Document in OPEN_ISSUES.md (resolved)

### If you find a bug in the SCANNER (existing code):
- DO NOT FIX IT
- Document in OPEN_ISSUES.md (open)
- Continue with Agent build
- User will address scanner bugs separately

### If user requests change mid-milestone:
- Note the request
- Ask: "Should I finish current milestone first, or pivot now?"
- Document the decision

### If Alpaca API behaves unexpectedly:
- Check status.alpaca.markets first
- Test in isolation
- Don't panic — Adapter Pattern means we can swap brokers later

### If `test_agent_matches_scanner` fails:
- STOP IMMEDIATELY
- Investigate: are agent score_calculator and formulas.calculate_score using same code path?
- If you re-implemented score logic instead of importing → fix that
- DO NOT proceed to M5+ until this passes

---

## 📖 Key References

While implementing, refer to:

**`00_STATE-UPDATE-SUMMARY.md`:**
- What changed since v1.0
- Current scanner state

**`01_FINAL-SPEC_v2.0.md`:**
- Section 5: The Trader specs
- Section 6: Score Analytics
- Section 7: Decision Logger
- Section 8: Critical Infrastructure
- Section 9: Email & Notifications
- Section 10: Streamlit Dashboard
- Section 11: Sheets Schema
- Section 13: Phase 1 Milestones (acceptance criteria)
- Section 17: PK_v2 Integration

**`03_SCANNER-REFERENCE_v2.0.md`:**
- Section 2: Scoring Formula (CRITICAL)
- Section 9: Critical Calculations
- Section 10: Validation Tests

**Repo files:**
- `docs/RidingHigh_Pro_PK_v2.md` — System documentation (UPDATE EACH MILESTONE)
- `formulas.py` — IMPORT from this, don't re-implement
- `config.py` — ADD constants, don't modify existing
- `data_provider.py` — Use for market data
- `OPEN_ISSUES.md` — Track issues here

---

## ✅ Final Checklist Before Starting

Before writing one line of code, verify:

- [ ] You've read the State Update Summary
- [ ] You've read the full v2.0 spec
- [ ] You've read the v2.0 scanner reference
- [ ] You've read PK_v2 in the repo
- [ ] You understand the philosophy (additive only, supervised on rules, autonomous on trades)
- [ ] You know which boundaries NOT to cross (especially: don't move scanner files!)
- [ ] You have access to the existing repo
- [ ] User has confirmed setup is complete

If all checked: announce Milestone 1 and begin.

---

## 💬 Communication Protocol

**Per milestone:**

1. **Start:** "🚀 Starting Milestone X: [Name]. Plan: [files to create/modify]."
2. **Progress:** "✅ Done with [task]. Now working on [next task]."
3. **Issues:** "⚠️ Found issue: [description]. Need clarification on [X]."
4. **PK_v2 Update:** "📝 Updated PK_v2 with §AX: [name]. Bumped to v2.Y."
5. **End:** "🎉 Milestone X complete. Tests: [X passed]. Ready for review."

**Always:**
- Be specific about what you did
- Show file paths and line counts
- Run tests and show output
- Update PK_v2 BEFORE asking for approval
- Wait for explicit user approval before next milestone

**Never:**
- Skip a milestone
- Auto-approve your own work
- Push to git without asking
- Deploy without verification
- **Skip PK_v2 updates** (Anti-Drift Contract violation)

---

## 🎯 The North Star

If you ever feel lost or overwhelmed, remember:

> **Build a system that עמיחי trusts to trade safely 24/5,**
> **based on his proven MxV strategy,**
> **with full transparency and supervised rule changes.**
> **Phase 1 is the foundation. Future phases add intelligence.**
> **The scanner is sacred. The Agent is additive. PK_v2 is updated continuously.**

---

Good luck. Build well. 🚀

— End of Prompt v2.0 —
