---
id: TASK-246
title: Clean up 83 stuck DRY_RUN_OPEN positions in 2026-07 paper_portfolio
status: To Do
assignee: []
created_date: '2026-07-29 09:28'
updated_date: '2026-08-05 20:33'
labels:
  - data-integrity
  - cleanup
dependencies: []
priority: medium
ordinal: 244000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Measured live 2026-07-29, read only.

STATE: paper_portfolio 2026-07 holds 137 rows. Status distribution is DRY_RUN_OPEN 83, DRY_RUN_CLOSED 46, MANUAL_CLEANUP 8. All 83 open rows have ExitPrice, ExitDate, ExitTime and ExitReason blank. Age in trading days runs 1 to 10 with a median of 5, and 29 of 83 already exceed MAX_HOLDING_DAYS of 5.

EVERY ONE OF THE 83 IS ON A SUSPECT SYMBOL. 64 are on confirmed phantom tickers, 19 are on doubled letter candidates that were not independently confirmed, and zero are on a clean ticker. The reason they never closed is almost certainly that the symbol does not resolve at the data provider, so no current price is available, so no TP or SL can be evaluated and the monitor never exits the position.

CONSEQUENCE FOR MEASUREMENT: any win rate or exit distribution computed over July 2026 mixes two different populations, the 46 that closed and predate the corruption, and everything opened after 2026-07-15 which is stuck. Performance for this month should not be computed before this is resolved.

BLOCKED ON: the finviz ticker fix, so that the cleanup rule can distinguish a phantom from a real symbol. Any correction is a write to Sheets and needs explicit approval and a dated backup first. Never delete rows, mark them.

OPEN QUESTION: whether these rows should be marked with a distinct status rather than reusing MANUAL_CLEANUP, so that research queries can exclude them by rule.
<!-- SECTION:DESCRIPTION:END -->

## TIER RULE SETTLED 2026-08-03

The open question in the description is answered. The rows get a mark of their own, and CLEAN is a statement about shape only.

classify_phantom_tier returns CONFIRMED when the first character is doubled and the stripped form appears in the universe, SUSPECT when it is doubled and nothing corroborates it, and CLEAN only when the first character is not doubled. Real symbols that double their own first letter, AA, AAPL, III, TTOO, MMM, CCJ, WW, are therefore SUSPECT, deliberately.

Why the earlier requirement that those return CLEAN was dropped. It is not satisfiable. The rule it implied is "the symbol is itself in the universe", and mark_phantom_rows_v1.build_universe is defined as every ticker seen anywhere in the loaded tabs, so the universe contains the corrupted values too and the test is true of everything. Under that rule PHANTOM_SUSPECT is never returned in production, and SSTKH and WWLDS classify as CLEAN. Both are phantoms: STKH and WLDS appeared in the live scan of 2026-08-03.

Why provider validation was rejected. AGENT_DRY_RUN is True (config.py:340). alpaca_broker.get_asset_info returns tradable True and status active for any string in dry run (:268), and tradability.check_tradability falls back to mock on any exception (:95). The only external validator available today is fail open and would bless every phantom. It would also put IO inside formulas.py and break the purity contract and the hermetic tests.

Cost asymmetry decides it. A wrong SUSPECT excludes one legitimate row from a research sample. A wrong CLEAN lets a stuck position count as a real trade. Nothing is deleted and no metric is rewritten either way.

Future second layer, recorded not implemented: utils.validate_stock_data already returns NO_DATA when a row has no price. That is offline, pure, and already in the data, and it is the corroborating signal that could promote SUSPECT to CONFIRMED without a network call. It belongs in a layer above formulas, not inside it.

TOOL WIRED 2026-08-03. mark_phantom_rows_v1 now filters on classify_phantom_tier instead of is_confirmed_phantom alone, so both tiers are marked with distinct values: PhantomTicker gets PHANTOM or PHANTOM_SUSPECT, and paper_portfolio.DataQuality gets PHANTOM_TICKER or PHANTOM_TICKER_SUSPECT. Column choices are unchanged, so post_analysis stays required_subset and paper_portfolio stays at 25 columns. Previously the tool would have marked 67 of the 83 stuck positions and left the 16 hardest with no mark at all.

NOT DONE: no dry run has been executed against July, and nothing has been written to any sheet. The market is open. Both wait for close.

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
MEASURED 2026-08-05 — SCOPE NARROWED. Historical, confined to 2026-07, blocking nothing.

Source: reports/2026-08-05_1455_measurement.md Q-246.

paper_portfolio 2026-08, live read after the close:
  total rows            = 16
  Status counts         = {'DRY_RUN_CLOSED': 15, 'DRY_RUN_OPEN': 1}
  DRY_RUN_OPEN          = 1     (SHPH, entered 2026-08-05)
  age in trading days   = 0     (min = median = max, n = 1)
  older than MAX_HOLDING_DAYS (config.py:133 = 5) = 0
  phantom tier counts   = {'CLEAN': 1}   via formulas.classify_phantom_tier

Age was counted in TRADING days through utils.is_trading_day (NASDAQ calendar), not
calendar days.

WHAT THIS CHANGES. The phenomenon this ticket describes does not exist in the active
month. There is no accumulation, nothing past the hold window, and nothing sitting on a
corrupted symbol. The ticker fix (TASK-238, 2026-07-29) and the fail-closed account-state
guard (TASK-244, 2026-08-03) both landed before August opened.

WHAT THIS DOES NOT CHANGE. The 83 rows in the 2026-07 paper_portfolio are still there and
were not touched. The owner decision this ticket asks for — mark them, never delete —
is still open. It is now a cleanup of a closed month rather than a live containment
problem, which is why the ticket is narrowed rather than closed.

Stays To Do at low priority. Reopen scope only if a new month starts accumulating.
<!-- SECTION:NOTES:END -->
