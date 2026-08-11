---
id: TASK-258
title: Build crossover-event detector — HYP-001 has no collection mechanism
status: To Do
assignee: []
created_date: '2026-08-05 19:30'
updated_date: '2026-08-05 19:30'
labels:
  - crossover-short
  - hyp-001
  - dropslab
  - blocker
dependencies: []
priority: high
ordinal: 256000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
HYP-001 is registered and locked since 2026-06-23 and TASK-179 waits on n>=150 crossover events, but no crossover-event detector exists in the live codebase — grep returns comment lines only. n is unmeasured, not merely low. Full evidence in Implementation Notes.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Source: stage-1 closure review 2026-08-05 (reports/2026-08-05_1406_stage1_closures.md §1).
Found while checking why TASK-179 was still blocked.

HYP-001 (crossover-short) is REGISTERED and LOCKED since 2026-06-23 (TASK-178) and awaits
validation in TASK-179 on n>=150 crossover events collected after that date.

VERIFIED 2026-08-05 — there is no crossover-event detector anywhere in the live codebase:

  $ grep -rniI "crossover" --include="*.py" .        (excluding backups/ project_sync/ research/)
  config.py:155                   -> comment only
  post_analysis_collector.py:210  -> comment only
  ...and nothing else. Zero executable code.

  $ grep -rniI "dropslab|drops_post" --include="*.py" .
  config.py:301 · formulas.py:353 · agent/trader/decision_logic.py:396
  All three are comments. There is no DropsLab module in this repo.

  $ grep -rliI "crossover" research/
  (empty)

CONSEQUENCE: n is not "below 150". It is unmeasured, and cannot be measured until a join
between a RidingHigh scanner trigger and a DropsLab drop-event within <=10 calendar days is
built and starts accumulating events dated after 2026-06-23. Until then TASK-179 cannot
start, regardless of how much calendar time passes.

BLOCKS: TASK-179 (High, To Do). RELATED: TASK-255 (DropsLab signal integration into Trader,
gated on 179) and TASK-153 (DropsLab PK adoption).

SCOPE NOTE — cross-project isolation: DropsLab is a SEPARATE repository. Any data path built
here must respect that boundary. Decide and record explicitly whether the join runs inside
RidingHigh reading an exported DropsLab artifact, or inside DropsLab writing a crossover
feed that RidingHigh consumes. Do not reach into the other repo's internals from this one.

NOT DECIDED HERE: which side owns the join, the storage target for the event log, or whether
events before 2026-06-23 may be backfilled (per HYP-001 §D they may NOT enter the validation
sample — the n=62 discovery set is locked and never recycled).
<!-- SECTION:NOTES:END -->

## ממצא 2026-08-10 — אותה שאלה עקרונית חוסמת גם כאן
המערכת האחות חיה ורצה (42 ריצות ב-30 יום, אחרונה 10/8 22:06Z), כך שאין "היא מתה
ולכן אין מה לחבר". שתי חלופות-הבנייה (היא כותבת ואנחנו קוראים / אנחנו קוראים תוצר
מיוצא) **שתיהן יוצרות תלות בין המערכות**, אחרי שהוכרזה הפרדה מוחלטת ב-10/8.
⇒ אין טעם לבחור ביניהן לפני שנענית השאלה העקרונית.
⏳ **ממתין להכרעת עמיחי:** האם "הפרדה מוחלטת" כוללת העברת קבצים.
ייסגר כאשר: הוכרע איזה צד מחשב את החיבור, ורשומת-האירועים מכילה לפחות אירוע אחד
מתוארך אחרי 2026-06-23.
