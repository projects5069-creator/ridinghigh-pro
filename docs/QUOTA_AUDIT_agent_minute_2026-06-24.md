# Quota Audit — `agent_minute` Sheets I/O (TASK-136)

**Date:** 2026-06-24 · **Mode:** DRY_RUN · **Sentinel:** shadow
**Scope:** measure per-component Google-Sheets reads/writes per `agent_minute` run,
verify logging-only vs decision-affecting, rank cuts by impact. Audit is read-only;
all file:line references are code-verified.

Entry point: `.github/workflows/agent_minute.yml` (cron `*/1 13-20 * * 1-5` UTC =
08:00–15:00 Peru, Mon–Fri) → `python -m agent.orchestrator` → `orchestrator.run()`.

---

## 1. Per-component I/O table (one typical run, 0 ENTERs / 0 closes)

| # | Component | Sheet | I/O | calls/run | Cached? | file:line | Decision-affecting? |
|---|-----------|-------|-----|-----------|---------|-----------|---------------------|
| 1 | Emergency-stop check | system_events | READ | 1 | yes (60s) | orchestrator.py:146 | yes (halt gate) |
| 2 | Account-state builder | paper_portfolio | READ | 1 | yes (60s) | orchestrator.py:222 | yes (position/entry counts) |
| 3 | Account-state builder | decision_log | READ | 1 | yes (60s) | orchestrator.py:271 | yes (today's ENTER count) |
| 4 | Signal reader | timeline_live | READ | 1 | yes (60s) | orchestrator.py:350 | **yes — life-line** |
| 5 | Outage detection | timeline_live | READ | 1 | yes (60s) | orchestrator.py:404 | no (observability) |
| 6 | Position manager | paper_portfolio | READ | 1 | **was NO → now yes** | position_manager.py:131 | yes (TP/SL/PnL) |
| 7 | Sentinel gate | sentinel_events | WRITE | 0–N | n/a | data_sentinel.py:59 | no (shadow, log-only) |
| 8 | News detective | news_findings | WRITE | 0–~20 | n/a (1h/ticker) | news_detective_v1.py:275 | **no — log-only (proven)** |
| 9 | Decision logger (ENTER) | decision_log | WRITE | 0–5 | n/a | decision_logger.py:270 | yes (audit trail) |
| 10 | Decision logger (SKIPs) | skip_summary | WRITE | 1 (batched) | n/a | decision_logger.py:199 | no (TASK-125 aggregated) |
| 11 | Order manager | paper_portfolio | WRITE | 0–5 | n/a | order_manager.py:290 | yes (entry row) |
| 12 | Position manager | paper_portfolio | WRITE | 0–N (1/pos) | n/a | orchestrator.py:622 | yes (price/PnL/exit) |
| 13 | Postmortem engine | postmortems | WRITE | 0–1 | n/a | postmortem_engine.py:259 | no (on close only) |

**Already-optimized infrastructure (no action):**
- 60s read cache `sheets_manager.get_sheet_values` / `get_sheet_records` (TASK-58), invalidated after writes.
- SKIP-aggregation: ~80–100 SKIPs/min → **1** batched `safe_append_rows` (TASK-125, `decision_logger.flush_skip_summary`).
- Quota gate `agent/sentinel/checks/quota_health.py`: defensive@50, halt@60 writes/min; writes tracked via `_track_write_quota` (AUDIT-2 restored 2026-05-24).

---

## 2. Ranked cut backlog (impact order)

| Cut | What | Status | Owner |
|-----|------|--------|-------|
| **C1** | position_manager read shares the paper_portfolio cache (uncached `get_all_records` → cached `get_sheet_records` via injected reader) | **DONE this session** (TDD, suite green) | TASK-136 |
| **C2** | news_detective per-ticker `news_findings` writes (log-only, proven) — demote to EOD-only or disable | deferred — already owned | **TASK-176** |
| **C3** | timeline_live double-read (`:350` signal reader + `:404` outage detection) → pass the first result through instead of a 2nd `get_sheet_records` | sub-task to open | (new) |
| **C4** | per-position `safe_batch_update` (`orchestrator.py:622`) → merge all open-position cell updates into ONE batch call | sub-task to open | (new) |
| **C5** | `agent_market_context` 14.8%/30d fail from top-of-hour 429 collisions — jitter/offset the read off the top-of-minute, or add 429 retry | sub-task to open (AC#1) | (new) |

C1 detail — the cut that landed:
- Root: orchestrator built `PositionManager` with **no `sheet_reader`** (`orchestrator.py:630-635`),
  so `_get_open_positions` fell back to an **uncached** `get_worksheet("paper_portfolio").get_all_records()`
  every minute (`position_manager.py:128-131`) — a duplicate of the cached read at `:222`.
- Fix: inject `cached_portfolio_reader` (routes through `get_sheet_records("paper_portfolio")`, 60s cache).
  Net: paper_portfolio API reads/run **2 → 1** (the position read becomes a same-run cache hit).
- Risk handled: `get_sheet_records` returns strings; `_coerce_portfolio_record` normalizes the numeric
  whitelist (prices→float, Quantity→int-via-float) to the gspread-equivalent types the pipeline consumes.
  Row order — hence the positional `_row_number` write target — is preserved by both paths.

---

## 3. AC#1 reconciliation (TASK-139-INV evidence)

- **`agent_market_context` 14.8% / 30d fail rate** traces to **top-of-hour 429 collisions** (run 27293631392):
  many workflows fire on the exact minute boundary and contend for the same Sheets quota window.
  → **C5**: offset/jitter the market_context read a few seconds off the top-of-minute, or wrap it in the
  existing 429 retry. Logged here; cut tracked as a sub-task (no live change in this audit).
- **Scanner "reads ~5–13/run vs counter total = 1" is NOT a lost-read bug** — it is *expected*:
  `sheets_manager.record_read` counts **only actual API fetches (cache misses)**; cache hits are free and
  uncounted (`sheets_manager.py:404-416,432`). counter=1 ⇒ 1 real API fetch + the rest served from the
  60s cache. The caching is working as designed; the "mismatch" is the cache doing its job.

**AC#1 verdict:** the two observations are explained — (a) market_context failures are a scheduling
collision (own sub-task C5), (b) the read-counter "gap" is correct cache behavior, not a leak.

---

## 4. Hard constraints honored
- **timeline_live = life-line** (`orchestrator.read_latest_signals` + dashboard) — never cut; C3 only
  removes the *duplicate* read, keeping the single authoritative fetch.
- **news_detective log-only — code-proven:** `orchestrator.py:702` ("log-only, never blocks"); Score
  (`formulas.calculate_score`), ENTER/SKIP (`agent/trader/decision_logic.py`) and sizing never read
  `news_findings`. Its only other reader is the Critic (dashboard/health). Safe to demote (→ TASK-176).
- No live workflow triggered; no live Sheet write during this audit (RULE #6).
