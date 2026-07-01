# Fix paper_portfolio Column Misalignment (2026-07 tab) — Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement task-by-task. Steps use `- [ ]` checkboxes.

**Goal:** Repair the drifted 2026-07 `paper_portfolio` tab so `Status`/`UnrealizedPnLPct` read correctly again, and harden the entry-writer so a future header drift can never corrupt data.

**Architecture:** The code is already correct — `create_agent_sheets.py:87` and `order_manager` both use the 25-column schema **with** `TPPrice`/`SLPrice` at index [11][12]. The **live 2026-07 tab** was provisioned with a stale 23-col header (no TP/SL); `order_manager`'s 25-value positional `append_row` shifted every value +2 from `CurrentPrice`, and Sheets auto-extended the tab with 2 blank columns. Fix is: (A) harden entry-write to by-name so positional drift can't corrupt again, (B) one-time migrate+repair the 2026-07 tab, (C) prevent recurrence in provisioning.

**Tech Stack:** Python 3.11 (prod) / 3.9.6 (local), gspread, pytest, `uv run`.

**Scope (verified 2026-07-01, market closed):** ONLY the `2026-07` tab is affected — 8 data rows. `2026-05`/`2026-06` headers are correct (TP/SL present, 0 phantom).

**Canonical 25-column header** (order_manager row order == create_agent_sheets):
```
0 PositionID · 1 Ticker · 2 EntryDate · 3 EntryTime · 4 EntryPrice · 5 Quantity ·
6 PositionSizeUSD · 7 Side · 8 EntryOrderID · 9 TPOrderID · 10 SLOrderID ·
11 TPPrice · 12 SLPrice · 13 CurrentPrice · 14 UnrealizedPnL · 15 UnrealizedPnLPct ·
16 Status · 17 ExitPrice · 18 ExitDate · 19 ExitTime · 20 ExitReason ·
21 RealizedPnL · 22 RealizedPnLPct · 23 LastUpdated · 24 DataQuality
```

---

## File Structure
- **Modify** `agent/execution/order_manager.py` — entry-write becomes by-name (dict → header-ordered list) instead of positional.
- **Create** `scripts/repair_paper_portfolio_misalign_v1.py` — one-time diagnostic + dry-run + repair for the 2026-07 tab (backup → remap rows → rewrite header + rows).
- **Modify** `agent/setup/create_agent_sheets.py` (or provisioning path) — idempotent header-reconcile so a stale tab is auto-corrected (ties to TASK-216).
- **Create** `tests/test_order_manager_by_name_row_v1.py` — entry-row alignment tests.
- **Create** `tests/test_repair_paper_portfolio_v1.py` — pure remap-logic tests.

---

## Task 1: Harden entry-write to by-name (prevents recurrence)

**Files:**
- Modify: `agent/execution/order_manager.py:241-267` (the positional `row = [...]`)
- Test: `tests/test_order_manager_by_name_row_v1.py`

- [ ] **Step 1: Write the failing test** — a helper `build_portfolio_row(values: dict, header: list) -> list` returns values ordered by `header`, blanks for missing, and never silently drops a key.

```python
from agent.execution.order_manager import build_portfolio_row

CANON = ["PositionID","Ticker","EntryDate","EntryTime","EntryPrice","Quantity",
    "PositionSizeUSD","Side","EntryOrderID","TPOrderID","SLOrderID","TPPrice","SLPrice",
    "CurrentPrice","UnrealizedPnL","UnrealizedPnLPct","Status","ExitPrice","ExitDate",
    "ExitTime","ExitReason","RealizedPnL","RealizedPnLPct","LastUpdated","DataQuality"]

def test_row_is_ordered_by_header():
    vals = {"PositionID":"P1","Ticker":"ABC","Status":"DRY_RUN_OPEN",
            "TPPrice":9.0,"SLPrice":11.0,"DataQuality":"CLEAN"}
    row = build_portfolio_row(vals, CANON)
    assert len(row) == len(CANON)
    assert row[CANON.index("Status")] == "DRY_RUN_OPEN"
    assert row[CANON.index("TPPrice")] == 9.0
    assert row[CANON.index("DataQuality")] == "CLEAN"
    assert row[CANON.index("ExitPrice")] == ""   # missing -> blank

def test_unknown_key_raises():
    import pytest
    with pytest.raises(KeyError):
        build_portfolio_row({"NotAColumn": 1}, CANON)
```

