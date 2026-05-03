# 📁 Files Checklist v2.0 — Phase 1 Implementation

**For: Claude Code**
**Purpose:** Complete inventory of every file involved in Phase 1
**Status:** Reference document — use alongside CLAUDE-CODE-PROMPT_v2.0

---

## 📑 Three Categories of Files

```
📂 Existing Files
   ├── 🔵 READ-ONLY (Claude Code reads but never modifies)
   ├── 🟡 ADD-ONLY (Claude Code adds new content; never modifies existing)
   └── 🟢 EXTEND (Claude Code adds new sections/items)

📂 New Files
   ├── 🆕 Agent module (~25 new Python files)
   ├── 🆕 Workflows (5 new YAML files)
   ├── 🆕 Sheets (8 new Google Sheets)
   └── 🆕 Tests (~15 new test files)
```

---

# 🔵 EXISTING — READ ONLY

These files are Claude Code's **knowledge sources**. Read them carefully. Never modify their behavior.

## Configuration & Constants

| File | Why Read It | Lines |
|------|-------------|-------|
| `formulas.py` | Source of truth for all 28 metric calculations. **Import from this** in agent/trader/score_calculator.py. | ~470 |
| `data_provider.py` | Abstraction layer for Alpaca/yfinance. **Use for market data**. | varies |
| `sheets_manager.py` | How scanner writes to Drive. Pattern reference for agent sheets. | varies |
| `utils.py` | Common utilities like `is_trading_day()`. May import from this. | varies |
| `auto_scanner.py` | How signals are generated. Understand the source data structure. | ~1500 |
| `post_analysis_collector.py` | How trades are simulated. Understand the model. | varies |

## Documentation

| File | Why Read It |
|------|-------------|
| `docs/RidingHigh_Pro_PK_v2.md` | **AUTHORITATIVE**. The system's own documentation. Read FULLY before Milestone 1. |
| `OPEN_ISSUES.md` | Current open issues. Don't fix scanner issues; document agent issues here. |
| `README.md` | Project overview. |
| `README_health_audit.md` | How health checks work. Agent extends this system. |

## Workflows (Reference Only)

| File | Why Read It |
|------|-------------|
| `.github/workflows/auto_scan.yml` | Pattern for agent_minute.yml |
| `.github/workflows/post_analysis.yml` | Pattern for daily workflows |
| `.github/workflows/health_audit.yml` | Pattern for agent_health_check.yml |
| `.github/workflows/monthly_rotation.yml` | Will need extension to handle agent sheets |

## Tests (Reference Only)

| File | Why Read It |
|------|-------------|
| `tests/test_formulas.py` | Pattern for agent unit tests |
| Existing scanner tests | Pattern for test structure |

---

# 🟡 EXISTING — ADD ONLY

These files Claude Code modifies, but ONLY by adding new content. Existing content stays untouched.

## `config.py`

**What to add (at END of file):**

```python
# ═══════════════════════════════════════════════════════════════════════
# AGENT MODULE CONFIGURATION (Phase 1)
# Added: YYYY-MM-DD by Phase 1 implementation
# ═══════════════════════════════════════════════════════════════════════

# Entry criteria (DIFFERENT from scanner intentionally)
AGENT_MIN_SCORE = 60
AGENT_MXV_MAX = -100
AGENT_RUNUP_MIN = 30
AGENT_VOLUME_MIN = 100_000
AGENT_MARKET_CAP_MIN = 5_000_000
AGENT_MARKET_CAP_MAX = 2_000_000_000

# Exit criteria
AGENT_TP_PCT = 10
AGENT_SL_PCT = 10
AGENT_NO_TIME_LIMIT = True
AGENT_EOD_CLOSE_MIN_BEFORE = 5

# Position sizing
AGENT_POSITION_SIZE_USD = 1000

# Cold Start Mode
AGENT_COLD_START_ENABLED = True
AGENT_COLD_START_DAYS = 30
AGENT_COLD_START_MAX_CONCURRENT = 5
AGENT_COLD_START_MAX_DAILY = 10
AGENT_COLD_START_DAILY_LOSS_ALERT_USD = 200

# Modes
AGENT_DRY_RUN = True              # Switch to False at Milestone 10
AGENT_LIVE_PAPER = False          # Switch to True at Milestone 10
```

**What NOT to touch:** Any existing constant. Especially `TRADE_ENTRY_MIN_SCORE`, `MAX_HOLDING_DAYS`, `SL_THRESHOLD_PCT`.

## `sheets_config.json`

