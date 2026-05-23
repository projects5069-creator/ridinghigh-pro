# DEV.1 — Devil's Advocate Agent — Implementation Plan

> **Task:** TASK-33 (DEV.1)
> **Plan version:** 1
> **Date:** 2026-05-23
> **Status:** APPROVED FOR IMPLEMENTATION
> **Author:** Amihay Levy + Claude

## 1. Purpose

The system has 7 metrics + 11 filters all designed to find "YES, enter." There is no component whose sole job is "WAIT, maybe not." This creates a built-in bias toward over-entering — a system designed to find opportunities will find them even when they aren't there.

Devil's Advocate is the formal skeptic. Approach B: post-hoc daily audit, no live intervention.

## 2. Why Approach B (not A — live blocking)

Decided in session 2026-05-23. Three reasons:

1. Phase 1 = data collection, not protection. We are in DRY_RUN. Blocked trades = lost data, not saved money. We want MORE decisions reviewed, not fewer made.
2. SKIPs are half the system. Live blocking only sees ENTERs. Daily review sees BOTH ENTERs and SKIPs — twice the learning surface.
3. Cost + risk asymmetry. Live agent calling LLM every minute × every ticker costs ~$500/month and a bug breaks production. Daily review costs ~$15/month and is fully isolated.

Future migration to live (Approach A) is open IF this V1 proves itself over 60+ reviewed decisions.

## 3. What it does

Once per day at 18:00 Peru (1h after Critic at 17:00), run an LLM analysis pass over today's decisions.

Inputs:
- decision_log — every ENTER and SKIP from today (Ticker, Score, 7 metrics, ENTER/SKIP, skip_reason)
- paper_portfolio — outcomes of yesterday's ENTERs (if matured)
- post_analysis — D1-D5 OHLC for tickers from past N days (to assess SKIPs retroactively)

LLM passes (3 separate prompts):
- Pass 1 ENTER review — for each ENTER today, ask "is this entry justified given the metrics? what is the strongest counter-argument?"
- Pass 2 SKIP review — for each SKIP today, fetch next-day price action, ask "did we correctly skip this, or did it drop and we missed?"
- Pass 3 Weekly pattern (Fridays only) — look at last 5 trading days of decisions + outcomes, ask "is there a pattern of mistakes that suggests a new filter?"

Outputs:
- New Google Sheet tab: devils_advocate — one row per reviewed decision per day
- Email (Hebrew RTL, same template as Critic): top 3 most questionable ENTERs + top 3 most questionable SKIPs + Friday weekly pattern

## 4. Non-goals (V1)

To prevent scope creep, V1 explicitly DOES NOT:
- Block, delay, or modify any live decision
- Write to decision_log or paper_portfolio
- Run more than once per day
- Train any model — pure LLM inference, no learning loop
- Generate patches or code changes
- Send Slack/SMS alerts — email only

## 5. Architecture

Follows the Critic pattern exactly:

agent/devils_advocate/__init__.py
agent/devils_advocate/devils_advocate_v1.py
agent/orchestrator_devils_advocate.py
.github/workflows/agent_devils_advocate.yml (cron 0 23 * * 1-5 = 23:00 UTC = 18:00 Peru)

config.py additions:
- DEVILS_ADVOCATE_ENABLED = True
- DEVILS_ADVOCATE_MODE = "shadow"
- DEVILS_ADVOCATE_LLM_MODEL = "claude-sonnet-4-5"
- DEVILS_ADVOCATE_MAX_ENTRIES_PER_DAY = 10
- DEVILS_ADVOCATE_WEEKLY_PATTERN_DAY = 4

Data flow:
GH Actions cron 23:00 UTC → orchestrator_devils_advocate.py → DevilsAdvocateAgent.run_daily() → (review_enters, review_skips, weekly_pattern if Friday) → write_devils_advocate_sheet → send_email_report

Why separate orchestrator: main orchestrator.py runs every minute. DA runs once per day. Same pattern as Critic and News Detective.

## 6. Sheet schema — devils_advocate

Single tab, append-only. Columns:
ReviewDate, ReviewTime, Pass (ENTER/SKIP/PATTERN), Ticker, DecisionTime, OriginalAction, OriginalReason, Score, MxV, RunUp, ATRX, RSI, VWAP, ScanChange, REL_VOL, Verdict (AGREE/DISAGREE/UNCERTAIN), CounterArgument (<=200 chars), Confidence (0.0-1.0), OutcomeKnown, ActualOutcome, LLM_Model, PromptVersion.

## 7. LLM prompts (skeleton)

Prompt 1 ENTER review:
"You are a skeptical short-seller reviewing today's entries. For the entry below, identify the single strongest reason this entry should NOT have been made. Be specific to the metrics provided. Respond with: VERDICT (AGREE/DISAGREE/UNCERTAIN), COUNTER_ARGUMENT (one sentence, <= 200 chars), CONFIDENCE (0.0-1.0). Entry data: {metrics}. System rationale: Score=X, ENTER per 11 filters."

