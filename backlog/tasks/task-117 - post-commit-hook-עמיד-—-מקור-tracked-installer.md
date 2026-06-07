---
id: TASK-117
title: post-commit hook עמיד — מקור tracked + installer
status: To Do
assignee: []
created_date: '2026-06-07 21:13'
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