- [ ] **Step 2: Run to verify it fails** — `uv run --with-requirements requirements.txt --with pytest python -m pytest tests/test_order_manager_by_name_row_v1.py -q` → FAIL (import error).

- [ ] **Step 3: Implement `build_portfolio_row`** in `order_manager.py` (module-level):

```python
def build_portfolio_row(values: dict, header: list) -> list:
    """Order `values` (col_name -> value) by `header`; blank for absent columns.
    Raises KeyError if `values` has a key not in `header` (catches schema drift)."""
    unknown = set(values) - set(header)
    if unknown:
        raise KeyError(f"paper_portfolio: unknown columns {sorted(unknown)}")
    return [values.get(col, "") for col in header]
```

- [ ] **Step 4: Rewrite the entry-write** (`order_manager.py:241-273`) to build a `dict` of the same fields, read the live header (`ws.row_values(1)`), and call `build_portfolio_row(vals, header)` before append. Keep the exact same field values; only the ordering source changes from positional to header-driven.

- [ ] **Step 5: Run tests + full suite** — `... pytest tests/test_order_manager_by_name_row_v1.py -q` PASS, then `... pytest -m "not integration" -q` (expect prior 600 + new, 1 pre-existing filename_length_guard fail).

- [ ] **Step 6: Commit** — `git add agent/execution/order_manager.py tests/test_order_manager_by_name_row_v1.py && git commit -m "fix(217): entry-write paper_portfolio by header-name (drift-proof)"`

---

## Task 2: Pure remap logic for the 8 corrupted rows

**Files:**
- Create: `scripts/repair_paper_portfolio_misalign_v1.py` (pure fn first)
- Test: `tests/test_repair_paper_portfolio_v1.py`

- [ ] **Step 1: Failing test** — `remap_row(stale_header, stale_row, canonical_header)` returns a row aligned to `canonical_header`, recovering shifted values by NAME from the stale layout.

