---
id: TASK-168
title: Delisting auto-detector (completes TASK-149 survivorship)
status: Done
assignee: []
created_date: '2026-06-12 22:55'
updated_date: '2026-06-24 18:52'
labels:
  - vision
dependencies: []
priority: medium
ordinal: 171000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Vision via TASK-156. Auto-detect delisted/NO_DATA tickers and classify: delisting of a short candidate is typically a WIN (price->0), so survivorship loss inflates apparent losses. Completes TASK-149 (19 NO_DATA rows).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Detect NO_DATA/delisted rows automatically
- [ ] #2 Classify delisting outcome (likely short WIN); surface as a known survivorship correction in WR/expectancy
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Carry-over from TASK-149 (2026-06-24): audit_flag=NO_DATA fires on rows with valid ScanPrice>0 AND full D1-D5 OHLC, even though validate_stock_data (utils.py:729-730) should return NO_DATA only for price None/0 -> a likely SECOND tagging path. Effect: it excludes valid rows from CLEAN-only research views (score_distribution.py:255, metric_quality_analysis.py:43), shrinking n. Investigate the real NO_DATA trigger when building the auto-detector (149 disproved 'NO_DATA=delisting'; the 19 are transient flags, not lost wins). See docs/research/SURVIVORSHIP_NO_DATA_2026-06-24.md (local).

ROOT CAUSE (2026-06-24, read-only): the NO_DATA-on-valid-price anomaly = a FROZEN PRE-v2.0-REFACTOR ARTIFACT, not a live bug. Evidence: validate_stock_data has a single NO_DATA path (price None/0, utils.py:729-730); audit_flag is written in exactly one place (post_analysis_collector.py:586) from one validate call (:559); stored ScanPrice=round(float(scan_price)) (:577) uses the SAME scan_price as validate (:560) -> current code CANNOT emit NO_DATA + a valid ScanPrice. The extinct 'REL_VOL_CAPPED_from_X' suffix on those April flags exists in NO current .py and NO git -S history (gone code). v2.0 refactor 55adc6e = 2026-04-17; the NO_DATA rows are ScanDate 4/3-4/10 (pre-refactor); the collector skips complete rows (:462-464) so their old-logic flags froze, never recomputed. EFFECT: ~21 April rows are wrongly excluded from CLEAN-only research views (score_distribution:255, metric_quality_analysis:43), shrinking April n there; WR is unaffected (classify_trade already settles them). Detector premise (TASK-149) disproven: 0 delistings among the 19, system-wide <=1 (SBLX). Decision: no live fix; no historical recompute (touches history, payoff low). Optional future = a forward delisting-surfacer (surface a long-PENDING row as candidate-delisting, NOT auto-count a WIN). See docs/research/NO_DATA_FLAG_ROOTCAUSE_2026-06-24.md (local).

Forward delisting-surfacer: CONSIDERED AND REJECTED (2026-06-24, record-don't-chase). Real delistings ~<=1/quarter (only SBLX system-wide to date) and PENDING rows already make them visible; a dedicated surfacer is not worth building. Documented so this does not return as an open question. Reopen only if real delistings become frequent.
<!-- SECTION:NOTES:END -->