Prompt 2 SKIP review:
"You are reviewing decisions to skip a short setup. The system skipped this ticker for reason: {skip_reason}. The price moved {price_change}% the next day. Was the skip correct? Respond with: VERDICT, COUNTER_ARGUMENT, CONFIDENCE."

Prompt 3 Weekly pattern:
"Here are the last 5 trading days of decisions and outcomes. Is there a single repeating pattern in the system's mistakes? If yes, describe it and propose ONE concrete filter threshold change. If no clear pattern, say so."

## 8. Email report (Hebrew RTL)

Sections in Hebrew:
1. סיכום היום — N ENTERים נבדקו, M SKIPים נבדקו, K נדרשים תשומת לב
2. 3 ENTERים בעייתיים — table: Ticker, Score, CounterArgument
3. 3 SKIPים בעייתיים — table: Ticker, SkipReason, what happened next
4. תובנה שבועית (Fridays only) — the pattern text from Pass 3

Reuses Critic email infrastructure (send_email from agent/notifications).

## 9. Implementation steps

| # | Step | Hours | Verifies |
|---|---|---|---|
| 1 | Directory structure + empty files | 0.25 | ls shows files |
| 2 | DevilsAdvocateAgent class skeleton (no LLM) | 0.5 | import works |
| 3 | Data loading (decision_log + paper_portfolio + post_analysis) | 1.0 | print today's ENTERs and SKIPs |
| 4 | LLM calls (anthropic SDK), 3 prompt functions | 1.5 | run on 1 ENTER + 1 SKIP, check response |
| 5 | Sheet writing (safe_append_row to devils_advocate tab) | 0.5 | rows land in sheet |
| 6 | Email report (Hebrew RTL) | 1.0 | send to self, verify rendering |
| 7 | orchestrator_devils_advocate.py | 0.5 | python -m runs end-to-end |
| 8 | Workflow agent_devils_advocate.yml | 0.25 | actionlint passes |
| 9 | config flags + sheet auto-create | 0.5 | config loads, sheet tab exists |
| 10 | End-to-end manual test (workflow_dispatch) | 0.5 | sheet has rows, email arrived |
| 11 | Update PK_v2 — add Agent #6 | 0.25 | reads correctly |
| 12 | Mark TASK-33 Done | 0.05 | backlog confirms |

Total: ~7 hours.

Safe stopping points:
- After step 2 (~45 min): scaffolding only, nothing wired
- After step 5 (~3 hours): agent works end-to-end but no email
- After step 10 (~6 hours): production-ready
- Steps 11-12: docs + cleanup

## 10. Rollout plan

Phase 1 — Shadow mode (always for V1)
- DEVILS_ADVOCATE_MODE = "shadow" — writes to sheet, sends email, never blocks
- Run 30 days, target ~60 reviewed ENTERs
- Review email daily

Phase 2 — Evaluation (after 30 days)
- Did "DISAGREE" verdicts correlate with worse outcomes?
- Did weekly patterns suggest real filter ideas?
- Yes → consider Phase 3. No → tune prompts or accept logging-only.

Phase 3 — Optional future (NOT in V1)
- Migrate to live (Approach A)
- Auto-create filter proposals
- Inter-agent voting with Risk Sentinel (DEV.2)

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| LLM hallucinates | PromptVersion column for A/B; CONFIDENCE in output |
| Email becomes noise | Hard cap top-3 ENTERs + top-3 SKIPs; weekly only Fridays |
| Sheet write 429s | safe_append_row (existing retry wrapper) |
| Anthropic API down | Log error + "DA failed" email; resume next day |
| LLM cost spirals | DEVILS_ADVOCATE_MAX_ENTRIES_PER_DAY = 10; one model only |
| Conflicts with Critic | Critic = CLOSED trades. DA = DECISIONS. No overlap. |
| User-perceived value low | Phase 2 evaluation built in — if no value after 30 days, archive without shame |

## 12. Open questions (resolve before step 4)

1. ANTHROPIC_API_KEY secret — does it exist? Check .github/workflows/. If no, add.
2. Cost — Claude Sonnet 4.5: ~10 ENTERs × ~500 tokens × $0.003/1K = ~$0.015/day = ~$5/year.
3. Post_analysis lookback for SKIP review — proposal: only SKIPs from yesterday (D1 exists).
4. Critic schedule overlap — Critic 17:00 Peru, DA 18:00. 1h gap should suffice; verify.

## 13. Success criteria (for marking DEV.1 Done)

- Agent runs end-to-end manually (workflow_dispatch) without errors
- devils_advocate sheet has >= 5 rows from real production data
- Email arrives with Hebrew RTL rendering correct
- No impact on Trader, Sentinel, Critic, News Detective, Market Context
- PK_v2 updated to mention Agent #6
- First scheduled cron run succeeds
- TASK-33 marked Done in backlog
