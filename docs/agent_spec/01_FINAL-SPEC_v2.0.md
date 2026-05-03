# 🎯 RidingHigh System — Final Specification v2.0

**Date:** 2026-05-03
**Author:** Designed for עמיחי (Amihay Levy)
**Status:** Approved for Phase 1 Implementation
**Replaces:** v1.0 (2026-04-30) — superseded due to scanner state changes
**Architecture:** Unified system, single repo, two complementary modules

---

## 🆕 v2.0 Changes from v1.0

This version updates the original spec to match current scanner state:

| Section | Change |
|---------|--------|
| Trading rules | SL +7% → **+10%**, no time limit confirmed |
| Min Score for entry | 60 (Agent), distinct from scanner's 70 |
| Data Provider | Alpaca confirmed as production (was yfinance in v1.0) |
| Workflows | 7 existing scanner workflows acknowledged (was 2) |
| Sheets | 9 existing scanner sheets acknowledged (was 7) |
| PK_v2 integration | Added Anti-Drift Contract obligations |
| Health Checks | Extends existing health_audit.py instead of building from scratch |
| Repo URL | `projects5069-creator/ridinghigh-pro` (not Ambroseius) |
| Streamlit URL | `ridinghigh-pro-v2.streamlit.app` (was v1) |

---

## 📑 Table of Contents

