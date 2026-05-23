# Work Allocation Policy — RidingHigh Pro

> **Version:** 2 (improved from META.1 v1)
> **Status:** Active from 2026-05-23
> **Owner:** Amihay Levy
> **First review:** 2026-06-06

## 1. The Problem

End-of-session review on 2026-05-23 revealed an unhealthy distribution across the 32 open backlog tasks: Maintenance 22 tasks (69%), Development 6 (19%), Analysis 3 (9%), Meta 1 (3%). Five sessions in a row went to maintenance only. Roadmap items (Devils Advocate, Risk Sentinel) sat idle.

## 2. The Policy

Target weekly time allocation (HOURS, not tasks):
- 40% Maintenance — bugs, regressions, hygiene, config drift
- 40% Development — new agents, filters, features
- 20% Analysis — research, post-trade study, statistical work

Meta time (planning, retros, this policy) is excluded from the budget. It is overhead, not work product.

## 3. The Single Decision Rule

Before starting any new task, compute three numbers for the current week:
- M_pct = maintenance_hours / (maintenance + development + analysis)
- D_pct = development_hours / (maintenance + development + analysis)
- A_pct = analysis_hours / (maintenance + development + analysis)

Priority order (first match wins):
1. If D_pct < 20% → next task MUST be Development.
2. Else if A_pct < 10% → next task MUST be Analysis.
3. Else if M_pct > 50% → next task MUST be Development or Analysis.
4. Else → free choice.

## 4. Exception — P0 Override

If a P0 task lands mid-week (system actively losing money or data), Rule §3 is suspended for that task only. The override must be logged in WORK_LOG.md with the reason. The next non-P0 task must rebalance.

P0 examples: Trader entering live trades with wrong sign; Sentinel blocking 100% of valid signals; data loss event.

NOT P0: high-priority bug that can wait a day; regression not affecting production decisions; urgent tech debt.

## 5. Category Definitions

Maintenance (40%): fixing what is broken. Examples: P0.2, P1.1, P1.2, P1.4, P1.5, P2.1, P2.4, P3.1, P3.2, P3.4, P3.6, P3.7, P4.1, P4.3, P4.4, P4.5, P4.6, P4.7, N1, N2, N3, N4, Wait.3.

Development (40%): building something new. Examples: DEV.1, DEV.2, P2.3, P3.3, Wait.2.

Analysis (20%): looking at data, drawing conclusions. Examples: P2.2, P3.5, Wait.1.

Meta (uncapped, excluded from budget): planning, retros.

## 6. Tracking

Each session appends to docs/WORK_LOG.md: date, task IDs, category, hours.

Hard rule: first action of every session is to read WORK_LOG.md and apply Rule §3 BEFORE choosing the next task. NEXT_SESSION.md enforces this by pointing the next reader at WORK_LOG.md first.

## 7. Weekly Review

Every Friday EOD: sum hours per category, compute M_pct / D_pct / A_pct, record in WORK_LOG.md as "Week summary". Any category deviating ±10% from target → note WHY. Two consecutive weeks outside ±10% → revisit the policy itself.

## 8. Why Not 33/33/33?

Maintenance is reactive and infinite. Capping at 40% forces prioritization. Development creates future value, equal weight. Analysis informs everything but does not ship code, smallest slice.

## 9. Changelog

- v2 (2026-05-23): single decision rule replaces 4 conflicting rules; P0 override added; weekly review formalized; tracking enforced via NEXT_SESSION.md handoff.
- v1 (2026-05-23): initial version.
