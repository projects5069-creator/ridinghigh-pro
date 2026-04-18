#!/usr/bin/env python3
"""
RidingHigh Pro - FINVIZ Scanner
"""

import pandas as pd
import yfinance as yf
import time
from finvizfinance.screener.overview import Overview
from config import WEIGHTS, THRESHOLDS, COLORS

class StockScanner:
    
    def fetch_finviz_stocks(self):
        """משיכת מניות מ-FINVIZ"""
        print(f"{COLORS['bold']}🔍 Fetching from FINVIZ...{COLORS['reset']}")
        
        try:
            fviz = Overview()
            
            filters_dict = {
                'Price': 'Over $2',
                'Performance': 'Today +10%',
            }
            
            fviz.set_filter(filters_dict=filters_dict)
            df = fviz.screener_view()
            
            if df is None or df.empty:
                print(f"{COLORS['hot']}No stocks found{COLORS['reset']}")
                return []
            
            tickers = df['Ticker'].tolist()
            print(f"{COLORS['cool']}✅ Found {len(tickers)} stocks{COLORS['reset']}")
            return tickers
            
        except Exception as e:
            print(f"{COLORS['hot']}❌ Error: {e}{COLORS['reset']}")
            return []
    
    def fetch_stock_data(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='5d')
            
            if hist.empty or len(hist) < 2:
                return None
            
            info = stock.info
            current = hist.iloc[-1]
            previous = hist.iloc[-2]
            
            change_pct = ((current['Close'] - previous['Close']) / previous['Close']) * 100
            
            vwap = (current['High'] + current['Low'] + current['Close']) / 3
            run_up = ((current['High'] - current['Open']) / current['Open']) * 100
            gap = ((current['Open'] - previous['Close']) / previous['Close']) * 100
            
            return {
                'ticker': ticker,
                'price': current['Close'],
                'change': change_pct,
                'volume': current['Volume'],
                'market_cap': info.get('marketCap', 0),
                'vwap': vwap,
                'run_up': run_up,
                'gap': gap,
                'rsi': 50,
                'atr': current['High'] - current['Low'],
            }
        except:
            return None
    
    def calculate_mxv(self, market_cap, price, volume):
        try:
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
    
    def scan(self):
        print(f"\n{COLORS['bold']}{'='*70}{COLORS['reset']}")
        print(f"{COLORS['bold']}🚀 RIDING HIGH PRO{COLORS['reset']}")
        print(f"{COLORS['bold']}{'='*70}{COLORS['reset']}\n")
        
        tickers = self.fetch_finviz_stocks()
        
        if not tickers:
            print("No stocks found")
            return
        
        print(f"\n📊 Analyzing {len(tickers)} stocks...\n")
        
        results = []
        
        for ticker in tickers[:20]:
            print(f"  {ticker}...", end=' ')
            
            data = self.fetch_stock_data(ticker)
            
            if not data:
                print("Skip")
                continue
            
            mxv = self.calculate_mxv(data['market_cap'], data['price'], data['volume'])
            atrx = self.calculate_atrx(data['atr'], data['price'])
            vwap_dist = ((data['price'] / data['vwap']) - 1) * 100
            
            metrics = {
                'mxv': mxv,
                'atrx': atrx,
                'run_up': data['run_up'],
                'vwap_distance': vwap_dist,
                'rsi': data['rsi'],
                'gap': data['gap'],
            }
            
            score = self.calculate_score(metrics)
            
            results.append({
                'Ticker': ticker,
                'Price': f"${data['price']:.2f}",
                'Change': f"{data['change']:+.1f}%",
                'MxV': f"{mxv:.0f}%",
                'Score': score,
            })
            
            color = COLORS['hot'] if score >= 80 else COLORS['warm'] if score >= 60 else COLORS['cool']
            print(f"{color}{score:.0f}{COLORS['reset']}")
            
            time.sleep(0.3)
        
        results.sort(key=lambda x: x['Score'], reverse=True)
        
        print(f"\n{COLORS['bold']}{'='*70}{COLORS['reset']}")
        print(f"{COLORS['bold']}📊 RESULTS{COLORS['reset']}")
        print(f"{COLORS['bold']}{'='*70}{COLORS['reset']}\n")
        
        if results:
            df = pd.DataFrame(results)
            print(df.to_string(index=False))
        
        print(f"\n{COLORS['bold']}{'='*70}{COLORS['reset']}\n")

if __name__ == "__main__":
    scanner = StockScanner()
    scanner.scan()
