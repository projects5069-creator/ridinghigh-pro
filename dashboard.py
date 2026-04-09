#!/usr/bin/env python3
"""
RidingHigh Pro v14.6 - Score 7 Metrics
- Timeline Archive exported as proper grid (pivot) per date
- New "Analysis Export" with Timeline Summary for AI analysis
- Full export unchanged except Timeline Archive fix
"""

import streamlit as st
import pandas as pd
import math
import time
import plotly.express as px
from finvizfinance.screener.overview import Overview
from datetime import datetime, time as dt_time, timedelta
import pytz
import pytz
from data_logger import DataLogger
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
import os
import shutil
from gsheets_sync import save_snapshot_to_sheets, save_timeline_to_sheets, save_portfolio_to_sheets, load_portfolio_from_sheets, load_timeline_dates_from_sheets, load_timeline_from_sheets
import json

st.set_page_config(
    page_title="RidingHigh Pro v14.6",
    page_icon="🚀",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
    }
    h1 {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        font-size: 1.8rem;
        margin-top: 0;
    }
    h2 {
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
        font-size: 1.2rem;
    }
    div[data-testid="metric-container"] {
        padding: 5px;
    }
</style>
""", unsafe_allow_html=True)

class Dashboard:
    
    def __init__(self):
        self.logger = DataLogger()
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.finviz_df = None
        
        self.cache_dir = os.path.expanduser("~/RidingHighPro/data")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "market_cap_cache.json")
        
        self.market_cap_cache = {}
        self.shares_cache = {}
    
    def load_from_cache_file(self, ticker):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    if ticker in cache_data:
                        return cache_data[ticker].get('market_cap', None)
            return None
        except:
            return None
    
    def save_to_cache_file(self, ticker, market_cap):
        try:
            cache_data = {}
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
            
            cache_data[ticker] = {
                'market_cap': int(market_cap),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            return True
        except:
            return False
    
    def get_from_history_all_days(self, ticker, field):
        try:
            dates = self.logger.get_all_dates()
            
            if not dates:
                return None
            
            for date in dates:
                try:
                    df = self.logger.load_date(date)
                    
                    if df is None or df.empty:
                        continue
                    
                    if 'Ticker' not in df.columns:
                        continue
                    
                    matching_rows = df[df['Ticker'] == ticker]
                    
                    if matching_rows.empty:
                        continue
                    
                    row = matching_rows.iloc[-1]
                    
                    if field in row and pd.notna(row[field]) and row[field] != 0:
                        return row[field]
                except:
                    continue
            
            return None
        except:
            return None
    
    def fetch_finviz_data(self):
        try:
            fviz = Overview()
            filters_dict = {
                'Price': 'Over $2',
                'Performance': 'Today +15%',
            }
            fviz.set_filter(filters_dict=filters_dict)
            
            df = fviz.screener_view()
            
            if df is None or df.empty:
                return None
            
            df_sorted = df.sort_values(by='Change', ascending=False)
            self.finviz_df = df_sorted
            
            return self.finviz_df
            
        except Exception as e:
            return None
    
    def parse_market_cap(self, market_cap_str):
        try:
            if pd.isna(market_cap_str) or market_cap_str == '-':
                return None
            
            market_cap_str = str(market_cap_str).replace(',', '')
            
            if 'B' in market_cap_str:
                return float(market_cap_str.replace('B', '')) * 1_000_000_000
            elif 'M' in market_cap_str:
                return float(market_cap_str.replace('M', '')) * 1_000_000
            else:
                return float(market_cap_str)
        except:
            return None
    
    def parse_volume(self, volume_str):
        try:
            if pd.isna(volume_str) or volume_str == '-':
                return None
            
            volume_str = str(volume_str).replace(',', '')
            
            if 'M' in volume_str:
                return int(float(volume_str.replace('M', '')) * 1_000_000)
            elif 'K' in volume_str:
                return int(float(volume_str.replace('K', '')) * 1_000)
            else:
                return int(float(volume_str))
        except:
            return None
    
    def get_market_cap_smart(self, ticker, price, finviz_mc=None):
        market_cap = None
        
        if finviz_mc and finviz_mc > 0:
            market_cap = int(finviz_mc)
            self.market_cap_cache[ticker] = market_cap
            self.save_to_cache_file(ticker, market_cap)
            return market_cap
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            mc = info.get('marketCap', None)
            if mc and mc > 0:
                market_cap = int(mc)
                self.market_cap_cache[ticker] = market_cap
                self.save_to_cache_file(ticker, market_cap)
                return market_cap
        except:
            pass
        
        try:
            if ticker not in self.shares_cache:
                stock = yf.Ticker(ticker)
                info = stock.info
                shares = info.get('sharesOutstanding', None)
                if shares and shares > 0:
                    self.shares_cache[ticker] = int(shares)
            
            if ticker in self.shares_cache:
                shares = self.shares_cache[ticker]
                if shares > 0 and price > 0:
                    market_cap = int(shares * price)
                    self.market_cap_cache[ticker] = market_cap
                    self.save_to_cache_file(ticker, market_cap)
                    return market_cap
        except:
            pass
        
        try:
            hist_mc = self.get_from_history_all_days(ticker, 'MarketCap')
            if hist_mc and hist_mc > 0:
                market_cap = int(hist_mc)
                self.market_cap_cache[ticker] = market_cap
                self.save_to_cache_file(ticker, market_cap)
                return market_cap
        except:
            pass
        
        try:
            cached_mc = self.load_from_cache_file(ticker)
            if cached_mc and cached_mc > 0:
                market_cap = int(cached_mc)
                self.market_cap_cache[ticker] = market_cap
                return market_cap
        except:
            pass
        
        return None
    
    def preload_market_caps(self, finviz_df, progress_callback=None):
        if finviz_df is None or finviz_df.empty:
            return
        
        total = len(finviz_df)
        
        for idx, row in finviz_df.iterrows():
            ticker = row['Ticker']
            
            if progress_callback:
                progress_callback(idx + 1, total, ticker)
            
            finviz_mc = self.parse_market_cap(row.get('Market Cap', None))
            price = float(row.get('Price', 0))
            
            market_cap = self.get_market_cap_smart(ticker, price, finviz_mc)
            
            time.sleep(0.3)
    
    def analyze_ticker_from_yahoo(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='5d')
            
            if hist.empty or len(hist) < 2:
                return None
            
            info = stock.info
            current = hist.iloc[-1]
            previous = hist.iloc[-2]
            
            price = current['Close']
            change = ((current['Close'] - previous['Close']) / previous['Close']) * 100
            volume = current['Volume']
            
            market_cap = self.get_market_cap_smart(ticker, price)
            
            if market_cap is None or market_cap == 0:
                return None
            
            rsi = 50
            atr = 0
            atrx = 0
            rel_vol = 1.0
            run_up = 0
            gap = 0
            vwap_dist = 0
            price_to_high = 0
            price_to_52w_high = 0
            shares_outstanding = self.shares_cache.get(ticker, 0)
            float_pct = 0
            
            full_hist = stock.history(period='60d')
            
            if not full_hist.empty and len(full_hist) >= 2:
                try:
                    if len(full_hist) >= 14:
                        rsi_indicator = RSIIndicator(close=full_hist['Close'], window=14)
                        rsi_values = rsi_indicator.rsi()
                        if not rsi_values.empty and not pd.isna(rsi_values.iloc[-1]):
                            rsi = rsi_values.iloc[-1]
                except:
                    rsi = 50
                
                try:
                    if len(full_hist) >= 14:
                        atr_indicator = AverageTrueRange(
                            high=full_hist['High'],
                            low=full_hist['Low'],
                            close=full_hist['Close'],
                            window=14
                        )
                        atr_values = atr_indicator.average_true_range()
                        if not atr_values.empty and not pd.isna(atr_values.iloc[-1]):
                            atr = atr_values.iloc[-1]
                        else:
                            atr = current['High'] - current['Low']
                    else:
                        atr = current['High'] - current['Low']
                    atrx = (atr / price) * 100 if price > 0 else 0
                except:
                    atr = 0
                    atrx = 0
                
                try:
                    avg_volume = info.get('averageVolume', volume)
                    if avg_volume > 0:
                        rel_vol = volume / avg_volume
                    else:
                        if len(full_hist) >= 20:
                            avg_vol_20 = full_hist['Volume'].tail(20).mean()
                        else:
                            avg_vol_20 = full_hist['Volume'].mean()
                        rel_vol = volume / avg_vol_20 if avg_vol_20 > 0 else 1.0
                except:
                    rel_vol = 1.0
                
                try:
                    if current['Open'] > 0:
                        run_up = ((price - current['Open']) / current['Open']) * 100
                except:
                    run_up = 0
                
                try:
                    gap = ((current['Open'] - previous['Close']) / previous['Close']) * 100
                except:
                    gap = 0
                
                try:
                    vwap = (current['High'] + current['Low'] + price) / 3
                    vwap_dist = ((price / vwap) - 1) * 100 if vwap > 0 else 0
                except:
                    vwap_dist = 0
                
                try:
                    high_today = current['High']
                    price_to_high = ((price - high_today) / high_today) * 100 if high_today > 0 else 0
                except:
                    price_to_high = 0
                
                try:
                    high_52w = info.get('fiftyTwoWeekHigh', price)
                    price_to_52w_high = ((price - high_52w) / high_52w) * 100 if high_52w > 0 else 0
                except:
                    price_to_52w_high = 0
                
                if shares_outstanding == 0:
                    try:
                        shares_outstanding = info.get('sharesOutstanding', 0)
                        if shares_outstanding == 0:
                            shares_outstanding = int(market_cap / price) if price > 0 else 0
                    except:
                        shares_outstanding = int(market_cap / price) if price > 0 else 0
                
                try:
                    float_pct = (volume / shares_outstanding * 100) if shares_outstanding > 0 else 0
                except:
                    float_pct = 0
            
            mxv = self.calculate_mxv(market_cap, price, volume)
            
            metrics = {
                'mxv': mxv,
                'price_to_52w_high': price_to_52w_high,
                'price_to_high': price_to_high,
                'rel_vol': rel_vol,
                'rsi': rsi,
                'atrx': atrx,
                'run_up': run_up,
                'float_pct': float_pct,
                'gap': gap,
                'vwap_dist': vwap_dist,
            }
            
            score = self.calculate_score(metrics)
            
            return {
                'Ticker': ticker,
                'Price': round(price, 2),
                'Change': round(change, 2),
                'Volume': int(volume),
                'MarketCap': int(market_cap),
                'SharesOutstanding': int(shares_outstanding) if shares_outstanding > 0 else 0,
                'MxV': round(mxv, 2),
                'RunUp': round(run_up, 2),
                'PriceToHigh': round(price_to_high, 2),
                'PriceTo52WHigh': round(price_to_52w_high, 2),
                'RSI': round(rsi, 2),
                'ATRX': round(atrx, 2),
                'REL_VOL': round(rel_vol, 2),
                'Gap': round(gap, 2),
                'VWAP': round(vwap_dist, 2),
                'Float%': round(float_pct, 2),
                'Score': round(score, 2),
            }
            
        except Exception as e:
            return None
    
    def analyze_ticker_complete(self, ticker, finviz_row):
        try:
            price = finviz_row.get('Price', None)
            if pd.isna(price) or price is None:
                return None
            price = float(price)
            
            if price < 2:
                return None
            
            change = finviz_row.get('Change', None)
            if pd.isna(change):
                return None
            change = float(change) * 100
            
            volume = self.parse_volume(finviz_row.get('Volume', None))
            if volume is None or volume == 0:
                return None
            
            finviz_mc = self.parse_market_cap(finviz_row.get('Market Cap', None))
            market_cap = self.get_market_cap_smart(ticker, price, finviz_mc)
            
            if market_cap is None or market_cap == 0:
                return None
            
            rsi = 50
            atr = 0
            atrx = 0
            rel_vol = 1.0
            run_up = 0
            gap = 0
            vwap_dist = 0
            price_to_high = 0
            price_to_52w_high = 0
            shares_outstanding = self.shares_cache.get(ticker, 0)
            float_pct = 0
            
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='60d')
                
                if not hist.empty and len(hist) >= 2:
                    info = stock.info
                    current = hist.iloc[-1]
                    previous = hist.iloc[-2]
                    
                    try:
                        if len(hist) >= 14:
                            rsi_indicator = RSIIndicator(close=hist['Close'], window=14)
                            rsi_values = rsi_indicator.rsi()
                            if not rsi_values.empty and not pd.isna(rsi_values.iloc[-1]):
                                rsi = rsi_values.iloc[-1]
                    except:
                        rsi = 50
                    
                    try:
                        if len(hist) >= 14:
                            atr_indicator = AverageTrueRange(
                                high=hist['High'],
                                low=hist['Low'],
                                close=hist['Close'],
                                window=14
                            )
                            atr_values = atr_indicator.average_true_range()
                            if not atr_values.empty and not pd.isna(atr_values.iloc[-1]):
                                atr = atr_values.iloc[-1]
                            else:
                                atr = current['High'] - current['Low']
                        else:
                            atr = current['High'] - current['Low']
                        atrx = (atr / price) * 100 if price > 0 else 0
                    except:
                        atr = 0
                        atrx = 0
                    
                    try:
                        avg_volume = info.get('averageVolume', volume)
                        if avg_volume > 0:
                            rel_vol = volume / avg_volume
                        else:
                            if len(hist) >= 20:
                                avg_vol_20 = hist['Volume'].tail(20).mean()
                            else:
                                avg_vol_20 = hist['Volume'].mean()
                            rel_vol = volume / avg_vol_20 if avg_vol_20 > 0 else 1.0
                    except:
                        rel_vol = 1.0
                    
                    try:
                        if current['Open'] > 0:
                            run_up = ((price - current['Open']) / current['Open']) * 100
                    except:
                        run_up = 0
                    
                    try:
                        gap = ((current['Open'] - previous['Close']) / previous['Close']) * 100
                    except:
                        gap = 0
                    
                    try:
                        vwap = (current['High'] + current['Low'] + price) / 3
                        vwap_dist = ((price / vwap) - 1) * 100 if vwap > 0 else 0
                    except:
                        vwap_dist = 0
                    
                    try:
                        high_today = current['High']
                        price_to_high = ((price - high_today) / high_today) * 100 if high_today > 0 else 0
                    except:
                        price_to_high = 0
                    
                    try:
                        high_52w = info.get('fiftyTwoWeekHigh', price)
                        price_to_52w_high = ((price - high_52w) / high_52w) * 100 if high_52w > 0 else 0
                    except:
                        price_to_52w_high = 0
                    
                    if shares_outstanding == 0:
                        try:
                            shares_outstanding = info.get('sharesOutstanding', 0)
                            if shares_outstanding == 0:
                                shares_outstanding = int(market_cap / price) if price > 0 else 0
                        except:
                            shares_outstanding = int(market_cap / price) if price > 0 else 0
                    
                    try:
                        float_pct = (volume / shares_outstanding * 100) if shares_outstanding > 0 else 0
                    except:
                        float_pct = 0
            
            except:
                if shares_outstanding == 0:
                    shares_outstanding = int(market_cap / price) if price > 0 else 0
            
            mxv = self.calculate_mxv(market_cap, price, volume)
            
            metrics = {
                'mxv': mxv,
                'price_to_52w_high': price_to_52w_high,
                'price_to_high': price_to_high,
                'rel_vol': rel_vol,
                'rsi': rsi,
                'atrx': atrx,
                'run_up': run_up,
                'float_pct': float_pct,
                'gap': gap,
                'vwap_dist': vwap_dist,
            }
            
            score = self.calculate_score(metrics)
            
            return {
                'Ticker': ticker,
                'Price': round(price, 2),
                'Change': round(change, 2),
                'Volume': int(volume),
                'MarketCap': int(market_cap),
                'SharesOutstanding': int(shares_outstanding) if shares_outstanding > 0 else 0,
                'MxV': round(mxv, 2),
                'RunUp': round(run_up, 2),
                'PriceToHigh': round(price_to_high, 2),
                'PriceTo52WHigh': round(price_to_52w_high, 2),
                'RSI': round(rsi, 2),
                'ATRX': round(atrx, 2),
                'REL_VOL': round(rel_vol, 2),
                'Gap': round(gap, 2),
                'VWAP': round(vwap_dist, 2),
                'Float%': round(float_pct, 2),
                'Score': round(score, 2),
            }
            
        except Exception as e:
            return None
    
    def scan(self, tracked_tickers=None, progress_callback=None, skip_preload=False):
        finviz_df = self.fetch_finviz_data()
        
        if finviz_df is None or finviz_df.empty:
            return []
        
        if not skip_preload:
            self.preload_market_caps(finviz_df, progress_callback)
        
        results = []
        scanned_tickers = set()
        
        for idx, row in finviz_df.iterrows():
            ticker = row['Ticker']
            scanned_tickers.add(ticker)
            data = self.analyze_ticker_complete(ticker, row)
            if data:
                results.append(data)
            
            time.sleep(0.1)
        
        if tracked_tickers:
            missing_tickers = tracked_tickers - scanned_tickers
            
            for ticker in missing_tickers:
                data = self.analyze_ticker_from_yahoo(ticker)
                if data:
                    results.append(data)
                
                time.sleep(0.2)
        
        return sorted(results, key=lambda x: x['Score'], reverse=True)
    
    def calculate_mxv(self, market_cap, price, volume):
        try:
            if market_cap == 0:
                return 0
            return ((market_cap - (price * volume)) / market_cap) * 100
        except:
            return 0
    
    def calculate_score(self, metrics):
        score = 0
        
        try:
            if metrics['mxv'] < 0:
                mxv_ratio = min(abs(metrics['mxv']) / 50, 1)
                score += mxv_ratio * 20
        except:
            pass
        
        try:
            if metrics['price_to_52w_high'] > 0:
                p52w_ratio = min(metrics['price_to_52w_high'] / 100, 1)
                score += p52w_ratio * 10
        except:
            pass
        
        try:
            if metrics['price_to_high'] < 0:
                pth_ratio = min(abs(metrics['price_to_high']) / 10, 1)
                score += pth_ratio * 15
        except:
            pass
        
        try:
            rel_vol_ratio = min(metrics['rel_vol'] / 2, 1)
            score += rel_vol_ratio * 15
        except:
            pass
        
        try:
            if metrics['rsi'] > 80:
                score += 15
            else:
                score += (metrics['rsi'] / 80) * 15
        except:
            pass
        
        try:
            atrx_ratio = min(metrics['atrx'] / 15, 1)
            score += atrx_ratio * 10
        except:
            pass
        
        try:
            if metrics['run_up'] < 0:
                runup_ratio = min(abs(metrics['run_up']) / 5, 1)
                score += runup_ratio * 5
        except:
            pass
        
        try:
            float_ratio = min(metrics['float_pct'] / 10, 1)
            score += float_ratio * 5
        except:
            pass
        
        try:
            gap_ratio = min(abs(metrics['gap']) / 20, 1)
            score += gap_ratio * 3
        except:
            pass
        
        try:
            vwap_ratio = min(abs(metrics['vwap_dist']) / 15, 1)
            score += vwap_ratio * 2
        except:
            pass
        
        return round(score, 2)

class LiveTracker:
    
    def __init__(self):
        self.tracker_dir = os.path.expanduser("~/RidingHighPro/data/live_tracker")
        self.archive_dir = os.path.expanduser("~/RidingHighPro/data/timeline_archive")
        self.snapshot_dir = os.path.expanduser("~/RidingHighPro/data/daily_snapshots")
        
        os.makedirs(self.tracker_dir, exist_ok=True)
        os.makedirs(self.archive_dir, exist_ok=True)
        os.makedirs(self.snapshot_dir, exist_ok=True)
        
        self.today_file = os.path.join(
            self.tracker_dir,
            f"tracker_{datetime.now().strftime('%Y-%m-%d')}.csv"
        )
    
    def get_tracked_tickers(self):
        if not os.path.exists(self.today_file):
            return set()
        
        try:
            df = pd.read_csv(self.today_file, index_col=0)
            return set(df.index.tolist())
        except:
            return set()
    
    def add_minute_data(self, results, scan_time):
        if not results:
            return 0
        
        filtered = []
        for r in results:
            try:
                score = float(r['Score'])
                if not pd.isna(score):
                    filtered.append(r)
            except:
                continue
        
        if not filtered:
            return 0
        
        current_time = scan_time.strftime('%H:%M')
        
        if os.path.exists(self.today_file):
            try:
                df = pd.read_csv(self.today_file, index_col=0)
                if df.index.name == 'index':
                    df.index.name = 'Ticker'
            except:
                df = pd.DataFrame()
                df.index.name = 'Ticker'
        else:
            df = pd.DataFrame()
            df.index.name = 'Ticker'
        
        for r in filtered:
            ticker = r['Ticker']
            score = round(r['Score'], 2)
            df.loc[ticker, current_time] = score
        
        df.to_csv(self.today_file)
        
        return len(filtered)
    
    def save_daily_snapshot(self, results):
        if not results:
            return False
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            snapshot_file = os.path.join(self.snapshot_dir, f"snapshot_{today}.csv")
            
            df = pd.DataFrame(results)
            df.to_csv(snapshot_file, index=False)
            save_snapshot_to_sheets(df)
            
            return True
        except:
            return False
    
    def get_today_grid(self):
        if not os.path.exists(self.today_file):
            return None
        
        try:
            df = pd.read_csv(self.today_file, index_col=0)
            
            if df.empty:
                return None
            
            if df.index.name == 'index':
                df.index.name = 'Ticker'
            
            columns = sorted(df.columns, reverse=True)
            df = df[columns]
            
            df = df.round(2)
            
            return df
        except Exception as e:
            return None
    
    def archive_today(self):
        if not os.path.exists(self.today_file):
            return False
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            archive_file = os.path.join(self.archive_dir, f"timeline_{today}.csv")
            
            shutil.copy2(self.today_file, archive_file)
            archive_df = pd.read_csv(self.today_file, index_col=0)
            save_timeline_to_sheets(archive_df, today)
            return True
        except:
            return False
    
    def get_archive_dates(self):
        try:
            files = os.listdir(self.archive_dir)
            dates = []
            
            for f in files:
                if f.startswith('timeline_') and f.endswith('.csv'):
                    date_str = f.replace('timeline_', '').replace('.csv', '')
                    dates.append(date_str)
            
            return sorted(dates, reverse=True)
        except:
            return []
    
    def load_archive(self, date):
        try:
            archive_file = os.path.join(self.archive_dir, f"timeline_{date}.csv")
            
            if not os.path.exists(archive_file):
                return None
            
            df = pd.read_csv(archive_file, index_col=0)
            
            if df.empty:
                return None
            
            if df.index.name == 'index':
                df.index.name = 'Ticker'
            
            columns = sorted(df.columns, reverse=True)
            df = df[columns]
            
            df = df.round(2)
            
            return df
        except:
            return None

class PortfolioTracker:
    
    def __init__(self):
        self.portfolio_dir = os.path.expanduser("~/RidingHighPro/data/portfolio")
        os.makedirs(self.portfolio_dir, exist_ok=True)
        
        self.portfolio_file = os.path.join(self.portfolio_dir, "portfolio.csv")
    
    def add_positions(self, results, date):
        if not results:
            return 0
        
        high_score_stocks = [r for r in results if r['Score'] >= 60]
        
        if not high_score_stocks:
            return 0
        
        if os.path.exists(self.portfolio_file):
            try:
                existing_df = pd.read_csv(self.portfolio_file)
            except:
                existing_df = pd.DataFrame()
        else:
            existing_df = pd.DataFrame()
        
        if is_cloud():
            try:
                from gsheets_sync import load_portfolio_from_sheets
                sheets_df = load_portfolio_from_sheets()
                if sheets_df is not None and not sheets_df.empty:
                    existing_df = sheets_df
            except:
                pass
        
        new_positions = []
        for stock in high_score_stocks:
            position_key = f"{stock['Ticker']}_{date}"
            
            if not existing_df.empty and position_key in existing_df['PositionKey'].values:
                continue
            
            new_positions.append({
                'PositionKey': position_key,
                'Date': date,
                'Ticker': stock['Ticker'],
                'Score': round(stock['Score'], 2),
                'BuyPrice': round(stock['Price'], 2),
                'Status': 'Open'
            })
        
        if new_positions:
            new_df = pd.DataFrame(new_positions)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(self.portfolio_file, index=False)
            save_portfolio_to_sheets(combined_df)
            return len(new_positions)
        
        return 0
    
    def get_portfolio_with_current_prices(self):
        if not os.path.exists(self.portfolio_file):
            return None
        
        try:
            df = pd.read_csv(self.portfolio_file)
            
            if df.empty:
                return None
            
            df['CurrentPrice'] = 0.0
            df['Change%'] = 0.0
            df['P/L'] = 0.0
            
            for idx, row in df.iterrows():
                ticker = row['Ticker']
                buy_price = row['BuyPrice']
                
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='1d')
                    
                    if not hist.empty:
                        current_price = hist.iloc[-1]['Close']
                        df.at[idx, 'CurrentPrice'] = round(current_price, 2)
                        
                        change_pct = ((current_price - buy_price) / buy_price) * 100
                        df.at[idx, 'Change%'] = round(change_pct, 2)
                        
                        pl = current_price - buy_price
                        df.at[idx, 'P/L'] = round(pl, 2)
                except:
                    df.at[idx, 'CurrentPrice'] = buy_price
                    df.at[idx, 'Change%'] = 0.0
                    df.at[idx, 'P/L'] = 0.0
                
                time.sleep(0.1)
            
            df = df.sort_values(by='Date', ascending=False)
            
            return df
        except:
            return None
    
    def close_position(self, position_key):
        if not os.path.exists(self.portfolio_file):
            return False
        
        try:
            df = pd.read_csv(self.portfolio_file)
            df.loc[df['PositionKey'] == position_key, 'Status'] = 'Closed'
            df.to_csv(self.portfolio_file, index=False)
            return True
        except:
            return False
    
    def delete_position(self, position_key):
        if not os.path.exists(self.portfolio_file):
            return False
        
        try:
            df = pd.read_csv(self.portfolio_file)
            df = df[df['PositionKey'] != position_key]
            df.to_csv(self.portfolio_file, index=False)
            return True
        except:
            return False


def is_cloud():
    try:
        import streamlit as st
        return "gcp_service_account" in st.secrets
    except:
        return False

def _get_gc():
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    try:
        import streamlit as st
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
            return gspread.authorize(creds)
    except: pass
    import os
    path = os.path.expanduser("~/RidingHighPro/google_credentials.json")
    if os.path.exists(path):
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_file(path, scopes=scopes)
        return gspread.authorize(creds)
    return None

SHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"
PERU_TZ = pytz.timezone("America/Lima")


# ── Cached sheet loaders ──────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def _cached_timeline_live() -> pd.DataFrame:
    """timeline_live → raw DataFrame. Refreshes every 2 min."""
    try:
        gc = _get_gc()
        if not gc: return pd.DataFrame()
        data = gc.open_by_key(SHEET_ID).worksheet("timeline_live").get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _cached_daily_snapshots() -> pd.DataFrame:
    """daily_snapshots → raw DataFrame. Refreshes every 5 min."""
    try:
        gc = _get_gc()
        if not gc: return pd.DataFrame()
        data = gc.open_by_key(SHEET_ID).worksheet("daily_snapshots").get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def _cached_portfolio() -> pd.DataFrame:
    """portfolio → DataFrame with numeric cols. Refreshes every 60 min."""
    try:
        gc = _get_gc()
        if not gc: return pd.DataFrame()
        data = gc.open_by_key(SHEET_ID).worksheet("portfolio").get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        for col in ["Score", "BuyPrice", "CurrentPrice", "Change%", "P/L"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _cached_post_analysis() -> pd.DataFrame:
    """post_analysis → DataFrame via gsheets_sync. Refreshes every 5 min."""
    from gsheets_sync import load_post_analysis_from_sheets
    return load_post_analysis_from_sheets()


@st.cache_data(ttl=60)
def _cached_portfolio_live() -> pd.DataFrame:
    """portfolio_live tab — RunningHigh/RunningLow per pending stock. Refreshes every 60s."""
    try:
        gc = _get_gc()
        if not gc:
            return pd.DataFrame()
        data = gc.open_by_key(SHEET_ID).worksheet("portfolio_live").get_all_values()
        if len(data) <= 1:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        for col in ["EntryPrice", "RunningHigh", "RunningLow", "TP10_Price", "SL_Price", "CurrentPrice"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def load_latest_from_sheets():
    try:
        df = _cached_timeline_live()
        if df.empty: return None, None
        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        df = df[df["Date"] == today]
        if df.empty: return None, None
        latest_time = df["ScanTime"].max()
        df = df[df["ScanTime"] == latest_time]
        results = []
        for _, row in df.iterrows():
            try:
                def f(k): return float(row[k]) if row.get(k,"") not in ["nan","","None"] else 0
                results.append({"Ticker":row["Ticker"],"Score":f("Score"),"Price":f("Price"),"Change":f("Change"),"MxV":f("MxV"),"PriceTo52WHigh":f("PriceTo52WHigh"),"PriceToHigh":f("PriceToHigh"),"RSI":f("RSI"),"ATRX":f("ATRX"),"REL_VOL":f("REL_VOL"),"RunUp":f("RunUp"),"Float%":f("Float%"),"Gap":f("Gap"),"VWAP":f("VWAP")})
            except: continue
        return results, latest_time
    except Exception:
        return None, None

def load_timeline_today_from_sheets():
    try:
        df = _cached_timeline_live()
        if df.empty: return None
        today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        df = df[df["Date"] == today].copy()
        if df.empty: return None
        df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
        pivot = df.pivot_table(index="Ticker", columns="ScanTime", values="Score", aggfunc="last")
        return pivot[sorted(pivot.columns, reverse=True)].round(2)
    except: return None

def is_market_hours():
    peru_tz = pytz.timezone("America/Lima")
    now = datetime.now(peru_tz)
    market_open = dt_time(8, 30)
    market_close = dt_time(15, 0)
    current_time = now.time()
    is_weekday = now.weekday() < 5
    return is_weekday and market_open <= current_time <= market_close

def check_snapshot_time():
    peru_tz = pytz.timezone("America/Lima")
    now = datetime.now(peru_tz)
    snapshot_time = dt_time(14, 59)
    current_time = now.time()
    return snapshot_time <= current_time < dt_time(15, 0)


def _build_timeline_summary(arch_df):
    """
    Given a timeline_archive DataFrame (long format with Date, Ticker, ScanTime, Score),
    returns a summary DataFrame with one row per stock per day containing:
    - PeakScore, PeakTime, ScoreAtOpen, ScoreAtClose
    - MinutesToPeak, ScoreTrend, TimeAbove60
    """
    arch_df = arch_df.copy()
    arch_df["Score"] = pd.to_numeric(arch_df["Score"], errors="coerce")
    arch_df = arch_df.dropna(subset=["Score"])

    rows = []
    for (date, ticker), grp in arch_df.groupby(["Date", "Ticker"]):
        grp = grp.sort_values("ScanTime")
        scores = grp["Score"].values
        times  = grp["ScanTime"].values

        peak_idx   = scores.argmax()
        peak_score = round(float(scores[peak_idx]), 2)
        peak_time  = str(times[peak_idx])

        score_open  = round(float(scores[0]),  2) if len(scores) > 0 else None
        score_close = round(float(scores[-1]), 2) if len(scores) > 0 else None

        # minutes from first scan to peak
        try:
            t0   = datetime.strptime(str(times[0]),      "%H:%M")
            tpk  = datetime.strptime(peak_time,           "%H:%M")
            mins_to_peak = int((tpk - t0).total_seconds() / 60)
        except:
            mins_to_peak = None

        # trend: compare first third vs last third average
        n = len(scores)
        if n >= 6:
            avg_start = scores[:n//3].mean()
            avg_end   = scores[-(n//3):].mean()
            diff = avg_end - avg_start
            if diff > 2:
                trend = "Rising"
            elif diff < -2:
                trend = "Falling"
            else:
                trend = "Stable"
        else:
            trend = "Stable"

        time_above_60 = int((scores >= 60).sum())

        rows.append({
            "Date":         date,
            "Ticker":       ticker,
            "PeakScore":    peak_score,
            "PeakTime":     peak_time,
            "ScoreAtOpen":  score_open,
            "ScoreAtClose": score_close,
            "MinutesToPeak": mins_to_peak,
            "ScoreTrend":   trend,
            "TimeAbove60":  time_above_60,
            "TotalScans":   n,
        })

    return pd.DataFrame(rows)


def main_page():
    st.title("🚀 RidingHigh Pro v14.6")
    st.caption("Portfolio Tracker - Auto-saves stocks with score 60+ at 14:59")
    system_health_bar()

    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = Dashboard()
    
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'last_scan' not in st.session_state:
        st.session_state.last_scan = None
    if 'force_scan' not in st.session_state:
        st.session_state.force_scan = False
    if 'preload_done' not in st.session_state:
        st.session_state.preload_done = False
    if 'snapshot_done_today' not in st.session_state:
        st.session_state.snapshot_done_today = False
    if 'portfolio_saved_today' not in st.session_state:
        st.session_state.portfolio_saved_today = False
    
    st.sidebar.header("⚙️ Settings")
    
    auto_scan = st.sidebar.checkbox("🔄 Auto-Scan (every minute)", value=is_market_hours())
    
    if st.sidebar.button("🔄 Scan Now", type="primary"):
        st.session_state.force_scan = True
    
    if st.sidebar.button("🗑️ Clear Timeline"):
        tracker = LiveTracker()
        if os.path.exists(tracker.today_file):
            os.remove(tracker.today_file)
            st.sidebar.success("✅ Cleared!")
            st.rerun()
    
    if check_snapshot_time() and not st.session_state.snapshot_done_today:
        tracker = LiveTracker()
        portfolio = PortfolioTracker()
        
        if st.session_state.results:
            if tracker.save_daily_snapshot(st.session_state.results):
                st.sidebar.success("📸 Daily snapshot saved!")
            
            if not st.session_state.portfolio_saved_today:
                today = datetime.now().strftime('%Y-%m-%d')
                added = portfolio.add_positions(st.session_state.results, today)
                if added > 0:
                    st.sidebar.success(f"💼 Added {added} stocks to portfolio!")
                    st.session_state.portfolio_saved_today = True
        
        if tracker.archive_today():
            st.sidebar.success("📦 Timeline archived!")
        
        st.session_state.snapshot_done_today = True
    
    now = datetime.now()
    if now.hour == 0 and now.minute < 5:
        st.session_state.snapshot_done_today = False
        st.session_state.portfolio_saved_today = False
    
    should_scan = False

    if is_cloud():
        now_peru = datetime.now(PERU_TZ)
        last = st.session_state.last_scan
        if last is None or (now_peru - (last if last.tzinfo else PERU_TZ.localize(last))).total_seconds() >= 60 or st.session_state.force_scan:
            st.session_state.force_scan = False
            results, latest_time = load_latest_from_sheets()
            if results:
                st.session_state.results = results
                st.session_state.last_scan = now_peru
                st.sidebar.success(f"✅ {len(results)} stocks! (scan: {latest_time})")
            else:
                st.sidebar.info("⏳ Waiting for next scan...")
    else:
        if st.session_state.force_scan:
            should_scan = True
            st.session_state.force_scan = False
        elif auto_scan:
            if st.session_state.last_scan is None:
                should_scan = True
            else:
                time_diff = (datetime.now() - st.session_state.last_scan).total_seconds()
                if time_diff >= 60:
                    should_scan = True
    
    if should_scan:
        scan_start_time = datetime.now()
        
        with st.sidebar:
            progress_placeholder = st.empty()
            
            def show_progress(current, total, ticker):
                progress_placeholder.info(f"🔍 Loading {ticker} ({current}/{total})")
            
            with st.spinner("🔍 Scanning..."):
                tracker = LiveTracker()
                
                tracked_tickers = tracker.get_tracked_tickers()
                
                skip_preload = st.session_state.preload_done
                
                results = st.session_state.dashboard.scan(
                    tracked_tickers=tracked_tickers,
                    progress_callback=show_progress if not skip_preload else None,
                    skip_preload=skip_preload
                )
                
                st.session_state.results = results
                st.session_state.last_scan = scan_start_time
                st.session_state.preload_done = True
                
                progress_placeholder.empty()
                
                if results:
                    logger = DataLogger()
                    logger.save_daily_snapshot(results)
                    
                    added_count = tracker.add_minute_data(results, scan_start_time)
                    
                    st.success(f"✅ {len(results)} stocks tracked!")
                else:
                    st.warning("⚠️ No stocks")
                
                time.sleep(1)
        st.rerun()
    
    st.subheader("📊 TABLE 1: Live Scanner")
    
    if st.session_state.results:
        results = st.session_state.results
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total", len(results))
        
        with col2:
            critical = len([r for r in results if r['Score'] >= 85])
            st.metric("🔥 Critical", critical)
        
        with col3:
            high = len([r for r in results if 60 <= r['Score'] < 85])
            st.metric("⚠️ High", high)
        
        with col4:
            if st.session_state.last_scan:
                _ls = st.session_state.last_scan
                if _ls.tzinfo is None: _ls = PERU_TZ.localize(_ls)
                st.metric("Last Scan", _ls.astimezone(PERU_TZ).strftime("%H:%M:%S"))
        
        display_data = []
        for r in results:
            display_data.append({
                'Ticker': r['Ticker'],
                'Score': f"{r['Score']:.2f}",
                'Price': f"${r['Price']:.2f}",
                'Change': f"{r['Change']:+.1f}%",
                'MxV': f"{r['MxV']:.1f}%",
                'RunUp': f"{r['RunUp']:+.1f}%",
                'REL VOL': f"{r['REL_VOL']:.1f}x",
                'RSI': f"{r['RSI']:.1f}",
                'ATRX': f"{r['ATRX']:.1f}",
                'Gap': f"{r['Gap']:+.1f}%",
                'VWAP': f"{r['VWAP']:+.1f}%",
            })
        
        df = pd.DataFrame(display_data)
        
        def highlight_score(row):
            score = float(row['Score'])
            if score >= 85:
                return ['background-color: #800020; color: white; font-weight: bold'] * len(row)
            elif score >= 60:
                return ['background-color: #cc0000; color: white'] * len(row)
            elif score >= 40:
                return ['background-color: #ff6600; color: white'] * len(row)
            else:
                return ['background-color: #ffcc00; color: black'] * len(row)
        
        styled_df = df.style.apply(highlight_score, axis=1)
        
        table_height = min(600, len(df) * 40 + 50)
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=table_height)
        
    else:
        st.info("👈 Click 'Scan Now' or enable Auto-Scan")
    
    st.markdown("---")
    st.subheader("⏱️ TABLE 2: Timeline Grid")
    
    if is_cloud():
        df_timeline = load_timeline_today_from_sheets()
    else:
        tracker = LiveTracker()
        df_timeline = tracker.get_today_grid()
    
    if df_timeline is None or df_timeline.empty:
        st.info("📊 No timeline data yet")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tracked", len(df_timeline))
        
        with col2:
            st.metric("Time Points", len(df_timeline.columns))
        
        with col3:
            if auto_scan and st.session_state.last_scan:
                _ls2 = st.session_state.last_scan
                if _ls2.tzinfo is None: _ls2 = PERU_TZ.localize(_ls2)
                time_since = (datetime.now(PERU_TZ) - _ls2).total_seconds()
                time_left = max(0, 60 - time_since)
                st.metric("Next", f"{int(time_left)}s")
        
        def color_score(val):
            try:
                score = float(val)
                if score >= 85:
                    return 'background-color: #800020; color: white; font-weight: bold'
                elif score >= 60:
                    return 'background-color: #cc0000; color: white'
                elif score >= 50:
                    return 'background-color: #ff6600; color: white'
                else:
                    return 'background-color: #ffcc00; color: black'
            except:
                return ''
        
        styled_timeline = df_timeline.style.map(color_score).format("{:.2f}")
        
        st.dataframe(styled_timeline, use_container_width=True, height=600)
        
        csv = df_timeline.to_csv()
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"timeline_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
    
    if auto_scan:
        time.sleep(3)
        st.rerun()

def daily_summary_page():
    st.title("📅 DAILY SUMMARY")
    system_health_bar()

    if is_cloud():
        all_df = _cached_daily_snapshots()
        if all_df.empty:
            st.warning("⚠️ No data yet - will be saved at 14:59")
            return
        dates = sorted(all_df["Date"].unique().tolist(), reverse=True)
    else:
        logger = DataLogger()
        dates = logger.get_all_dates()

    if not dates:
        st.warning("⚠️ No data")
        return

    selected_date = st.selectbox("📆 Date", dates, index=0)

    if is_cloud():
        df = all_df[all_df["Date"] == selected_date].drop(columns=["Date"], errors="ignore")
    else:
        df = logger.load_date(selected_date)
    
    if df is None or df.empty:
        st.error("❌ No data")
        return
    
    table_height = min(800, len(df) * 40 + 50)
    
    def highlight_score(row):
        try:
            score = float(row['Score'])
            if score >= 85:
                return ['background-color: #800020; color: white; font-weight: bold'] * len(row)
            elif score >= 60:
                return ['background-color: #cc0000; color: white'] * len(row)
            elif score >= 40:
                return ['background-color: #ff6600; color: white'] * len(row)
            else:
                return ['background-color: #ffcc00; color: black'] * len(row)
        except:
            return [''] * len(row)
    
    METRIC_COLS = ["Ticker", "Score", "MxV", "RunUp", "REL_VOL", "RSI", "ATRX", "Gap", "VWAP"]
    display_cols = [c for c in METRIC_COLS if c in df.columns]
    df = df[display_cols].copy()

    for col in df.columns:
        if col != "Ticker":
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.sort_values("Score", ascending=False, ignore_index=True) if "Score" in df.columns else df

    def fmt(val):
        try:
            v = float(val)
            if abs(v) >= 1000 and v == int(v):
                return f"{int(v):,}"
            return f"{v:.2f}"
        except:
            return val

    numeric_cols = [c for c in df.columns if c != "Ticker" and df[c].dtype in ['float64','float32','int64','int32']]
    styled_df = df.style.apply(highlight_score, axis=1).format(fmt, subset=numeric_cols)
    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=table_height)
    
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download",
        data=csv,
        file_name=f"{selected_date}.csv",
        mime="text/csv"
    )

def timeline_archive_page():
    st.title("📦 Timeline Archive")
    system_health_bar()

    if is_cloud():
        try:
            gc = _get_gc()
            sh = gc.open_by_key(SHEET_ID)
            ws = sh.worksheet("timeline_archive")
            data = ws.get_all_values()
            if len(data) <= 1:
                st.warning("⚠️ No archived timelines yet")
                return
            all_df = pd.DataFrame(data[1:], columns=data[0])
            dates = sorted(all_df["Date"].unique().tolist(), reverse=True)
        except Exception as e:
            st.error(f"Error: {e}")
            return
    else:
        tracker = LiveTracker()
        dates = tracker.get_archive_dates()
    
    if not dates:
        st.warning("⚠️ No archived timelines yet")
        st.info("💡 Timelines are automatically archived at 14:59")
        return
    
    selected_date = st.selectbox("📆 Select Date", dates, index=0)
    
    if is_cloud():
        all_data = ws.get_all_values()
        all_df = pd.DataFrame(all_data[1:], columns=all_data[0])
        day_df = all_df[all_df["Date"] == selected_date].drop(columns=["Date"], errors="ignore")
        day_df["Score"] = pd.to_numeric(day_df.get("Score", 0), errors="coerce")
        if "ScanTime" in day_df.columns:
            df = day_df.pivot_table(index="Ticker", columns="ScanTime", values="Score", aggfunc="last")
            df = df[sorted(df.columns, reverse=True)].round(2)
        else:
            numeric_cols = day_df.select_dtypes(include="number").columns
            df = day_df.set_index("Ticker")[numeric_cols].round(2) if "Ticker" in day_df.columns else day_df.round(2)
    else:
        df = tracker.load_archive(selected_date)
    
    if df is None or df.empty:
        st.error("❌ No data for this date")
        return
    
    st.subheader(f"Timeline Grid - {selected_date}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Stocks Tracked", len(df))
    
    with col2:
        st.metric("Time Points", len(df.columns))
    
    def color_score(val):
        try:
            score = float(val)
            if score >= 85:
                return 'background-color: #800020; color: white; font-weight: bold'
            elif score >= 60:
                return 'background-color: #cc0000; color: white'
            elif score >= 50:
                return 'background-color: #ff6600; color: white'
            else:
                return 'background-color: #ffcc00; color: black'
        except:
            return ''
    
    styled_df = df.style.map(color_score).format("{:.2f}")
    
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    csv = df.to_csv()
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"timeline_{selected_date}.csv",
        mime="text/csv"
    )

@st.cache_data(ttl=3600)
def _fetch_live_prices(tickers: tuple) -> dict:
    """Batch-fetch latest prices from yfinance. Cached 1 hour. Accepts tuple for hashability."""
    tickers = list(tickers)
    if not tickers:
        return {}
    try:
        data = yf.download(tickers, period="1d", progress=False, auto_adjust=True)["Close"]
        if len(tickers) == 1:
            prices = data.dropna()
            return {tickers[0]: round(float(prices.iloc[-1]), 2)} if not prices.empty else {}
        return {
            t: round(float(data[t].dropna().iloc[-1]), 2)
            for t in tickers
            if t in data.columns and not data[t].dropna().empty
        }
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def _fetch_high_low_since(ticker_dates: tuple) -> dict:
    """
    Fetch High and Low for each ticker starting from D1 (next trading day after scan_date).
    ticker_dates: tuple of (ticker, scan_date_str) pairs
    Returns: {ticker_scandate: {"high": x, "low": y}}
    """
    if not ticker_dates:
        return {}

    from collections import defaultdict
    from datetime import datetime, timedelta

    def next_trading_day(date_str):
        """Returns the next weekday after scan_date (= D1 start)"""
        d = datetime.strptime(date_str, "%Y-%m-%d")
        d += timedelta(days=1)
        while d.weekday() >= 5:   # skip Sat/Sun
            d += timedelta(days=1)
        return d.strftime("%Y-%m-%d")

    # Group tickers by their D1 start date
    d1_to_tickers = defaultdict(list)
    scan_to_d1    = {}
    for ticker, scan_date in ticker_dates:
        d1 = next_trading_day(scan_date)
        d1_to_tickers[d1].append((ticker, scan_date))
        scan_to_d1[scan_date] = d1

    result = {}
    for d1_date, ticker_scan_pairs in d1_to_tickers.items():
        try:
            all_tickers = list({t for t, _ in ticker_scan_pairs})
            data = yf.download(all_tickers, start=d1_date, progress=False, auto_adjust=True)
            if data.empty:
                continue
            highs = data["High"] if "High" in data else None
            lows  = data["Low"]  if "Low"  in data else None
            if highs is None or lows is None:
                continue
            for ticker, scan_date in ticker_scan_pairs:
                key = f"{ticker}_{scan_date}"
                try:
                    if len(all_tickers) == 1:
                        h = round(float(highs.dropna().max()), 2)
                        l = round(float(lows.dropna().min()),  2)
                    else:
                        h = round(float(highs[ticker].dropna().max()), 2)
                        l = round(float(lows[ticker].dropna().min()),  2)
                    result[key] = {"high": h, "low": l}
                except Exception:
                    continue
        except Exception:
            continue
    return result


def _simulate_short_trades(pa_df: pd.DataFrame):
    """
    Simulate $1000 short trades for every row in post_analysis.
    Returns (table_a, table_b):
      table_a — entry at ScanPrice (EOD scan day)
      table_b — entry at D1_Open  (next day open)
    """
    POSITION = 1000.0
    TP_PCT   = 0.10   # 10% take-profit (short: price drops)
    SL_PCT   = 0.07   # 7%  stop-loss   (short: price rises)
    TP15_PCT = 0.15   # 15% stretch target — mark only

    # ── טעון portfolio_live (RunningHigh/RunningLow מה-scanner) ─────────────
    pl_df = _cached_portfolio_live()

    # Pre-fetch live prices רק למניות שאין להן נתון ב-portfolio_live
    pending_tickers = list({
        str(row.get("Ticker", ""))
        for _, row in pa_df.iterrows()
        if pd.isna(pd.to_numeric(row.get("D1_High"), errors="coerce"))
    })
    live_prices = _fetch_live_prices(tuple(sorted(set(pending_tickers))))

    rows_a, rows_b = [], []

    for _, row in pa_df.iterrows():
        ticker     = str(row.get("Ticker", ""))
        scan_date  = str(row.get("ScanDate", ""))
        score      = pd.to_numeric(row.get("Score"),     errors="coerce")
        scan_price = pd.to_numeric(row.get("ScanPrice"), errors="coerce")
        d1_open    = pd.to_numeric(row.get("D1_Open"),   errors="coerce")

        for entry_label, entry_price in [("A", scan_price), ("B", d1_open)]:
            # Current price = most recent Di_Close available, fallback to ScanPrice
            current_price = None
            for day in range(5, 0, -1):
                c = pd.to_numeric(row.get(f"D{day}_Close"), errors="coerce")
                if not pd.isna(c):
                    current_price = round(float(c), 2)
                    break
            if current_price is None and not pd.isna(scan_price) and scan_price > 0:
                current_price = round(float(scan_price), 2)

            if pd.isna(entry_price) or entry_price <= 0:
                # If scan_price exists, treat as Pending (D1 not yet available)
                if not pd.isna(scan_price) and scan_price > 0:
                    live_price = live_prices.get(ticker)
                    proxy_shares = int(max(1, math.ceil(POSITION / scan_price)))
                    proxy_investment = round(proxy_shares * scan_price, 2)
                    proxy_current = live_price if live_price is not None else current_price
                    proxy_pnl = round(proxy_shares * (scan_price - live_price), 2) if live_price else None
                    # RunningHigh/Low מה-portfolio_live
                    rh_disp, rl_disp = None, None
                    if not pl_df.empty:
                        pl_m = (pl_df["Ticker"] == ticker) & (pl_df["ScanDate"] == scan_date)
                        if pl_m.any():
                            rh = pl_df[pl_m].iloc[0].get("RunningHigh")
                            rl = pl_df[pl_m].iloc[0].get("RunningLow")
                            if pd.notna(rh): rh_disp = round(float(rh), 2)
                            if pd.notna(rl): rl_disp = round(float(rl), 2)
                    rec = {
                        "Ticker": ticker, "ScanDate": scan_date,
                        "Score": None if pd.isna(score) else round(float(score), 2),
                        "EntryPrice": None, "CurrentPrice": proxy_current,
                        "Shares": proxy_shares, "Investment": f"${proxy_investment:.2f}",
                        "TP10_Price": None, "SL_Price": None,
                        "MaxHigh": rh_disp, "MinLow": rl_disp,
                        "Status": "Pending ⏳", "Exit_Day": "—", "PnL_$": proxy_pnl, "TP15_reached": "—",
                    }
                else:
                    rec = {
                        "Ticker": ticker, "ScanDate": scan_date,
                        "Score": None if pd.isna(score) else round(float(score), 2),
                        "EntryPrice": None, "Shares": None, "Investment": None,
                        "TP10_Price": None, "SL_Price": None, "CurrentPrice": current_price,
                        "Status": "No Data", "Exit_Day": "—", "PnL_$": None, "TP15_reached": "—",
                    }
            else:
                shares     = int(max(1, math.ceil(POSITION / entry_price)))  # always >= $1000
                investment = round(shares * entry_price, 2)
                tp10_price = round(entry_price * (1 - TP_PCT),  4)
                sl_price   = round(entry_price * (1 + SL_PCT),  4)
                tp15_price = round(entry_price * (1 - TP15_PCT), 4)

                status   = "Open ⏳"
                exit_day = None
                pnl      = None
                tp15_hit = False
                has_data = False

                for day in range(1, 6):
                    high = pd.to_numeric(row.get(f"D{day}_High"), errors="coerce")
                    low  = pd.to_numeric(row.get(f"D{day}_Low"),  errors="coerce")
                    if pd.isna(high) or pd.isna(low):
                        break
                    has_data = True

                    if low <= tp15_price:
                        tp15_hit = True

                    sl_hit = high >= sl_price
                    tp_hit = low  <= tp10_price

                    if sl_hit and tp_hit:
                        status, exit_day, pnl = "SL ❌", day, round(-investment * SL_PCT, 2)
                        break
                    elif sl_hit:
                        status, exit_day, pnl = "SL ❌", day, round(-investment * SL_PCT, 2)
                        break
                    elif tp_hit:
                        status, exit_day, pnl = "TP10 ✅", day, round(investment * TP_PCT, 2)
                        break

                if status == "Open ⏳":
                    if not has_data:
                        # ── קרא מ-portfolio_live (נתון מהscanner כל דקה) ──────
                        pl_key  = None
                        pl_row  = None
                        if not pl_df.empty:
                            pl_mask = (pl_df["Ticker"] == ticker) & (pl_df["ScanDate"] == scan_date)
                            if pl_mask.any():
                                pl_row = pl_df[pl_mask].iloc[0]

                        if pl_row is not None:
                            running_high  = pl_row.get("RunningHigh")
                            running_low   = pl_row.get("RunningLow")
                            pl_status     = str(pl_row.get("Status", ""))
                            pl_current    = pl_row.get("CurrentPrice")
                            if pd.notna(pl_current):
                                current_price = round(float(pl_current), 2)

                            # חשב ימי מסחר
                            try:
                                scan_dt      = datetime.strptime(scan_date, "%Y-%m-%d")
                                today_dt     = datetime.now().replace(tzinfo=None)
                                trading_days = 0
                                d = scan_dt
                                while d < today_dt:
                                    d += timedelta(days=1)
                                    if d.weekday() < 5:
                                        trading_days += 1
                                trading_days = max(trading_days, 1)
                            except:
                                trading_days = 1

                            if "SL" in pl_status:
                                status   = "SL ❌"
                                exit_day = trading_days
                                pnl      = round(-investment * SL_PCT, 2)
                            elif "TP10" in pl_status:
                                status   = "TP10 ✅"
                                exit_day = trading_days
                                pnl      = round(investment * TP_PCT, 2)
                            else:
                                status = "Pending ⏳"
                                if current_price is not None:
                                    pnl = round(shares * (entry_price - current_price), 2)
                        else:
                            # אין נתון ב-portfolio_live עדיין — fallback למחיר חי
                            live_price = live_prices.get(ticker)
                            if live_price is not None:
                                current_price = live_price
                            status = "Pending ⏳"
                            if current_price is not None:
                                pnl = round(shares * (entry_price - current_price), 2)
                    elif current_price is not None:
                        pnl = round(shares * (entry_price - current_price), 2)

                # ── MaxHigh / MinLow לתצוגה ──────────────────────────────────
                # קודם מנסה מנתוני D1-D5 שיש בשורה
                running_high_disp = None
                running_low_disp  = None
                highs, lows = [], []
                for d in range(1, 6):
                    h = pd.to_numeric(row.get(f"D{d}_High"), errors="coerce")
                    l = pd.to_numeric(row.get(f"D{d}_Low"),  errors="coerce")
                    if pd.notna(h): highs.append(float(h))
                    if pd.notna(l): lows.append(float(l))
                if highs: running_high_disp = round(max(highs), 2)
                if lows:  running_low_disp  = round(min(lows),  2)
                # fallback: portfolio_live (למניות Pending)
                if running_high_disp is None and not pl_df.empty:
                    pl_mask2 = (pl_df["Ticker"] == ticker) & (pl_df["ScanDate"] == scan_date)
                    if pl_mask2.any():
                        rh = pl_df[pl_mask2].iloc[0].get("RunningHigh")
                        rl = pl_df[pl_mask2].iloc[0].get("RunningLow")
                        if pd.notna(rh): running_high_disp = round(float(rh), 2)
                        if pd.notna(rl): running_low_disp  = round(float(rl), 2)

                rec = {
                    "Ticker":       ticker,
                    "ScanDate":     scan_date,
                    "Score":        None if pd.isna(score) else round(float(score), 2),
                    "EntryPrice":   round(entry_price, 2),
                    "CurrentPrice": current_price,
                    "Shares":       shares,
                    "Investment":   f"${investment:.2f}",
                    "TP10_Price":   tp10_price,
                    "SL_Price":     sl_price,
                    "MaxHigh":      running_high_disp,
                    "MinLow":       running_low_disp,
                    "Status":       status,
                    "Exit_Day":     f"D{exit_day}" if isinstance(exit_day, int) else (exit_day if exit_day else ("—" if status == "Pending ⏳" else "D5+")),
                    "PnL_$":        pnl,
                    "TP15_reached": "✅" if tp15_hit else "—",
                }

            (rows_a if entry_label == "A" else rows_b).append(rec)

    return pd.DataFrame(rows_a), pd.DataFrame(rows_b)


def _render_short_table(df: pd.DataFrame, download_key: str):
    """Render a styled short-trade simulation table with summary metrics at top."""
    if df.empty:
        st.info("No data")
        return

    # ── Summary ───────────────────────────────────────────────────────────────
    closed    = df[df["Status"].isin(["TP10 ✅", "SL ❌"])]
    alive     = df[df["Status"].isin(["Pending ⏳", "Open ⏳"])]
    total     = len(closed)
    wins      = int((closed["Status"] == "TP10 ✅").sum())
    losses    = int((closed["Status"] == "SL ❌").sum())
    alive_cnt = len(alive)
    total_pnl = pd.to_numeric(closed["PnL_$"], errors="coerce").sum()
    win_rate  = wins / total * 100 if total > 0 else 0.0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Closed trades",  total)
    c2.metric("✅ Wins (TP10)", wins)
    c3.metric("❌ Losses (SL)", losses)
    c4.metric("🟡 Alive",       alive_cnt)
    c5.metric("Win rate",       f"{win_rate:.1f}%")
    c6.metric("Total PnL",      f"${total_pnl:+.2f}")

    # ── Row color coding ─────────────────────────────────────────────────────
    def row_style(row):
        s = str(row.get("Status", ""))
        if "TP10" in s:
            return ["background-color: #1a4d2e; color: #90EE90"] * len(row)   # 🟢 ירוק — רווח
        elif "SL" in s:
            return ["background-color: #4d1a1a; color: #FFB6C1"] * len(row)   # 🔴 אדום — הפסד
        elif "Pending" in s or "Open" in s:
            return ["background-color: #4d3800; color: #FFD700"] * len(row)   # 🟡 צהוב — חיה, ממתינה
        return ["color: #888888"] * len(row)                                   # אפור — אין נתונים

    # ── Format display columns ───────────────────────────────────────────────
    display = df.copy()
    for col in ["Score", "EntryPrice", "TP10_Price", "SL_Price", "MaxHigh", "MinLow", "CurrentPrice"]:
        if col in display.columns:
            display[col] = display[col].apply(
                lambda v: f"{float(v):.2f}" if pd.notna(v) else "—"
            )
    if "Shares" in display.columns:
        display["Shares"] = display["Shares"].apply(
            lambda v: str(int(v)) if pd.notna(v) and v != "" else "—"
        )
    if "PnL_$" in display.columns:
        display["PnL_$"] = display["PnL_$"].apply(
            lambda v: f"${float(v):+.2f}" if pd.notna(v) else "—"
        )

    st.dataframe(
        display.style.apply(row_style, axis=1),
        use_container_width=True, hide_index=True,
        height=min(15 * 35 + 40, max(len(display) * 35 + 40, 500)),
    )

    st.download_button(
        label="📥 Download CSV",
        data=df.to_csv(index=False),
        file_name=f"short_sim_{download_key}_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
        key=f"dl_{download_key}",
    )


def portfolio_tracker_page():
    # ── כותרת ────────────────────────────────────────────────────────────────
    t1, t2 = st.columns([6, 1])
    with t1:
        st.title("💼 SHORT TRADE SIMULATOR")
    with t2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", help="מחיר חי מתעדכן כל שעה — לחץ לרענון מיידי"):
            st.cache_data.clear()
            st.rerun()

    # ── caption + health bar בשורה אחת ──────────────────────────────────────
    last_scan, last_collector = _fetch_health_data()
    today     = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
    yesterday = (datetime.now(PERU_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")

    scan_icon = "✅" if last_scan and last_scan[:10] == today else ("⚠️" if last_scan and last_scan[:10] == yesterday else "🔴")
    coll_icon = "✅" if last_collector and (datetime.now(PERU_TZ).replace(tzinfo=None) - datetime.strptime(last_collector, "%Y-%m-%d")).days <= 2 else "🔴"

    st.markdown(
        f"$1,000 short · TP 10% · SL 7% &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"{scan_icon} Last scan: **{last_scan or '—'}** &nbsp;|&nbsp; "
        f"{coll_icon} Last collector: **{last_collector or '—'}**"
    )
    st.markdown("<hr style='margin:4px 0 8px 0; border-color:#333'>", unsafe_allow_html=True)

    with st.spinner("Loading post-analysis data..."):
        pa = _cached_post_analysis()

    if pa.empty:
        st.info("📭 No post-analysis data yet.")
        return

    # ── ללא פילטרים — ברירות מחדל קבועות ───────────────────────────────────
    all_dates  = sorted(pa["ScanDate"].dropna().unique().tolist(), reverse=True)
    sel_dates  = all_dates
    sel_status = ["TP10 ✅", "SL ❌", "Open ⏳", "Pending ⏳"]
    min_score  = 60

    # Filter source data
    pa_filtered = pa.copy()
    score_col = pd.to_numeric(pa_filtered["Score"], errors="coerce")
    pa_filtered = pa_filtered[score_col >= min_score]

    if pa_filtered.empty:
        st.warning("No rows match the current filters.")
        return

    with st.spinner("Running simulation..."):
        table_a, table_b = _simulate_short_trades(pa_filtered)

    # Apply status filter
    table_a = table_a[table_a["Status"].isin(sel_status)]
    table_b = table_b[table_b["Status"].isin(sel_status)]

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_a, tab_b = st.tabs([
        "📌 Table A — Entry at ScanPrice (EOD)",
        "📌 Table B — Entry at D1_Open (next day)",
    ])

    with tab_a:
        _render_short_table(table_a, "table_a")

    with tab_b:
        _render_short_table(table_b, "table_b")


def post_analysis_page():
    st.title("🔬 Post Analysis")
    st.caption("מניות עם Score 60+ — מה קרה ב-5 ימים אחרי הסריקה")
    system_health_bar()

    with st.spinner("טוען נתונים..."):
        df = _cached_post_analysis()

    if not df.empty and "Ticker" in df.columns:
        import yfinance as yf
        tickers = df["Ticker"].unique().tolist()
        try:
            prices = yf.download(tickers, period="1d", progress=False, auto_adjust=True)["Close"]
            if len(tickers) == 1:
                current_price = {tickers[0]: round(float(prices.iloc[-1]), 2)}
            else:
                current_price = {t: round(float(prices[t].iloc[-1]), 2) for t in tickers if t in prices.columns}
            df["CurrentPrice"] = df["Ticker"].map(current_price)
            df["EntryChange%"] = ((df["CurrentPrice"] - df["ScanPrice"]) / df["ScanPrice"] * 100).round(2)
        except:
            df["CurrentPrice"] = None
            df["EntryChange%"] = None

    if df.empty:
        st.info("📭 אין נתונים עדיין — הקולקטור יתחיל לאסוף לאחר 5 ימי מסחר מהסריקה הראשונה")
        return

    complete_df = df[df["MaxDrop%"].notna() & (df["MaxDrop%"] != 0)] if "MaxDrop%" in df.columns else df
    total = len(complete_df)
    tp10  = int(complete_df["TP10_Hit"].sum()) if "TP10_Hit" in complete_df.columns else 0
    tp15  = int(complete_df["TP15_Hit"].sum()) if "TP15_Hit" in complete_df.columns else 0
    tp20  = int(complete_df["TP20_Hit"].sum()) if "TP20_Hit" in complete_df.columns else 0
    avg_drop = complete_df["MaxDrop%"].mean() if "MaxDrop%" in complete_df.columns else 0

    winners = complete_df[complete_df["TP10_Hit"] == 1] if "TP10_Hit" in complete_df.columns else pd.DataFrame()
    losers  = complete_df[complete_df["TP10_Hit"] == 0] if "TP10_Hit" in complete_df.columns else pd.DataFrame()
    avg_win  = winners["MaxDrop%"].mean() if not winners.empty else 0
    avg_loss = losers["MaxDrop%"].mean() if not losers.empty else 0
    expected_value = (tp10/total * abs(avg_win) - (1 - tp10/total) * abs(avg_loss)) if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("סה״כ מניות", total)
    c2.metric("TP 10% Hit", f"{tp10}/{total}", f"{tp10/total*100:.0f}%" if total else "")
    c3.metric("TP 15% Hit", f"{tp15}/{total}", f"{tp15/total*100:.0f}%" if total else "")
    c4.metric("TP 20% Hit", f"{tp20}/{total}", f"{tp20/total*100:.0f}%" if total else "")
    c5.metric("Avg Max Drop", f"{avg_drop:.1f}%")

    st.divider()
    st.subheader("📊 ניתוח רווח/הפסד")
    w1, w2, w3, w4 = st.columns(4)
    w1.metric("✅ מנצחות", f"{len(winners)}", f"הגיעו ל-10%+")
    w2.metric("📈 רווח ממוצע", f"{abs(avg_win):.1f}%", "על המנצחות")
    w3.metric("❌ מפסידות", f"{len(losers)}", f"לא הגיעו ל-10%")
    w4.metric("📉 הפסד ממוצע", f"{abs(avg_loss):.1f}%", "על המפסידות")

    st.info(f"💡 Expected Value: על כל עסקה אתה מצפה לרוויח **{expected_value:.1f}%** בממוצע — ({tp10/total*100:.0f}% × {abs(avg_win):.1f}% רווח) פחות ({(1-tp10/total)*100:.0f}% × {abs(avg_loss):.1f}% הפסד)" if total else "")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        score_filter = st.slider("Score מינימום", 60, 100, 60)
    with col2:
        show_only_hits = st.checkbox("הצג רק מניות שהגיעו ל-TP 10%")

    filtered = df[df["Score"] >= score_filter].copy()
    if show_only_hits and "TP10_Hit" in filtered.columns:
        filtered = filtered[filtered["TP10_Hit"] == 1]

    st.subheader(f"📋 תוצאות ({len(filtered)} מניות)")

    display_cols = ["Ticker", "ScanDate", "Score", "ScanChange%", "ScanPrice",
                    "IntraHigh", "IntraLow", "DayRunUp%", "PeakScoreTime", "PeakScorePrice",
                    "CurrentPrice", "EntryChange%", "MaxDrop%", "BestDay", "TP10_Hit", "TP15_Hit", "TP20_Hit"]
    display_cols = [c for c in display_cols if c in filtered.columns]

    def color_tp(val):
        if val == 1:
            return "background-color: #1a4a1a; color: #00ff88"
        elif val == 0:
            return "background-color: #4a1a1a; color: #ff4444"
        return ""

    def color_drop(val):
        try:
            v = float(val)
            if v <= -15: return "color: #e74c3c; font-weight: bold"
            if v <= -10: return "color: #c0392b"
            if v <= -5:  return "color: #e67e22"
            return "color: #f1c40f"
        except:
            return ""

    def color_change(val):
        try:
            v = float(val)
            if v > 0:  return "color: #2ecc71"
            if v < 0:  return "color: #e74c3c"
            return ""
        except:
            return ""

    for col in filtered[display_cols].select_dtypes(include="number").columns:
        filtered[col] = filtered[col].round(2)
    styled = filtered[display_cols].style
    for col in ["TP10_Hit", "TP15_Hit", "TP20_Hit"]:
        if col in display_cols:
            styled = styled.map(color_tp, subset=[col])
    if "MaxDrop%" in display_cols:
        styled = styled.map(color_drop, subset=["MaxDrop%"])
    if "ScanChange%" in display_cols:
        styled = styled.map(color_change, subset=["ScanChange%"])
    if "EntryChange%" in display_cols:
        styled = styled.map(color_change, subset=["EntryChange%"])
    format_dict = {}
    for col in filtered[display_cols].select_dtypes(include="number").columns:
        if col in ["TP10_Hit", "TP15_Hit", "TP20_Hit", "BestDay"]:
            continue
        elif "%" in col:
            format_dict[col] = "{:.2f}%"
        else:
            format_dict[col] = "{:.2f}"
    styled = styled.format(format_dict)
    st.dataframe(styled, use_container_width=True, height=500, hide_index=True)

    st.divider()

    if "BestDay" in df.columns and not df["BestDay"].dropna().empty:
        st.subheader("📅 באיזה יום הגיע ה-Low הכי נמוך?")
        best_day_counts = df["BestDay"].value_counts().sort_index()
        best_day_df = pd.DataFrame({
            "יום": [f"D+{int(d)}" for d in best_day_counts.index],
            "מניות": best_day_counts.values
        })
        st.bar_chart(best_day_df.set_index("יום"))

    st.divider()

    # ── Dynamic Score ──────────────────────────────────────────────────────
    st.subheader("⚡ ציון דינמי — מבוסס נתונים אמיתיים")
    st.caption("ציון חדש המבוסס רק על MxV ו-ATRX — שני המדדים שהוכחו כמנבאים ירידה. השווה אותו לציון המקורי.")

    if "MxV" in df.columns and "ATRX" in df.columns:
        df_dyn = df.copy()
        mxv_min, mxv_max = -5000, 0
        df_dyn["MxV"] = pd.to_numeric(df_dyn["MxV"], errors="coerce").fillna(0)
        df_dyn["ATRX"] = pd.to_numeric(df_dyn["ATRX"], errors="coerce").fillna(0)
        df_dyn["MxV_norm"] = ((df_dyn["MxV"].clip(mxv_min, mxv_max) - mxv_max) / (mxv_min - mxv_max) * 100).clip(0, 100)
        atrx_min, atrx_max = 0, 50
        df_dyn["ATRX_norm"] = ((df_dyn["ATRX"].clip(atrx_min, atrx_max) - atrx_min) / (atrx_max - atrx_min) * 100).clip(0, 100)
        df_dyn["DynamicScore"] = (df_dyn["MxV_norm"] * 0.6 + df_dyn["ATRX_norm"] * 0.4).round(2)

        dyn_display = df_dyn[["Ticker","ScanDate","Score","DynamicScore","MxV","ATRX","TP10_Hit","MaxDrop%"]].copy()
        dyn_display["הפרש"] = (dyn_display["DynamicScore"] - dyn_display["Score"]).round(2)

        def color_diff(val):
            try:
                v = float(val)
                if v < -10: return "color: #e74c3c"
                if v > 10:  return "color: #2ecc71"
                return "color: #f1c40f"
            except:
                return ""

        for col in dyn_display.select_dtypes(include="number").columns:
            dyn_display[col] = dyn_display[col].round(2)
        format_dyn = {col: "{:.2f}" for col in dyn_display.select_dtypes(include="number").columns}
        styled_dyn = dyn_display.style.map(color_diff, subset=["הפרש"]).format(format_dyn)
        st.dataframe(styled_dyn, use_container_width=True, hide_index=True)
        st.caption("הפרש אדום = הציון המקורי גבוה מהדינמי (אולי מוערך יתר על המידה). ירוק = הציון הדינמי גבוה יותר.")
    else:
        st.info("אין מספיק נתונים לציון דינמי")

    st.divider()

    # ── Score Tier Analysis ─────────────────────────────────────────────────
    st.subheader("🎯 ניתוח לפי רמת ציון")
    st.caption("האם ציון גבוה יותר = שיעור הצלחה גבוה יותר? כל שורה מראה קבוצת מניות לפי טווח ציון.")
    tiers = [(60,70,"60-70"), (70,80,"70-80"), (80,90,"80-90"), (90,101,"90+")]
    tier_rows = []
    for low, high, label in tiers:
        t = df[(df["Score"] >= low) & (df["Score"] < high)]
        if len(t) == 0:
            continue
        tp10_t = int(t["TP10_Hit"].sum()) if "TP10_Hit" in t.columns else 0
        tp15_t = int(t["TP15_Hit"].sum()) if "TP15_Hit" in t.columns else 0
        avg_drop_t = t["MaxDrop%"].mean() if "MaxDrop%" in t.columns else 0
        tier_rows.append({
            "טווח ציון": label,
            "מניות": len(t),
            "הגיע ל-10%": f"{tp10_t}/{len(t)} ({tp10_t/len(t)*100:.0f}%)",
            "הגיע ל-15%": f"{tp15_t}/{len(t)} ({tp15_t/len(t)*100:.0f}%)",
            "ירידה ממוצעת": f"{avg_drop_t:.2f}%"
        })
    if tier_rows:
        st.dataframe(pd.DataFrame(tier_rows), use_container_width=True, hide_index=True)

    st.divider()

    # ── Metric Correlation ──────────────────────────────────────────────────
    st.subheader("📐 אילו מדדים מנבאים ירידה גדולה יותר?")
    st.caption("קורלציה חיובית = ככל שהמדד גבוה יותר, הירידה קטנה יותר. קורלציה שלילית = ככל שהמדד גבוה יותר, הירידה גדולה יותר.")
    metric_cols = ["Score", "ScanChange%", "MxV", "ATRX", "RSI", "RunUp", "REL_VOL", "Float%", "Gap"]
    available_metrics = [c for c in metric_cols if c in df.columns]
    if available_metrics and "MaxDrop%" in df.columns:
        corr_data = []
        for col in available_metrics:
            try:
                corr = df[col].corr(df["MaxDrop%"])
                corr_data.append({"מדד": col, "קורלציה עם הירידה": round(corr, 3)})
            except:
                pass
        if corr_data:
            corr_df = pd.DataFrame(corr_data).sort_values("קורלציה עם הירידה")
            st.dataframe(corr_df, use_container_width=True, hide_index=True)
            st.caption("ערך שלילי = המדד מנבא ירידה. ערך חיובי = המדד לא מנבא ירידה.")

    st.divider()

    # ── Catalyst ────────────────────────────────────────────────────────────
    st.subheader("🔍 ניתוח חדשות")
    st.caption("סיווג אוטומטי של סוג האירוע שגרם לעלייה — מתעדכן אוטומטית בכל יום.")

    cat_col_map = {
        "cat_merger_acquisition":     "מיזוג",
        "cat_fda_approval":           "FDA",
        "cat_clinical_trial":         "מחקר קליני",
        "cat_marketing_announcement": "הודעה שיווקית",
        "cat_earnings_report":        "דוח רווחים",
        "cat_regulatory_compliance":  "ציות רגולטורי",
        "cat_lawsuit":                "תביעה",
        "cat_share_dilution":         "דילול",
        "cat_reverse_split":          "ספליט הפוך",
        "cat_no_clear_reason":        "Pump"
    }

    available_cat_cols = [c for c in cat_col_map.keys() if c in df.columns]

    if available_cat_cols:
        cat_display = df[["Ticker","ScanDate"] + available_cat_cols].copy()
        cat_display = cat_display.rename(columns=cat_col_map)
        label_cols = [cat_col_map[c] for c in available_cat_cols]
        for col in label_cols:
            cat_display[col] = cat_display[col].apply(
                lambda x: "✅" if str(x) in ["1","1.0","True","true"] else ""
            )
        def color_check(val):
            if val == "✅": return "color: #2ecc71; font-weight: bold"
            return ""
        styled_cat = cat_display.style.map(color_check, subset=label_cols)
        st.dataframe(styled_cat, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("⏳ נתוני catalyst יופיעו כאן לאחר הריצה הראשונה של הקולקטור")

    st.divider()
    csv = filtered.to_csv(index=False)
    st.download_button("⬇️ הורד CSV", csv, "post_analysis.csv", "text/csv")

    # ═══════════════════════════════════════════════════════════════════════
    # EXPORT SECTION
    # ═══════════════════════════════════════════════════════════════════════
    st.divider()
    st.subheader("📦 הורד את כל הנתונים")

    exp_col1, exp_col2 = st.columns(2)

    # ── Export 1: Full Excel ────────────────────────────────────────────────
    with exp_col1:
        st.markdown("#### 📊 Export מלא")
        st.caption("כל הטאבים — Timeline Archive כגריד דקות. לשמירה ולארכיון.")

        if st.button("📊 הכן קובץ Excel מלא"):
            with st.spinner("טוען נתונים מכל הטאבים..."):
                try:
                    import io
                    from gsheets_sync import _get_client, SPREADSHEET_ID

                    gc = _get_client()
                    sh = gc.open_by_key(SPREADSHEET_ID)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:

                        # Regular tabs
                        regular_tabs = {
                            "Post Analysis":  "post_analysis",
                            "Daily Snapshots": "daily_snapshots",
                            "Portfolio":       "portfolio",
                        }
                        for sheet_name, tab_name in regular_tabs.items():
                            try:
                                ws = sh.worksheet(tab_name)
                                data = ws.get_all_values()
                                tab_df = pd.DataFrame(data[1:], columns=data[0])
                                tab_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            except Exception as e:
                                st.warning(f"⚠️ {tab_name}: {e}")

                        # Timeline Archive — one pivot sheet per date
                        try:
                            ws_arch = sh.worksheet("timeline_archive")
                            arch_data = ws_arch.get_all_values()
                            arch_df = pd.DataFrame(arch_data[1:], columns=arch_data[0])
                            arch_df["Score"] = pd.to_numeric(arch_df["Score"], errors="coerce")
                            arch_dates = sorted(arch_df["Date"].unique().tolist(), reverse=True)

                            for date_val in arch_dates:
                                day_df = arch_df[arch_df["Date"] == date_val]
                                pivot = day_df.pivot_table(
                                    index="Ticker", columns="ScanTime", values="Score", aggfunc="last"
                                )
                                pivot = pivot[sorted(pivot.columns, reverse=True)].round(2)
                                pivot.reset_index(inplace=True)
                                sheet_label = f"Archive {date_val}"[:31]
                                pivot.to_excel(writer, sheet_name=sheet_label, index=False)
                        except Exception as e:
                            st.warning(f"⚠️ timeline_archive: {e}")

                    output.seek(0)
                    filename = f"RidingHigh_Full_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    st.download_button(
                        "⬇️ הורד Excel מלא",
                        output,
                        filename,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("✅ הקובץ מוכן!")
                except Exception as e:
                    st.error(f"שגיאה: {e}")

    # ── Export 2: Analysis Export (lightweight) ─────────────────────────────
    with exp_col2:
        st.markdown("#### 🔬 Export לניתוח AI")
        st.caption("קובץ קל — Post Analysis + סיכום Timeline לכל מניה. מתאים להעלאה לצ'אט לניתוח.")

        if st.button("🔬 הכן קובץ ניתוח"):
            with st.spinner("בונה קובץ ניתוח..."):
                try:
                    import io
                    from gsheets_sync import _get_client, SPREADSHEET_ID

                    gc = _get_client()
                    sh = gc.open_by_key(SPREADSHEET_ID)

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:

                        # Tab 1: Post Analysis (full)
                        try:
                            ws_pa = sh.worksheet("post_analysis")
                            pa_data = ws_pa.get_all_values()
                            pa_df = pd.DataFrame(pa_data[1:], columns=pa_data[0])
                            pa_df.to_excel(writer, sheet_name="Post Analysis", index=False)
                        except Exception as e:
                            st.warning(f"⚠️ post_analysis: {e}")

                        # Tab 2: Timeline Summary (computed from archive)
                        try:
                            ws_arch = sh.worksheet("timeline_archive")
                            arch_data = ws_arch.get_all_values()
                            arch_df = pd.DataFrame(arch_data[1:], columns=arch_data[0])

                            if not arch_df.empty and "ScanTime" in arch_df.columns:
                                summary_df = _build_timeline_summary(arch_df)
                                summary_df.to_excel(writer, sheet_name="Timeline Summary", index=False)
                            else:
                                st.warning("⚠️ Timeline archive ריק או חסר עמודת ScanTime")
                        except Exception as e:
                            st.warning(f"⚠️ timeline summary: {e}")

                        # Tab 3: Daily Snapshots (last 10 days only to keep light)
                        try:
                            ws_snap = sh.worksheet("daily_snapshots")
                            snap_data = ws_snap.get_all_values()
                            snap_df = pd.DataFrame(snap_data[1:], columns=snap_data[0])
                            if "Date" in snap_df.columns:
                                last_10_dates = sorted(snap_df["Date"].unique().tolist(), reverse=True)[:10]
                                snap_df = snap_df[snap_df["Date"].isin(last_10_dates)]
                            snap_df.to_excel(writer, sheet_name="Daily Snapshots (10d)", index=False)
                        except Exception as e:
                            st.warning(f"⚠️ daily_snapshots: {e}")

                    output.seek(0)
                    filename = f"RidingHigh_Analysis_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    st.download_button(
                        "⬇️ הורד קובץ ניתוח",
                        output,
                        filename,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("✅ הקובץ מוכן! העלה אותו לצ'אט עם Claude לניתוח מעמיק 🤖")
                except Exception as e:
                    st.error(f"שגיאה: {e}")


def _fetch_health_data():
    """Return last scan timestamp and last collector date using cached loaders."""
    last_scan = None
    last_collector = None
    try:
        df_tl = _cached_timeline_live()
        if not df_tl.empty and "Date" in df_tl.columns and "ScanTime" in df_tl.columns:
            df_tl = df_tl.copy()
            df_tl["_dt"] = df_tl["Date"] + " " + df_tl["ScanTime"]
            last_scan = df_tl["_dt"].max()
    except Exception:
        pass
    try:
        df_pa = _cached_post_analysis()
        if not df_pa.empty and "ScanDate" in df_pa.columns:
            last_collector = df_pa["ScanDate"].max()
    except Exception:
        pass
    return last_scan, last_collector


def system_health_bar():
    try:
        today     = datetime.now(PERU_TZ).strftime("%Y-%m-%d")
        yesterday = (datetime.now(PERU_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")

        last_scan, last_collector = _fetch_health_data()

        parts = []

        # ── Last scan status ────────────────────────────────────────────────
        if last_scan:
            scan_date = last_scan[:10]
            if scan_date == today:
                scan_icon = "✅"
            elif scan_date == yesterday:
                scan_icon = "⚠️"
            else:
                scan_icon = "🔴"
            parts.append(f"{scan_icon} Last scan: **{last_scan}**")
        else:
            parts.append("🔴 Last scan: **unknown**")

        # ── Last collector status ────────────────────────────────────────────
        if last_collector:
            collector_dt = datetime.strptime(last_collector, "%Y-%m-%d")
            days_old = (datetime.now(PERU_TZ).replace(tzinfo=None) - collector_dt).days
            if days_old > 2:
                parts.append(f"🔴 Collector may be failing — last update: **{last_collector}**")
            else:
                parts.append(f"✅ Last collector: **{last_collector}**")
        else:
            parts.append("🔴 Last collector: **unknown**")

        st.markdown("&nbsp;&nbsp;|&nbsp;&nbsp;".join(parts))
        st.markdown("<hr style='margin:4px 0 12px 0; border-color:#333'>", unsafe_allow_html=True)
    except Exception as e:
        st.caption(f"⚠️ Health bar error: {e}")




def main():
    page = st.sidebar.radio(
        "🧭 Navigation",
        ["📊 Live Tracker", "💼 Portfolio Tracker", "🎯 Portfolio Score Tracker", "📅 Daily Summary", "📦 Timeline Archive", "🔬 Post Analysis"]
    )

    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh data", help="Clear all caches and reload from Google Sheets"):
        st.cache_data.clear()
        st.rerun()
    
    if page == "📊 Live Tracker":
        main_page()
    elif page == "💼 Portfolio Tracker":
        portfolio_tracker_page()
    elif page == "📅 Daily Summary":
        daily_summary_page()
    elif page == "📦 Timeline Archive":
        timeline_archive_page()
    elif page == "🎯 Portfolio Score Tracker":
        post_analysis_page()

if __name__ == "__main__":
    main()
