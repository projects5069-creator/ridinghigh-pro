# WORK PRIORITY — 2026-06-14
*Decided with Amihay. Iron principle: contaminated data = a system failure, not a "quality" item. No research, no 178 lock, no Decision Gate is valid on dirty data. Data integrity comes FIRST.*

## Iron rule for next sessions
Before any crossover / edge-research / decision-gate work: the data feeding it must be clean and stable. A polluted input poisons every downstream conclusion. Verify before trusting any report number (mirrors the borrow / PK-live-verify discipline).

## PHASE 0 — DATA INTEGRITY (must clear before anything research-facing)
> **CORRECTION 2026-06-14 (post-investigation):** of the four items originally listed here, **TASK-150 and TASK-105 are already `Done` in backlog** — they are NOT open blockers. The genuine open PHASE-0 work is **TASK-180 + TASK-144** only. Items 2–3 are retained below marked DONE for traceability.

1. **TASK-180 [open, high] split/halt detector** — unifies TASK-90 + TASK-148 + TASK-173 (merge these three into 180). One detector cleans BOTH DropsLab and RH. Highest ROI: fixes every aggregate/email/dashboard/research in one move. Symptoms: DropsLab d1 mean +124% vs median 0; CTNT +28567%, RDGT +22400%, PCLA +150%/day; 5.6% DropsLab + ~3% RH rows >100% inter-day. **RH half is unblocked now; DropsLab half waits on TASK-144 (+ TASK-153 DropsLab-PK home). Data model decided: non-destructive boolean flag (no value mutation); detector threshold definition still OPEN.**
2. ~~**TASK-150** — schema contract / header-aware reads.~~ **DONE** (commit `a7897a5`, PK v3.06): audit-check + §15 schema doc shipped; `cross_month_loaders.py` already aligns by name. (Note: a broader "enforce *all* readers header-aware" remains a separate un-scoped flag, not part of 150's AC — track separately if needed.)
3. ~~**TASK-105** — paper_portfolio entry-write swallows 429.~~ **DONE** (PR #4 / `dc3ddbf`, PK v2.66): write status surfaced, failed write counted as error, `_APPEND_RETRY_MAX=4`.
4. **TASK-144 [open, high]** — revive DropsLab collector (dead 6/5, drops_post frozen 27/5, 1766 raw rows unprocessed). Stale = no new crossover events; also a hard blocker for the whole crossover chain and for TASK-180's DropsLab half.

## PHASE 1 — SURVIVORSHIP / COUNTING CORRECTNESS
5. TASK-149 (19 NO_DATA delisting = lost short-wins) + TASK-168 (delisting auto-detector).
6. TASK-132 (14 stuck PENDING rows out of count).
7. TASK-137 (ticker_follow_up RSI/ATR SMA->Wilder, D1-D3 not comparable to D0).
8. TASK-87 (mxv sentinel values — currently neutralized, blocks re-add).

## PHASE 2 — DEADLINES (do before the calendar date regardless)
- TASK-135 — orchestrator holiday-blind, runs on Independence Day 7/4. HARD.
- TASK-143 — duplicate RH-2026-07-post_analysis before 7/1 rotation. HARD.

## PHASE 3 — CROSSOVER CHAIN (only after PHASE 0+1 clean)
- TASK-144 done (Phase 0) -> TASK-177 (close AC#3 live-verify: materialize/verify D6-D25 auto-grow via a real collector run; overlaps TASK-83) -> TASK-172 live-verify -> **TASK-178 LOCK** (strategy already decided 6/14: entry d1_close of drop-event, exit <=5 trading days or +/-10%, 5d hold from economic reasoning, NO peeking, forward-only hold-out) -> TASK-179 validate (n>=150, worst-case borrow+slip).

## PHASE 4 — DECISION GATES (Fable-5 investigation; need clean data first)
- TASK-141 (Filter1 -> Option B), TASK-174 (Score demotion), TASK-127, TASK-128.

## PHASE 5+ — research-edge, agents, infra, cleanup
Per the full 63-task priority table (chat 6/14). Edge research (71/72/75/80...) only on verified-clean data.

## KEY DRIFTS TO FIX WHEN TOUCHING THESE
- TASK-177: code+TDD done, AC#3 live-verify pending (status To Do BY DESIGN, like TASK-172) — NOT a status conflict. §D's "DONE" = the D6-D25 data-collection layer; the task stays open until a real collector run materializes the cols (RULE #6). See TASK-177 notes (auto-grow gap).
- Titles stale: 177 says "D6-D15" but built D6-D25; 178 says "pre-register" but TASK-165 already did the framework.
- TASK-83 overlaps TASK-177 (same hold-window) — resolve duplication.

*Next session starts at PHASE 0 item 1.*
