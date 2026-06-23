# RidingHigh Pro — Research Hypotheses Register

*Pre-registration ledger. Single source of truth for every research hypothesis
before it touches new data. Exists to prevent post-hoc overfit (cf. the n=26
EXPLORATORY tag on TASK-26): the fitness, the entry/exit rule, the success
threshold, and the hold-out split are written down and LOCKED before the
validation data is collected — never tuned to the data afterward.*

*Created: TASK-165 (2026-06-13). Methodology anchored to Investigation II.*

---

## §0 · Purpose

When a candidate edge is discovered, the temptation is to refine the rule until
the historical numbers look good — which is exactly how Investigation I's
"edge" turned out to be look-ahead. This register breaks that loop. A hypothesis
is registered (§B form) with a **locked, zero-discretion** rule and a **single
GO/NO-GO fitness number** BEFORE validation data exists. Validation (TASK-179)
then runs on data collected strictly AFTER registration. The discovery sample
that generated the hypothesis is locked and never re-used as evidence.

---

## §A · Locked research policy (iron rules — apply to every hypothesis)

These define HOW fitness is measured. The methodology here is locked; only the
per-hypothesis VALUES (in each §B record) move, and only until that record is
registered.

1. **Purged train/validation split + 5-day embargo** between discovery and
   validation windows (no leakage across the boundary).
2. **Multiple-testing deflation** — Benjamini-Hochberg; the number of
   hypotheses/configs tested (k) is reported alongside any result.
3. **Minimum power** — n ≥ 150 events for a primary validation; n ≥ 30 floor
   for any sub-segment examined. Locked before data collection so the run
   cannot stop "when it looks good".
4. **Out-of-sample mandatory** — the discovery sample is NEVER recycled as
   validation evidence.
5. **Locked fitness = worst-case net expectancy, three components, all required:**
   - **(a) Cost model:** `calculate_net_pnl` (TASK-140) at worst-case
     **borrow 500%/yr** + **slip 2× (= 2 × config.SLIP = 2%/side)**.
     Borrow accrues on the holding period: `borrow_cost = 500%/yr ×
     HOLD_DAYS / 365`. The dual-bound 50/200/500 is REPORTED for context, but
     the **gate is the worst-case (500%) only**.
   - **(b) Significance, not point estimate:** GO requires the **entire
     bootstrap CI** to stay on the profitable side (for a short: net
     expectancy significantly negative price-move ⇒ short profit). A bare
     negative point estimate that straddles zero is NO-GO.
   - **(c) Power:** n ≥ 150 new events (rule 3).
6. **Discovery sample is locked** — recorded for provenance, never re-scored.

---

## §B · Pre-registration form (template)

Copy this block per hypothesis into §C. A record is REGISTERED only when every
field is filled with a zero-discretion value and its dependencies are met.

```
### HYP-<NN> · <short name>
- Status:            DRAFT | REGISTERED | VALIDATING | CONCLUDED:GO | CONCLUDED:NO-GO
- Registered:        <date the rule was locked, or "—" while DRAFT>
- Hypothesis:        <one sentence — the edge>
- Universe:          <which instruments/events are eligible — zero discretion>
- Entry:             <exact trigger, side, price type — zero discretion>
- Exit:              <exact rule: time / TP / SL — zero discretion>
- HOLD_DAYS:         <fixed holding period used in the borrow accrual>
- Locked fitness:    net expectancy via calculate_net_pnl @ borrow 500%/yr ×
                     HOLD_DAYS/365 + slip 2%/side; GO = full bootstrap CI on the
                     profitable side; dual-bound 50/200/500 reported for context
- Power target:      n ≥ 150 new events (post-registration)
- Hold-out rule:     validation runs ONLY on events detected after Registered
                     date; discovery sample locked, never re-scored
- Discovery sample:  <n + window + source — provenance only, NOT evidence>
- Dependencies:      <tasks/data that must land before REGISTERED>
- Result:            <filled at CONCLUDED: verdict + worst-case net exp + CI + k>
```

---

## §C · Experiment journal (append-only)

One row per registered hypothesis. Never edit a CONCLUDED row — append a new
record if a hypothesis is re-opened under a new rule.

| ID | Name | Status | Registered | Verdict |
|----|------|--------|-----------|---------|
| HYP-001 | crossover-short | **REGISTERED** | 2026-06-23 | validation pending TASK-179 (n≥150, ~mid-July) |

---

## §D · HYP-001 — crossover-short (REGISTERED)

> **REGISTERED 2026-06-23 (TASK-178). The rule is now LOCKED — HOLD_DAYS,
> entry, and exit are fixed and may NOT be tuned to validation data. Dependencies
> cleared at registration: TASK-172 (coverage) ✅, TASK-177 (D1-D25 superset) ✅,
> and PHASE 0 data-integrity blockers (TASK-180/150/105/144) all ✅. Validation
> (TASK-179) runs only on crossover events detected AFTER this date.**

**Hypothesis.** SHORT a DropsLab breakdown-event in a ticker that was an
RH pump (scanner trigger, e.g. +15%) within the preceding <=10 calendar days —
betting on continuation of the fall.

