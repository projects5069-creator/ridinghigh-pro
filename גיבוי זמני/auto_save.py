#!/usr/bin/env python3
"""
Auto-save daily at 6PM
"""

import schedule
import time
from datetime import datetime
from finvizfinance.screener.overview import Overview
import yfinance as yf
from data_logger import DataLogger
from config import WEIGHTS

class AutoSaver:
    
    def calculate_mxv(self, market_cap, price, volume):
        try:
            if market_cap == 0:
                return 0
            return ((market_cap - (price * volume)) / market_cap) * 100
        except:
            return 0
    
    def calculate_atrx(self, atr, price):
        try:
            return (atr / price) * 100
        except:
            return 0
    
    def calculate_score(self, metrics):
        score = 0
        
        if metrics['mxv'] < 0:
            score += WEIGHTS['MXV']
        
        vwap_ratio = abs(metrics['vwap_distance']) / 50
        score += min(vwap_ratio, 1) * WEIGHTS['VWAP']
        
        atrx_ratio = metrics['atrx'] / 15
        score += min(atrx_ratio, 1) * WEIGHTS['ATRX']
        
        score += WEIGHTS['REL_VOL'] * 0.5
        
        run_up_ratio = metrics['run_up'] / 5
        score += min(run_up_ratio, 1) * WEIGHTS['RUN_UP']
        
        gap_ratio = abs(metrics['gap']) / 20
        score += min(gap_ratio, 1) * WEIGHTS['GAP']
        
        score += (metrics['rsi'] / 80) * WEIGHTS['RSI']
        
        return round(score, 2)
    
    def scan_and_save(self):
        """סריקה ושמירה"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting daily scan...")
        
        try:
            # משיכת טיקרים
            fviz = Overview()
            filters_dict = {
                'Price': 'Over $2',
                'Performance': 'Today +10%',
            }
            fviz.set_filter(filters_dict=filters_dict)
            tickers = fviz.screener_view(columns=['Ticker'])
            
            if tickers is None or tickers.empty:
                print("No stocks found")
                return
            
            ticker_list = tickers['Ticker'].tolist()[:50]
            
            results = []
            
            for ticker in ticker_list:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    hist = stock.history(period='2d')
                    
                    if hist.empty or len(hist) < 2:
                        continue
                    
                    current = hist.iloc[-1]
                    previous = hist.iloc[-2]
                    
                    price = current['Close']
                    if price < 2:
                        continue
                    
                    change = ((current['Close'] - previous['Close']) / previous['Close']) * 100
                    volume = current['Volume']
                    market_cap = info.get('marketCap', 0)
                    
                    vwap = (current['High'] + current['Low'] + current['Close']) / 3
                    run_up = ((current['High'] - current['Open']) / current['Open']) * 100 if current['Open'] > 0 else 0
                    gap = ((current['Open'] - previous['Close']) / previous['Close']) * 100
                    
                    mxv = self.calculate_mxv(market_cap, price, volume)
                    atr = current['High'] - current['Low']
                    atrx = self.calculate_atrx(atr, price)
                    vwap_dist = ((price / vwap) - 1) * 100 if vwap > 0 else 0
                    
                    metrics = {
                        'mxv': mxv,
                        'atrx': atrx,
                        'run_up': run_up,
                        'vwap_distance': vwap_dist,
                        'rsi': 50,
                        'gap': gap,
                        'rel_vol': 1.0,
                    }
                    
                    score = self.calculate_score(metrics)
                    
                    results.append({
                        'Ticker': ticker,
                        'Score': score,
                        'Price': price,
                        'Change': change,
                        'MxV': mxv,
                        'RunUp': run_up,
                        'Gap': gap,
                        'ATRX': atrx,
                        'VWAP_Dist': vwap_dist,
                    })
                    
                    if len(results) >= 20:
                        break
                        
                except:
                    continue
            
            # שמירה
            if results:
                logger = DataLogger()
                logger.save_daily_snapshot(results)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Saved {len(results)} stocks!")
            else:
                print("No results to save")
                
        except Exception as e:
            print(f"Error: {e}")

def run_scheduler():
    """הרץ scheduler"""
    saver = AutoSaver()
    
    # קבע שעה: 18:00 (6 PM בפרו)
    schedule.every().day.at("18:00").do(saver.scan_and_save)
    
    print("🤖 Auto-saver started!")
    print("📅 Will save daily at 6:00 PM")
    print("⏰ Waiting for next scheduled time...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # בדוק כל דקה

if __name__ == "__main__":
    run_scheduler()
