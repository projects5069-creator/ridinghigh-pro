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
| HYP-002 | minimal-MxV-gate | **REGISTERED** | 2026-07-02 | live forward-capture since 6/29 flip; concludes at n≥150 post-flip entries OR 45 trading days, first-of |
| HYP-003 | 4-dim-gate (MxV+TPD+REL_VOL+Float%) | **DRAFT** | — | tracking-only, awaiting n; criterion TBD |

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

## §F · HYP-002 — minimal-MxV-gate (REGISTERED)

### HYP-002 · minimal-MxV-gate
- Status:            REGISTERED  (live capture since the 2026-06-29 flip; criterion locked 2026-07-02)
- Registered:        2026-07-02  (criterion locked; gate itself live in config since 2026-06-29:
                     EXPLICIT_GATE_MODE=active, ENTRY_GATE_MINIMAL=True)
- Scope:             DUAL-CONDITION ONLY (MxV<=-100 ∧ price>=$3). The 3 additional research-199
                     dimensions (TPD>=6, REL_VOL>=15, Float%>=60) are TRACKING-ONLY here and are
                     deferred to HYP-003 — they do NOT gate and do NOT enter this fitness.
- Hypothesis:        the minimal entry gate (MxV<=-100 ∧ price>=$3, with Score AND the 6
                     universe/protective filters OFF) yields forward net outcomes at least
                     as good as the prior Score+full-filter gate.
- Universe:          FINVIZ screener (Price>$2 ∧ Today+15%) → tickers passing the LIVE
                     ENTRY_GATE_MINIMAL gate (MxV<=-100 ∧ price>=$3 ∧ data-quality ∧ exposure-safety).
- Entry:             SHORT, ScanPrice basis, agent DRY_RUN entry; reentry <= 1/ticker/day.
- Exit:              standard agent TP/SL (AGENT_TP_PCT / AGENT_SL_PCT).
- HOLD_DAYS:         <=5 (classify window / MAX_HOLDING_DAYS).
- Locked fitness:    net expectancy via calculate_net_pnl @ borrow 500%/yr × HOLD/365 +
                     slip 2%/side; GO = bootstrap CI on the profitable side AND not-worse
                     than the Score-gated baseline (test below).
- Not-worse test:    baseline = Score-gated entries 2026-06-01→2026-06-28, scored with the SAME
                     fitness (calculate_net_pnl @ borrow 500%/yr, slip 2%/side). Test = bootstrap
                     95% CI on the difference (minimal − baseline) in net expectancy;
                     not-worse iff the CI lower bound > −2pp. GO = profitable CI AND not-worse.
- Stopping rule:     decide ONLY at n>=150 post-flip entries OR 45 trading days post-flip
                     (2026-06-29), whichever comes FIRST. Interim peeks = safety-only (halt on
                     catastrophic loss), never decisional. The 2026-07-27 promote checkpoint
                     (TASK-194 AC#4 / TASK-128 AC#4) is a SEPARATE shadow→active decision and
                     does NOT conclude this hypothesis.
- Config freeze:     AGENT_TP_PCT=10 · AGENT_SL_PCT=10 · HOLD<=5 (the classify/fitness window,
                     = CLASSIFY_DAYS, as in the HOLD_DAYS line at :194 — NOT a live forced-exit:
                     MAX_HOLDING_DAYS is display-only and the agent has no time-based exit;
                     wording clarified 2026-07-03, E2E-audit S2/S5, zero change to the frozen values) ·
                     reentry<=1/ticker/day (AGENT_MAX_REENTRIES_PER_TICKER=1) — frozen for this
                     hypothesis; ANY change to these voids the run and requires re-registration.
- k reported:        k=2 (dual-condition HYP-002 + 4-dim HYP-003 candidate) per §A.2.
- Power target:      n >= 150 entries detected AFTER 2026-06-29 (the flip date).
- Hold-out rule:     measure ONLY post-flip entries; pre-flip Score-gated trades are the
                     comparison baseline, never recycled as discovery.
- Discovery sample:  research-199 (raw/exploratory, single-regime June, small n) —
                     provenance only, NOT evidence.
- Dependencies:      flip live ✅ · shadow_gate_events provisioned ✅ · decision_log capture ✅.
- Result:            <filled at CONCLUDED: verdict + worst-case net exp + CI + k>.

**Caveat.** This is a forward live experiment in DRY_RUN, fully reversible (ENTRY_GATE_MINIMAL=False
restores the 6 filters; EXPLICIT_GATE_MODE=shadow restores Score). It was flipped ahead of the
≥2-week multi-regime shadow precondition (TASK-194 AC#4, 0 shadow rows at flip) as an explicit
owner decision — so the early n is single-regime and NOT evidence until the power target is met.

---

## §G · HYP-003 — 4-dim-gate (DRAFT stub)

### HYP-003 · 4-dim-gate (MxV + TPD + REL_VOL + Float%)
- Status:            DRAFT  (stub — tracking-only; criterion TBD)
- Registered:        —
- Hypothesis:        adding TPD>=6 (profit engine, +6.5pp in research-199) and the tail filters
                     REL_VOL>=15 and Float%>=60 to the HYP-002 dual-condition gate improves
                     worst-case net expectancy without collapsing entry count.
- Universe:          same as HYP-002; the 3 extra dimensions are recorded as TRACKING metrics
                     only (never gate) while this is DRAFT.
- Entry/Exit/HOLD:   TBD at registration (inherit HYP-002 frozen params unless re-specified).
- Locked fitness:    TBD — criterion deliberately NOT locked yet; awaiting n
                     (research-199 reliability boundary: 3-dim n=28, +Float% collapses to n=13).
- Power target:      TBD.
- Hold-out rule:     only events after future registration date; research-199 discovery sample
                     locked, never re-scored.
- Discovery sample:  research-199 (raw/exploratory, June-concentrated, Spearman~0 between dims) —
                     provenance only, NOT evidence.
- Dependencies:      HYP-002 concluded (or its capture mature) · tracking columns accumulating ·
                     Float% integrity guards (TASK-201/203 ✅).
- Result:            —

---

## §H · NULL RESULTS (measured 2026-07-02)

Measured, not promoted — recorded so they are not re-litigated without new data
(analyze_trades_vix_v1.py, n from joined closed trades):

- **(a) MxV/ATRX per-trade outcome (TASK-62)** — no separation, n=229. MxV WIN
  med −698 vs LOSS med −559 (inverted); ATRX WIN 5.00 vs LOSS 4.90 (negligible).
  Consistent with research-199: MxV is a candidate-selection engine, not a
  per-trade predictor; ATRX ≈ noise.
- **(b) VIX-regime WR (TASK-70 / TASK-170)** — inconclusive. VIX<20 n=205 WR 53.7%,
  20-30 n=14 WR 57.1%, >30 n=0. The whole 05-07 window was low-vol → no regime
  variance; the original TASK-70 finding (72% vs 58%) did NOT reproduce.
- **Neither promoted.** Re-test triggers: real VIX variance (entries at >30) /
  larger n in the mid-bucket.

---

## §E · Integration (TASK-165 AC#2)

- **Session close ritual** (`docs/SESSION_PROTOCOL.md`): when a session produced
  or touched a research hypothesis, confirm it is registered here before close.
- **PK** (`docs/RidingHigh_Pro_PK_v2.md`): this register is the SoT for research
  governance; the PK points here rather than duplicating the policy.
- Any change to §A (the locked policy) is an Anti-Drift event — bump the PK.

---

*— END —*
