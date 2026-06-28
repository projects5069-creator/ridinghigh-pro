---
id: TASK-199
title: מחקר כוח-חיזוי per-מדד מול עסקאות רווח/הפסד אמיתיות (IB ground-truth)
status: To Do
assignee: []
created_date: '2026-06-28 00:11'
updated_date: '2026-06-28 03:28'
labels: []
dependencies: []
ordinal: 205000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
מחקר READ-ONLY. לכל מדד בנפרד (MxV, RunUp, ATRX, RSI, REL_VOL, TypicalPriceDist, ScanChange) — לבדוק כיוון + עוצמת הקשר לתוצאות העסקאות האמיתיות (ground-truth: תיקייה חודשית + דוח IB), ולא מול post_analysis/Score>=60. בנוסף לזהות באילו עסקאות-רווח/הפסד אמיתיות כל מדד בא לידי ביטוי. ממשיך TASK-171 (per-metric AUC) אך מתקן את פער-אוכלוסייה #1 שזוהה ב-PK v3.63: TASK-171 רץ על post_analysis (Score>=60), כאן על אוכלוסיית עסקאות-אמת (MxV<=-100%, הקריטריון שעמיחי סוחר בו). מוטיבציה: ה-edge-verdict השלילי (edge_audit v3.61 + Batch 1-8) הופרך ע"י דוח IB אמיתי 2025 (NAV +32.71%, borrow ~161 שנתי) בגלל אוכלוסייה/borrow/holding/exit שגויים.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 טבלת per-מדד: כיוון + עוצמת-קשר + n לכל אחד מ-7 המדדים מול תוצאות עסקאות אמיתיות (IB + תיקייה חודשית), לא מול post_analysis/Score>=60
- [ ] #2 מיפוי: באילו עסקאות-רווח/הפסד אמיתיות כל מדד בא לידי ביטוי
- [ ] #3 READ-ONLY; אסור לגעת בטכניקת הכניסה (MxV<=-100%) או ביציאה הדינמית
- [ ] #4 תלות: שם התיקייה החודשית יסופק ע"י עמיחי לפני התחלה
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
התקדמות (צ'אט 2026-06-27, READ-ONLY, raw דפוס-לילה night=(ScanPrice-D1_Open)/ScanPrice, post_analysis CLEAN n=161, ללא Borrow/Score): דירוג 7 המדדים מול תוצאת-לילה —
(1) MxV = אות-בסיס חזק+יציב (Spearman -0.315; MxV<=-100% → 77% ירדו, night חציון +12.71% מול 58%/+1.87% ב->-100%; 3/3 חודשים).
(2) TPD (מרחק close מ-(H+L+C)/3) = אות מותנה אורתוגונלי, התוספת הגדולה בתוך MxV<=-100% (Δ+11.80pp; חצי-עליון night +20.2%, maxrise שלילי). standalone~0.
(3) ScanChange% = השני standalone (Spearman +0.240) והשני בתוספת (Δ+8.14pp), אך חופף ל-MxV (גודל-פאמפ). הערה: נדחה בטעות קודם עקב שם-עמודה (ScanChange מול ScanChange%) — תוקן, מלא 88-100%.
(4) RunUp = חופף ל-MxV (Δ-2.35pp redundant). (5) REL_VOL = תוספת קלה לא-יציבה (Δ+3.78pp). (6) RSI = חלש+הפוך (RSI נמוך עדיף, overbought 91-99 הגרוע; מנוגד למשקל RSI>=90=מלא בנוסחת Score — אישור נוסף למחיקת Score). (7) ATRX = רעש (Δ+0.18pp).
caveats: raw; Score>=60 (מגבלת-מבנה → TASK-200); ריכוז-יוני (33/50); רבעונים n~25/15 רועשים; אימות רב-חודשי ~2026-07-27. שלב הבא = IB ground-truth (האוכלוסייה האמיתית) כשתסופק התיקייה החודשית.
<!-- SECTION:NOTES:END -->
