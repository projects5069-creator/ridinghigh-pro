import pandas as pd
import os
from datetime import datetime

class DataLogger:
    def __init__(self):
        self.data_dir = os.path.expanduser("~/RidingHighPro/data")
        os.makedirs(self.data_dir, exist_ok=True)

    def save_daily_snapshot(self, results):
        """
        שמירת snapshot יומי
        רק הסריקה האחרונה של היום (לא הכפלות!)
        """
        if not results:
            return

        today = datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(self.data_dir, f"{today}.csv")

        # המרה ל-DataFrame
        df = pd.DataFrame(results)

        # הוספת timestamp
        df['Date'] = today
        df['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # עיגול Score ל-2 ספרות
        if 'Score' in df.columns:
            df['Score'] = df['Score'].round(2)

        # אם הקובץ קיים - נחליף אותו (לא נוסיף!)
        # כך נשמור רק את הסריקה האחרונה
        df.to_csv(filepath, index=False)

        return filepath

    def load_date(self, date):
        """טעינת נתונים לפי תאריך"""
        filepath = os.path.join(self.data_dir, f"{date}.csv")

        if not os.path.exists(filepath):
            return None

        try:
            df = pd.read_csv(filepath)

            # וידוא שאין כפילויות (במקרה של קבצים ישנים)
            if 'Ticker' in df.columns:
                # שמור רק את השורה האחרונה של כל טיקר
                df = df.drop_duplicates(subset=['Ticker'], keep='last')

            return df
        except Exception as e:
            print(f"Error loading {date}: {e}")
            return None

    def get_all_dates(self):
        """קבלת רשימת כל התאריכים הזמינים"""
        if not os.path.exists(self.data_dir):
            return []

        files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
        dates = [f.replace('.csv', '') for f in files]

        # מיון לפי תאריך (מהחדש לישן)
        return sorted(dates, reverse=True)