**What to add:** 8 new sheet IDs to current month + each subsequent month.

```json
{
  "2026-05": {
    // ... 9 existing scanner sheets ...
    "decision_log": "<id_to_be_filled>",
    "paper_portfolio": "<id_to_be_filled>",
    "score_analytics": "<id_to_be_filled>",
    "postmortems": "<id_to_be_filled>",
    "system_events": "<id_to_be_filled>",
    "pending_suggestions": "<id_to_be_filled>",
    "config_history": "<id_to_be_filled>",
    "borrow_data": "<id_to_be_filled>"
  }
}
```

## `dashboard.py`

**What to add:** New page conditionals after existing pages.

```python
# ... existing pages 1-8 ...

# Add agent sidebar option:
page = st.sidebar.radio("Page", [
    # ... existing options ...
    "🤖 Live Agent",
    "🧠 Score Brain",
])

# ... existing render conditionals ...

# Add agent renders:
elif page == "🤖 Live Agent":
    from agent.dashboard.live_agent import render_live_agent
    render_live_agent()
elif page == "🧠 Score Brain":
    from agent.dashboard.score_brain import render_score_brain
    render_score_brain()
```

**Alternative:** Import and call existing helpers, keep page logic in `agent/dashboard/` files.

## `requirements.txt`

**What to add:** New dependencies needed by agent module.

```
# Agent module dependencies (Phase 1)
alpaca-trade-api>=3.0.0       # If not already there for data_provider
cachetools>=5.3.0             # For SheetsCache TTL
jinja2>=3.1.0                 # For email templates
```

**Verify what's already there before adding** — Alpaca SDK might already be installed.

## `.gitignore`

**What to add (if not already there):**
```
# Agent module
agent/__pycache__/
agent/**/__pycache__/
.health_audit_sheet_id
```

---

# 🟢 EXISTING — EXTEND

These files Claude Code adds new functionality to.

## `health_audit.py`

**What to add:** 8 new agent-specific health checks.

```python
# Add new check functions:
def check_alpaca_paper_responsive(): ...
def check_alpaca_buying_power(): ...
def check_agent_decision_log_writable(): ...
def check_agent_no_stuck_positions(): ...
def check_agent_no_orphan_orders(): ...
def check_agent_score_matches_scanner(): ...
def check_agent_cold_start_limits(): ...
def check_agent_emergency_stop_status(): ...

# Add to ALL_CHECKS list:
ALL_CHECKS.extend([
    ("AGENT-1", "Alpaca Paper Responsive", check_alpaca_paper_responsive),
    # ... etc
])
```

## `.github/workflows/monthly_rotation.yml`

**What to add:** Steps to create the 8 new agent sheets when rotating to a new month.

## `docs/RidingHigh_Pro_PK_v2.md`

**What to add:** 10 new sections (one per milestone):

```
§A1: Agent Module Overview          (Milestone 1)
§A2: Agent Configuration            (Milestone 1, with §A1)
§A3: Agent Decision Logic           (Milestone 3)
§A4: Decision Log Schema            (Milestone 4)
§A5: Order Execution Architecture   (Milestone 5)
§A6: Postmortem Engine              (Milestone 6)
§A7: Score Analytics System         (Milestone 7)
§A8: Email System                   (Milestone 8)
§A9: Dashboard Extensions           (Milestone 9)
§A10: Production Operations         (Milestone 10)
```

Plus updates to existing sections:
- §15 (Schema Reference): Add 8 new sheets
- §17 (Glossary): Add new terms
- §21 (Workflows): Add 5 new workflows  
- §25 (Secrets): Add EMERGENCY_CLEAR_PASSWORD
- §36 (Cross-References): Add agent module file paths

**Increment version:** v2.0 → v2.1 → v2.2 → ... → v3.0 (Phase 1 complete)

## `OPEN_ISSUES.md`

**What to add:** Track issues discovered during agent build. Use #N{number} format consistent with existing.

---

# 🆕 NEW FILES — Agent Module

## Phase 1 Module Structure (~25 files)

### `agent/`