1. [Vision & Core Principles](#1-vision--core-principles)
2. [Unified Architecture](#2-unified-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Phase 1: Detailed Specification](#4-phase-1-detailed-specification)
5. [The Trader — Phase 1 Agent](#5-the-trader--phase-1-agent)
6. [Score Analytics System](#6-score-analytics-system)
7. [Decision Logger](#7-decision-logger)
8. [Critical Infrastructure](#8-critical-infrastructure)
9. [Email & Notifications](#9-email--notifications)
10. [Streamlit Dashboard Extension](#10-streamlit-dashboard-extension)
11. [Google Sheets — New Agent Sheets](#11-google-sheets--new-agent-sheets)
12. [Setup Manual](#12-setup-manual)
13. [Phase 1 Milestones](#13-phase-1-milestones)
14. [Future Phases Roadmap](#14-future-phases-roadmap)
15. [Risks & Mitigations](#15-risks--mitigations)
16. [Code Conventions](#16-code-conventions)
17. [PK_v2 Integration & Anti-Drift](#17-pk_v2-integration--anti-drift)
18. [Glossary](#18-glossary)

---

# 1. Vision & Core Principles

## 1.1 The Mission

RidingHigh System is a **unified trading platform** combining:

1. **RidingHigh Pro Scanner** (existing, mature) — Active in data collection
2. **RidingHigh Agent** (new, Phase 1) — Active in execution

These two modules form a **feedback loop**:

```
Scanner collects data
    ↓
Agent uses data to make decisions
    ↓
Agent observes what's missing or could be better
    ↓
User updates Scanner with new metrics
    ↓
Scanner now collects improved data
    ↓
(loop continues)
```

## 1.2 Three Core Goals

### **Goal 1: Eliminate Time Constraint**
> *"I only enter near market close. I miss stocks that met conditions earlier in the day."*

**Solution:** Agent monitors signals every minute, 24/5.

### **Goal 2: Validate and Improve the Strategy**
> *"I trade based on MxV but I don't have proof of what works."*

**Solution:** Score Analytics continuously analyzes which metrics work and proposes improvements (Score Analytics observes, user approves).

### **Goal 3: Reduce Catastrophic Losses**
> *"Sometimes I exit at -7% and the stock continues +30-100%."*

**Solution:** Future agents (Phase 2+) will improve entry timing and exit logic. Phase 1 establishes the foundation.

## 1.3 Seven Guiding Principles

1. **Human-AI Partnership** — Agent executes trades automatically. Human approves rule changes only.
2. **Iterative Building** — Phase 1 = ONE trading agent. Each phase adds ONE more.
3. **Full Transparency** — Every decision has complete reasoning logged.
4. **Quality Over Speed** — No deadlines. Build correctly.
5. **Always Supervised on Rules** — Trades autonomous. Rule changes require human approval forever.
6. **Default to Skip** — When uncertain or unanswered: do nothing.
7. **Data Drives Decisions** — Score Analytics observes, suggests, but never changes anything alone.

## 1.4 The Agent Is NOT the Scanner

This is critical. The Agent is **intentionally different**:

| Aspect | Scanner | Agent |
|--------|---------|-------|
| **Purpose** | Detect signals + simulate | Execute on Alpaca Paper |
| **Min Score** | 70 (simulation entry) | **60** (more permissive — for learning) |
| **Position duration** | 5-day limit (simulation) | **No limit** (TP/SL/EOD only) |
| **Output** | Sheets data | Sheets + Alpaca orders + emails |
| **Schedule** | Every min, market hours | Every min, market hours (separate code) |

---

# 2. Unified Architecture

## 2.1 The Big Picture

```
                    ridinghigh-pro-v2.streamlit.app
                              │
                ┌─────────────┴─────────────┐
                │                           │
        Pages 1-8 (Scanner)         Pages 9-10 (Agent)
                │                           │
        ┌───────┴───────┐           ┌──────┴──────┐
        │               │           │             │
   Scanner Logic   Scanner Sheets   Agent Logic  Agent Sheets
   (existing)      (existing 9)     (NEW)        (NEW 8)
        │               │           │             │
        └───────┬───────┘           └──────┬──────┘
                │                          │
                └──────────┬───────────────┘
                           │
                Same Google Drive folder
                Same Service Account
                Same GitHub repo
                Same Streamlit app
                Same Alpaca credentials
```

## 2.2 Why One System

The two modules are interdependent:

| Need | Solution |
|------|----------|
| Agent needs Scanner data | Reads from existing sheets |
| Agent identifies missing metrics | User updates Scanner code |
| Scanner improvements help Agent | Same repo = atomic deploys |
| User reviews both | Single dashboard |
| Shared utilities | Most already in `formulas.py`, `config.py`, etc. |

## 2.3 Tech Stack

| Component | Technology | Status |
|-----------|------------|--------|
| Code | Python 3.11+ | Both modules |
| Storage | Google Sheets | Both modules |
| Compute | GitHub Actions | Both modules |
| Dashboard | Streamlit Cloud | Both modules |
| Broker | Alpaca Paper | Agent only (scanner uses for data) |
| Market Data | Alpaca (via data_provider) | Both modules |
| Notifications | Gmail SMTP | Agent + health_audit |
| **Total Cost** | | **$0/month** |

## 2.4 Timezone

```
Peru = UTC-5, NO DST, year-round
Market hours (NYSE):
   08:30 Peru = 13:30 UTC = 09:30 ET (open)
   15:00 Peru = 20:00 UTC = 16:00 ET (close)

Saturday weekly review = 18:00 Peru = 23:00 UTC
   (Saturday so user can work on insights Sunday)
```

---

# 3. Repository Structure

## 3.1 Current State (already exists)

```
📦 projects5069-creator/ridinghigh-pro/
├── auto_scanner.py
├── post_analysis_collector.py
├── formulas.py                  ← Single source of truth for metrics
├── config.py                    ← All thresholds, weights
├── data_provider.py             ← Alpaca/yfinance/IEX abstraction
├── sheets_manager.py
├── dashboard.py                 ← Single-file Streamlit
├── health_audit.py              ← 18 checks, 3×/day
├── enrich_post_analysis.py
├── backfill_ohlc.py
├── code_auditor.py
├── utils.py
├── docs/
│   └── RidingHigh_Pro_PK_v2.md  ← Authoritative documentation
├── OPEN_ISSUES.md               ← Issue tracker
├── tests/                       ← Existing test suite
├── .github/workflows/
│   ├── auto_scan.yml
│   ├── post_analysis.yml
│   ├── health_audit.yml
│   ├── backup.yml
│   ├── monthly_rotation.yml
│   ├── prepare_next_month.yml
│   └── code_audit.yml
├── requirements.txt
└── ... other files
```

## 3.2 Target State (after Phase 1)

```
📦 projects5069-creator/ridinghigh-pro/
│
├── 🟦 EXISTING (DO NOT MODIFY behavior)
│   ├── auto_scanner.py
│   ├── post_analysis_collector.py
│   ├── formulas.py                  ← Agent imports from here
│   ├── config.py                    ← Agent ADDS constants here
│   ├── data_provider.py             ← Agent uses for market data
│   ├── sheets_manager.py
│   ├── dashboard.py                 ← New pages added as separate files
│   ├── health_audit.py              ← Agent EXTENDS with new checks
│   ├── (... all other existing files)
│   ├── docs/
│   │   └── RidingHigh_Pro_PK_v2.md  ← Updated each milestone
│   └── .github/workflows/           ← 5 new agent workflows added
│
└── 🟩 NEW — Agent Module
    ├── agent/
    │   ├── __init__.py
    │   ├── orchestrator.py
    │   ├── trader/
    │   │   ├── __init__.py
    │   │   ├── trader.py
    │   │   ├── decision_logic.py
    │   │   ├── score_calculator.py     ← Imports from formulas.py
    │   │   └── position_manager.py
    │   ├── perception/
    │   │   ├── __init__.py
    │   │   ├── data_quality.py
    │   │   └── tradability.py
    │   ├── execution/
    │   │   ├── __init__.py
    │   │   ├── alpaca_broker.py        ← ORDERS only (data via data_provider)
    │   │   ├── order_manager.py
    │   │   └── reconciler.py
    │   ├── analytics/
    │   │   ├── __init__.py
    │   │   ├── score_analytics.py
    │   │   ├── postmortem_engine.py
    │   │   └── correlation_finder.py
    │   ├── monitoring/
    │   │   ├── __init__.py
    │   │   ├── agent_health.py         ← Adds checks to health_audit
    │   │   ├── self_test.py
    │   │   └── emergency_stop.py
    │   ├── logging/
    │   │   ├── __init__.py
    │   │   ├── decision_logger.py
    │   │   └── decision_id_generator.py
    │   └── notifications/
    │       ├── __init__.py
    │       ├── email_sender.py
    │       └── templates/
    │           ├── daily_brief.html
    │           ├── weekly_review.html
    │           └── urgent_alert.html
    │
    ├── dashboard_pages/                ← NEW pages added as separate files
    │   ├── 9_Live_Agent.py
    │   └── 10_Score_Brain.py
    │
    ├── .github/workflows/
    │   ├── agent_minute.yml
    │   ├── agent_morning_test.yml
    │   ├── agent_daily_email.yml
    │   ├── agent_weekly_review.yml     ← Saturday 18:00 Peru
    │   └── agent_health_check.yml
    │
    └── tests/agent/                    ← Agent-specific tests
        ├── unit/
        │   ├── test_score_calculator.py
        │   ├── test_decision_logic.py
        │   └── ...
        └── integration/
            └── test_scanner_agent_match.py  ← CRITICAL test
```

## 3.3 Why No Migration?

The original v1.0 spec proposed moving all scanner files to `scanner/` subdirectory. **v2.0 abandons this plan** because:

1. The scanner is in production with 7 active workflows
2. Moving files breaks all workflow paths simultaneously
3. The scanner team (you) has invested heavily in stability (PK_v2, health checks, 18 monitors)
4. Risk/reward unfavorable: high risk of breaking scanner, low benefit (just organization)

**Instead:** The Agent module sits in a NEW `agent/` subdirectory alongside existing scanner files. No moves, no breaks.

---

# 4. Phase 1: Detailed Specification

## 4.1 What Phase 1 Delivers

By end of Phase 1:

1. ✅ `agent/` directory with all sub-modules
2. ✅ The Trader (single agent) operating 24/5 on Alpaca Paper
3. ✅ Decision Logger capturing every signal
4. ✅ Score Analytics running daily + weekly (Saturday 18:00)
5. ✅ Email notifications (daily + weekly + urgent)
6. ✅ Dashboard pages 9-10 deployed
7. ✅ 5 new GitHub Actions workflows
8. ✅ Cold Start Mode (30-day cautious operation)
9. ✅ Emergency Stop Button working
10. ✅ Daily Self-Test passing
11. ✅ PK_v2 updated with Agent module documentation

## 4.2 Phase 1 Success Criteria

Phase 1 is **complete** when:

- [ ] At least 50 paper trades executed
- [ ] All trades have full decision_log entries
- [ ] Postmortems run automatically on closed positions
- [ ] Daily emails reliable (7 consecutive days)
- [ ] Weekly Score Analytics report generated (Saturday)
- [ ] Dashboard pages 9-10 live
- [ ] System runs 7 consecutive days without manual intervention
- [ ] Emergency Stop tested
- [ ] Self-Test passes daily for 5 days
- [ ] User has reviewed at least one Score Analytics suggestion
- [ ] PK_v2 reflects new Agent module
- [ ] All Agent-related health checks passing

## 4.3 What Comes After Phase 1

After Phase 1 completion, **30-day Data-Only Phase**:

- Trader continues operating
- Score Analytics observes (still no auto-changes)
- Goal: accumulate ~200-500 trades for Phase 2 analysis

After 30 days:
- Cold Start Mode disables
- Phase 2 (full Entry Score Optimizer) begins
- User starts approving suggestions

---

# 5. The Trader — Phase 1 Agent

## 5.1 Role

Single decision-maker in Phase 1.

**Responsibilities:**
- Read signals from scanner data
- Evaluate against entry criteria
- Execute trades via Alpaca Paper
- Manage open positions (TP/SL monitoring)
- Log every decision

## 5.2 Trading Rules — Final Version

### **Entry Criteria (ALL must pass):**

```python
# To be added to config.py:

# Agent-specific entry criteria (distinct from scanner)
AGENT_ENTRY_CRITERIA = {
    "score_min":         60,            # More liberal than scanner (70)
    "mxv_max":           -100,          # Must be very negative
    "runup_min":         30,            # %, intraday rise
    "volume_min":        100_000,       # Liquidity floor
    "market_cap_min":    5_000_000,     # $5M minimum
    "market_cap_max":    2_000_000_000, # $2B maximum
    "shortable":         True,          # Alpaca shortable
}
```

**Why Score 60 (not 70 like scanner):**
- Scanner's 70 is for SIMULATION research (track for 5 days)
- Agent operates in REAL paper trading and benefits from MORE data
- Score Analytics will analyze if 60-70 trades are worth keeping
- User decides via weekly suggestions flow

### **Exit Criteria:**

```python
AGENT_EXIT_CRITERIA = {
    "take_profit_pct":     -10,    # Same as scanner
    "stop_loss_pct":       +10,    # Same as scanner (after Issue #1 unification)
    "no_time_limit":       True,   # ⚠️ DIFFERENT from scanner's 5-day limit
    "eod_close_min_before": 5,     # Close 5 min before market close
}
```

**Why no time limit (vs scanner's 5 days):**
- Scanner's 5-day limit is for simulation accounting
- Real Alpaca Paper has no such constraint
- TP/SL/EOD are clean exits
- Time-based exits are arbitrary
- Phase 5 will add smart exit strategies

### **Position Size:**

```python
AGENT_POSITION_SIZE_USD = 1000  # Same as scanner
```

## 5.3 Decision Flow

```
1. SIGNAL ARRIVES
   Scanner detected: AKAN, Score 67, MxV -845, RunUp 32%
        ↓
2. PRE-FILTER (fast checks)
   ✓ Score >= 60? Yes
   ✓ MxV <= -100? Yes (-845)
   ✓ RunUp >= 30%? Yes (32%)
   ✓ Volume >= 100K? Yes
   ✓ MarketCap in range? Yes
        ↓
3. TRADABILITY (Alpaca check)
   ✓ Shortable? Yes
   ✓ Borrow available? Yes (12.5% fee)
        ↓
4. SAFETY (account checks)
   ✓ No existing position on AKAN? Yes
   ✓ Account has buying power? Yes
   ✓ Within Cold Start limits? Yes (3/5 today)
        ↓
5. CALCULATE POSITION
   Position: $1,000
   Quantity: floor(1000 / 4.32) = 231 shares
   TP price: 4.32 × 0.90 = 3.89
   SL price: 4.32 × 1.10 = 4.75
        ↓
6. SUBMIT ORDERS (with retries)
   Entry: limit short 231 @ $4.32
   TP: limit buy 231 @ $3.89 (GTC)
   SL: stop_limit buy 231 @ $4.75 (GTC)
        ↓
7. LOG DECISION
   Write 40-column row to decision_log
        ↓
8. MONITOR (every minute)
   - Check current price
   - Verify TP/SL still active in Alpaca
   - Update paper_portfolio
        ↓
9. POSITION CLOSES
   Either: TP hit (WIN), SL hit (LOSS), or EOD close
   Calculate final PnL
   Trigger Postmortem Engine
   Update statistics
```

## 5.4 Cold Start Mode (First 30 Days)

```python
AGENT_COLD_START = {
    "enabled":                  True,    # First 30 days
    "max_concurrent_positions": 5,
    "max_daily_trades":         10,
    "skip_propose_changes":     True,    # No formula changes during cold start
    "extra_logging":            True,
    "alert_on_daily_loss_above": 200,    # USD
}
```

After 30 days of clean operation, Cold Start Mode disables automatically.

## 5.5 Position Monitoring

```
Every minute during market hours:
    For each open position:
        1. Get current price (via data_provider)
        2. Verify TP order still active in Alpaca
        3. Verify SL order still active in Alpaca
        4. If both missing → ERROR, alert user
        5. Update paper_portfolio sheet

5 minutes before market close (14:55 Peru):
    For each open position:
        Submit market buy order (close short)
        Cancel TP and SL orders
        Mark as EOD_CLOSE in paper_portfolio
        Trigger postmortem

When TP hit (auto via Alpaca):
    Detect on next monitoring cycle
    Mark as TP_HIT (WIN)
    Trigger postmortem

When SL hit (auto via Alpaca):
    Mark as SL_HIT (LOSS)
    Trigger postmortem
```

**No max-hold check.** Positions ride until TP/SL/EOD.

---

# 6. Score Analytics System

## 6.1 Role

**Observational analysis layer** examining:
- Which metrics correlate with winning trades
- Which weights might need adjustment
- Which metrics are missing that could add value

**Phase 1 = OBSERVATIONAL ONLY.** Suggests but never modifies.

## 6.2 Daily Analysis (16:30 Peru, every trading day)

After post_analysis runs, aggregate today's closed positions.

For each closed position:
```python
{
    "ticker": "AKAN",
    "outcome": "WIN",
    "pnl_pct": +10.2,
    "score_at_entry": 67,     # Note: agent uses 60+ minimum
    "metrics_at_entry": {...all 28 metrics...},
    "duration_hours": 2.4,
    "exit_reason": "TP_HIT",
}
```

Store in `score_analytics` sheet (Section 11.4).

## 6.3 Weekly Analysis (Saturday 18:00 Peru)

Aggregate the week's data:

### **A. Win Rate by Score Range**
```
Score 60-70: 65% (n=23)  ⭐ AGENT-SPECIFIC TIER
Score 70-80: 78% (n=45)  ⭐ Sweet spot
Score 80-90: 70% (n=18)
Score 90+:   55% (n=4)
```

This is unique value of Agent: data on 60-70 range that scanner doesn't simulate.

### **B. Win Rate by Each Metric**
### **C. Metric Correlation with Outcome**
### **D. Missing Metrics Hypothesis**

Full templates in original v1.0 spec Section 6.

## 6.4 Weekly Email Report (Saturday 18:00 Peru)

Sent every Saturday so user can review Sunday.

Full template:

```
═══════════════════════════════════════════════════
📊 RidingHigh Agent — Weekly Score Analytics
Week of 2026-04-25 to 2026-05-01 (Saturday)
═══════════════════════════════════════════════════

🎯 Performance Summary:
   Total trades: 47
   Win rate: 72%
   Total P&L: +$1,840
   Best trade: AKAN +$108
   Worst trade: PBM -$100  (note: SL is now -$100 at +10%)

📊 Score Performance:
   60-70: 8 trades, 63% WR, +$45 avg
   70-80: 28 trades, 78% WR, +$32 avg ⭐ SWEET SPOT
   80-90: 9 trades, 67% WR, +$18 avg
   90+: 2 trades, 50% WR, -$15 avg ⚠️

📊 Metric Insights:
   ✅ Strong predictors:
      • MxV (correlation -0.34)
      • ATRX in range 1.5-2.5 (correlation +0.21)
      
   ⚠️ Weak predictors:
      • RSI overall (correlation -0.05)
      • Gap removed from v2 — confirmed not helpful
      
   🤔 Surprising findings:
      • RSI 90+ correlates with LOSSES
      • Score 90+ has lowest win rate

💡 Suggestions for Discussion:
   
   1. ⚠️ Consider lowering RSI weight (10% → 5%?)
      Reasoning: Correlation near zero
      Sample: 47 trades
      Confidence: 45%
      [Approve] [Reject] [Need more data]
   
   2. ✅ Consider raising MxV weight (25% → 30%?)
      Reasoning: Strongest predictor
      Sample: 47 trades
      Confidence: 65%
      [Approve] [Reject] [Need more data]

🌐 Detailed analysis: ridinghigh-pro-v2.streamlit.app

📅 Next analysis: Saturday 2026-05-08 18:00 Peru
═══════════════════════════════════════════════════
```

## 6.5 Suggestion Approval Flow

```
1. User clicks "Approve" in email or dashboard
2. System creates GitHub Issue documenting change
3. User confirms in Issue (final safety check)
4. System updates relevant config (e.g., score weights)
5. PK_v2 updated to reflect new weights
6. Git commit with descriptive message
7. Trader uses new config starting next signal
8. 30-day observation period begins
9. Results auto-reviewed in next weekly report
```

If user rejects: change logged but not applied.
If user does nothing for 7 days: change NOT applied (default = SKIP).

---

# 7. Decision Logger

## 7.1 Role

Creates **immutable audit trail** of every decision.

## 7.2 Schema (40 Columns)

Stored in `decision_log` sheet. See Section 11.2 for full column list.

## 7.3 Postmortem Engine

When position closes, automatically generate analysis:
- Compare predicted vs actual
- Auto-generate lessons
- Write to `postmortems` sheet

Auto-lessons examples:

```python
def auto_generate_lessons(decision, outcome):
    lessons = []
    
    if outcome.status == "LOSS":
        if decision.perception.atrx > 3:
            lessons.append("High ATRX — consider archetype-specific limits")
        if decision.perception.rsi > 90:
            lessons.append("RSI 90+ at entry — momentum may have continued")
    
    if outcome.duration_hours < 1:
        lessons.append("Very fast outcome — entry timing optimization candidate")
    
    if outcome.pnl_pct > 15:
        lessons.append("Exited at TP10 but stock continued falling — dynamic TP candidate")
    
    return lessons
```

---

# 8. Critical Infrastructure

## 8.1 Why Critical?

Without these, the agent fails subtly:

| Component | Without it... |
|-----------|---------------|
| Sheets Cache | Rate limit errors crash system |
| Data Quality Monitor | Bad data → bad decisions |
| Order Reliability | Failed orders → state inconsistency |
| Health Monitor | Outages undetected (extends existing health_audit) |
| Self-Test Suite | Problems found only after damage |
| Emergency Stop | No way to halt quickly |
| Cold Start Mode | Aggressive trading before validation |

## 8.2 Sheets Cache Layer

```python
# agent/utils/sheets_cache.py

from cachetools import TTLCache
from threading import Lock
from time import time

class SheetsCache:
    def __init__(self):
        self.read_cache = TTLCache(maxsize=1000, ttl=60)
        self.write_queue = []
        self.write_lock = Lock()
        self.last_flush = 0
    
    def read(self, sheet_id, range_a1):
        cache_key = f"{sheet_id}:{range_a1}"
        if cache_key in self.read_cache:
            return self.read_cache[cache_key]
        data = self._api_read(sheet_id, range_a1)
        self.read_cache[cache_key] = data
        return data
    
    def queue_write(self, sheet_id, row_data):
        with self.write_lock:
            self.write_queue.append({
                "sheet_id": sheet_id,
                "data": row_data,
                "timestamp": time()
            })
        if len(self.write_queue) >= 10 or (time() - self.last_flush) > 2:
            self.flush()
    
    def flush(self):
        # ... batched API calls
        pass
```

## 8.3 Data Quality Monitor

```python
# agent/perception/data_quality.py

class DataQualityMonitor:
    QUALITY_RULES = {
        "atrx_max_reasonable":  50,
        "change_pct_max":       200,
        "rsi_range":            (0, 100),
        "volume_max_vs_shares": 1.0,
        "price_min":            0.01,
    }
    
    def validate(self, signal):
        flags = []
        if signal.atrx > self.QUALITY_RULES["atrx_max_reasonable"]:
            flags.append("SUSPICIOUS_ATRX")
        # ... more checks
        return {
            "is_trustworthy": len(flags) == 0,
            "quality_score": max(0, 1.0 - len(flags) * 0.25),
            "flags": flags,
        }
```

## 8.4 Order Reliability

```python
# agent/execution/order_manager.py

class OrderManager:
    def submit_with_retry(self, order, max_retries=3):
        for attempt in range(max_retries):
            try:
                result = self.broker.submit_order(order)
                if result.status in ["filled", "accepted"]:
                    return result
                if result.status == "rejected":
                    self._log_rejection(order, result)
                    return None
                time.sleep(2)
                result = self.broker.get_order(result.id)
                if result.status == "filled":
                    return result
            except APIConnectionError as e:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
        self._alert_critical(order, last_error)
        return None
```

## 8.5 Agent Health Checks (Extension of health_audit.py)

The Agent does NOT replace health_audit.py — it ADDS new checks:

```python
# agent/monitoring/agent_health.py

# To be added to health_audit.py via extension pattern:

AGENT_HEALTH_CHECKS = [
    "alpaca_paper_account_responsive",
    "alpaca_buying_power_sufficient",
    "agent_decision_log_writable",
    "agent_no_stuck_positions",
    "agent_no_orphan_orders",
    "agent_score_calculator_matches_scanner",  # CRITICAL
    "agent_cold_start_within_limits",
    "agent_emergency_stop_status",
]
```

These run every 5 minutes during market hours via the new `agent_health_check.yml` workflow.

## 8.6 Daily Self-Test (08:00 Peru)

Before market opens, comprehensive system check:

```python
DAILY_TESTS = [
    "alpaca_paper_account_active",
    "all_sheets_readable",
    "all_sheets_writable",
    "data_provider_returning_data",        # via existing abstraction
    "scanner_workflows_active",
    "email_sendable",
    "dashboard_responsive",
    "no_orphan_orders",
    "decision_log_writable",
    "agent_score_matches_scanner",        # CRITICAL — see Section 13.3
    "calc_position_size_works",
]
```

If any fail → trading suspended + urgent email.

## 8.7 Emergency Stop Button

```python
# agent/monitoring/emergency_stop.py

class EmergencyStop:
    @classmethod
    def trigger(cls, reason: str, triggered_by: str = "user"):
        cls._set_emergency_flag(True, reason, triggered_by)
        for order in alpaca.list_orders(status="open"):
            alpaca.cancel_order(order.id)
        for pos in alpaca.list_positions():
            alpaca.submit_order(
                symbol=pos.symbol,
                qty=abs(int(pos.qty)),
                side="buy" if pos.qty < 0 else "sell",
                type="market",
                time_in_force="ioc"
            )
        cls._send_emergency_email(reason, triggered_by)
        cls._log_event(reason, triggered_by)
    
    @classmethod
    def clear(cls, password: str):
        if password != os.getenv("EMERGENCY_CLEAR_PASSWORD"):
            raise PermissionError("Invalid password")
        cls._set_emergency_flag(False, "cleared", "user")
```

**Trigger sources:**
1. Big red button in Dashboard page 9
2. Auto-trigger if daily loss exceeds $200 (Cold Start Mode)
3. Auto-trigger if 5 consecutive errors
4. Manual command via Python

---

# 9. Email & Notifications

## 9.1 Three Email Types

| Type | When | Frequency |
|------|------|-----------|
| Daily Brief | 16:30 Peru | Every trading day |
| Weekly Review | **Saturday 18:00 Peru** | Every Saturday |
| Urgent Alert | Anytime | As needed |

**Important:** Weekly Review is **Saturday**, not Sunday.

## 9.2 Email Configuration

Uses **existing Gmail account** (no new account needed). Same credentials as health_audit emails.

```python
EMAIL_CONFIG = {
    "smtp_server":    "smtp.gmail.com",
    "smtp_port":      587,
    "from_address":   "<your existing email>",
    "to_address":     "<same — sends to self>",
    "use_tls":        True,
}
```

GitHub Secrets:
- `GMAIL_USER` (already exists for health_audit)
- `GMAIL_APP_PASS` (already exists for health_audit)
- `REPORT_TO` (already exists for health_audit)

**No new email credentials needed.**

---

# 10. Streamlit Dashboard Extension

## 10.1 Existing Dashboard

`ridinghigh-pro-v2.streamlit.app` already has scanner pages.

**Phase 1 adds 2 new pages:** Pages 9 and 10.

## 10.2 Implementation Pattern

The current dashboard is a single-file `dashboard.py` with conditional rendering. To add Agent pages:

**Option A:** Add to existing single-file dashboard (preferred for now, matches ADR-008)
**Option B:** Convert to multi-page Streamlit app (defer to Phase 2)

Phase 1 uses Option A. Pages 9-10 are added as new sections in `dashboard.py` triggered by the existing radio button or new sidebar option.

## 10.3 Page 9: Live Agent Activity

(Full mockup in v1.0 spec Section 10.2)

Key elements:
- 🚨 Emergency Stop button (with confirmation)
- 📊 Today's stats
- 🔄 Live activity stream (last 50 events)
- 📈 Open positions table
- 🤖 Agent status indicators
- ⚙️ System health

Auto-refresh every 60 seconds + manual refresh button.

## 10.4 Page 10: Score Brain

(Full mockup in v1.0 spec Section 10.3)

Key elements:
- 🎯 Current Score Configuration display
- 📊 Score Performance Analysis charts
- 💡 Pending Suggestions with [Approve]/[Reject]/[Need more data]
- 📜 Approved Changes History
- 🎓 What the Agent is Learning

---

# 11. Google Sheets — New Agent Sheets

## 11.1 Folder Structure

**Use existing folder, add 8 new sheets:**

```
📁 RidingHighPro-2026-XX/  (existing folder)
   
   📂 Scanner Sheets (existing — 9):
   ├── timeline_live
   ├── daily_snapshots
   ├── daily_summary
   ├── post_analysis
   ├── portfolio
   ├── portfolio_live
   ├── score_tracker
   ├── live_trades
   └── ticker_follow_up           ← NEW since v1.0 spec
   
   🆕 Agent Sheets (NEW — 8):
   ├── decision_log
   ├── paper_portfolio
   ├── score_analytics
   ├── postmortems
   ├── system_events
   ├── pending_suggestions
   ├── config_history
   └── borrow_data
```

## 11.2 - 11.9 Sheet Schemas

(Same as v1.0 spec Sections 11.2-11.9 — schemas unchanged)

Quick reference:

| Sheet | Purpose | Columns |
|-------|---------|---------|
| `decision_log` | Every signal evaluated | 40 |
| `paper_portfolio` | Mirror of Alpaca state | 22 |
| `score_analytics` | Daily Score Analytics | 25 |
| `postmortems` | Per-position analysis | 17 |
| `system_events` | System events log | 7 |
| `pending_suggestions` | Suggestions awaiting user | 14 |
| `config_history` | Config change audit trail | 10 |
| `borrow_data` | HTB cache | 9 |

## 11.10 Monthly Rotation

Sheets rotate monthly (matching scanner pattern via existing `monthly_rotation.yml` workflow).

**Action needed:** Update `monthly_rotation.yml` to also rotate the 8 agent sheets.

---

# 12. Setup Manual

## 12.1 What's Already In Place

✅ Gmail account (yours, already used by health_audit)
✅ GitHub: `projects5069-creator/ridinghigh-pro`
✅ Streamlit: `ridinghigh-pro-v2.streamlit.app`
✅ Google Drive folder: `RidingHighPro-2026-XX/`
✅ Service Account credentials
✅ Existing 9 sheets
✅ **Alpaca Paper credentials** (already used by data_provider!)
✅ Email credentials (already used by health_audit)

## 12.2 What You Need to Add

**Setup time: ~10 minutes (much less than v1.0 spec said!)**

The original v1.0 spec said "30 minutes for Alpaca + Gmail." But **Alpaca and Gmail are ALREADY connected** since the scanner uses them.

You only need to add:

### **One New GitHub Secret (~5 min)**

```
EMERGENCY_CLEAR_PASSWORD = <strong password you choose>
```

That's literally it. Existing secrets stay:
```
GOOGLE_CREDENTIALS_JSON          (already exists)
GOOGLE_OAUTH_TOKEN_JSON          (already exists)
ALPACA_API_KEY_ID                (already exists)
ALPACA_SECRET_KEY                (already exists)
GMAIL_USER                       (already exists)
GMAIL_APP_PASS                   (already exists)
REPORT_TO                        (already exists)
```

### **Verification Checklist (~5 min)**

Before Phase 1 implementation begins:

- [ ] Run `python health_audit.py --local` — all green
- [ ] Verify Alpaca paper account: `python -c "from data_provider import test; test()"`
- [ ] Verify can read Drive folder (already working since scanner does)
- [ ] EMERGENCY_CLEAR_PASSWORD added to secrets and remembered

**Done. Phase 1 implementation can begin.**

---

# 13. Phase 1 Milestones

10 milestones, each with clear acceptance criteria.

## 13.1 Milestone 1: Foundation & Configuration

**Goal:** Add agent constants, create directory structure, validate setup.

**Tasks:**
- [ ] Create `agent/` directory with empty `__init__.py` files
- [ ] Add agent constants to `config.py` (additive only, do not modify existing)
- [ ] Create `agent/utils/sheets_cache.py`
- [ ] Verify can import existing modules (formulas, config, data_provider)
- [ ] Update PK_v2 with §A2: Agent Module Overview

**No `scanner/` migration!** This is a v2.0 change from v1.0 spec.

**Acceptance:**
- [ ] All scanner workflows still passing
- [ ] `from agent import sheets_cache` works
- [ ] `from formulas import calculate_score` works from agent code
- [ ] PK_v2 has new section §A2

## 13.2 Milestone 2: Agent Sheets Setup

**Goal:** Create 8 new sheets, update sheets_config.json, update monthly_rotation.

**Tasks:**
- [ ] Create programmatic script `agent/setup/create_agent_sheets.py`
- [ ] Create the 8 sheets in current month's folder
- [ ] Update `sheets_config.json` to include agent sheets
- [ ] Update `monthly_rotation.yml` workflow to handle agent sheets
- [ ] Update PK_v2 §15 (Schema Reference) with 8 new sheets

**Acceptance:**
- [ ] All 8 agent sheets exist with correct headers (40, 22, 25, 17, 7, 14, 10, 9 columns)
- [ ] sheets_config.json validates
- [ ] monthly_rotation tested (run manually in test mode)
- [ ] PK_v2 reflects new sheets

## 13.3 Milestone 3: The Trader Core Logic

**Goal:** Trader can evaluate signals (without executing).

**Tasks:**
- [ ] Implement `agent/trader/score_calculator.py` — IMPORTS from formulas.py
- [ ] Implement `agent/perception/data_quality.py`
- [ ] Implement `agent/perception/tradability.py` (mock Alpaca for now)
- [ ] Implement `agent/trader/decision_logic.py`
- [ ] Implement `agent/trader/trader.py` (main class)
- [ ] Write `test_agent_matches_scanner` test (CRITICAL)

**Critical test:**
```python
def test_agent_matches_scanner():
    """
    Read 100 random rows from scanner's timeline_live,
    pass them to agent's score_calculator,
    must match scanner's Score within 0.01.
    """
```

**Acceptance:**
- [ ] All 28 metrics correctly read from scanner data
- [ ] Score calculation matches scanner within 0.01
- [ ] Decision logic returns ENTER/SKIP correctly with proper reasons
- [ ] 100 test signals processed correctly
- [ ] PK_v2 updated with §A3: Agent Decision Logic

## 13.4 Milestone 4: Decision Logger

**Goal:** Every decision logged to Sheets.

**Tasks:**
- [ ] Implement `agent/logging/decision_id_generator.py`
- [ ] Implement `agent/logging/decision_logger.py`
- [ ] Wire trader to logger
- [ ] Use sheets cache for batched writes

**Acceptance:**
- [ ] 100 test decisions write correctly
- [ ] All 40 columns populated
- [ ] No rate limit errors (cache works)
- [ ] Decisions appear in sheet within 5 seconds
- [ ] PK_v2 updated with §A4: Decision Log Schema

## 13.5 Milestone 5: Alpaca Execution

**Goal:** Trader actually submits orders.

**Tasks:**
- [ ] Implement `agent/execution/alpaca_broker.py` (orders only, NOT market data)
- [ ] Implement `agent/execution/order_manager.py` (with retries)
- [ ] Implement `agent/execution/position_manager.py`
- [ ] Implement `agent/execution/reconciler.py`
- [ ] Wire trader to broker
- [ ] Update `paper_portfolio` sheet on every order

**Acceptance:**
- [ ] Submit test order, see in Alpaca dashboard
- [ ] TP/SL bracket orders register
- [ ] Position appears in `paper_portfolio` sheet
- [ ] Can manually close position
- [ ] Reconciler detects mismatches
- [ ] PK_v2 updated with §A5: Order Execution Architecture

**⚠️ Critical:** Test with $1 positions first. Then $1,000.

## 13.6 Milestone 6: Postmortem Engine

**Goal:** Closed positions analyzed automatically.

**Tasks:**
- [ ] Implement `agent/analytics/postmortem_engine.py`
- [ ] Implement lesson generator
- [ ] Detect position closes (every minute monitoring)
- [ ] Compare predicted vs actual
- [ ] Auto-generate lessons
- [ ] Write to `postmortems` sheet

**Acceptance:**
- [ ] Position closes → postmortem appears within 1 minute
- [ ] Lessons reasonable (not generic)
- [ ] PK_v2 updated with §A6: Postmortem Engine

## 13.7 Milestone 7: Score Analytics System

**Goal:** Daily + weekly analysis.

**Tasks:**
- [ ] Implement `agent/analytics/score_analytics.py`
- [ ] Implement `agent/analytics/correlation_finder.py`
- [ ] Daily aggregation (writes to `score_analytics`)
- [ ] Weekly aggregation (writes to `pending_suggestions`)
- [ ] Generate reports for emails

**Acceptance:**
- [ ] Daily report generated 16:30 Peru
- [ ] Weekly report generated **Saturday 18:00 Peru**
- [ ] 3-5 suggestions per weekly report
- [ ] Suggestions stored as PENDING
- [ ] PK_v2 updated with §A7: Score Analytics System

## 13.8 Milestone 8: Email System

**Goal:** Reliable email delivery.

**Tasks:**
- [ ] Implement `agent/notifications/email_sender.py`
- [ ] Build daily brief HTML template
- [ ] Build weekly review HTML template
- [ ] Build urgent alert HTML template
- [ ] Set up GitHub Actions schedules
- [ ] Reuse existing GMAIL_USER/GMAIL_APP_PASS/REPORT_TO secrets

**Acceptance:**
- [ ] Daily email arrives 16:30 Peru
- [ ] Weekly email arrives Saturday 18:00 Peru
- [ ] Urgent alert sends within 30 seconds
- [ ] Emails render correctly
- [ ] PK_v2 updated with §A8: Email System

## 13.9 Milestone 9: Streamlit Dashboard Pages 9-10

**Goal:** New dashboard sections live.

**Tasks:**
- [ ] Add Agent pages to existing dashboard.py (single-file pattern)
- [ ] Implement Emergency Stop button (with confirmation)
- [ ] Auto-refresh every 60 seconds
- [ ] Mobile-responsive layout
- [ ] Deploy to existing Streamlit Cloud app

**Acceptance:**
- [ ] Both pages load in < 3 seconds
- [ ] Real-time data updates
- [ ] Emergency Stop tested (test mode first!)
- [ ] Suggestions can be approved/rejected from dashboard
- [ ] PK_v2 updated with §A9: Dashboard Extensions

## 13.10 Milestone 10: Critical Infrastructure & Production

**Goal:** All safety systems + first real paper trading.

**Tasks:**
- [ ] Implement `agent/monitoring/agent_health.py` — adds checks to health_audit
- [ ] Implement `agent/monitoring/self_test.py`
- [ ] Implement `agent/monitoring/emergency_stop.py`
- [ ] Set up all 5 new GitHub Actions workflows
- [ ] Run DRY_RUN day (logs only, no execution)
- [ ] Review DRY_RUN with user
- [ ] Switch to LIVE_PAPER mode
- [ ] First real paper trading day

**5 New Workflows:**
```
agent_minute.yml         → */1 13-20 * * 1-5
agent_morning_test.yml   → 0 13 * * 1-5     (08:00 Peru)
agent_daily_email.yml    → 30 21 * * 1-5    (16:30 Peru)
agent_weekly_review.yml  → 0 23 * * 6       (Saturday 18:00 Peru) ⚠️
agent_health_check.yml   → */5 13-20 * * 1-5
```

**Acceptance:**
- [ ] Health checks every 5 min during market
- [ ] Morning self-test at 08:00 Peru
- [ ] All 5 workflows running on schedule
- [ ] Emergency Stop tested end-to-end
- [ ] Cold Start Mode active
- [ ] DRY_RUN day completed successfully
- [ ] User approved go-live
- [ ] First real paper trade executed
- [ ] All systems showing green
- [ ] PK_v2 fully updated reflecting Phase 1 complete state

🎉 **Phase 1 Complete!**

---

# 14. Future Phases Roadmap

(Same as v1.0 spec Section 14 — roadmap unchanged)

| Phase | Adds | Trigger |
|-------|------|---------|
| 2 | Entry Score Optimizer (Full) | After 30-day Data-Only + 200+ trades |
| 3 | Timing Agent | Phase 2 complete |
| 4 | Devil's Advocate | Phase 3 complete |
| 5 | Exit Strategy Agent | Phase 4 complete |
| 6 | News Detective | Phase 5 complete |
| 7 | Pattern Hunter | Phase 6 complete |
| 8 | Risk Sentinel | Phase 7 complete |
| 9 | TP/SL Optimizer | Phase 8 complete |
| 10 | Market Context Agent | Phase 9 complete |
| 11 | Multiple Personalities (3 traders) | Phase 10 complete |
| 12+ | Mentor / Sandbox / Strategy Inventor | Phase 11 complete |

---

# 15. Risks & Mitigations

(Same as v1.0 spec Section 15 — risks unchanged)

Key risks:
- ✅ Alpaca API instability → Retry logic, Health Monitor
- ✅ Google Sheets quota limits → Sheets cache layer
- ✅ Code bugs cause runaway behavior → Cold Start Mode, Emergency Stop
- ✅ Paper performance ≠ Live performance → 6+ month paper period
- ✅ Overfitting to limited data → Tiered Confidence, default = SKIP

---

# 16. Code Conventions

(Same as v1.0 spec Section 16 — conventions unchanged, with these additions)

## 16.1 Versioned Filenames (User Memory Rule)

⚠️ **Iron Rule §12 (from user memory):**
> *"Always use versioned filenames for new code files. Never reuse a filename that exists or that user has already downloaded. Use _v1, _v2, _v3 suffixes."*

This applies to deliverables, not source code in the repo.

## 16.2 No Modification of Scanner Code

The Agent build is **purely additive**:
- ✅ ADD new files in `agent/`
- ✅ ADD new constants to `config.py`
- ✅ ADD new health checks to `health_audit.py`
- ✅ ADD new sections to `dashboard.py`
- ✅ ADD new workflows to `.github/workflows/`
- ✅ ADD new sheets to Drive folder
- ✅ ADD new sections to PK_v2

- ❌ NEVER modify existing scanner functions
- ❌ NEVER modify existing scanner workflows
- ❌ NEVER modify formulas.py
- ❌ NEVER move scanner files

---

# 17. PK_v2 Integration & Anti-Drift

## 17.1 The Anti-Drift Contract

PK_v2 contains an Anti-Drift Maintenance Contract (§35):

> *"Whenever a session adds, modifies, or removes Python files, workflows, sheets, constants, metrics, formulas, weights, health checks, email alerts, schedules, phases, KPIs, or known issues — PK_v2 MUST be updated before commit."*

**Phase 1 will add ALL of these.** Therefore, every milestone MUST end with PK_v2 update.

## 17.2 New PK_v2 Sections to Add

The Agent build adds these sections to PK_v2:

```
§A1: Agent Module Overview          (Milestone 1)
§A2: Agent Configuration            (Milestone 1)
§A3: Agent Decision Logic           (Milestone 3)
§A4: Decision Log Schema            (Milestone 4)
§A5: Order Execution Architecture   (Milestone 5)
§A6: Postmortem Engine              (Milestone 6)
§A7: Score Analytics System         (Milestone 7)
§A8: Email System                   (Milestone 8)
§A9: Dashboard Extensions           (Milestone 9)
§A10: Production Operations         (Milestone 10)
```

## 17.3 Version Bumping

After each milestone, increment PK_v2:
- Patch (v2.0 → v2.0.1) for content edits
- Minor (v2.0 → v2.1) for new sections

Phase 1 will likely bump PK_v2 to v3.0 or v2.10 after Milestone 10.

## 17.4 Cross-References

The PK_v2 §36 (Cross-References to Code) MUST include all new agent files.

---

# 18. Glossary

Additions to PK_v2 glossary:

| Term | Definition |
|------|------------|
| **Agent** | Phase 1 implementation: The Trader, Score Analytics, Decision Logger, etc. |
| **The Trader** | The single agent in Phase 1 making entry/exit decisions |
| **Score Analytics** | Observational analysis layer, suggests but doesn't change |
| **Decision Logger** | Audit trail of every signal evaluated, 40-column rows |
| **Postmortem** | Auto-generated post-trade analysis comparing predicted vs actual |
| **Cold Start Mode** | First 30 days of cautious operation (limits on positions/trades) |
| **DRY_RUN** | Logs decisions but doesn't execute |
| **LIVE_PAPER** | Real paper trading mode |
| **Emergency Stop** | One-click halt of all trading + close all positions |
| **Pending Suggestion** | Score Analytics proposal awaiting user approval |

---

**End of Specification v2.0**

*This document is the complete plan for the unified RidingHigh System Phase 1 build.*
*Phase 1 builds on the existing scanner without modifying it.*
*Future phases add agents incrementally based on real performance data.*
