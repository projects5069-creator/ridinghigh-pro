# PIII Anomaly — Postmortem

> **Investigation:** P1.5 (TASK-7)
> **Date:** 2026-05-23
> **Event date:** 2026-05-15
> **Ticker:** PIII
> **Status:** Investigation complete. P1.5 → Done. Follow-up: N5 (Verify Filter 9 fix).

## Summary

PIII was a classic pump-and-dump on 2026-05-15. The Score correctly identified it (Score reached 100, avg 94 across 298 scans). The next-day open was $8.80 vs scan price $12.81 — a **31% gap down**, confirming the short thesis.

But the trade execution was catastrophic: **14 separate ENTERs on one ticker in one day**, vs the expected max of 3 per Filter 9. Net P&L: **-$423** despite the underlying thesis being correct.

## Numbers

### Decision_log
- 14 ENTERs on 2026-05-15 (between 09:40 and 14:42 Peru)
- 2 SKIPs (both earlier, on 2026-05-07, with score < 50 — correctly filtered)

### Paper_portfolio outcomes
| Outcome | Count | P&L |
|---|---|---|
| TP_HIT (win) | 4 | +$571 |
| SL_HIT (loss) | 8 | -$994 |
| MANUAL_CLEANUP | 2 | $0 |
| **Net** | | **-$423** |

Win rate: 4/12 = **33%** (vs expected ~65%)

### Score saturation
| Date | Scans | Min | Max | Avg |
|---|---|---|---|---|
| 2026-05-15 | 298 | 26.19 | 100.00 | **94.05** |

Massive concentration at the top end. 7+ ENTERs at exact Score=100.

## Root cause analysis

### What went RIGHT
- Score formula correctly identified the pump (high accuracy)
- The thesis was correct — stock fell 31% the next day
- Skip logic worked when score was low (2 early SKIPs)

### What went WRONG — Filter 9 leak (SAME bug as HCAI on 18/5)

PK v2.24 (2026-05-19) documented the same bug for HCAI:
> Filter 9 re-entry limit leak — entries_today_by_ticker was counted from paper_portfolio, whose writes can be lost to 429s. Fixed by counting from decision_log instead.

PIII on 15/5 is the SAME failure mode, 3 days EARLIER. The fix was deployed on 19/5 — after both PIII (15/5) and HCAI (18/5) occurred.

### What is STILL UNCLEAR

Was the Filter 9 fix on 19/5 complete? Two possible scenarios:

**Scenario A:** Fix is complete. PIII×14 and HCAI×4 were the only manifestations. After 19/5, no ticker exceeds 3 entries/day.

**Scenario B:** Fix only addressed the 429 case. There may be another path that lets re-entries through (e.g., timing race condition).

**This question is unanswered and is the basis for follow-up task N5.**

## Secondary finding: Score saturation

When Score >= 100 for 7+ scans in a row, the score has lost discrimination power at the top end. This is not a bug — the formula is capped. But it means the system has no way to differentiate "very strong pump" from "extreme pump." Worth tracking but not P0.

## Trade-level damage assessment

Despite a correct directional thesis (31% gap down next day), execution lost $423.

Root cause: the 14 entries caused whipsaw. Each entry chased a small intraday rebound, hit SL on the next pump leg, then re-entered. The system was fighting itself instead of holding one position for the 31% drop.

If Filter 9 had held (max 3 entries), expected outcome with same hit rate: ~3 positions × avg P&L = roughly break-even or small win.

## Action items

1. **P1.5 (TASK-7) → Done** — investigation complete.
2. **New task N5 (HIGH priority):** "Verify Filter 9 fix (v2.24) didn't leave residual re-entry leaks. Check for tickers with >3 ENTERs/day after 2026-05-19."
3. **Score saturation observation** — log for future analysis when n>91 (Wait.1 territory).

## Cross-references

- PK v2.24 (2026-05-19): Filter 9 leak root cause + fix
- TASK-4 (P1.1): HCWB×5 regression — likely same family
- TASK-26 (Wait.1): WHIPSAW analysis (when n>91) — PIII is exhibit A
