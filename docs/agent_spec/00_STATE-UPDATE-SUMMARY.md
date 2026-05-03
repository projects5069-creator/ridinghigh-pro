# 📋 RidingHigh System — State Update Summary

**Date:** 2026-05-03
**Author:** Claude (for עמיחי)
**Purpose:** Bridge document between original spec (2026-04-30) and current reality (2026-05-03)
**Status:** Read this FIRST before reading the v2.0 spec

---

## 🎯 TL;DR — In One Paragraph

The Scanner has matured significantly since the original Phase 1 spec was written. Key changes: SL unified to +10% (was 7%), `TRADE_ENTRY_MIN_SCORE=70`, Alpaca is already the production data provider (not yfinance), 7 workflows are running (not 2), `RidingHigh_Pro_PK_v2.md` is now the authoritative system documentation, and 18 health checks run 3×/day with email alerts. The Agent module being built sits ON TOP of this stable foundation — it does NOT rebuild what already exists. **The Agent will be intentionally different from the Scanner: Min Score 60 (vs 70), and no time limit on positions (vs 5 days).**

---

## 📊 What Changed — Side-by-Side

### Configuration & Trading Rules

| Item | Original Spec (2026-04-30) | Current Reality (2026-05-03) | Decision for Agent |
|------|----------------------------|------------------------------|---------------------|
| **TP** | -10% | -10% | **-10%** ✅ |
| **SL** | +7% | +10% (unified Issue #1) | **+10%** ✅ |
| **Min Score** | 60 | 70 (`TRADE_ENTRY_MIN_SCORE`) | **60** (Agent more liberal) |
| **Position size** | $1,000 | $1,000 | **$1,000** ✅ |
| **Max holding** | "no limit" | 5 days (`MAX_HOLDING_DAYS=5`) | **No limit** (TP/SL/EOD only) |
| **MxV threshold** | < -100 | not formalized in scanner | **< -100** ✅ |
| **RunUp threshold** | > 30% | not formalized in scanner | **> 30%** ✅ |

### Infrastructure

| Item | Original Spec | Current Reality |
|------|---------------|-----------------|
| **Data Provider** | yfinance | **Alpaca** (`DATA_PROVIDER=alpaca`) — already in production |
| **Workflows** | 2 (auto_scan, post_analysis) | **7** (added: health_audit, backup, monthly_rotation, prepare_next_month, code_audit) |
| **Sheets** | 7 monthly | **9** (added: ticker_follow_up, RidingHigh-Health-Audit) |
| **Health Checks** | none | **18 checks running 3×/day** with email alerts |
| **Repo URL** | `Ambroseius/-ridinghigh-pro` | `projects5069-creator/ridinghigh-pro` ⚠️ |
| **Service Account** | `ridinghigh-sheets@...` | Same ✅ |
| **Streamlit** | `ridinghigh-pro.streamlit.app` | `ridinghigh-pro-v2.streamlit.app` ⚠️ |
| **PK Document** | none | **`docs/RidingHigh_Pro_PK_v2.md`** — Source of truth, 36 sections |

### What Stayed the Same

| Item | Status |
|------|--------|
| Score v2 formula (weights, caps) | ✅ Identical |
| 28 metrics inventory | ✅ Identical |
| Trade simulation logic | ✅ Identical (TP/SL/timeout) |
| Position size $1,000 | ✅ Identical |
| Saturday 18:00 Peru weekly review | ✅ Confirmed |
| Cold Start Mode (30 days) | ✅ Plan unchanged |
| 12-phase roadmap | ✅ Unchanged |
| Unified architecture (one repo, two modules) | ✅ Confirmed |

---

## 🆕 New Components You Should Know About

These exist in the current codebase and the Agent will INTERACT with them (not replace):

### 1. `data_provider.py` — Abstraction Layer
```
Already abstracts Alpaca / yfinance / IEX behind a unified interface.
The Agent should use this, not call Alpaca directly for market data.
```

### 2. `health_audit.py` — 18 Automated Checks
```
Runs at 06:00, 12:00, 22:00 Peru daily.
Sends email alerts on CRITICAL issues.
Checks: code integrity, data freshness, data quality, config consistency, 
        repo health, sync.
The Agent's monitoring layer should integrate with this.
```

### 3. `formulas.py` — Single Source of Truth
```
ALL metric calculations live here. Importing from anywhere else is a bug.
The Agent's score_calculator.py MUST use formulas.calculate_score().
NOT a re-implementation. Direct import.
```

### 4. `config.py` — Centralized Configuration
```
All thresholds, weights, caps live here.
The Agent should READ from this for scanner-related values.
The Agent will ADD its own constants (AGENT_MIN_SCORE=60, etc.) WITHOUT 
changing existing constants.
```

### 5. `docs/RidingHigh_Pro_PK_v2.md` — Authoritative Documentation
```
36 sections, the master reference for the entire system.
Has an "Anti-Drift Maintenance Contract" — any change to the codebase 
must update PK_v2.

The Agent build must update PK_v2 with new sections covering:
- Agent module architecture
- New sheets (8 agent sheets)
- New workflows (5 agent workflows)  
- New configuration constants
```

### 6. `OPEN_ISSUES.md` — Issue Tracker
```
Living document tracking all open/closed issues.
Format: #N1, #N2, ... for newly discovered issues.
The Agent build will add issues as discovered, close them when fixed.
```

---

## 🔥 Critical Rules That Apply NOW

These weren't in the original spec but are critical:

### Rule 1: Anti-Drift Contract (from PK_v2 §35)
> *"Whenever a session adds, modifies, or removes Python files, workflows, sheets, constants, metrics, formulas, weights, health checks, email alerts, schedules, phases, KPIs, or known issues — PK_v2 MUST be updated before commit."*

**Translation for Claude Code:** Every Agent milestone MUST end with a PK_v2 update.

### Rule 2: formulas.py Is Sacred
> *"Any metric calculation lives in formulas.py or it is a bug."*

**Translation:** The Agent's score_calculator MUST import from formulas, not re-implement.

### Rule 3: Health Checks Already Catch Bugs
> *"check_05, check_16, check_17, check_18 already monitor scanner health."*

**Translation:** Don't re-build health monitoring. EXTEND health_audit.py with agent-specific checks.

### Rule 4: data_provider Is the Interface
> *"Don't call Alpaca/yfinance directly — use data_provider abstraction."*

**Translation:** The Agent's broker module is for ORDERS only. Market data goes through data_provider.

---

## 🛡️ What's Stable Now (Don't Touch)

Before starting Agent build, confirm scanner stability:

✅ **18 health checks passing** (or with known false positives only)
✅ **post_analysis populating daily** (>0 rows after 16:00 Peru on trading days)
✅ **timeline_live populating** (>5,000 rows on trading days)
✅ **Alpaca paper credentials working** (used by scanner already)
✅ **Email alerts working** (you receive health_audit emails)
✅ **PK_v2 reflects current reality** (no drift)

If any of these is broken — fix BEFORE starting Agent build.

---

## 🎯 What the Agent Adds (Phase 1)

Net new components:

### New Code
- `agent/` directory (~15 new files)
- 2 new Streamlit pages (9, 10)
- 5 new workflows

### New Data
- 8 new Google Sheets (decision_log, paper_portfolio, etc.)
- New rows added daily (~50-200 decisions/day)

### New Behavior
- Automatic order submission to Alpaca Paper
- Position monitoring every minute
- Decision logging (every signal evaluated)
- Daily Score Analytics (16:30 Peru)
- Weekly Score Analytics (Saturday 18:00 Peru)
- 3 email types (daily / weekly / urgent)

### New Configuration
```python
# To be added to config.py:

# Agent-specific constants (do NOT modify existing scanner constants)
AGENT_MIN_SCORE = 60               # Different from TRADE_ENTRY_MIN_SCORE=70
AGENT_MXV_MAX = -100               # Entry filter
AGENT_RUNUP_MIN = 30               # Entry filter
AGENT_TP_PCT = 10                  # Same as scanner TP
AGENT_SL_PCT = 10                  # Same as scanner SL (unified)
AGENT_NO_TIME_LIMIT = True         # Different from scanner's 5-day limit
AGENT_POSITION_SIZE_USD = 1000     # Same
AGENT_EOD_CLOSE_MIN_BEFORE = 5     # Close 5 min before market close
AGENT_COLD_START_DAYS = 30
AGENT_COLD_START_MAX_CONCURRENT = 5
AGENT_COLD_START_MAX_DAILY = 10
AGENT_COLD_START_DAILY_LOSS_ALERT = 200  # USD
```

---

## ⚠️ Important Distinctions

### The Agent Is NOT the Scanner

| Question | Scanner | Agent |
|----------|---------|-------|
| What does it do? | Detects signals | Acts on signals |
| Min Score for trades | 70 | **60** |
| Max position duration | 5 days | **No limit** |
| Real broker integration | No (simulation only) | **Yes (Alpaca Paper)** |
| Decisions logged | Score-only | **Full reasoning, 40 columns** |
| Schedule | Every minute | Every minute (different code) |
| Output | Sheets | Sheets + Alpaca orders + emails |

### Why Min Score 60 (Not 70)?

The scanner's `TRADE_ENTRY_MIN_SCORE=70` is for SIMULATION research (which signals to track for 5 days). The Agent operates in REAL paper trading and benefits from more data points (more trades = faster learning). Score 60-70 might be lower-EV but the Agent's job is to LEARN — not just confirm what 70+ does.

The Score Analytics weekly report will analyze whether 60-70 trades are worth keeping or should be filtered out. Then the user decides via the suggestions flow.

### Why No Time Limit?

The Scanner's 5-day limit is for simulation accounting (otherwise tracking is unbounded). The Agent in real Alpaca Paper has no such constraint — TP/SL/EOD are clean exits, time-based exits are arbitrary. Phase 5 will add smart exit strategies; Phase 1 keeps it simple.

---

## 📅 What Comes Next

After you read this summary:

1. **Read FINAL-SPEC v2.0** — The full updated specification
2. **Read Claude-Code-PROMPT v2.0** — Implementation instructions
3. **Read FILES-CHECKLIST** — Exact files to read/create/modify
4. **(Optional) Re-read SCANNER-REFERENCE** — Same as before, validated against current code

Then:
- Setup: ~30 min (mostly already done — Alpaca credentials already exist for scanner!)
- Implementation: 10 milestones over 4-6 weeks (with you reviewing each)

---

## 🤝 The Promise

The Agent build will:

✅ Not modify any scanner code
✅ Not change scanner behavior
✅ Reuse existing infrastructure (Alpaca credentials, service account, Drive folder)
✅ Update PK_v2 at every milestone
✅ Pass `test_agent_matches_scanner` before any trading
✅ Run in DRY_RUN mode before LIVE_PAPER
✅ Stop at every milestone for your review

The Agent build will NOT:

❌ Touch `auto_scanner.py`, `post_analysis_collector.py`, `formulas.py`, or `config.py` beyond ADDITIVE changes
❌ Use real money
❌ Skip the Cold Start Mode
❌ Auto-modify scoring formula or weights

---

## 📞 Questions Before Proceeding?

If anything in this summary is unclear or doesn't match your expectations — **ask now**, before reading the v2.0 spec. Better to align understanding upfront than fix it during implementation.

Common questions to consider:

- ❓ Is the scanner truly stable now? (run `python health_audit.py --local` to verify)
- ❓ Is Alpaca paper trading working? (check `python -c "from agent.execution.alpaca_broker import test_connection; test_connection()"` — wait, this doesn't exist yet, check via Alpaca dashboard)
- ❓ Are you ready for ~4-6 weeks of incremental work?
- ❓ Do you want to handle Score Analytics suggestions weekly? (Saturday emails)
- ❓ Are you OK with paper-only trading for at least 6 months?

---

**End of State Update Summary**

*Read FINAL-SPEC_v2.0 next.*
