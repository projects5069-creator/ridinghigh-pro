---
id: TASK-312
title: >-
  Order-submit retry treats a duplicate-rejection as a transient failure and
  retries it three times
status: To Do
assignee: []
created_date: '2026-08-11 03:50'
labels: []
dependencies: []
priority: low
ordinal: 310000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נמצא 10/8 בחקירת הפתרונות ל-TASK-301. order_manager._submit_with_retry (:176-190) תופס except Exception עירום ומנסה שוב MAX_RETRIES פעמים עם נסיגה מעריכית. דחיית-כפילות מהברוקר (Alpaca 422, code 40010001 client_order_id must be unique) היא **התוצאה הרצויה** ולא שגיאה חולפת — היא תנוסה שלוש פעמים לחינם ואז תיפול ל-STATUS_REJECTED (:122) ותיספר ככשל.
<!-- SECTION:DESCRIPTION:END -->

## ⚠️ אינו יכול לירות היום — וזו הסיבה שהוא נפתח ולא נקבר
`config.py:340 AGENT_DRY_RUN=True` ⇒ `alpaca_broker.py:153` מחזיר SimulatedOrder מקומי,
ו-`config.py:342 AGENT_LIVE_PAPER=False` ⇒ המסלול האמיתי זורק RuntimeError לפני כל שליחה.
⇒ אף הזמנה לא מגיעה לברוקר, ולכן אף דחייה לא מגיעה ללולאה. **הפגם רדום עד M10.**
נפתח כתיק נפרד ולא כהערה בגוף של 301, כי הוא בקובץ אחר, בעל תיקון אחר, ו"רדום"
אינו "לא קיים" — זו בדיוק מחלקת "מתועד ולעולם לא מטופל" שהמכניזם של TASK-310 נפתח עליה.
בודק-הכפילות החזיר ✅ אין מועמד חזק.

## מה שאומת (ולא נלקח מהזיכרון)
· `alpaca-py 0.43.5` — `LimitOrderRequest.client_order_id: str | None = None` **קיים**;
  הקוד שלנו ב-`alpaca_broker.py:169-177` **אינו מעביר אותו**.
· הסמנטיקה מתועדת: מזהה כפול ⇒ `422` · `{"code":40010001,"message":"client_order_id must be unique"}`.
· ⚠️ סייג מהתיעוד הרשמי: הייחודיות מנוסחת על **הזמנות פעילות** ("each active order"),
  ואין חלון-שימור מתועד. פער של 1-2 שניות אצלנו ⇒ עובד בפועל, אך אינו מובטח בכתב.

## התיקון הנכון
לתפוס את `40010001` **לפני** לולאת-הנסיונות (או להחריג אותו ממנה), למפות אותו
לדילוג עם סיבה ייעודית, ולא לספור אותו ב-`errors`. דחייה כזו היא הצלחה של השער,
לא כשל של המערכת.

ייסגר כאשר: דחיית-כפילות מסומנת כדילוג עם סיבה ייעודית, אינה מנוסה שוב אף פעם,
ואינה נספרת ב-errors — מאומת בבדיקה דו-כיוונית: 422 של כפילות ⇒ דילוג יחיד בלי retry;
שגיאת-רשת חולפת ⇒ עדיין מנוסה MAX_RETRIES פעמים.
⚠️ נוגע ב-`order_manager.py` — קפוא עד 4/9, ובלתי-נגיש ממילא עד M10.
