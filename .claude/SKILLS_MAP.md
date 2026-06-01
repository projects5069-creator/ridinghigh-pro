# Skills Map — RidingHigh Pro

> **Usage:** Claude Code invokes the relevant skill before every task.
> **Iron Rule:** see `CLAUDE.md` RULE #11 v3.
> **Integrity:** `scripts/check_skills_integrity.sh` runs at session open (RULE #13).

---

## Quick Reference — task → skill

### Process (how to approach)
| Task type | Skill | Source |
|---|---|---|
| Bug investigation / regression / root cause | `systematic-debugging` | superpowers plugin |
| Open-ended question / new direction | `brainstorming` | superpowers plugin |
| Multi-step plan / refactor | `writing-plans` | superpowers plugin |
| Unclear / underspecified task | `ask-questions-if-underspecified` | trailofbits plugin |

### Implementation (do the work)
| Task type | Skill | Source |
|---|---|---|
| New feature with tests | `test-driven-development` | superpowers plugin |
| Python tooling / lint / refactor | `modern-python` | trailofbits plugin |
| Git branch / cleanup | `git-cleanup` | trailofbits plugin |
| Long-running multi-task | `subagent-driven-development` | superpowers plugin |

### Verification
| Task type | Skill | Source |
|---|---|---|
| Before declaring "done" / before commit | `verification-before-completion` | superpowers plugin |
| Skills/infra integrity at session open | `scripts/check_skills_integrity.sh` | local |

### RH-dedicated (project skills)
| Task type | Skill | Path |
|---|---|---|
| Session open/close ritual | `rhpro-session` | `~/.claude/skills/rhpro-session/` |
| Any RH question (pointer to live PK) | `rhpro-live` | `~/.claude/skills/rhpro-live/` |
| Backtest / strategy validation | `backtest-expert` | `~/.claude/skills/backtest-expert/` |
| Data quality / pipeline validation | `data-quality-checker` | `~/.claude/skills/data-quality-checker/` |
| Position sizing / risk-based shares | `position-sizer` | `~/.claude/skills/position-sizer/` |
| Trade postmortem / WHIPSAW / win-rate | `signal-postmortem` | `~/.claude/skills/signal-postmortem/` |
| Trader's prior context / memory recall | `trader-memory-core` | `~/.claude/skills/trader-memory-core/` |
| Time / market hours verification | `time-check` | `~/.claude/skills/time-check/` |

### Anthropic-skills bundle (`~/.claude/skills/anthropic-skills/skills/`)
| Task type | Skill |
|---|---|
| Word doc creation/edit | `docx` |
| PDF creation/extraction | `pdf` |
| PowerPoint deck | `pptx` |
| Excel / spreadsheet | `xlsx` |
| Frontend / React / UI | `frontend-design` |
| Creating a new skill | `skill-creator` |
| API / MCP server | `claude-api`, `mcp-builder` |
| Other: `algorithmic-art`, `brand-guidelines`, `canvas-design`, `doc-coauthoring`, `internal-comms`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `webapp-testing` |

---

## Activation priority (from `using-superpowers`)
1. **Process first** — brainstorming / systematic-debugging
2. **Implementation second** — TDD / writing-plans
3. **Verification last** — verification-before-completion

## Maintenance
- New skill installed → re-run integrity guard → add row here → commit with PK update.
- Skill removed → remove row here → commit.
- Integrity guard run at every session open per RULE #13.

---

## Plugin skill paths (corrected 2026-06-01)

Plugin skills (superpowers / trailofbits / knowledge-work) do NOT live in
~/.claude/skills/. They live under the plugin cache:

- superpowers: ~/.claude/plugins/cache/superpowers-marketplace/superpowers/VERSION/skills/NAME/SKILL.md
- trailofbits: ~/.claude/plugins/cache/trailofbits/NAME/VERSION/skills/NAME/SKILL.md
- knowledge-work: ~/.claude/plugins/cache/knowledge-work-plugins/data/VERSION/skills/NAME/SKILL.md

Searching ~/.claude/skills/NAME/ for a plugin skill returns "not found" even
though the skill IS installed and active. This path error caused a full-morning
false alarm on 2026-06-01 (thought superpowers was missing; it had 14 working
skills in cache).

Verified inventory 2026-06-01: about 53 active skills total —
8 dedicated + 14 superpowers + 18 anthropic-bundle + 3 trailofbits + 10 knowledge-work.

## End-of-output proof (RULE 11 v3.2)

Every response doing real work ends with a block "skills executed": for each
skill, name + full SKILL.md path + wc -l. The chat-side reviewer verifies it
and flags to the user if no skill was used.