**Universe.** Tickers that (a) fired an RH scanner trigger AND (b) recorded a
DropsLab drop-event within <=10 calendar days of the RH scan.
**Shortability gate:** an event whose ticker is IsShortable=FALSE (e.g. EDHL,
6/12) is EXCLUDED from the tradable universe — not counted as a loss — with an
explicit survivorship-transparency note in any reported result.

**[!] Three distinct time anchors — RESOLVED by TASK-178 (2026-06-23):**
- **Crossover window = <=10 calendar days** — how soon after the RH pump the
  ticker crosses into DropsLab. Defines universe membership.
- **Hold window = D1→D5 from the drop-event** (entry d1_close → exit d5_close,
  5 trading days, time-only). **LOCKED to equal the discovery window.** The
  earlier D6-D15 framing is REJECTED: it was an untested window, and validating a
  different window than the one discovery measured is methodologically unsound
  (backtest-expert: validate the window you actually discovered). TASK-177's
  D6-D25 data remains available but is NOT used by this hold rule.
- **Discovery window = 5 days post-event** — what the discovery sample measured;
  the validation hold window now EQUALS it (no window mismatch remains).

**Entry.** SHORT at **d1_close of the drop-event day** (DropsLab is
closes-only per OQ-2 -> close-to-close entry, zero-discretion).

**Exit (LOCKED by TASK-178).** Cover at **D5_Close — exactly 5 trading days after
the d1_close entry; time-only, zero-discretion, NO TP/SL.** This matches the
discovery measurement (close-to-close D1→D5), verified against
`docs/research/INVESTIGATION_2026-06-12_II/phase_evidence.md` (the −17.75% n=62 is a
pure 5-day continuation with no stops). *TP/SL grid-sensitivity remains a TASK-179
question (explored with BH deflation). The **±10% band (TP10/SL10)** that appears in
the dashboard short-simulation is the **SIMULATION exit (sim/179), NOT this
pre-registered rule** — see the §D↔PK-v3.21 reconciliation in the PK changelog.*

**Locked fitness (sealed by 178).** Per §A.5: `calculate_net_pnl(short)` at
borrow **500%/yr x HOLD_DAYS/365** + slip **2%/side**, GO only if the entire
bootstrap CI stays profitable-for-short on **n >= 150 new events** (n >= 30 per
sub-segment). **HOLD_DAYS = 5** (LOCKED by TASK-178) → borrow accrual
**500%/yr × 5/365 ≈ 6.85%** of position value.
*Borrow sensitivity (illustration only, NOT the gate): at 5d ≈ 6.85%, at 15d
≈ 20.5% — the gate uses the locked HOLD_DAYS=5.*
*Why slip 2x and not the 0.5%/side phase-5 baseline: crossover-short enters
stocks in active collapse (HTB, thin liquidity, wide spreads) where realistic
slippage exceeds baseline — part of the deliberate "punish".*

**Discovery signal (EXPLORATORY, locked, never re-scored).** 66% (123/185) of
RH pumps cross into DropsLab within <=10 days; post-event continuation
**-17.75% [-24.5, -11.0], n=62** over 5 days (≈ +17.75% gross short profit).
MEDIUM confidence, selection on a known event, borrow unpriced -> NOT evidence
for the validation.

**[✓] Discovery and validation windows now MATCH.** TASK-178 resolved this by
locking the hold window to the **same 5-day** post-event window the discovery
measured (entry d1_close → exit d5_close). The −17.75% is gross-price evidence for
exactly this window; validation (179) re-measures it net of worst-case borrow +
slip 2× on a fresh out-of-sample n≥150. (The former "biggest open weakness" — a
mismatched D6-D15 hold — is removed, not papered over: D6-D15 was rejected, not
adopted.) Remaining honest caveat: the discovery n=62 is selection on a known event,
borrow unpriced, MEDIUM confidence → still NOT evidence; only the hold-out validates.

**Hold-out.** Validation events = any crossover identified AFTER the
registration date. The n=62 discovery set is locked, never recycled (179 AC#1).
Power target: >=150 new events (~450 RH rows, ~4-5 months at current rate).

**Dependencies (AC#2 — all cleared at registration).** TASK-172 ✅ DONE (borrow
shortability flags + borrow_coverage tab) · TASK-177 ✅ DONE (scan-anchored D1-D25
superset) · PHASE 0 data-integrity ✅ (TASK-180 split/halt detector, TASK-150 schema
drift, TASK-105 paper_portfolio write, TASK-144 DropsLab — all Done). The hold-window
definition was TASK-178's to make (now locked above), not TASK-177's.

**Status: REGISTERED (2026-06-23, TASK-178)** — rule LOCKED. Next: TASK-179
validation on the forward hold-out (n≥150, ~mid-July).

---

## §E · Integration (TASK-165 AC#2)

- **Session close ritual** (`docs/SESSION_PROTOCOL.md`): when a session produced
  or touched a research hypothesis, confirm it is registered here before close.
- **PK** (`docs/RidingHigh_Pro_PK_v2.md`): this register is the SoT for research
  governance; the PK points here rather than duplicating the policy.
- Any change to §A (the locked policy) is an Anti-Drift event — bump the PK.

---

*— END —*
