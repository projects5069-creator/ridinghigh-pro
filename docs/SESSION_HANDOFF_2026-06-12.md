# Session Handoff — 2026-06-12

## TL;DR
Implemented **TASK-142** (rebase official WR onto executable D1_Open entry; demote ScanPrice Table A to diagnostic) **+ the WR-half of TASK-147** (WHIPSAW-as-loss pessimistic dual bound). Work is on branch **`task-142-147-wr-d1open`** (9 commits) — **pushed, NOT merged to main** (awaiting approval). PK bumped to **v3.07**.

## What shipped (branch `task-142-147-wr-d1open`)

| # | Commit | What |
|---|--------|------|
| 1 | d134b21 | split WR/expectancy — open TASK-162, 147→In Progress |
| 2 | 7695514 | `classify_trade(scan, ohlc, entry_price=None)` — core WIN/LOSS/WHIPSAW mapping frozen, only TP/SL anchor moves |
| 3 | 589005a | `classify_trade_row(row, entry_basis="ScanPrice")` — `"D1_Open"` executable; missing D1_Open → PENDING (no silent fallback) |
| 4 | 159b136 | lock `calculate_net_pnl` entry-scale-invariance (NO param — PnL fraction is scale-free; basis carried by `(cls, day)`) |
| 5 | 00b922f | pure `metrics_bounds.wr_bounds` (optimistic vs WHIPSAW-as-loss) |
| 6 | a15be4b | headline WR (Post Analysis + Home) on D1_Open + pessimistic WHIPSAW bound |
| 7 | 2d41e5d | demote Table A (ScanPrice) → diagnostic; Table B (D1_Open) → official |
| 8 | dc9e7fa | rename ScanPrice `TP10_Hit` "Win Rate" → "TP10 Hit-Rate" (disambiguate from official D1_Open WR) |
| 9 | 2aeb2dc | Anti-Drift PK v3.07 (§20 Table A/B + new WR-basis section) |

## Key design decisions (vs the original plan)
- **`calculate_net_pnl` got NO `entry_price` param.** The plan called for one; empirical+analytical proof showed it's a numerical no-op — the PnL fraction `1 − (1∓frac)(1+slip)/(1−slip)` is scale-invariant (entry cancels). The D1_Open expectancy is carried entirely by the `(classification, resolution_day)` from `classify_trade`. Locked by `tests/test_netpnl_entry_basis_v1.py`. No WR-D1_Open / PnL-ScanPrice drift.
- **WHIPSAW-as-loss is policy-layer only** (`wr_bounds` + dashboard). Core `classify_trade` still returns WHIPSAW.
- **Persisted `TP10_Hit` columns stay ScanPrice** (window-touch diagnostic) — renamed "TP10 Hit-Rate" so they're not confused with the official D1_Open WR. No schema change (§15 unchanged).

## Verification (local — see "No test-CI" below)
- **`pytest tests/` → 311 passed**, with only **2 failures**: `tests/agent/integration/test_decision_logger_writes.py` + `test_scanner_agent_match.py` — both write/read **live Google Sheets** (`googleapis.com`), fail on missing creds in the sandbox, are flaky, and **do not reference any code changed here**. Environmental, pre-existing, unrelated.
- New + regression: 56 passed (142 suite 7, netpnl-lock 3, wr_bounds 5, classify_trade_day, net_pnl×3, backfill_netpnl). Legacy scripts: `test_formulas.py` 107/107, `test_utils.py` 38/38. `dashboard.py` ast.parse OK.

## ⚠️ No test-CI in the repo (truth gap → TASK-163)
We assumed "CI confirms 221/0" through the whole task. **There is no workflow that runs pytest** — only `filename_guard.yml` runs on push (it passed ✅). The documented "221/0" runner (PK v3.03) is **local only**: `uv run --with-requirements requirements.txt pytest`. Opened **TASK-163** (priority MEDIUM) to add a real test-CI workflow.
- Two traps for TASK-163: (1) `project_sync_20260418/` (gitignored snapshot) pollutes local collection via duplicate `test_formulas.py`/`config.py` — exclude it; (2) `tests/agent/integration/` needs Sheets creds — mark + skip in CI.