```
agent/
├── __init__.py                            (empty)
├── orchestrator.py                        ← Main entry per minute
│
├── trader/
│   ├── __init__.py
│   ├── trader.py                          ← Main Trader class
│   ├── decision_logic.py                  ← Decision tree
│   ├── score_calculator.py                ← Imports from formulas.py
│   └── position_manager.py                ← Position lifecycle
│
├── perception/
│   ├── __init__.py
│   ├── data_quality.py                    ← Validate signal quality
│   └── tradability.py                     ← Alpaca shortable check
│
├── execution/
│   ├── __init__.py
│   ├── alpaca_broker.py                   ← Order submission
│   ├── order_manager.py                   ← Retry logic
│   ├── reconciler.py                      ← Sheets vs Alpaca sync
│   └── position_monitor.py                ← Every-minute monitoring
│
├── analytics/
│   ├── __init__.py
│   ├── score_analytics.py                 ← Daily + weekly analysis
│   ├── postmortem_engine.py               ← Per-position analysis
│   ├── correlation_finder.py              ← Metric correlations
│   └── lesson_generator.py                ← Auto-generated insights
│
├── monitoring/
│   ├── __init__.py
│   ├── agent_health.py                    ← Adds to health_audit.py
│   ├── self_test.py                       ← Daily 08:00 Peru test
│   └── emergency_stop.py                  ← Halt all trading
│
├── logging/
│   ├── __init__.py
│   ├── decision_logger.py                 ← Write to decision_log
│   └── decision_id_generator.py           ← DEC-YYYY-MM-DD-NNNNN
│
├── notifications/
│   ├── __init__.py
│   ├── email_sender.py                    ← SMTP + templates
│   └── templates/
│       ├── daily_brief.html
│       ├── weekly_review.html
│       └── urgent_alert.html
│
├── dashboard/
│   ├── __init__.py
│   ├── live_agent.py                      ← Page 9 render logic
│   └── score_brain.py                     ← Page 10 render logic
│
├── utils/
│   ├── __init__.py
│   ├── sheets_cache.py                    ← Rate limit protection
│   └── decisions_io.py                    ← Read/write helpers
│
└── setup/
    ├── __init__.py
    └── create_agent_sheets.py             ← Programmatic sheet creation
```

**Total Python files: ~25**

---

# 🆕 NEW FILES — Workflows

5 new YAML files in `.github/workflows/`:

## 1. `agent_minute.yml`

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
          DATA_PROVIDER: 'alpaca'
          EMERGENCY_CLEAR_PASSWORD: ${{ secrets.EMERGENCY_CLEAR_PASSWORD }}
```

## 2. `agent_morning_test.yml`

```yaml
name: Agent — Morning Self-Test

on:
  schedule:
    - cron: '0 13 * * 1-5'        # 13:00 UTC = 08:00 Peru

jobs:
  self-test:
    # ... runs agent.monitoring.self_test
```

## 3. `agent_daily_email.yml`

```yaml
name: Agent — Daily Email Brief

on:
  schedule:
    - cron: '30 21 * * 1-5'       # 21:30 UTC = 16:30 Peru

jobs:
  daily-email:
    # ... runs agent.notifications email_sender daily
```

## 4. `agent_weekly_review.yml` ⚠️ SATURDAY

```yaml
name: Agent — Weekly Review

on:
  schedule:
    - cron: '0 23 * * 6'          # 23:00 UTC Saturday = 18:00 Peru Saturday

jobs:
  weekly-review:
    # ... runs Score Analytics weekly + email
```

## 5. `agent_health_check.yml`

```yaml
name: Agent — Health Check

on:
  schedule:
    - cron: '*/5 13-20 * * 1-5'   # every 5 min, market hours

jobs:
  health-check:
    # ... runs agent.monitoring.agent_health
