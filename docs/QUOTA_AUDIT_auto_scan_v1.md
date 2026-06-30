# Quota Audit — auto_scan (auto_scanner.py)
*TASK-214 · recon 2026-06-30 · propose-only (no implementation)*
*Mirror of QUOTA_AUDIT_agent_minute_2026-06-24.md (TASK-136, Done)*

## Context
After TASK-58 closed health_audit out of the shared commercial SA
(dedicated HA SA + moved off-hours), auto_scan became the heaviest
un-audited per-minute reader on the shared SA (project 591299446687).
**Empirical confirmation (live 2026-06-30 12:22 Peru, run 28463021682):**
auto_scan 429-crashed mid-chain at portfolio_live — the 429 driver,
caught live in market hours.

## AC#1 — read-site map (run_scan, per-minute)
| line | tab | note |
|---|---|---|
| 373/560/783 | timeline_live | cached 60s (TASK-58 S1) |
| 474→478 | daily_snapshots | full get_all_values |
| 489→492 | portfolio | full ← #1 |
| 525→628 (update_portfolio_live) | portfolio | full ← #2 DUPLICATE |
| 647→648 | portfolio_live | full |
| 533→825 (update_ticker_follow_up) | ticker_follow_up | full |
| 541→1008 (update_live_trades) | live_trades | full |
| 541→1155 (update_live_trades) | portfolio | full ← #3 DUPLICATE |
| 550→1273 (sync_score_tracker) | score_tracker | row_values(1) — already optimized |
| 514→598 (_save_daily_summary) | daily_summary | full |

run_eod (once/day): 1317 timeline_live (RAW, not cached) · 1341 portfolio.

Estimated per-minute reads (static map): ~8-9 intended.

## AC#2 — baseline (ground-truth)
**NOT numerically measurable live** — catch-22: the run 429-crashes
*because of* the read volume, so the in-run read-counter (TASK-112)
always under-counts (last run showed total=1, truncated by the early 429).
True success metric = **429-frequency reduction** after the cut (ties
into TASK-213 measurement window).

## AC#3 — proposed cuts (PROPOSE ONLY — do NOT implement here)
1. ⭐ **portfolio 3×→1×** — `portfolio` is read fully 3 times per run
   (lines 492, 628, 1155). Inject one cached_portfolio_reader into
   run_scan / update_portfolio_live / update_live_trades. Exact pattern
   TASK-136 used for position_manager. Certain −2 reads/min.
2. **run_eod timeline RAW (1317)** → route through `_read_timeline_live`
   (cached) like run_scan.
3. (optional) batch daily_snapshots + portfolio if same spreadsheet.

## Next step
Implementation = separate task (mirror how TASK-136 split audit→fix).
Touches live trading path → TDD + careful, market-hours-aware.

---
## REVISED FINDING (deep-recon 2026-06-30, supersedes AC#3 estimate)
The "portfolio 3×/min → −2 reads/min" estimate was OPTIMISTIC. Live deep-recon:
- portfolio read **2×/min** (489 run_scan + 625 update_portfolio_live), NOT 3×.
- 3rd read (1155) is in **sync_score_tracker** (called line 550), which runs
  **every 5 min only** — AC#1 mis-attributed it to update_live_trades (541).
- ⚠️ **Line 510 WRITES portfolio between reads 489↔625** → a cached reader
  CANNOT save the per-minute pair (write invalidates cache; caching a
  written-within-minute tab = data-corruption bug, worse than 429).
- Pure cached-reader saves ONLY the 5-min read (1155): ~1 read / 5 min.
  Per-minute saving requires an in-memory frame pass (combined_port already
  built at 510) → invasive signature refactor on 2 call-sites, live-path risk.

**Conclusion:** portfolio de-dup is a SMALL, EXPENSIVE win and NOT the right
fix for auto_scan's 429. Most per-minute reads (daily_snapshots, portfolio_live,
daily_summary) are write-accompanied → not cache-able. The architecturally
correct fix mirrors TASK-58: **dedicated SA for auto_scan** (or frequency
reduction), NOT read de-dup. De-dup track CLOSED. See new follow-up task.
