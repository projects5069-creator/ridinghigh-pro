---
id: TASK-207
title: Mid-month agent sheet provisioning gap
status: Done
assignee: []
created_date: '2026-06-29 13:44'
updated_date: '2026-06-29 20:24'
labels:
  - infra
dependencies: []
priority: low
ordinal: 213000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
_ensure_month() in sheets_manager iterates only SHEET_NAMES (legacy core), not AGENT_SHEET_NAMES. An agent tab added to the schema mid-month is therefore never auto-created for an already-existing month: get_sheet_id raises KeyError, the consumer catches it and silent-fails. Confirmed: shadow_gate_events missing for 2026-06 (flush_shadow_gate_summary wrote 0 rows since 24/6); borrow_coverage missing for 2026-07. Future-month rotation is unaffected (prepare_next_month.yml runs create_agent_sheets --next-month, which already lists the new tabs).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An agent tab added to AGENT_SHEET_NAMES gets provisioned for the current already-existing month — either by extending _ensure_month to cover AGENT_SHEET_NAMES, or via a documented one-shot procedure. Approach decided in-task after recon.
- [x] #2 create_agent_sheets --dry-run performs the same per-sheet idempotency check as the live run, so its output reflects what the live run will actually create (no false N-would-create for tabs already in sheets_config).
<!-- AC:END -->
