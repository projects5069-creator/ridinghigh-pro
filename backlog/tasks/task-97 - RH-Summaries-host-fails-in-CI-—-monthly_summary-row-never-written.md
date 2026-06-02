---
id: TASK-97
title: RH-Summaries host fails in CI — monthly_summary row never written
status: Done
assignee: []
created_date: '2026-06-02 17:15'
updated_date: '2026-06-02 17:36'
labels: []
dependencies: []
priority: high
ordinal: 97000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
write_monthly_summary reads RH-Summaries sheet ID only from local dotfile ~/.rh_summaries_sheet_id, which is gitignored and absent in GitHub Actions. Monthly email sends, but the monthly_summary sheet row is never written in production. Fix: fallback to os.environ['RH_SUMMARIES_SHEET_ID'] + GitHub Secret + env in agent_critic_monthly.yml. Discovered 2026-06-02 during TASK-60 verification. Blocks full TASK-48 monthly acceptance.
<!-- SECTION:DESCRIPTION:END -->
