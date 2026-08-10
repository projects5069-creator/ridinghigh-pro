---
id: TASK-296
title: Rotate the exposed ridinghigh-sheets-v2 service account key on 2026-08-15
status: To Do
assignee: []
created_date: '2026-08-10 02:04'
labels: []
dependencies: []
priority: high
ordinal: 294000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
נחשף 9/8. מפתח חשבון-השירות ridinghigh-sheets-v2, key id 6cdaadb7a4f3c47d6be965eb1f4f24323d7bff62 שנוצר 19/4, נמצא בקובץ google_credentials.json בתוך עותק-ריפו ישן שהועבר בטעות ל-ClaudeWork וסונכרן ל-Google Drive למשך כ-11 דקות. Drive פרטי, לא ציבורי. עמיחי רוקן את האשפה ב-Drive באותו ערב. הקובץ בודד ל-secrets_quarantine.
שני מפתחות נוספים שנמצאו באותו מקום כבר מתים ואינם בקונסולה.

תזמון: שבת 2026-08-15 או ראשון 16/8. הנימוק: ההחלפה אינה משנה התנהגות אלא אימות בלבד, אך כשל בה מפסיק כתיבה - ובתוך חלון-המדידה זה אובדן דאטה בלתי הפיך. בסוף שבוע אין ריצות משמעותיות ויש יומיים מרווח.

סדר הביצוע מחייב, כל היפוך שלו משבית את המערכת:
1. Google Cloud, ridinghigh-sheets-v2, Keys, ADD KEY, מפתח חדש
2. GitHub Secrets, עדכון ה-Secret לתוכן החדש
3. הרצת workflow אחד ואימות שהוא עובר וכותב
4. רק אז מחיקת המפתח מ-19/4
שער-קבלה: המפתח מ-19/4 אינו קיים בקונסולה, וריצה אחת אחרי ההחלפה כתבה ל-Sheets בהצלחה.
<!-- SECTION:DESCRIPTION:END -->
