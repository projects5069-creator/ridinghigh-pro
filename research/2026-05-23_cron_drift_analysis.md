# Cron Drift Analysis — agent_minute workflow

> **Investigation:** P1.2 (TASK-5)
> **Date:** 2026-05-23
> **Analyst:** Amihay + Claude
> **Status:** Complete. P1.2 → Done. Follow-up: P3.4 (catch-up logic).

## Method

Analyzed `timeline_live` Sheet as a proxy for `agent_minute` workflow execution. Each unique (Date, ScanTime) pair represents one successful workflow run that wrote signals. Measured gaps between consecutive scans within the same trading day (market hours 08:30-15:00 Peru).

Note: `agent_minute` runs every minute via cron `*/1 13-20 * * 1-5`. Expected gap = 60s.

## Findings — Two Separate Phenomena

### Phenomenon 1: GitHub Actions outage on 2026-05-22 (Friday)

External event. 37-minute gap from 12:02 to 12:39 Peru. 16 severe drifts total that day.

Evidence it was external (not our code):
- `system_events` on 22/5: 2,699 rows, ALL Sentinel events (BLOCK/WARN). Zero non-Sentinel events.
- During the outage window 11:50-12:40: NO errors, warnings, or events from our code.
- The system was simply silent — GitHub didn't dispatch the workflow.

Impact: ~25% of the trading day lost (no signals scanned, no decisions made, no position updates).

Mitigation: cannot prevent. Catch-up logic on next successful run could backfill missed data.

### Phenomenon 2: Structural drift (every trading day)

Drift exists even on normal days. Sample of last 4 normal days (excluding 22/5):

| Metric | Value |
|---|---|
| On-time (<=90s) | 78.5% |
| Slight drift (90-150s) | 16.6% |
| Moderate drift (150-300s) | 4.5% |
| Severe drift (>300s) | 0.4% |

Per-day breakdown (excluding 22/5):
- 18/5 Mon: 5 severe, MaxGap 420s (7 min lost)
- 19/5 Tue: 0 severe, MaxGap 300s
- 20/5 Wed: 0 severe, MaxGap 300s
- 21/5 Thu: 0 severe, MaxGap 240s

Conclusion: structural drift is a known property of GitHub Actions `*/1` cron — it cannot guarantee per-minute execution. Average loss: 5-10 minutes of scans per trading day.

## Cannot Be Fixed at the Cron Layer

The drift is inherent to GitHub Actions scheduler behavior under load. Offsets (used in backup.yml, post_analysis.yml) help hour-boundary workflows, not per-minute. Changing to self-hosted runner would solve drift but adds operational burden.

## Recommended Solution: Catch-up Logic (P3.4)

When agent_minute runs, it should detect "my last successful run was more than 90s ago" and backfill missed minutes by:
1. Reading from data providers (yfinance/Alpaca) historical 1-min bars
2. Computing scores for those minutes retroactively
3. Writing to timeline_live with the original timestamp (not now())

This fixes both phenomena (single outage AND structural drift) with one mechanism.

P3.4 (TASK-16) was MEDIUM priority. Bumped to HIGH after this investigation.

## Decision Log

- P1.2 → Done. Investigation complete, no code change needed (cron behavior is external).
- P3.4 → HIGH priority. The actual fix lives there.
- No regression introduced. No urgent action required if data loss is acceptable in Phase 1.