## Task status
- **TASK-142 → Done** (implemented; not merged).
- **TASK-147 → In Progress** — WR-half shipped here; **expectancy-half = TASK-162** (live expectancy dual-bound surface on D1_Open + ScanPrice-NetPnL demotion; consumes the locked `calculate_net_pnl`).
- **TASK-162** (open) — expectancy half.
- **TASK-163** (open) — test-CI workflow.

## Next steps
1. Review branch `task-142-147-wr-d1open` → merge to main (NOT done yet — needs approval).
2. TASK-163: add test-CI.
3. TASK-162: build the expectancy dual-bound surface.

Sentinel=shadow, DRY_RUN, zero change to ENTER/SKIP/sizing logic.

---

## Addendum — same session: TASK-142 merged + TASK-163 (test-CI) done

- **TASK-142 + WR-half of TASK-147 merged to main** (ff-only). HEAD after that: `f68f119`.
- **TASK-163 — Done & merged** (`649c2bb`): added the repo's **first real test-CI**. `.github/workflows/tests.yml` runs `pytest -m "not integration"` + the script-style tests on push/PR; `pytest.ini` (`testpaths=tests`) + `tests/conftest.py` (auto-mark `tests/agent/integration` as `integration`). **Verified running green on a clean runner — on both the branch AND main**: 301 passed / 2 skipped / 3 deselected (integration), formulas 107/107, utils 38/38, conclusion=success. PK → v3.08 (workflow count 16→17).
- Net: the "no pytest CI" gap that TASK-142 surfaced is closed — every push/PR now runs the suite.

**Still open:** TASK-162 (TASK-147 expectancy half) · TASK-147 In Progress until 162 lands.

---

## Addendum — same session: TASK-155 minute-bars cache + WHIPSAW resolution

**Done on branch `task-155-minute-bars` (NOT merged — branch review first). PK v3.09.**

- **New modules:** `intraday_cache.py` (`get_intraday_bars_cached` — settled-day disk cache under `data/intraday_cache/`, atomic, dependency-free; wraps the existing `get_intraday_bars`) + `utils.resolve_whipsaw` (intraday WHIPSAW resolver — WIN/LOSS only if BOTH sides appear in separate minute bars, earlier decides; one-side/same-bar/neither → UNRESOLVED, never a guessed verdict; `classify_trade` untouched). TDD: cache 4 + resolver 9.
- **Phase-0 spike was a feasibility GATE.** Critical data-quality fix: the first run enumerated 44 WHIPSAW from the raw CSV snapshot (March + v1); aligning to the official population (v2 filter + dedup + entry=D1_Open) gives **exactly 26**, and IEX coverage jumps from 62%→**96% RESOLVABLE**. Population matters.
- **Finding (offline, `docs/research/WHIPSAW_RESOLUTION_2026-06-12/`, gitignored):** the 26 WHIPSAW resolve to **8 WIN / 17 LOSS / 1 UNRESOLVED** (XNDU — only one extreme printed on IEX). Executable WR (D1_Open): optimistic **53.5%** / **RESOLVED 49.2%** / pessimistic **42.4%**. WHIPSAW skew strongly negative (68% of resolved = LOSS) — confirms RH-6.3.
- **Fed into:** TASK-162 (use resolved verdicts for the expectancy surface) + TASK-26 (WHIPSAW analysis). Offline only — **no change to official WR/dashboard/dataset** (that wiring is 162).
- Provenance note for future readers: v2 filter on the CSV snapshot yields n=128 (not the report's 149) but WHIPSAW=26 matches exactly on v2/D1_Open — bookkeeping, not a contradiction. Same-ticker rows (AEHL/AIIO/CODX/MASK ×2) are distinct scans, not dups.

**TASK-155 → Done. Branches awaiting review/merge: `task-155-minute-bars`.**
