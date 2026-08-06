---
id: TASK-224
title: >-
  qty guard: quantity<1 => SKIP with dedicated skip_reason (notional-uniformity
  ruling)
status: Done
assignee: []
created_date: '2026-07-04 01:48'
updated_date: '2026-08-05 20:32'
labels: []
dependencies: []
priority: medium
ordinal: 230000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
E2E-audit S2 (3/7): _calculate_position (decision_logic.py:139-151) does qty=int(AGENT_POSITION_SIZE_USD/price) — price>$1000 => qty=0, and NO qty>=1 guard exists anywhere in the execution path (order_manager/alpaca_broker/decision_logic — grep empty). An ENTER with quantity=0 would reach the broker. RULING (עמיחי 3/7): direction 'up to $1000' — qty<1 => SKIP with a dedicated skip_reason (NOT a 1-share fallback; preserves notional uniformity). LIVE ENTRY PATH — implement only on a separate explicit go. Not a HYP-002 frozen param (guard, not threshold). Evidence: plans/stateless-seeking-sifakis.md S2.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 qty<1 returns SKIP with dedicated skip_reason (e.g. PRICE_ABOVE_NOTIONAL), TDD RED->GREEN
- [ ] #2 no behavior change for any price where qty>=1 (regression suite green)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
RULING 2026-08-05 (עמיחי)

הכרעה: ההחלטה נדחית עד למדידה אחת — כמה סיגנלים במחיר מעל $1000 היו בפועל.
עד שהמספר הזה ידוע, אין בסיס להכריע בין "לממש עכשיו" ל"להמתין לאוקטובר".

ממצא הביקורת (2026-08-05) — ההתנהגות הפוכה ממה שהתיק מניח:

תחת DRY_RUN, שהוא המצב היום: _sim_bracket_order (alpaca_broker.py:322) אינו בודק qty
ומחזיר SimulatedOrder(qty="0"). _write_to_portfolio כותב שורת paper_portfolio עם
Quantity=0. ב-position_manager.py:254 qty=int(...)=0 ולכן unrealized_pnl=0, אבל בדיקת
ה-TP/SL של DRY_RUN (position_manager.py:244-251) בודקת מחיר בלבד ואינה בודקת qty —
ולכן הפוזיציה תיסגר על TP או SL עם RealizedPnL=0 ותיכנס למדגם.

תחת LIVE_PAPER: submit_bracket_order בונה LimitOrderRequest(qty=0) ושולח ל-Alpaca,
ה-API דוחה, _submit_with_retry מנסה 3 פעמים ומחזיר None, order_status=REJECTED ואין
שורת paper_portfolio כלל.

כלומר הברוקר אוכף את מה שהקוד לא, והמצב שאנחנו נמצאים בו — DRY_RUN — הוא היחיד מבין
השניים שבו הבאג מייצר רשומה.

על שאלת הנייטרליות למדידת HYP-002:
גארד qty<1 יכול לעשות דבר אחד בלבד — להסיר תצפיות מנוונות. הוא אינו יכול להוסיף תצפית,
אינו יכול לשנות מחיר כניסה, ואינו יכול להזיז TP או SL. השפעתו על ה-expectancy חד-כיוונית:
הוצאת אפסים. אין תרחיש שבו הוא מטה את התוצאה לטובה. סעיף ה-config freeze
(HYPOTHESES.md:210-215) מונה ארבעה פרמטרים — TP, SL, HOLD, reentry — וגארד אינו אחד מהם,
כפי שהתיק עצמו כותב.

הצד השני, לתיעוד: שדה Universe ברישום (HYPOTHESES.md:193-194) מתאר את השער כארבעה תנאים —
MxV<=-100 AND price>=$3 AND data-quality AND exposure-safety. תנאי חמישי הופך את התיאור
הזה ללא מדויק. מי שיבקר את ההרצה בעוד חודשיים יראה שער שאינו מה שנרשם.

