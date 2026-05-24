# RidingHigh Pro — Open Issues

> **As of 2026-05-23, all task tracking has moved to `Backlog.md`.**
> This file is intentionally minimal — do not add new issues here.

## Where to find current open issues

- **Live state:** Run `backlog task list --plain`
- **Detailed task files:** `backlog/tasks/`
- **Allocation policy:** `docs/WORK_ALLOCATION.md`
- **Session continuity:** `NEXT_SESSION.md`

## Where to find historical context

- **Pre-2026-05-23 issues archive:** `OPEN_ISSUES_archive.md` (frozen for reference)
- **PK changelog:** `docs/RidingHigh_Pro_PK_v2.md` (system-level decisions)
- **Research artifacts:** `research/` (investigations, postmortems)

## Why this changed

The free-form `OPEN_ISSUES.md` format (issue numbers, ad-hoc structure) became unwieldy as the system grew. Backlog.md (managed via `backlog` CLI) provides:
- Structured priorities (HIGH / MEDIUM / LOW)
- Status tracking (To Do / Done)
- Acceptance criteria per task
- Single source of truth for active work

The archive preserves all historical issue records for context, but new work flows through Backlog.

---

*Last updated: 2026-05-23 by P4.1 (TASK-20).*