```

---

# 🆕 NEW FILES — Google Sheets

8 new sheets in current month's Drive folder.

| Sheet Name | Columns | Purpose |
|------------|---------|---------|
| `decision_log` | 40 | Every signal evaluated, full reasoning |
| `paper_portfolio` | 22 | Mirror of Alpaca paper positions |
| `score_analytics` | 25 | Daily Score Analytics observations |
| `postmortems` | 17 | Per-position outcome analysis |
| `system_events` | 7 | System events log |
| `pending_suggestions` | 14 | Score Analytics suggestions awaiting user |
| `config_history` | 10 | Configuration change audit trail |
| `borrow_data` | 9 | HTB/borrow info cache |

**Headers:** See `01_FINAL-SPEC_v2.0.md` Section 11.2-11.9 for complete column lists.

**Created by:** `agent/setup/create_agent_sheets.py` (Milestone 2)

---

# 🆕 NEW FILES — Tests

## Unit Tests

```
tests/agent/unit/
├── test_score_calculator.py        ← Tests calculate_agent_score()
├── test_decision_logic.py          ← Tests entry decision tree
├── test_data_quality.py            ← Tests validation rules
├── test_tradability.py             ← Tests tradability checks
├── test_decision_logger.py         ← Tests sheet writes
├── test_decision_id_generator.py   ← Tests ID format
├── test_alpaca_broker.py           ← Mocks Alpaca, tests order logic
├── test_order_manager.py           ← Tests retry logic
├── test_position_manager.py        ← Tests EOD close, monitoring
├── test_postmortem_engine.py       ← Tests lesson generation
├── test_score_analytics.py         ← Tests aggregation
├── test_correlation_finder.py      ← Tests math
├── test_email_sender.py            ← Tests templates
├── test_sheets_cache.py            ← Tests TTL + batching
├── test_emergency_stop.py          ← Tests trigger + clear
└── test_self_test.py               ← Tests morning checks
```

## Integration Tests

```
tests/agent/integration/
├── test_scanner_agent_match.py    ← 🚨 CRITICAL — score parity test
├── test_alpaca_paper_real.py      ← Real Alpaca paper API
├── test_full_decision_flow.py     ← Signal → decision → log → execute
├── test_monthly_rotation.py       ← Month-end rotation works
└── test_emergency_stop_e2e.py     ← End-to-end stop test
```

---

# 📋 GitHub Secrets Required

Existing secrets (already configured):

| Secret | Used By | Status |
|--------|---------|--------|
| `GOOGLE_CREDENTIALS_JSON` | Scanner + Agent | ✅ Already exists |
| `GOOGLE_OAUTH_TOKEN_JSON` | Scanner | ✅ Already exists |
| `ALPACA_API_KEY_ID` | Scanner (data) + Agent (orders) | ✅ Already exists |
| `ALPACA_SECRET_KEY` | Scanner (data) + Agent (orders) | ✅ Already exists |
| `GMAIL_USER` | health_audit + Agent emails | ✅ Already exists |
| `GMAIL_APP_PASS` | health_audit + Agent emails | ✅ Already exists |
| `REPORT_TO` | health_audit + Agent emails | ✅ Already exists |

New secret to add:

| Secret | Used By | Status |
|--------|---------|--------|
| `EMERGENCY_CLEAR_PASSWORD` | Agent emergency stop | 🆕 Add manually |

**That's the only new secret. Setup time: ~5 minutes.**

---

# 🎯 Quick-Look Summary

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1 — File Operations Summary                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🔵 Read 14 existing files (don't modify)                    │
│ 🟡 Add to 5 existing files (additive only)                  │
│ 🟢 Extend 4 existing files (new functionality)              │
│ 🆕 Create ~25 new Python files in agent/                    │
│ 🆕 Create 5 new workflow YAML files                         │
│ 🆕 Create 8 new Google Sheets                               │
│ 🆕 Create ~15 new test files                                │
│ 🆕 Add 1 new GitHub secret                                  │
│                                                             │
│ Total touched files: ~75 (mostly new)                       │
│ Total existing files modified: 9                            │
│ Total existing files left alone: ~60                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 🛡️ The "Don't Touch" List

If Claude Code modifies any of these files' BEHAVIOR, that's a violation:

```
🚫 auto_scanner.py                    Scanner is sacred
🚫 post_analysis_collector.py          Scanner is sacred
🚫 formulas.py                         Single source of truth
🚫 sheets_manager.py                   Scanner is sacred
🚫 backfill_ohlc.py                    Scanner is sacred
🚫 enrich_post_analysis.py             Scanner is sacred
🚫 code_auditor.py                     Scanner is sacred
🚫 .github/workflows/auto_scan.yml     Already in production
🚫 .github/workflows/post_analysis.yml Already in production
🚫 .github/workflows/backup.yml        Already in production
🚫 .github/workflows/code_audit.yml    Already in production
```

The only exception: if a change is REQUIRED to add functionality for the agent (e.g., adding agent sheets to monthly_rotation.yml). In that case:
1. ASK the user first
2. Document why in OPEN_ISSUES.md
3. Make minimal change
4. Test that scanner still works

---

# ✅ Pre-Milestone-1 Checklist

Before starting any code:

- [ ] All 4 spec documents read
- [ ] PK_v2 read fully
- [ ] User has confirmed setup
- [ ] EMERGENCY_CLEAR_PASSWORD added to secrets
- [ ] `python health_audit.py --local` shows all CRITICAL passing
- [ ] Repo is at clean `git status`
- [ ] On `main` branch, up to date

If all checked: announce Milestone 1 and begin.

---

**End of Files Checklist v2.0**

*Use alongside `02_CLAUDE-CODE-PROMPT_v2.0.md` when implementing.*
