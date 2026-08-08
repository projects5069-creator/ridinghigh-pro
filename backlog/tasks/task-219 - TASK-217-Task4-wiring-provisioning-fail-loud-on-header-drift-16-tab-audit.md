---
id: TASK-219
title: 'TASK-217 Task4 wiring: provisioning fail-loud on header drift (+16-tab audit)'
status: Done
assignee: []
created_date: '2026-07-02 04:42'
updated_date: '2026-07-03 02:06'
labels: []
dependencies: []
ordinal: 225000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Guard functions header_matches_canonical + assert_header_canonical are committed (ad95806, pure, 5/5). WIRING deferred: add to create_agent_sheets._already_done a per-tab check vs AGENT_SHEET_HEADERS. DECISION NEEDED: raise (halt rotation) vs warn+log; scope (paper_portfolio only vs all 16). PREREQ: audit all 16 agent tabs x3 months (05/06/07) to find other drifts before enabling raise (avoid halting 1/8 rotation). Follow-up of TASK-217.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Wiring implemented+committed (66c984c, PK v4.01): CORE_TABS raise (paper_portfolio/decision_log/postmortems), observability warn, _set_headers hardened. Guard sits in create_agent_sheets idempotency (not-dry-run). Live audit confirmed CORE 9/9 MATCH across 05-07 pre-commit. CI green. NOT Done: raise fires only at rotation 1/8 — pending live behavior verification (or controlled dry-run). Kept To Do.
<!-- SECTION:NOTES:END -->

## RESTATED 2026-08-04

The description says the wiring is deferred. It is not. Verified live: create_agent_sheets.py line 337 calls assert_header_canonical for tabs in CORE_TABS and line 338 warns for the rest, exactly the raise versus warn split the task asked to decide. The decision was made and implemented in commit 66c984c under PK v4.01.

What actually remains is one thing and it is not code: the raise has never fired, because it only runs at a rotation. The next rotation is 2026-09-01, twenty eight days from now, and that is the same run that creates October and the same run TASK-243 is about.

So this task is waiting on an event, not on work. Either verify it at the 1/9 rotation, or force a controlled dry run before then rather than letting the first real test be the one that provisions October.

--- נסגר Done 2026-08-08 (מרשם TASK_REGISTER_2026-08-08 §3) ---
ה"החלטה הנדרשת" שבתיאור כבר הוכרעה ומומשה: הפיצול raise-ל-CORE_TABS /
warn-לשאר חי בקוד — `agent/setup/create_agent_sheets.py:339` (`if name in
CORE_TABS:`) ו-`:343-344` (`assert_header_canonical(...)`), קומיט 66c984c.
audit חי אישר CORE 9/9 MATCH על 05-07, ו-CI ירוק.
מה שנותר אינו עבודה אלא **אירוע**: הירי הראשון של ה-raise יקרה ברוטציית
2026-09-01. ⚠️ המעקב אחרי אותו אירוע לא אובד — TASK-243 פותח על אותה ריצה
בדיוק (פריטים 1-6, ובכללם "(6) Unify the two SHEET_NAMES lists"), והוא נשאר
פתוח. אם הרוטציה תיעצר בגלל ה-raise — זה ייתפס שם.
