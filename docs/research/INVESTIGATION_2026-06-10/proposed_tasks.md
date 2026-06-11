# proposed_tasks — TASK-139 Investigation 2026-06-10

כותרות באנגלית, <200 בתים. ממוינות לפי חומרה. אף משימה לא נפתחה בפועל (READ-ONLY run).

## P0 — research validity
1. `Decouple Score from entry decisions — kill-criterion met (random-in-filter WR .659 vs top-Score .629, p=.56); implement explicit filter-gate in shadow (Option B)`
2. `Fix EOD portfolio look-ahead entry — peak-Score BuyPrice inflates WR by 13.6pp; rebase research on D1_Open entries`

## P1 — operational / data integrity
3. `Add post-scan reverse-split detector — TDIC 2026-05-12 sits CLEAN in n=123 as fake LOSS; flag D-day price jumps >3x in audit`
4. `Fix DropsLab collector timeout death-spiral — cancelled daily since 6/5, drops_post frozen at 27/5, 1766-row backlog; add checkpointing`
5. `Wire real tradability/borrow data — borrow_data tab empty, mock is_shortable=True + fee=12.5 const masks the cost that kills the edge (~388%/yr breakeven)`
6. `Resolve 26 WHIPSAW rows with intraday data — edge sign flips negative if whipsaws resolve at SL; blocking question for any go-live decision`

## P2 — pipeline correctness
7. `Fix high_today mutation inconsistency in analyze_ticker — TypicalPrice uses stale bar high while High_today/PriceToHigh use adjusted price`
8. `Unify duplicate RSI calculation — ticker_follow_up uses SMA-based RSI vs Wilder EWM in analyze_ticker (sec-10 violation, numerically divergent)`
9. `Store FINVIZ prev_close at scan time — ScanChange% (strongest predictor) is unreproducible from stored raws (deviations up to 109pp found)`
10. `Move market_context cron off top-of-hour — 14.8% failure rate from 429 read-quota collisions with minute workflows`
11. `Harden df_to_sheet clear+update pattern — mid-write failure loses whole sheet (live_trades/portfolio_live rewritten every minute)`
12. `Surface scanner write failures — runs stay green when all Sheets writes fail (print-only error handling, no exit code)`
13. `Archive orphan RH-2026-07-post_analysis duplicate (1ASXu2..., created 71s before the live one); add post-rotation duplicate check`
14. `Recalibrate or drop ROCKET_GUARD — original "16 losses/0 winners" not replicating (OOS: 5 correct/3 wrong; full set: blocks 12 winners)`
15. `Review no-discrimination filters F2 (MxV<=-100) and F5 (MarketCap) — zero WR separation on n=123; MxV correlation sign opposes F2 direction`

## P3 — hygiene / docs / monitoring
16. `Verify skip_summary first live writes after 2026-06-11 market open (TASK-125 deployed post-close, unverifiable today)`
17. `Fix PK sec-18 RSI docs (bell-curve + RSI_LOW=50 stale) and delete dead RSI constants (extends TASK-129)`
18. `Update PK sec-1 metadata: active workflows 7 -> 15; codebase size unverified`
19. `Re-sync or retire PK mirror Sheet RidingHigh-Pro-System-Reference (stale since 2026-05-16)`
20. `Remove dead config constants (MIN_PRICE/MIN_VOLUME/MIN_MARKET_CAP/MAX_HOLDING_DAYS/MEDIUM_SCORE/AGENT_NO_TIME_LIMIT/market-hours consts) or wire them`
21. `Add health_audit checks: skip_summary written on trading days; post-scan split artifacts; orphan month-sheet duplicates`
22. `Back up closed-month post_analysis after backfill runs — current backup covers active month only`
23. `Document/normalize DropsLab schema — docstring says 22 cols, sheet has 25; 3 duplicate date|ticker keys; d1_pct split artifacts unflagged`
24. `Make read-counter measure raw Sheets reads, not cache-misses only (actual ~5-13 reads/run vs reported total=1) — extends TASK-113`
25. `Adopt DROPSLAB_PK_DRAFT.md as living DropsLab PK after review`