מצב מאומת בקוד 2026-08-05: אין שום בדיקת quantity על נתיב הביצוע. grep על
decision_logic.py, order_manager.py, alpaca_broker.py, position_manager.py מחזיר אפס
השוואות. הרצפה היחידה היא AGENT_MIN_SCANPRICE_USD=3.0 (config.py:300); אין תקרת מחיר
בשום מקום, ו-AGENT_MARKET_CAP_MAX כבוי תחת ENTRY_GATE_MINIMAL.

הערה על מקור הראיה: התיק מפנה ל-plans/stateless-seeking-sifakis.md S2. הקובץ אינו קיים
בריפו (ls -d plans -> No such file or directory). ה-RULING של 3/7 שהתיק נשען עליו אינו
ניתן לאימות מהריפו. נפתח תיק נפרד על כך.

MEASURED 2026-08-05 — CLOSED. The scenario is not reachable in the current scan universe.

Source: reports/2026-08-05_1455_measurement.md Q-224.

timeline_live 2026-08, all 71,397 rows carry a parseable price:
  rows with price > 1000 = 0
  price distribution: min = 2.0   p50 = 9.25   max = 545.38

decision_logic.py:145 computes qty = int(AGENT_POSITION_SIZE_USD / price), and
config.py:320 sets AGENT_POSITION_SIZE_USD = 1000. qty == 0 therefore requires a signal
priced above $1000. The highest price the scanner produced in August is 545.38, and the
median is 9.25 — an order of magnitude below the threshold. The degenerate order this
ticket guards against cannot occur on this data.

EXPLICITLY NOT A RETRACTION OF THE ANALYSIS. The review of 2026-08-05
(reports/2026-08-05_1244_decisions_review.md) established that qty=0 is dangerous under
DRY_RUN — SimulatedOrder accepts it and a zero-quantity row reaches paper_portfolio —
while under LIVE_PAPER the broker rejects it. That reasoning is unchanged and is retained
here on purpose.

IF THE UNIVERSE CHANGES, THE GUARD IS NEEDED AGAIN. The finviz filter today is
"Price: Over $2" (auto_scanner.py:346-348) with no upper bound, so a single high-priced
pump entering the screen is enough to reintroduce the case. Reopen this ticket if the
scan universe ever produces a price above AGENT_POSITION_SIZE_USD, or if
AGENT_POSITION_SIZE_USD is lowered.
<!-- SECTION:NOTES:END -->

## FROZEN UNTIL OCTOBER, 2026-08-04

Staying open on purpose. This is a decision with a return date, not an oversight.

The bug is real and unchanged. _calculate_position in decision_logic.py computes qty as int(AGENT_POSITION_SIZE_USD / price), so any price above 1000 dollars yields zero, and a grep across the whole execution path, decision_logic, order_manager and alpaca_broker, finds no qty greater than or equal to one guard anywhere. An ENTER carrying quantity zero would reach the broker.

Why it is not being fixed now. HYP-002 was voided on 2026-08-03 and re-registered the same day with 45 trading days of forward capture, reaching early October. The registration states that any change to the frozen configuration voids the run. This task argues it is a guard rather than a threshold and therefore outside the freeze, and that argument is reasonable, but the thing that voided the previous run was precisely a change in behaviour on the entry path during a registered run. Being right about the category is not worth a second voiding.

Why waiting costs nothing measurable. The universe this scanner produces is micro caps. The live scan of 2026-08-03 returned 55 tickers with prices between 0.33 and 48.62 dollars. A price above 1000 dollars does not occur in that universe, so the failing branch is not reachable in practice today.

RETURN DATE: early October 2026, when HYP-002 concludes. At that point implement as ruled on 2026-07-03: qty below one returns SKIP with a dedicated skip_reason, not a one share fallback, so notional uniformity is preserved. TDD, RED before GREEN, and an explicit go because it is the live entry path.

WHAT WOULD BRING IT FORWARD: a scanned universe that starts producing prices near or above 1000 dollars. That would make the branch reachable and the freeze would no longer be the cheaper risk.
