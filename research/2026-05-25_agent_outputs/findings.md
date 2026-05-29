# Agent Outputs — 2026-05-25T17:36:37.572736


## agent_scorecard

- 2026-04: empty or not configured
- 2026-05: 40 rows, 7 cols
  - Columns: ['Date', 'Agent', 'Facts', 'Anomaly_Count', 'Anomaly_High', 'Anomaly_Detail', 'Generated_At']
  - 2026-05-22 | Sentinel | {"blocks": 2440, "warns": 259} | 0 | 0 | 
  - 2026-05-22 | Market Context | {"regime": "NEUTRAL", "changed | 0 | 0 | 
  - 2026-05-22 | News Detective | {"tickers_checked": 505, "mate | 0 | 0 | 

## postmortems

- 2026-04: empty or not configured
- 2026-05: 71 rows, 17 cols
  - Columns: ['PostmortemID', 'PositionID', 'Ticker', 'EntryDate', 'EntryPrice', 'ScoreAtEntry', 'MetricsAtEntry', 'ExitDate', 'ExitPrice', 'PnLPct', 'ExitReason', 'DurationHours']
  - PM-690beb6b5218 | DEC-2026-05-20-HCWB-110704-74 | HCWB | 2026-05-20 | 2.28 | 0
  - PM-ffb196242225 | DEC-2026-05-20-CODX-120615-51 | CODX | 2026-05-20 | 2.48 | 0
  - PM-aa93c5c7ffe6 | DEC-2026-05-20-MTVA-110710-77 | MTVA | 2026-05-20 | 2.775 | 0

## score_analytics

- 2026-04: empty or not configured
- 2026-05: empty or not configured

## pending_suggestions

- 2026-04: empty or not configured
- 2026-05: empty or not configured

## news_findings

- 2026-04: empty or not configured
- 2026-05: 8559 rows, 11 cols
  - Columns: ['Timestamp', 'Ticker', 'Has_Material_News', 'EDGAR_Filing_Count', 'EDGAR_Latest_Form', 'EDGAR_Latest_Date', 'EDGAR_All_Filings', 'Finnhub_News_Count', 'Finnhub_Latest_Headline', 'Finnhub_All_News', 'Errors']
  - 2026-05-22T10:07:49.674176-05: | RGTI | TRUE | 2 | 8-K | 2026-05-21
  - 2026-05-22T10:07:56.547815-05: | EZRA | TRUE | 4 | 8-K | 2026-05-14
  - 2026-05-22T10:07:59.976824-05: | QBTS | TRUE | 6 | 8-K | 2026-05-21

## system_events

- 2026-04: empty or not configured
- 2026-05: 8632 rows, 7 cols
  - Columns: ['Timestamp', 'EventType', 'Severity', 'Component', 'Message', 'Details', 'ActionTaken']
  - 2026-05-22T15:00:11.349047-05: | SENTINEL_BLOCK | CRITICAL | scan_freshness | STALE_SCAN | {"ticker": "RYOJ", "scan_age_m
  - 2026-05-22T15:00:12.053376-05: | SENTINEL_BLOCK | CRITICAL | scan_freshness | STALE_SCAN | {"ticker": "HOVR", "scan_age_m
  - 2026-05-22T15:00:12.882167-05: | SENTINEL_BLOCK | CRITICAL | scan_freshness | STALE_SCAN | {"ticker": "PCLA", "scan_age_m


## 3-Numbers Conflict Resolution

### paper_portfolio
- May rows: 89
- Apr rows: 0

### May (RealizedPnLPct)
- Rows with PnL: 89
- Wins: 39, Losses: 40
- WR (decided only): 49.4%
- Total PnL%: -49.13

### portfolio sheet (Scanner sim, different from paper_portfolio)
- May rows: 65
- Columns: ['PositionKey', 'Date', 'Ticker', 'Score', 'BuyPrice', 'Status']