```python
from scripts.repair_paper_portfolio_misalign_v1 import remap_row

STALE = ["PositionID","Ticker","EntryDate","EntryTime","EntryPrice","Quantity",
  "PositionSizeUSD","Side","EntryOrderID","TPOrderID","SLOrderID","CurrentPrice",
  "UnrealizedPnL","UnrealizedPnLPct","Status","ExitPrice","ExitDate","ExitTime",
  "ExitReason","RealizedPnL","RealizedPnLPct","LastUpdated","DataQuality","",""]
CANON = [...]  # the 25-col canonical from the header block above

def test_recovers_status_from_exitdate_position():
    # stale row as observed: Status value sits in ExitDate col, DataQuality in trailing blank
    row = ["P1","CANF","2026-07-01","08:45","4.77","190","999.4","short","oid","tp","sl",
           "4.293","5.247","", "", "", "DRY_RUN_OPEN","","","","","","2026-07-01T08:45","","CLEAN"]
    out = remap_row(STALE, row, CANON)
    assert out[CANON.index("Status")] == "DRY_RUN_OPEN"
    assert out[CANON.index("DataQuality")] == "CLEAN"
    assert out[CANON.index("CurrentPrice")] == "4.293"
    assert out[CANON.index("TPPrice")] == ""   # never captured on this tab; blank is acceptable
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement `remap_row`** — build `{stale_header[i]: row[i]}` (last non-blank wins for duplicate ''), then order by `canonical_header`. Because the stale write mixed positional-entry + by-name-update, map by the *stale header name* where present, else leave blank. Document that `TPPrice`/`SLPrice` are unrecoverable on this tab (were never in its header) → blank, non-fatal.

- [ ] **Step 4: Run → PASS.**

- [ ] **Step 5: Commit** — `git add scripts/repair_paper_portfolio_misalign_v1.py tests/test_repair_paper_portfolio_v1.py && git commit -m "feat(217): pure remap_row for stale paper_portfolio rows + tests"`

---

## Task 3: Live migration of the 2026-07 tab (backup → dry-run → apply)

**Files:** `scripts/repair_paper_portfolio_misalign_v1.py` (main()); no prod-code.

- [ ] **Step 1: Backup** — main() first dumps the full 2026-07 tab (`ws.get_all_values()`) to `research/paper_portfolio_2026-07_backup_<ts>.json` (gitignored). Abort if backup write fails.
- [ ] **Step 2: Dry-run (default)** — read stale header + rows, compute `remap_row` for each, print a before/after diff table (Ticker, old Status-col, new Status), and the new header. **No writes.** Flag: `--apply` required to write.
- [ ] **Step 3: SAFETY GATE — open positions** — if ANY remapped row has `Status in (OPEN, DRY_RUN_OPEN)`, print a loud warning and require `--force`; migrating a live-monitored row risks a monitor race. (Market must be closed; agent_minute idle.)
- [ ] **Step 4: Apply (`--apply`)** — write the canonical 25-col header to row 1, then `batch_update` each remapped data row. Delete the 2 phantom trailing columns LAST (`ws.delete_columns` / resize) so the tab is exactly 25 cols. Never `clear()` the whole tab (avoids a window with zero data).
- [ ] **Step 5: Live verify** — re-read the tab: header == canonical, phantom==0, and every previously-corrupted row now has non-empty `Status` where it had a value. Print PASS/FAIL.
- [ ] **Step 6: Do NOT commit sheet state** (it's live data). Commit only the script if changed. Record the run + row-count in TASK-217 notes + PK.

---

## Task 4: Prevent recurrence (provisioning header-reconcile)

**Files:** `agent/setup/create_agent_sheets.py`

- [ ] **Step 1: Failing test** — a helper `header_matches_canonical(existing, canonical) -> bool` and, when a tab exists with a stale header, provisioning logs a LOUD error (fail-closed) rather than silently leaving it. (Mirror TASK-91/216 "atomic + fail-loud" intent.)
- [ ] **Step 2–4:** Implement the check in the provisioning path; on mismatch for an existing tab, raise/log (do NOT auto-rewrite live data — that's Task 3's job). Link to TASK-216.
- [ ] **Step 5: Commit** — `git commit -m "feat(217/216): provisioning fails loud on paper_portfolio header drift"`

---

## Verification (end-to-end)
1. `uv run ... pytest -m "not integration" -q` → all green except the known pre-existing `filename_length_guard`.
2. Dry-run the repair script → before/after diff looks correct; NO writes.
3. `--apply` (market closed) → live-verify PASS (header canonical, 0 phantom, Status populated).
4. Read `paper_portfolio` 2026-07 via `get_sheet_records` → `UnrealizedPnLPct` + `Status` now read correctly for the repaired rows.
5. Trigger one agent_minute run (or wait for the schedule) → confirm no NEW misaligned rows (Task 1's by-name write) and that any still-open position is now found by `monitor_all`.

## Rollback
- If `--apply` misbehaves: restore from `research/paper_portfolio_2026-07_backup_<ts>.json` (write header + rows back verbatim). Script must include a `--restore <backup.json>` path.
- Task 1 (code) rolls back via `git revert`.

## Risks / Open Questions
- **TPPrice/SLPrice unrecoverable** on the 8 rows (never stored on the stale tab) → they stay blank; acceptable (they're reference levels, not P&L). Note in PK.
- **Mixed positional+by-name writes** on the stale rows mean the exact per-cell provenance can differ per row — Task 3 dry-run diff MUST be eyeballed before `--apply`.
- **Open positions during migration** — do only when market closed + agent idle (Task 3 Step 3 gate).
- **2026-08+ tabs** — verify their header at next rotation (Task 4); if the rotation used the same stale path, 08 could drift too.

## Anti-Drift
Before committing Task 1/4 code: bump PK + changelog (§4) describing the by-name entry-write + provisioning guard.
