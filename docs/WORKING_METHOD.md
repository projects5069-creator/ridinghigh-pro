# Working Method

Distilled from `reports/2026-08-06_0911_method_final.md` — the **corrected** method only.
Every correction in it came from evidence that contradicted the first draft; the audit
trail and the eight things that changed stay in the report, not here.

⚠️ This document describes how work is *conducted*. It does not override `CLAUDE.md`,
`docs/SESSION_PROTOCOL.md` or `docs/RUN_MODE_DECISION.md`. Where it appears to, the
written rule wins and the conflict goes to §7 below.

---

## 1. The dividing line — reversibility

The question is not "is this important" but **"can one command undo it".**

**Requires עמיחי:**
- an action that **cannot be undone with a single command** — merge, push to `main`,
  a write to a live sheet, a deletion, a force-push
- a policy decision
- a choice between genuinely equivalent alternatives
- ⚠️ **when the evidence contradicts the instruction**
- ⚠️ **when something fails in a way the instruction did not anticipate**

**Does not require עמיחי:**
- verifying that an already-approved action actually happened
- pushing to a feature branch
- an investigation that changes nothing
- carrying out a step that was explicitly approved

---

## 2. Four kinds of turn

| kind | what it does | עמיחי | chat output |
|---|---|---|---|
| **RECON** | investigates, measures. **May write to `reports/` and to local artifacts** — that is not "a change" | only if the finding needs a decision | **10 lines of numbers** |
| **BUILD** | TDD → implement → `py_compile` → tests → diff → **stop** | **always** — approves the diff | **15 lines** + the five mandatory items |
| **LAND** | add → verify the index → commit → `git log -1` → push → verify → report + INDEX | no — **unless it fails** | **5 lines** |
| **GATE** | irreversible | **always** | the evidence + the question + the alternatives |

---

## 3. Decision tree

```
irreversible with one command?                    → GATE
edits a protected path (RUN_MODE_DECISION:40-43)? → BUILD, and a SEPARATE GATE to deploy
a decision whose outcome is a write to a live sheet?
                                                  → RECON (designs) then GATE (executes).
                                                    No BUILD in between.
produces a local artifact only (CSV, report)?     → RECON
changes code?                                     → BUILD then LAND
an investigation?                                 → RECON
```

The three boundaries that used to be ambiguous are the middle three. They are the ones
worth re-reading.

---

## 4. Chat summaries — subject to RULE #7

**Not "10 lines of interpretation".** RULE #7 (`CLAUDE.md:112-119`) forbids paraphrasing
output and prescribes: raw output; if long, **first 50 lines + last 20 with a marker**;
interpretation only when asked.

⚠️ **The numbers above (10 / 15 / 5) are a ceiling on INTERPRETATION, not on OUTPUT.**
Raw output is not counted against them.

---

## 5. The standard block

- **No line limit.** Measured: the long blocks produced the best work.
- **One task per block.** This is already `SESSION_PROTOCOL:154`.
- The report file is created **on the first line**, so a truncated turn still leaves a file.
- A completion marker is mandatory.

---

## 6. Safety — unchanged

`/goal` and auto-mode stay **frozen** until:
- **TASK-237** closes (a ceiling enforced *inside* a run), and
- **TASK-262** closes (a stable suite), and
- a measurable stop condition is written **in advance**.

**TASK-121 was not cancelled.**

---

## 7. Metrics

| metric | today | target | measurable? |
|---|---|---|---|
| turns per day | **30** | ≤15 | ✅ from `ls reports/` |
| lines per report (median) | **344** | — *(not a target; the report is not read end to end)* | ✅ `wc -l` |
| **plumbing share** | **24%** (8/34) | **≤10%** | ✅ `grep -cE "_commit\|_push\|_merge"` |
| ~~lines עמיחי reads~~ | — | — | ❌ **not measurable. Removed.** |

"Plumbing" = turns that only commit, push or merge and produce no new knowledge.

---

## 8. Open — not settled, and the method is incomplete until they are

1. **RULE #7 vs. the short summary.** The rule forbids paraphrase and allows 50+20. Is a
   short summary an approved exception, or is 50+20 the format? Without a ruling the
   method contradicts a written rule.
2. **RULE #12 (`.rh-run.sh`).** Enforce it, retire it, or record it as a standing
   exception? It has been skipped in effectively every turn.
3. **Does approving the diff in BUILD also cover commit and push?** `RULE #5` requires
   *"The user will say commit or push explicitly"*.
4. **Who writes `INDEX.md`, and when**, once LAND is a single step.
5. ⚠️ **Are the stop thresholds (`RUN_MODE_DECISION:47`) and the protected paths (`:40-43`)
   actually implemented in code?** Never checked. If they are prose only, the entire
   safety layer is discipline rather than enforcement.
6. ⚠️ **The third branch of the decision tree** — RECON→GATE with no BUILD — has never
   been tried on a real ticket.
