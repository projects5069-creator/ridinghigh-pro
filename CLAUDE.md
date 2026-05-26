# Claude Code Behavior Rules — RidingHigh Pro

**READ THIS BEFORE EVERY TASK.** These rules are non-negotiable.

---

## RULE #1: Data vs. Interpretation

When running a command that returns data:
- **Show the RAW output only**
- **Do NOT add explanations, reasoning, or context**
- **Do NOT speculate about WHY the data looks the way it does**
- **STOP after showing the output**

If the user wants interpretation, they will ask explicitly.

### FORBIDDEN phrases (do NOT say these):
- "This is because..."
- "This makes sense given..."
- "This is normal ��� [holiday/weekend/event]"
- "The reason is..."
- "As expected..."
- "Good Friday", "market closed", "weekend" — unless user asked about calendar

### CORRECT behavior:
- Print the raw output
- Wait for user to ask next question
- If you have a HYPOTHESIS about the data, say: "I have a hypothesis but need to verify with another command. Want me to run it?"

---

## RULE #2: Calendar and Date Facts

You CANNOT claim:
- What day of the week a date is (unless you ran `date` command)
- Holidays for any year
- Market open/closed status (unless verified via code)
- Historical events

If a date-related question matters, **run `date` first**:
```bash
TZ='America/Lima' date
```

**Example violation (DO NOT DO):**
> "Today is Sunday, so the market is closed"

**Correct approach:**
> "Let me check what day it is: [runs `date`]. Result: Monday. So market should be open."

---

## RULE #3: Uncertainty Honesty

If you don't know something with certainty:
- **Say "I don't know"**
- **Do NOT invent plausible-sounding explanations**
- **Suggest a command to check**

Silence is better than made-up facts.

---

## RULE #4: Before Any File Edit

1. **Create backup**: `cp file.py file.py.bak_$(date +%Y%m%d-%H%M%S)`
2. **Read the exact lines** you're about to edit (view tool)
3. **Make the change**
4. **Run `python3 -m py_compile <file>`**
5. **If tests exist, run `python3 test_formulas.py`** — must show 107/107 passed
6. **Report what changed** — no commit yet

---

## RULE #5: Never Commit Without Explicit Approval

- After changes: show the diff, show test results, **WAIT**
- The user will say "commit" or "push" explicitly
- Never assume silence = approval

### RULE #5b: NEVER run `git commit` twice for the same change

If a block you just ran already contained a `git commit`, the commit is
DONE — do NOT run `git commit` again. A short or truncated tail of the
output (e.g. only seeing "commit created") does NOT mean the commit
failed. Re-running creates a duplicate / confusing history.

If you genuinely need to verify whether a commit landed:
1. Run `git log -1 --oneline` FIRST.
2. Only if the expected commit is NOT at HEAD, run `git commit` again.
Never re-commit on a guess.

---

## RULE #6: Never Run Live Workflows Without Approval

- Do not trigger GitHub Actions workflows manually
- Do not run `auto_scanner.py` or `post_analysis_collector.py` unless explicitly asked
- Dry-runs are OK if clearly marked as `--dry-run`

---

## RULE #7: Full Output, Not Summaries

When showing file contents or command output:
- Show the **actual** output
- Do NOT paraphrase ("the file has 46 lines with cron schedule")
- Use `cat`, `head`, `tail`, `sed -n` — whatever shows raw content

If output is too long, show first 50 + last 20 lines with a clear marker.

---

## RULE #8: System Architecture — Current State (2026-04-20)

### Source of Truth Hierarchy
- **config.py**: All weights, caps, thresholds (SCORE_WEIGHTS_V2, TP/SL, REL_VOL_CAP, etc.)
- **formulas.py**: All calculations (metrics + 9 score variants + entry score)
- **auto_scanner.py**: FINVIZ scraping, Sheets I/O, orchestration (NOT calculations)
- **dashboard.py**: Streamlit UI (NOT calculations)
- **utils.py**: Shared utilities

### Sheet Column Names (Current)
- Score main column: `Score` (v2 formula since 2026-04-11, commit f3d96ca)
- Typical Price distance: `TypicalPriceDist` (renamed from "VWAP" in #11)
- All monthly rotation automated — do NOT hardcode month keys

### Do NOT Touch Without Explicit Request
- Score variants B-I (research experiments with distinct parameters)
- Historical backup files `*.bak_*` (auto-ignored by gitignore)
- OPEN_ISSUES.md (except when closing an issue)

---

## RULE #9: When Tests Fail

1. **STOP immediately**
2. Do NOT try to "fix" by modifying tests
3. Report the exact failure to user
4. Offer to revert from backup

---

## RULE #10: Timezone Awareness

- User is in **Peru (UTC-5, no DST year-round)**
- GitHub Actions runs in **UTC**
- 16:00 Peru = 21:00 UTC
- Always specify which timezone when discussing times

### US Market Hours vs Peru
- US market opens **09:30 ET** (Eastern Time)
- ET has DST; Peru does NOT:
  - **Summer (Mar–Nov): ET = UTC-4 (EDT)** → 09:30 ET = **08:30 Peru**
  - **Winter (Nov–Mar): ET = UTC-5 (EST)** → 09:30 ET = **09:30 Peru**
- **Do NOT guess** — if market-open time matters, compute from current UTC offset:
  ```bash
  TZ='America/New_York' date +%Z    # EDT or EST
  ```
- Market close: 16:00 ET = 15:00 Peru (summer) / 16:00 Peru (winter)

---

## RULE #11: Skills Are Mandatory (HARD ENFORCEMENT)

**THIS RULE OVERRIDES ALL OTHER GUIDANCE.**

Before responding to ANY user prompt — including this one — you MUST:

1. **Call Skill tool first**, with the relevant skill name:
   - `Skill(name="using-superpowers")` at session start (once per session)
   - `Skill(name="systematic-debugging")` before any investigation
   - `Skill(name="writing-plans")` before any code edit
   - `Skill(name="brainstorming")` before new feature design
   - `Skill(name="verification-before-completion")` before declaring "done"
   - Other relevant skill names as appropriate

2. **Append to skill audit log** (`~/RidingHighPro/.skill_audit.log`):
echo "$(TZ='America/Lima' date '+%Y-%m-%d %H:%M:%S') | TASK_TYPE | skill_name | brief_description" >> ~/RidingHighPro/.skill_audit.log

3. **Print to stdout** at the start of your response:
SKILL INVOKED: <skill_name> (audit logged)

### Failure Mode

If you respond WITHOUT calling the Skill tool first:
- You have FAILED RULE #11
- Report failure explicitly: "RULE #11 VIOLATED — proceeding anyway"
- The user will see this and know to remind you

### Why This Matters

The user (Amihay) has explicitly stated: "תמיד תמיד תמיד תעבוד עם כל הסקילים. תמיד!"
This is non-negotiable. Skills exist for quality control. Skipping them
because "the task seems simple" is the exact failure mode that loses trust.

### Audit Trail

The `~/RidingHighPro/.skill_audit.log` file is the evidence. The user can
review it at any time. Empty log = you skipped skills. Populated log = you
followed the rule.

---

## Summary: The Prime Directive

**Show data. Don't explain data. Let the user drive interpretation.**

When in doubt: output, wait, ask.

---
@.claude-startup.md
