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

1. **Create backup**: `cp file.py file.py.BEFORE_<task_id>`
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
- Historical backup files `*.BEFORE_issue*`
- OPEN_ISSUES.md (except when closing an issue)

---

## RULE #9: When Tests Fail

1. **STOP immediately**
2. Do NOT try to "fix" by modifying tests
3. Report the exact failure to user
4. Offer to revert from backup

---

## RULE #10: Timezone Awareness

- User is in **Peru (UTC-5, no DST)**
- GitHub Actions runs in **UTC**
- 16:00 Peru = 21:00 UTC
- Always specify which timezone when discussing times

---

## Summary: The Prime Directive

**Show data. Don't explain data. Let the user drive interpretation.**

When in doubt: output, wait, ask.
