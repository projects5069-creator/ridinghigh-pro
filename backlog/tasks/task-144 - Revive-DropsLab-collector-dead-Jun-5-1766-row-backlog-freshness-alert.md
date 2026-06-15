---
id: TASK-144
title: 'Revive DropsLab collector (dead Jun 5, 1766-row backlog) + freshness alert'
status: To Do
assignee: []
created_date: '2026-06-11 04:02'
updated_date: '2026-06-15 20:51'
labels:
  - TASK-139-INV
dependencies: []
priority: high
ordinal: 147000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-139-INV DL-7.1: drops_collect.yml cancelled daily since 5/6 (timeout 20m death-spiral, repeat of 19/5 pattern); drops_post frozen at scan_date 27/5; 1,766 raw rows unprocessed. Fix: checkpoint/batch processing + freshness alert (post max date vs raw max date). Evidence: phase7_evidence.md
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
TASK-171 link (2026-06-12): crossover-short (TASK-178/179 — the one promising direction, -17.75% post-drop continuation n=62) DEPENDS on a live DropsLab collector. Reviving this is now on the critical path of the only edge candidate.

MERGE: MASTER 13.6 (drops_collect optimization: skip-processed + --date) is the same fix as this task. Root cause confirmed from live Actions logs: runtime grew monotonically 15->18min, crossed timeout-minutes:20 on 6/5 -> GitHub cancels; cancelled x5 since. bump-timeout = treadmill (26/5 fix bought ~10 days). Real fix = skip-processed (O(new) not O(all)) + one-time drain of 1766-row backlog. Plan: build skip-processed today (code+TDD), live-verify DEFERRED to post-15:00 Peru (market open = no Sheets write).

CORRECTION (read drops_collector.py 2026-06-15): skip-processed ALREADY EXISTS (process_raw_row L278 skips keys already in drops_post, BEFORE yfinance). Real root cause = (1) main-loop calls time.sleep(RATE_LIMIT_SLEEP) UNCONDITIONALLY per raw row incl. skipped ones -> O(all 1766) sleep floor growing linearly forever; (2) incompletables (yfinance-missing/delisted, L310) never written -> never enter existing_keys -> re-fetched every run. Fix = pre-filter raw_rows by existing_keys BEFORE loop (O(pending)) + sleep only on real fetch + quarantine incompletables. Sheet ID confirmed correct (capital-I). NOT a timeout-bump.

LIVE QUANTIFY 2026-06-15 (read-only via collector readers): drops_raw=4236 (NOT 1766 - title stale), processed=2227, pending-D5-not-ready=608, pending-D5-ready=1401 (actionable drain), of which 152 are >15d-old incompletables (delisted/yfinance-missing: AMSS/ADTX/AEVA/BIYA 5/22-5/28). sleep-floor now 24.7min (>timeout=root cause). pre-filter alone -> 11.7min (partial); 1401-row drain needs real yfinance -> WONT fit one 20min run. Fix = 3 parts: (1) pre-filter existing_keys before loop; (2) drain strategy for 1401 (chunked / temp-timeout / local run); (3) quarantine 152 incompletables (marker row / skiplist tab / age-cutoff). Needs brainstorming before code.

FIX IN CODE 2026-06-15 (DropsLab repo, 2 commits 91f9061+52d9b32, NOT pushed yet). Root cause: time.sleep(0.35) ran UNCONDITIONALLY per raw row -> 4236*0.35=24.7min sleep-floor alone, grew monotonically, crossed timeout-minutes:20 on 6/5 (write-once at end -> timeout = zero progress, nothing written). Fix: filter_actionable (pure, TDD 3/3) excludes processed/not-ripe/stale BEFORE loop -> O(actionable) not O(all); existing_keys case-normalized (upper). STALE_CUTOFF_DAYS=20 quarantine (logged). DRY-RUN verified live (read-only): 1400 actionable (median age 11d, 0 rows >20d, 0 dupes), 1 quarantined, ~20-31min local. PENDING (RULE #6): (1) local drain ~1400 rows post-15:00 Peru (market open now - no Sheets write); (2) push AFTER drain (CI 16:30 must see drained existing_keys, else write-once deadlock repeats); (3) commit #3 --date quarantine-bypass deferred (not needed for this drain, all <=18d). TASK-144 stays To Do until live drain succeeds. 151 rows 15-18d are self-healing incompletables (will quarantine once they cross 20d).

DRAIN SUCCEEDED 2026-06-15 15:43 Peru. 1400 rows written to drops_post (2227->3627, verified +1400 exact). Re-query: actionable 1400->0 (write landed, steady-state proven fast). 0 failures (151 'incompletables' were just unprocessed, not broken). DropsLab pushed (b5b7cd8..52d9b32). Collector-revival HALF = DONE+verified. Freshness-alert HALF split to new task. AWAITING CI 16:30 Peru green run before marking 144 Done.
<!-- SECTION:NOTES:END -->
