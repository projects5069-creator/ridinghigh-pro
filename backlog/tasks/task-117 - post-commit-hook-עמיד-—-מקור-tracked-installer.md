---
id: TASK-117
title: post-commit hook עמיד — מקור tracked + installer
status: Done
assignee: []
created_date: '2026-06-07 21:13'
updated_date: '2026-06-08 20:17'
labels:
  - infra
  - hooks
dependencies: []
priority: low
ordinal: 117000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
ה-post-commit hook תוקן מקומית (TASK-116) אך לא tracked. ליצור scripts/git_hooks/post-commit (uv run python3) + לחווט scripts/git_hooks/install.sh שיתקין גם post-commit. מסיר את הפנייה המתה ל-setup_project_state.sh. הופך את התיקון לבר-clone ומשותף.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Done via PR #15 (squash, merged to main `ff9b1c9`, 2026-06-08). Created tracked `scripts/git_hooks/post-commit` (mode 100755, `uv run python3 generate_project_state.py` — makes TASK-116 fix clone-survivable); dead `setup_project_state.sh` header ref removed (now points to install.sh). Wired `scripts/git_hooks/install.sh` to install both pre-commit + post-commit via a loop (`core.hooksPath` deliberately unset). NIGHT_RUN doc `docs/NIGHT_RUN_2026-06-08_TASK117.md` with `## Run Log`. Agent #8 verdict: Ready (7 safety rules pass, Anti-Drift clean). Post-merge installer run verified: `.git/hooks/post-commit` == tracked source (diff IDENTICAL).
<!-- SECTION:FINAL_SUMMARY:END -->
