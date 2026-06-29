---
id: TASK-206
title: add fundamental fields (core cols + raw_fundamentals_json) with guards
status: To Do
assignee: []
created_date: '2026-06-29 04:15'
updated_date: '2026-06-29 17:10'
labels: []
dependencies: []
ordinal: 212000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Maximize per-stock fundamental documentation. Availability verified on a nano-cap sample (29/6): the structural/short + ownership + profitability/solvency fields (ShortFloat, Days-to-Cover, InstOwn, InsiderOwn, Beta, ROE, ProfitMargins, Sector, Industry) come back clean even for nano-caps from BOTH yfinance .info and FINVIZ-Custom. Only floatShares (TASK-201) and growth fields are unreliable/NaN in nano-caps. P/E is frequently null for unprofitable nano-caps (legitimate NA, not garbage). Delisted tickers return 404 (survivorship gap). Hybrid design: FINVIZ-Custom one-call-per-scan primary + yfinance fallback + raw_fundamentals_json catch-all, with per-field guard + source-tag.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Core columns (verified high-availability in nano-caps): Sector, Industry, ShortFloat, Days-to-Cover (shortRatio), InstOwn, InsiderOwn, Beta, IPO-age, ROE, ProfitMargins, plus P/E (NA-tolerant — frequently null for unprofitable nano-caps)
- [ ] #2 raw_fundamentals_json catch-all for the rest (PEG, forwardPE, solvency, growth — growth is mostly NaN in nano-caps so JSON-only, not a column)
- [ ] #3 Guard + NaN-tolerance + source-tag per field (reuse TASK-203 clamp pattern); guard must distinguish NA-missing-field from NA-delisted (404 from yfinance) — ties survivorship TASK-149/168
- [ ] #4 FINVIZ-Custom one call per scan as primary (ShortFloat/InstOwn/InsiderOwn/Beta/P/E) + yfinance .info per-ticker as fallback/supplement; both verified available
- [ ] #5 schema-union write; zero reader breakage
<!-- AC:END -->
