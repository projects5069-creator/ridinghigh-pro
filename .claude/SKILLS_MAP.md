# Skills Map — RidingHigh Pro

> **Usage:** Claude Code invokes `Skill` tool before every task. This table maps tasks → skills.
> **Iron Rule:** see `CLAUDE.md` RULE #11.

---

## Quick Reference — which skill for each task type

| Task type | Primary skill | Secondary skill |
|---|---|---|
| Bug investigation / regression | `systematic-debugging` | `verification-before-completion` |
| New feature | `brainstorming` | `writing-plans` + `test-driven-development` |
| Statistical / data analysis | `statistical-analysis` | `explore-data` + `validate-data` |
| Post-trade analysis | `signal-postmortem` | — |
| Git cleanup / branches | `git-cleanup` | — |
| Python tooling / refactor | `modern-python` | — |
| Unclear task | `ask-questions-if-underspecified` | — |
| Before completing task | `verification-before-completion` | — |
| Dashboard / data viz | `data-visualization` / `create-viz` | `build-dashboard` |

---

## Active Tasks (2026-05-23)

### P0 — Critical
| Task | Primary | Secondary |
|---|---|---|
| **P0.2** errors mislabel | `systematic-debugging` | `verification-before-completion` |

### P1 — Important
| Task | Primary | Secondary |
|---|---|---|
| **P1.1** HCWB×5 regression | `systematic-debugging` | `signal-postmortem` |
| **P1.2** GH Actions cron drift | `brainstorming` | `writing-plans` |
| **P1.4** PnL empty bug | `systematic-debugging` | `signal-postmortem` + `test-driven-development` |
| **P1.5** PIII anomaly | `systematic-debugging` | `explore-data` + `statistical-analysis` |

### P2 — Strategic
| Task | Primary | Secondary |
|---|---|---|
| **P2.1** system_events refactor | `writing-plans` | `brainstorming` + `using-git-worktrees` |
| **P2.2** Sentinel Analytics | `explore-data` | `statistical-analysis` + `validate-data` + `data-visualization` |
| **P2.3** Filter 12 ticker_reputation | `brainstorming` | `writing-plans` + `test-driven-development` |
| **P2.4** Cross-month aggregation | `writing-plans` | `systematic-debugging` |

### P3 — Medium
| Task | Primary | Secondary |
|---|---|---|
| **P3.1** retry auto_scanner | `systematic-debugging` | `test-driven-development` |
| **P3.2** nan/inf + duplicate | `systematic-debugging` | — |
| **P3.3** Market Context wiring | `brainstorming` | `writing-plans` + `test-driven-development` |
| **P3.5** D1_Open outlier | `explore-data` | `statistical-analysis` |
| **P3.6** Sentinel serialization | `verification-before-completion` | — |
| **P3.7** cosmetic dashboard | — | (no skill needed) |

### P4 — Maintenance
| Task | Primary | Secondary |
|---|---|---|
| **P4.1** OPEN_ISSUES rebuild | `doc-coauthoring` | `internal-comms` |
| **P4.2** clean .bak files | `git-cleanup` | — |
| **P4.3** dashboard expander drift | `systematic-debugging` | — |
| **P4.4** PK_v2 update | `doc-coauthoring` | `internal-comms` |
| **P4.5** delete archive vault | — | (one-off) |
| **P4.6** hardcoded thresholds | `modern-python` | `brainstorming` |
| **P4.7** Node.js verification | `verification-before-completion` | — |

### Waiting for data
| Task | Primary | Secondary |
|---|---|---|
| **Wait.1** WHIPSAW analysis | `explore-data` | `statistical-analysis` + `validate-data` |
| **Wait.2** DropsLab integration | `brainstorming` | `writing-plans` |
| **Wait.3** Live Write Verification | `verification-before-completion` | `test-driven-development` |

---

## Skill Priority Order (from using-superpowers)

1. **Process skills first** — how to approach: `brainstorming`, `systematic-debugging`
2. **Implementation skills second** — do the work: `test-driven-development`, `writing-plans`
3. **Verification last** — `verification-before-completion`

---

## Maintenance

- New task added → add row to appropriate table
- New skill installed → add to Quick Reference
- Skill removed → update tables
- Changes committed together with CLAUDE.md

**Last updated:** 2026-05-23 — initial creation with 14 tasks + 3 Waiting.
