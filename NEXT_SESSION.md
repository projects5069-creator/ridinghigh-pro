# 🎯 Next Session — Start Here

## ⚠️ Required reading order (do NOT skip)

1. docs/WORK_LOG.md — see "Next required category" line
2. docs/WORK_ALLOCATION.md §3 — the single decision rule
3. backlog task list --plain — current task state

Only after these three: pick the next task.

## Last session summary (2026-05-23)

- ✅ META.1 closed — work allocation policy written (v2)
- ✅ Created: docs/WORK_ALLOCATION.md, docs/WORK_LOG.md
- ✅ Policy: 40% maintenance / 40% development / 20% analysis (weekly hours)
- ✅ Single decision rule replaces v1 four-rule conflict
- ✅ P0 override clause added for true emergencies
- ✅ 35 tasks in backlog (4 Done, 31 To Do)

## 🎯 Computed next task: DEV.1 — Build Agent #6 Devils Advocate

Derivation:
- Current week: 4.0h Maintenance, 0h Development, 0h Analysis
- D_pct = 0% < 20% → Rule §3.1 fires → must do Development
- DEV.1 is data-independent (no historical data dependency)
- DEV.1 is next item on roadmap

Alternative dev tasks if DEV.1 blocked: DEV.2 Risk Sentinel, P2.3 Filter 12, P3.3 Market Context wiring.

## After DEV.1

Recompute Rule §3. Likely: M_pct < 50%, D_pct > 20%, A_pct still 0% → next probably Analysis (P3.5 or Wait.1).
