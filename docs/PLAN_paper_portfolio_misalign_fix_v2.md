# Fix paper_portfolio Column Misalignment — Implementation Plan **v2**

> Supersedes v1. Change vs v1: the 8 corrupted rows are **not** given reconstructed exits. Decision (עמיחי, 2026-07-01): an honest record beats a fabricated P&L. Repair recovers the shifted values and marks the rows `MANUAL_CLEANUP`; timeline_live is used only for separate after-the-fact analysis, never written back as "real" exits.

> **For agentic workers:** Use superpowers:executing-plans, task-by-task, `- [ ]` checkboxes.

**Goal:** Repair the drifted 2026-07 `paper_portfolio` tab (Status/UnrealizedPnLPct readable again) and harden the entry-writer so header drift can never corrupt data — without fabricating trade outcomes.

**Architecture:** Code is already correct (`create_agent_sheets.py:87` + `order_manager` both use the 25-col schema WITH `TPPrice`/`SLPrice`). The live 2026-07 tab was provisioned with a stale 23-col header; the 25-value positional `append_row` shifted values +2 and Sheets auto-added 2 blank columns. Fix = (A) by-name entry-write, (B) migrate 2026-07 header + recover shifted values, (C) mark the 8 rows MANUAL_CLEANUP, (D) prevent recurrence.

**Scope (verified 2026-07-01, market closed):** ONLY `2026-07` — 8 rows. `2026-05`/`06` correct.

**Canonical 25-col header:**
`PositionID·Ticker·EntryDate·EntryTime·EntryPrice·Quantity·PositionSizeUSD·Side·EntryOrderID·TPOrderID·SLOrderID·TPPrice·SLPrice·CurrentPrice·UnrealizedPnL·UnrealizedPnLPct·Status·ExitPrice·ExitDate·ExitTime·ExitReason·RealizedPnL·RealizedPnLPct·LastUpdated·DataQuality`

---

## Task 1: Harden entry-write to by-name (drift-proof) — **THIS SESSION**

**Files:** Modify `agent/execution/order_manager.py:241-273`; Test `tests/test_build_portfolio_row_v1.py`.

- [ ] **Step 1 (RED):** test `build_portfolio_row(values: dict, header: list) -> list`:
  - `test_ordered_by_header` — values placed at their header index.
  - `test_missing_col_blank` — absent column → `""` (no crash).
  - `test_unknown_key_raises` — key not in header → `KeyError` (catches drift).
  - `test_equivalence_healthy` — on the canonical header, output == the old positional list (regression guard).
- [ ] **Step 2:** run → FAIL (function missing).
- [ ] **Step 3 (GREEN):** add `build_portfolio_row` to `order_manager.py`:
  ```python
  def build_portfolio_row(values: dict, header: list) -> list:
      unknown = set(values) - set(header)
      if unknown:
          raise KeyError(f"paper_portfolio: unknown columns {sorted(unknown)}")
      return [values.get(col, "") for col in header]
  ```
- [ ] **Step 4:** rewrite the entry-write (241-273): build the same field values into a `dict`, read live header (`ws.row_values(1)`), `row = build_portfolio_row(vals, header)`, then append. Same values; ordering source = header.
- [ ] **Step 5:** run new test + `pytest -m "not integration" -q` (green except pre-existing filename_length_guard).
- [ ] **Step 6:** PK bump + changelog (§4); commit `fix(217): entry-write paper_portfolio by header-name (drift-proof)`. **No push until market close confirmed + approval.**

## Task 2: Pure recovery + MANUAL_CLEANUP tagging (no exit fabrication)

**Files:** Create `scripts/repair_paper_portfolio_misalign_v1.py`; Test `tests/test_repair_paper_portfolio_v1.py`.

- [ ] `remap_row(stale_header, stale_row, canonical)` — recover shifted values BY NAME from the stale layout; set `Status="MANUAL_CLEANUP"`, append `DataQuality` note `"orphaned by misalign 2026-07-01; no valid live exit"`. `TPPrice`/`SLPrice` → blank (unrecoverable). Exit* / Realized* → blank (NOT reconstructed).
- [ ] Tests: Status recovered→then forced to MANUAL_CLEANUP; note present; Exit fields stay blank.

## Task 3: Live migration of 2026-07 (backup → dry-run → apply)

- [ ] Backup tab → `research/…backup_<ts>.json` (abort on failure).
- [ ] Dry-run default: before/after diff table; NO writes.
- [ ] Apply (`--apply`): write canonical header row 1 → batch_update remapped rows (Status=MANUAL_CLEANUP) → delete 2 phantom cols last (never `clear()`).
- [ ] Safety gate: market closed + agent idle required.
- [ ] Live verify: header canonical, phantom==0, the 8 rows read `Status=MANUAL_CLEANUP` + note. `--restore <backup.json>` rollback path.

## Task 4: Prevent recurrence (provisioning fail-loud on header drift)

- [ ] `header_matches_canonical(existing, canonical)`; provisioning raises/logs LOUD on stale existing tab (no auto-rewrite of live data). Link TASK-216/91.

## Verification
1. `pytest -m "not integration" -q` green (except pre-existing guard).
2. Dry-run diff eyeballed → correct.
3. `--apply` (market closed) → live-verify PASS; `get_sheet_records` → Status/UnrealizedPnLPct read correctly; 8 rows = MANUAL_CLEANUP.
4. New agent_minute run → no NEW misaligned rows (Task 1).

## Rollback
`--restore <backup.json>` verbatim; Task 1/4 code via `git revert`.

## Risks
- TPPrice/SLPrice + real exits unrecoverable for the 8 rows → blank + MANUAL_CLEANUP note (honest record).
- timeline_live is FINVIZ-snapshot (≠ Alpaca) + ScanTime padding drift → usable for SEPARATE retro analysis only, never written back as live exits. (Open a separate TASK for ScanTime zero-pad.)
- Migration only market-closed + agent idle.
- 2026-08+ tabs: verify header at next rotation (Task 4).
