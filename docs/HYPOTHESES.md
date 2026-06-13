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
| HYP-001 | crossover-short | **DRAFT** | — | pending (blocked on TASK-172 coverage + TASK-177) |

---

## §D · HYP-001 — crossover-short (DRAFT)

> **Methodology (§A) is LOCKED. The specific VALUES of this record
> (HOLD_DAYS, the entry/exit hold window) are NOT locked — they are sealed by
> TASK-178, after TASK-172 (coverage) and TASK-177 (hold window) land.**

**Hypothesis.** SHORT a DropsLab breakdown-event in a ticker that was an
RH pump (scanner trigger, e.g. +15%) within the preceding <=10 calendar days —
betting on continuation of the fall.

**Universe.** Tickers that (a) fired an RH scanner trigger AND (b) recorded a
DropsLab drop-event within <=10 calendar days of the RH scan.
**Shortability gate:** an event whose ticker is IsShortable=FALSE (e.g. EDHL,
6/12) is EXCLUDED from the tradable universe — not counted as a loss — with an
explicit survivorship-transparency note in any reported result.

**[!] Three distinct time anchors — do NOT conflate (this is the central open
question TASK-177 must resolve):**
- **Crossover window = <=10 calendar days** — how soon after the RH pump the
  ticker crosses into DropsLab. Defines universe membership.
- **Hold window = D6-D15** — how long the short is held after entry. TASK-177
  must define this precisely, including D6-D15 measured from WHAT (the pump, or
  the drop-event). Currently UNRESOLVED.
- **Discovery window = 5 days post-event** — what the discovery sample actually
  measured. This is NOT the validation hold window.

**Entry.** SHORT at **d1_close of the drop-event day** (DropsLab is
closes-only per OQ-2 -> close-to-close entry, zero-discretion).

**Exit.** `[PENDING TASK-177]` — discovery used the D+5 close; the validation
hold window is **D6-D15, to be locked by TASK-177**. NOT fixed to D+5 here. No
discretionary TP/SL in the DRAFT; TP/SL grid-sensitivity is a TASK-179 question.

**Locked fitness (sealed by 178).** Per §A.5: `calculate_net_pnl(short)` at
borrow **500%/yr x HOLD_DAYS/365** + slip **2%/side**, GO only if the entire
bootstrap CI stays profitable-for-short on **n >= 150 new events** (n >= 30 per
sub-segment). HOLD_DAYS is the §A.5(a) placeholder — locked by TASK-177, NOT
fixed here.
*Borrow sensitivity (illustration only, NOT the gate): at 5d ≈ 6.8%, at 15d
≈ 20.5% of position value — the gate uses whatever HOLD_DAYS 177 locks.*
*Why slip 2x and not the 0.5%/side phase-5 baseline: crossover-short enters
stocks in active collapse (HTB, thin liquidity, wide spreads) where realistic
slippage exceeds baseline — part of the deliberate "punish".*

**Discovery signal (EXPLORATORY, locked, never re-scored).** 66% (123/185) of
RH pumps cross into DropsLab within <=10 days; post-event continuation
**-17.75% [-24.5, -11.0], n=62** over 5 days (≈ +17.75% gross short profit).
MEDIUM confidence, selection on a known event, borrow unpriced -> NOT evidence
for the validation.

**[!] Discovery vs validation windows DIFFER.** The -17.75% is evidence for the
**5-day** post-event window ONLY. The proposed validation hold (D6-D15) is a
**different, not-yet-tested window** — the -17.75% does NOT transfer to it.
TASK-177 must resolve whether D6-D15 extends or replaces the discovery window,
and TASK-178 must NOT lock until it does. This is the hypothesis's biggest open
weakness, kept visible by design.

**Hold-out.** Validation events = any crossover identified AFTER the
registration date. The n=62 discovery set is locked, never recycled (179 AC#1).
Power target: >=150 new events (~450 RH rows, ~4-5 months at current rate).

**Dependencies.** TASK-172 (borrow shortability flags — collecting verified
6/11, universe-coverage still open) · TASK-177 (hold window D6-D15).

**Status: DRAFT** — not locked until TASK-178, after 172 + 177.

---

## §E · Integration (TASK-165 AC#2)

- **Session close ritual** (`docs/SESSION_PROTOCOL.md`): when a session produced
  or touched a research hypothesis, confirm it is registered here before close.
- **PK** (`docs/RidingHigh_Pro_PK_v2.md`): this register is the SoT for research
  governance; the PK points here rather than duplicating the policy.
- Any change to §A (the locked policy) is an Anti-Drift event — bump the PK.

---

*— END —*
