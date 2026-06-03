# RidingHigh Pro — Data Sources Map
*מפה מרכזית: כל מקור דאטה (Sheet/קובץ), מה יש בו, מי כותב, מי קורא.*
*מבוסס סריקת קוד חי + אימות writers בפועל (2026-06-02) · סוגר TASK-64 · מ-TASK-62*

---

## למה הקובץ קיים
כדי שסריקת recon ראשונה תספיק — בלי ריצה משלימה. במקום לחפש בכל סשן
מי כותב לאיזה גיליון, הכל מתועד כאן. כל שורת writer אומתה מול הקוד
בפועל (append/update אמיתי, לא docstring ולא grep-שם); קבצי .bak סוננו.

---

## גיליונות הסקאנר (auto_scanner.py)
- timeline_live — append-only כל סריקת-דקה. כותב: run_scan() (df_to_sheet). קורא: dashboard, post_analysis.
- daily_snapshots — snapshot יומי (is_snapshot_time). כותב: auto_scanner.
- daily_summary — סיכום יומי. כותב: _save_daily_summary() (auto_scanner).
- portfolio_live — מעקב חי לפוזיציות. כותב: update_portfolio_live().
- live_trades — סימולציה תוך-יומית דקה-דקה. כותב: update_live_trades().
- ticker_follow_up — מסע 5-ימים. כותב: update_ticker_follow_up().
- score_tracker — דגימת 5-דקות. כותב: sync_score_tracker().
- post_analysis — דאטהסט המחקר (תוצאות 5d). **כותב: gsheets_sync.py** (מחושב ע"י post_analysis_collector.py).
- portfolio — רשימת tickers ל-Score Tracker (6 עמ׳, מועמד deprecation TASK-47).

---

## גיליונות הסוכנים — כותבי נתונים אוטומטיים
- decision_log — כל החלטה. כותב: decision_logger.log() + orchestrator. (critic קורא בלבד)
- paper_portfolio — פוזיציות Alpaca paper. כותב: order_manager + orchestrator. (critic קורא בלבד)
- postmortems — ניתוח לכל פוזיציה סגורה. כותב: postmortem_engine + critic_v1.
- sentinel_events — אירועי Sentinel (BLOCK/WARN). כותב: data_sentinel. (critic קורא בלבד)
- system_events — אירועי מערכת. כותב: orchestrator (+ emergency_stop מהדאשבורד).
- market_context — SPY/IWM/VIX. כותב: market_context_v1. (critic קורא בלבד)
- news_findings — EDGAR+Finnhub. כותב: news_detective_v1. (critic קורא בלבד)
- agent_scorecard — דירוג סוכנים. כותב: critic_v1.write_scorecard().
- weekly_summary — סיכום שבועי. כותב: critic_v1.write_weekly_summary().
- monthly_summary — סיכום חודשי. כותב: critic_v1.write_monthly_summary() + setup_summaries_sheet.
- score_analytics — ניתוח ניקוד (postmortems→ניקוד). כותב: agent/analytics/score_analytics.py.

---

## גיליונות עם כתיבת פעולת-משתמש (מהדאשבורד, לא אוטומטי)
- pending_suggestions — הצעות שינוי-ניקוד. יוצר שורות SUG: score_analytics.py.
  מעדכן סטטוס: _data_loaders.update_suggestion_status() (משתמש Approve/Reject, K:M). יוצר מבנה: create_agent_sheets.
- system_events — גם emergency stop: _data_loaders.log_emergency_stop()
  רק כשהמשתמש לוחץ Emergency Stop בדאשבורד (M9 רושם, M10 יוסיף עצירה).

---

## גיליונות מבנה-בלבד (אומת: אין writer פעיל, "מוכן טרם בשימוש")
- config_history — audit trail לשינויי config. יוצר: create_agent_sheets. קורא: dashboard.
- borrow_data — נתוני borrow rate. יוצר: create_agent_sheets. קורא: dashboard.
  (אומת מול טבלת התיעוד-העצמי ב-dashboard.py:4183-4186 — "כותב: —")

---

## הערות חשובות
- כל גיליונות הסוכנים נוצרים ע"י agent/setup/create_agent_sheets.py (founder).
- The Critic (critic_v1.py) כותב ל-**4 גיליונות בלבד**: postmortems, agent_scorecard,
  weekly_summary, monthly_summary. הוא **קורא** מ-decision_log / paper_portfolio /
  market_context / sentinel_events / news_findings כדי לבנות בריפים — לא כותב אליהם.
- dashboard.py + health_audit.py = קוראים בלבד (תצוגה + בדיקות).
- apply_text_format_v1.py = one-shot format-only ("never data"), מועמד ניקוי TASK-45.

---

## קבצים מקומיים (לא Sheets)
- data/market_cap_cache.json — מטמון market cap. כותב/קורא: auto_scanner + sma20_cache.py. קורא: dashboard.
- data/sma20_cache.json — מטמון SMA20. כותב/קורא: agent/enrichment/sma20_cache.py.
- post_analysis_snapshot.json — snapshot מקומי. **לא נמצא writer חי** (חקירה ב-TASK-63).
- sheets_config.json — מיפוי IDs לכל גיליון לכל חודש. כותב: monthly_rotation.py + prepare_next_month.py.
