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
import sheets_manager
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

SHEET_ID = "1oyefUPV52SMeAlC4UejECYoPRNRudJJS42rukNGYx5k"  # legacy backup
PERU_TZ = pytz.timezone("America/Lima")


# ── Cached sheet loaders ──────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def _cached_timeline_live() -> pd.DataFrame:
    """timeline_live → raw DataFrame. Refreshes every 2 min."""
    try:
        gc = _get_gc() or sheets_manager._get_gc()
        if not gc: return pd.DataFrame()
        ws = sheets_manager.get_worksheet("timeline_live", gc=gc)
        if not ws: return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception as e:
        st.warning(f"⚠️ timeline_live read error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _cached_daily_snapshots() -> pd.DataFrame:
    """daily_snapshots → raw DataFrame. Refreshes every 5 min."""
    try:
        gc = _get_gc()
        if not gc: return pd.DataFrame()
        ws = sheets_manager.get_worksheet("daily_snapshots", gc=gc)
        if not ws: return pd.DataFrame()
        data = ws.get_all_values()
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
        ws = sheets_manager.get_worksheet("portfolio", gc=gc)
        if not ws: return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        for col in ["Score", "BuyPrice", "CurrentPrice", "Change%", "P/L"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def calc_score_v2(row):
    s = 0
    try:
        mxv = float(row.get('MxV_calc', 0) or 0)
        if mxv < 0: s += min(abs(mxv)/200, 1) * 25
    except: pass
    try:
        ru = float(row.get('RunUp_calc', 0) or 0)
        if ru > 0: s += min(ru/30, 1) * 25
    except: pass
    try:
        atrx = float(row.get('ATRX_calc', 0) or 0)
        s += min(atrx/5, 1) * 20
    except: pass
    try:
        rsi = float(row.get('RSI', 0) or 0)
        if rsi < 50:    s += (rsi/50)*5
        elif rsi <= 70: s += 5 + ((rsi-50)/20)*5
        else:           s += max(0, 10 - ((rsi-70)/30)*5)
    except: pass
    try:
        vwap = float(row.get('VWAP_calc', 0) or 0)
        if vwap > 0: s += min(vwap/8, 1) * 10
    except: pass
    try:
        sc = float(row.get('ScanChange%', 0) or 0)
        if sc > 0: s += min(sc/60, 1) * 5
    except: pass
    try:
        rv = float(row.get('REL_VOL_calc', 0) or 0)
        s += min(rv/15, 1) * 5
    except: pass
    return round(s, 2)


@st.cache_data(ttl=60)
def _cached_post_analysis() -> pd.DataFrame:
    """post_analysis → DataFrame via gsheets_sync. Refreshes every 5 min."""
    from gsheets_sync import load_post_analysis_from_sheets
    return load_post_analysis_from_sheets()


@st.cache_data(ttl=60)
def _cached_tl_today() -> pd.DataFrame:
    """Today's timeline_live rows with canonical column names. Refreshes every 60s."""
    try:
        gc = _get_gc() or sheets_manager._get_gc()
        if not gc: return pd.DataFrame()
        ws = sheets_manager.get_worksheet("timeline_live", gc=gc)
        if not ws: return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        # Sheet header may be stale — enforce canonical column names
        if len(df.columns) == len(sheets_manager.TIMELINE_LIVE_COLS):
            df.columns = sheets_manager.TIMELINE_LIVE_COLS
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=30)
def _cached_live_trades() -> pd.DataFrame:
    """live_trades sheet → DataFrame. Refreshes every 30s."""
    try:
        gc = _get_gc()
        if gc is None:
            return pd.DataFrame()
        ws = sheets_manager.get_worksheet("live_trades", gc=gc)
        if ws is None:
            return pd.DataFrame()
        raw = ws.get_all_values()
        if len(raw) <= 1:
            return pd.DataFrame()
        df = pd.DataFrame(raw[1:], columns=raw[0])
        for col in ["EntryPrice", "CurrentPrice", "RunningHigh", "RunningLow",
                    "TP10_Price", "SL_Price", "Score", "EntryScore",
                    "IntraHigh", "PnL_pct"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def _cached_portfolio_live() -> pd.DataFrame:
    """portfolio_live tab — RunningHigh/RunningLow per pending stock. Refreshes every 60s."""
    try:
        gc = _get_gc()
        if not gc:
            return pd.DataFrame()
        ws = sheets_manager.get_worksheet("portfolio_live", gc=gc)
        if not ws:
            return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        for col in ["EntryPrice", "RunningHigh", "RunningLow", "TP10_Price", "SL_Price", "CurrentPrice"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _cached_daily_summary() -> pd.DataFrame:
    """daily_summary → raw DataFrame. Refreshes every 5 min."""
    try:
        gc = _get_gc()
        if not gc: return pd.DataFrame()
        ws = sheets_manager.get_worksheet("daily_summary", gc=gc)
        if not ws: return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) <= 1: return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
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
                results.append({"Ticker":row["Ticker"],"Score":f("Score"),"EntryScore":f("EntryScore"),"Price":f("Price"),"Change":f("Change"),"MxV":f("MxV"),"PriceTo52WHigh":f("PriceTo52WHigh"),"PriceToHigh":f("PriceToHigh"),"RSI":f("RSI"),"ATRX":f("ATRX"),"REL_VOL":f("REL_VOL"),"RunUp":f("RunUp"),"Float%":f("Float%"),"Gap":f("Gap"),"VWAP":f("VWAP")})
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


def health_check_section():
    """Collapsible health check panel at the top of the main page."""
    with st.expander("🔍 System Health Check", expanded=False):
        col_btn, col_quiet, _ = st.columns([1, 1, 4])
        run_full   = col_btn.button("▶ Run Full Check", key="hc_run_full")
        run_quiet  = col_quiet.button("▶ Errors Only",   key="hc_run_quiet")

        if run_full or run_quiet:
            with st.spinner("בודק מערכת..."):
                try:
                    import health_check
                    lines = health_check.run(quiet=run_quiet)
                    st.session_state["hc_result"] = lines
                except Exception as e:
                    st.session_state["hc_result"] = [f"❌ Health check נכשל: {e}"]

        if "hc_result" in st.session_state:
            report = "\n".join(st.session_state["hc_result"])
            # Colour the output: errors red, warnings orange, ok green
            has_critical = any("❌" in l for l in st.session_state["hc_result"])
            has_warn     = any("⚠️" in l for l in st.session_state["hc_result"])
            border = "#e74c3c" if has_critical else ("#f39c12" if has_warn else "#27ae60")
            st.markdown(
                f"<pre style='background:#111;color:#eee;padding:12px;border-radius:6px;"
                f"border-left:4px solid {border};font-size:0.82rem;white-space:pre-wrap'>"
                f"{report}</pre>",
                unsafe_allow_html=True,
            )


def main_page():
    st.title("🚀 RidingHigh Pro v14.6")
    st.caption("Portfolio Tracker - Auto-saves stocks with score 60+ at 14:59")
    system_health_bar()
    health_check_section()

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
    
    if st.sidebar.button("🗑️ Clear Local Cache", help="מוחק קובץ cache מקומי בלבד — נתוני Sheets לא נפגעים"):
        tracker = LiveTracker()
        if os.path.exists(tracker.today_file):
            os.remove(tracker.today_file)
            st.sidebar.success("✅ Cleared local cache!")
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
                # Fallback: read timeline_live directly without going through session_state.results
                _tl_fallback = _cached_timeline_live()
                if not _tl_fallback.empty:
                    _today_fb = now_peru.strftime("%Y-%m-%d")
                    _tl_today = _tl_fallback[_tl_fallback["Date"] == _today_fb]
                    if not _tl_today.empty:
                        _lt = _tl_today["ScanTime"].max()
                        _latest = _tl_today[_tl_today["ScanTime"] == _lt]
                        _fake = []
                        for _, _r in _latest.iterrows():
                            try:
                                _fake.append({
                                    "Ticker": _r["Ticker"],
                                    "Score": float(_r.get("Score", 0) or 0),
                                    "EntryScore": float(_r.get("EntryScore", 0) or 0),
                                    "Price": float(_r.get("Price", 0) or 0),
                                    "Change": 0, "MxV": float(_r.get("MxV", 0) or 0),
                                    "PriceTo52WHigh": 0, "PriceToHigh": 0, "RSI": 0, "ATRX": 0,
                                    "REL_VOL": float(_r.get("REL_VOL", 0) or 0),
                                    "RunUp": float(_r.get("RunUp", 0) or 0),
                                    "Float%": 0, "Gap": 0, "VWAP": 0,
                                })
                            except Exception:
                                pass
                        if _fake:
                            st.session_state.results = _fake
                            st.session_state.last_scan = now_peru
                            st.sidebar.success(f"✅ {len(_fake)} stocks! (scan: {_lt})")
                        else:
                            st.sidebar.info("⏳ Waiting for next scan...")
                    else:
                        st.sidebar.info("⏳ Waiting for next scan...")
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
        
        # Sort by EntryScore desc (stocks ready for entry float to top)
        results_sorted = sorted(results, key=lambda x: x.get('EntryScore', 0), reverse=True)

        display_data = []
        _has_change = any(r.get('Change', 0) != 0 for r in results_sorted)
        _has_rsi    = any(r.get('RSI', 0) != 0 for r in results_sorted)
        for r in results_sorted:
            entry_s = r.get('EntryScore', 0)
            row_d = {
                'Ticker': r['Ticker'],
                'Score': f"{r['Score']:.2f}",
                'EntryScore': f"{entry_s:.2f}" if r['Score'] >= 60 else "—",
                'Price': f"${r['Price']:.2f}",
                'MxV': f"{r['MxV']:.0f}%",
                'RunUp': f"{r['RunUp']:+.1f}%",
                'REL VOL': f"{r['REL_VOL']:.1f}x",
            }
            if _has_change:
                row_d['Change'] = f"{r['Change']:+.1f}%"
            if _has_rsi:
                row_d['RSI']  = f"{r['RSI']:.1f}"
                row_d['ATRX'] = f"{r['ATRX']:.1f}"
                row_d['Gap']  = f"{r['Gap']:+.1f}%"
                row_d['VWAP'] = f"{r['VWAP']:+.1f}%"
            display_data.append(row_d)

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

        def color_entry_score(val):
            try:
                if val == "—":
                    return 'background-color: #444444; color: #aaaaaa'
                v = float(val)
                if v >= 60:
                    return 'background-color: #006400; color: white; font-weight: bold'
                elif v >= 40:
                    return 'background-color: #808000; color: white'
                else:
                    return 'background-color: #555555; color: #cccccc'
            except:
                return ''

        styled_df = df.style.apply(highlight_score, axis=1)
        if 'EntryScore' in df.columns:
            try:
                styled_df = styled_df.map(color_entry_score, subset=['EntryScore'])
            except AttributeError:
                styled_df = styled_df.map(color_entry_score, subset=['EntryScore'])
        
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
        all_df = _cached_daily_summary()
        if all_df.empty:
            # fallback: daily_snapshots has full-column 14:59 snapshot data
            all_df = _cached_daily_snapshots()
        if all_df.empty:
            st.warning("⚠️ No data yet - will be populated at 14:59")
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

    # Column-specific format dict (rules: Score=2dp, MxV=0dp int, %=1dp, REL_VOL=1dp, others=2dp)
    _fmt_map = {
        "Score":   "{:.2f}",
        "MxV":     "{:.0f}",
        "RunUp":   "{:.1f}",
        "REL_VOL": "{:.1f}",
        "RSI":     "{:.1f}",
        "ATRX":    "{:.1f}",
        "Gap":     "{:.1f}",
        "VWAP":    "{:.1f}",
    }
    fmt_dict = {c: _fmt_map.get(c, "{:.2f}") for c in df.columns if c != "Ticker"}
    numeric_cols = [c for c in df.columns if c != "Ticker" and df[c].dtype in ['float64','float32','int64','int32']]
    styled_df = df.style.apply(highlight_score, axis=1).format(fmt_dict, subset=numeric_cols)
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
    st.caption("Score timeline per scan — pivoted by ScanTime (from timeline_live)")
    system_health_bar()

    if is_cloud():
        try:
            all_df = _cached_timeline_live()
            if all_df.empty:
                st.warning("⚠️ No timeline data yet")
                return
            dates = sorted(all_df["Date"].unique().tolist(), reverse=True)
        except Exception as e:
            st.error(f"Error: {e}")
            return
    else:
        tracker = LiveTracker()
        dates = tracker.get_archive_dates()

    if not dates:
        st.warning("⚠️ No timeline data yet")
        return

    selected_date = st.selectbox("📆 Select Date", dates, index=0)

    if is_cloud():
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


def _is_day_complete(date_str: str) -> bool:
    """
    A D-day is safe to use for exit evaluation only when the full trading
    session has closed in Peru time:
      - date_str < today (Peru TZ), AND
      - date_str is a weekday
    Never returns True for today or any future date.
    """
    try:
        today_peru = datetime.now(PERU_TZ).date()
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
        return day < today_peru and day.weekday() < 5
    except Exception:
        return False


def _simulate_short_trades(pa_df: pd.DataFrame):
    """
    Simulate $1000 short trades for every row in post_analysis.
    Returns (table_a, table_b):
      table_a — entry at ScanPrice (EOD scan day)
      table_b — entry at D1_Open  (next day open)
    Only evaluates TP/SL exits on days where the full trading session has
    closed (strictly before today in Peru TZ). Pre-market / intraday data
    can never trigger an exit.
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

        # Pre-compute the 5 D-day dates for this row so exit loop can gate on them
        try:
            _row_trading_days = []
            _d = datetime.strptime(scan_date, "%Y-%m-%d")
            while len(_row_trading_days) < 5:
                _d += timedelta(days=1)
                if _d.weekday() < 5:
                    _row_trading_days.append(_d.strftime("%Y-%m-%d"))
        except Exception:
            _row_trading_days = [""] * 5

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
                    # Skip this day if the full trading session hasn't closed yet
                    day_date = _row_trading_days[day - 1] if day - 1 < len(_row_trading_days) else ""
                    if not _is_day_complete(day_date):
                        break
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
            df["CurrentChange%"] = ((df["CurrentPrice"] - df["ScanPrice"]) / df["ScanPrice"] * 100).round(2)
        except:
            df["CurrentPrice"] = None
            df["CurrentChange%"] = None

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

    filtered["Score_v2"] = filtered.apply(calc_score_v2, axis=1)

    st.subheader(f"📋 תוצאות ({len(filtered)} מניות)")

    display_cols = ["Ticker", "ScanDate", "Score", "Score_v2", "ScanChange%", "ScanPrice",
                    "IntraHigh", "IntraLow", "DayRunUp%", "PeakScoreTime", "PeakScorePrice",
                    "CurrentPrice", "CurrentChange%", "MaxDrop%", "BestDay", "TP10_Hit", "TP15_Hit", "TP20_Hit"]
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

    # Step 1: force-convert all non-text columns to numeric (data from Sheets = strings)
    TEXT_COLS = {"Ticker", "ScanDate", "PeakScoreTime"}
    for col in display_cols:
        if col in filtered.columns and col not in TEXT_COLS:
            filtered[col] = pd.to_numeric(filtered[col], errors="coerce")

    # Step 2: round numeric columns to 2 decimal places
    num_cols = [c for c in display_cols if c in filtered.columns and c not in TEXT_COLS]
    for col in num_cols:
        filtered[col] = filtered[col].round(2)

    # Step 3: clean text columns only (NaN → "-")
    for col in TEXT_COLS:
        if col in filtered.columns:
            filtered[col] = filtered[col].fillna("-").replace({"None": "-", "nan": "-", "": "-"})

    # Step 4: build format dict on actually-numeric columns (NaN stays NaN — na_rep handles display)
    format_dict = {}
    for col in num_cols:
        if col in ["TP10_Hit", "TP15_Hit", "TP20_Hit", "BestDay"]:
            format_dict[col] = "{:.0f}"
        elif "%" in col:
            format_dict[col] = "{:.1f}%"
        else:
            format_dict[col] = "{:.2f}"

    styled = filtered[display_cols].style
    for col in ["TP10_Hit", "TP15_Hit", "TP20_Hit"]:
        if col in display_cols:
            styled = styled.map(color_tp, subset=[col])
    if "MaxDrop%" in display_cols:
        styled = styled.map(color_drop, subset=["MaxDrop%"])
    if "ScanChange%" in display_cols:
        styled = styled.map(color_change, subset=["ScanChange%"])
    if "CurrentChange%" in display_cols:
        styled = styled.map(color_change, subset=["CurrentChange%"])
    styled = styled.format(format_dict, na_rep="-")
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
            "ירידה ממוצעת": f"{avg_drop_t:.1f}%"
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
                corr_data.append({"מדד": col, "קורלציה עם הירידה": round(corr, 2)})
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
                    from gsheets_sync import _get_client
                    gc = _get_client()

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:

                        # Regular tabs — each is its own Spreadsheet now
                        regular_tabs = {
                            "Post Analysis":   "post_analysis",
                            "Daily Snapshots": "daily_snapshots",
                            "Daily Summary":   "daily_summary",
                            "Portfolio":       "portfolio",
                        }
                        for sheet_name, tab_name in regular_tabs.items():
                            try:
                                ws = sheets_manager.get_worksheet(tab_name, gc=gc)
                                data = ws.get_all_values()
                                tab_df = pd.DataFrame(data[1:], columns=data[0])
                                tab_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            except Exception as e:
                                st.warning(f"⚠️ {tab_name}: {e}")

                        # Timeline Live — one pivot sheet per date
                        try:
                            tl_df = _cached_timeline_live()
                            if not tl_df.empty and "ScanTime" in tl_df.columns:
                                tl_df["Score"] = pd.to_numeric(tl_df["Score"], errors="coerce")
                                for date_val in sorted(tl_df["Date"].unique().tolist(), reverse=True):
                                    day_df = tl_df[tl_df["Date"] == date_val]
                                    pivot = day_df.pivot_table(
                                        index="Ticker", columns="ScanTime", values="Score", aggfunc="last"
                                    )
                                    pivot = pivot[sorted(pivot.columns, reverse=True)].round(2)
                                    pivot.reset_index(inplace=True)
                                    sheet_label = f"TL {date_val}"[:31]
                                    pivot.to_excel(writer, sheet_name=sheet_label, index=False)
                        except Exception as e:
                            st.warning(f"⚠️ timeline_live pivot: {e}")

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
                    from gsheets_sync import _get_client
                    gc = _get_client()

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:

                        # Tab 1: Post Analysis (full)
                        try:
                            ws_pa = sheets_manager.get_worksheet("post_analysis", gc=gc)
                            pa_data = ws_pa.get_all_values()
                            pa_df = pd.DataFrame(pa_data[1:], columns=pa_data[0])
                            pa_df.to_excel(writer, sheet_name="Post Analysis", index=False)
                        except Exception as e:
                            st.warning(f"⚠️ post_analysis: {e}")

                        # Tab 2: Timeline Summary (from timeline_live)
                        try:
                            tl_df = _cached_timeline_live()
                            if not tl_df.empty and "ScanTime" in tl_df.columns:
                                summary_df = _build_timeline_summary(tl_df)
                                summary_df.to_excel(writer, sheet_name="Timeline Summary", index=False)
                            else:
                                st.warning("⚠️ timeline_live ריק או חסר ScanTime")
                        except Exception as e:
                            st.warning(f"⚠️ timeline summary: {e}")

                        # Tab 3: Daily Snapshots (last 10 days only to keep light)
                        try:
                            snap_df = _cached_daily_snapshots()
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

    # ── Admin: Restore from Backup ────────────────────────────────────────────
    with st.expander("🔧 Admin — Restore from Backup", expanded=False):
        st.caption("שחזור post_analysis מגיבוי — קודם Drive, fallback ל-CSV מקומי")
        available_local = []
        backup_dir = os.path.join(os.path.dirname(__file__), "backups")
        if os.path.isdir(backup_dir):
            available_local = sorted(
                [f.replace("post_analysis_", "").replace(".csv", "")
                 for f in os.listdir(backup_dir)
                 if f.startswith("post_analysis_") and f.endswith(".csv")],
                reverse=True
            )

        if available_local:
            st.markdown(f"**גיבויים מקומיים זמינים:** {', '.join(available_local[:5])}")
        else:
            st.info("אין גיבויים מקומיים ב-backups/")

        restore_date = st.text_input(
            "תאריך לשחזור (YYYY-MM-DD)",
            value=available_local[0] if available_local else "",
            key="restore_date_input"
        )
        if st.button("📦 Restore from Backup", key="restore_btn"):
            if not restore_date or len(restore_date) != 10:
                st.error("הכנס תאריך בפורמט YYYY-MM-DD")
            else:
                with st.spinner(f"משחזר מגיבוי {restore_date}..."):
                    try:
                        from backup_manager import restore_from_backup
                        ok = restore_from_backup(restore_date)
                        if ok:
                            st.success(f"✅ שוחזר בהצלחה מגיבוי {restore_date}")
                            st.cache_data.clear()
                        else:
                            st.error(f"❌ שחזור נכשל — בדוק logs")
                    except Exception as e:
                        st.error(f"❌ שגיאה: {e}")


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
    # Fallback: if timeline_live is empty, derive last scan from daily_snapshots
    if not last_scan:
        try:
            df_snap = _cached_daily_snapshots()
            if not df_snap.empty and "Date" in df_snap.columns:
                last_date = df_snap["Date"].max()
                scan_time = df_snap[df_snap["Date"] == last_date]["ScanTime"].max() if "ScanTime" in df_snap.columns else "14:59"
                last_scan = f"{last_date} {scan_time}"
        except Exception:
            pass
    # Second fallback: daily_summary
    if not last_scan:
        try:
            df_ds = _cached_daily_summary()
            if not df_ds.empty and "Date" in df_ds.columns:
                last_date = df_ds["Date"].max()
                last_scan = f"{last_date} (daily summary)"
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


def score_tracker_page():
    import plotly.graph_objects as _go
    st.title("🎯 Portfolio Score Tracker")
    system_health_bar()

    def _trading_days_after(sd, n=3):
        d = datetime.strptime(sd, "%Y-%m-%d")
        days = []
        while len(days) < n:
            d += timedelta(days=1)
            if d.weekday() < 5:
                days.append(d.strftime("%Y-%m-%d"))
        return days

    @st.cache_data(ttl=60)
    def _load_data():
        try:
            gc = sheets_manager._get_gc()
            if gc is None:
                return pd.DataFrame(), pd.DataFrame()

            ws_port = sheets_manager.get_worksheet("portfolio", gc=gc)
            port = ws_port.get_all_values() if ws_port else []
            port_df = pd.DataFrame(port[1:], columns=port[0]) if len(port) > 1 else pd.DataFrame()

            ws_st = sheets_manager.get_worksheet("score_tracker", gc=gc)
            raw = ws_st.get_all_values() if ws_st else []
            if len(raw) > 1:
                tracker_df = pd.DataFrame(raw[1:], columns=raw[0])
                tracker_df["Score"] = pd.to_numeric(tracker_df["Score"], errors="coerce")
            else:
                tracker_df = pd.DataFrame()

            return port_df, tracker_df
        except Exception as e:
            st.error(f"Load error: {e}")
            return pd.DataFrame(), pd.DataFrame()

    with st.spinner("טוען נתונים..."):
        port_df, tracker_df = _load_data()

    if port_df.empty:
        st.info("אין מניות בפורטפוליו.")
        return

    # ── Download button ────────────────────────────────────────────────────────
    if not tracker_df.empty:
        _dl_csv  = tracker_df.to_csv(index=False).encode("utf-8")
        _dl_name = f"score_tracker_{datetime.now(PERU_TZ).strftime('%Y-%m-%d')}.csv"
        st.download_button("📥 Download CSV", data=_dl_csv,
                           file_name=_dl_name, mime="text/csv")

    today = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    # Build stock list: stocks whose D0–D3 window spans today
    # (includes weekends/holidays that fall between trading days)
    DAY_LABELS = ["📅 D0 — יום כניסה", "📈 D1", "📈 D2", "📈 D3"]
    stocks = []
    for r in port_df.itertuples():
        sd = str(getattr(r, "Date", "")).strip()
        tk = str(getattr(r, "Ticker", "")).strip()
        if not sd or not tk:
            continue
        try:
            if sd < "2026-04-10":   # תיעוד score_tracker רק מ-10/4
                continue
            window      = _trading_days_after(sd, 3)   # [D1, D2, D3]
            trading_seq = [sd] + window                 # [D0, D1, D2, D3]
            d3          = trading_seq[-1]

            # active if sd <= today <= D3
            if not (sd <= today <= d3):
                continue

            # find which "slot" today falls in
            day_idx = 0
            for i, tday in enumerate(trading_seq):
                if today >= tday:
                    day_idx = i
            status = DAY_LABELS[day_idx]
            stocks.append({"Ticker": tk, "ScanDate": sd, "Window": window, "Status": status})
        except Exception:
            pass

    stocks = sorted(stocks, key=lambda x: x["ScanDate"], reverse=True)
    seen = set()
    stocks = [s for s in stocks if (s["Ticker"], s["ScanDate"]) not in seen
              and not seen.add((s["Ticker"], s["ScanDate"]))]

    if not stocks:
        st.info("⏳ אין מניות פעילות בחלון D0–D3 כרגע.")
        return

    # Pre-build datetime column once
    if not tracker_df.empty and "Date" in tracker_df.columns and "ScanTime" in tracker_df.columns:
        tracker_df["dt"] = pd.to_datetime(
            tracker_df["Date"] + " " + tracker_df["ScanTime"], errors="coerce"
        )

    # ── One expander per stock ───────────────────────────────────────────────────
    for s in stocks:
        tk     = s["Ticker"]
        sd     = s["ScanDate"]
        window = s["Window"]

        # ── Precompute stats for expander label ──────────────────────────────
        _entry_score = _cur_score = _scan_price = _cur_price = None
        _tp_price = _sl_price = None
        _trade_status = "⏳ Pending"
        _n_pts = 0

        if not tracker_df.empty and "dt" in tracker_df.columns:
            _sdf_pre = tracker_df[
                (tracker_df["Ticker"] == tk) & (tracker_df["ScanDate"] == sd)
            ].dropna(subset=["dt", "Score"]).sort_values("dt")
            _n_pts = len(_sdf_pre)

            if not _sdf_pre.empty:
                _entry_score = float(_sdf_pre["Score"].iloc[0])
                _cur_score   = float(_sdf_pre["Score"].iloc[-1])
                if "Price" in _sdf_pre.columns:
                    _pp = pd.to_numeric(_sdf_pre["Price"], errors="coerce").dropna()
                    if not _pp.empty:
                        _scan_price = round(float(_pp.iloc[0]), 2)
                        _cur_price  = round(float(_pp.iloc[-1]), 2)
                        _tp_price   = round(_scan_price * 0.90, 2)
                        _sl_price   = round(_scan_price * 1.07, 2)
                        if _pp.min() <= _tp_price:
                            _trade_status = "✅ TP10"
                        elif _pp.max() >= _sl_price:
                            _trade_status = "❌ SL"

        # Build rich label
        _score_str = f" | Score: {_entry_score:.0f}" if _entry_score is not None else ""
        if _scan_price and _cur_price:
            _chg_lbl = (_cur_price - _scan_price) / _scan_price * 100
            _dir     = "▼" if _chg_lbl < 0 else "▲"
            _price_str = f" | ${_scan_price:.2f}→${_cur_price:.2f} {_dir}{abs(_chg_lbl):.1f}%"
        else:
            _price_str = ""
        label = f"**{tk}** · {sd}{_score_str}{_price_str} · {_trade_status} · ({_n_pts} נק')"

        with st.expander(label, expanded=False):
            if tracker_df.empty:
                st.info("⏳ אין נתוני score_tracker עדיין.")
                continue

            sdf = tracker_df[
                (tracker_df["Ticker"] == tk) & (tracker_df["ScanDate"] == sd)
            ].dropna(subset=["dt", "Score"]).sort_values("dt").copy()

            if sdf.empty:
                st.info("⏳ אין עדיין נתונים עבור מניה זו.")
                continue

            if "Price" in sdf.columns:
                sdf["Price"] = pd.to_numeric(sdf["Price"], errors="coerce")

            # Use precomputed price stats (already computed above)
            scan_price = _scan_price
            cur_price  = _cur_price
            tp_price   = _tp_price
            sl_price   = _sl_price

            gran = st.radio("רזולוציה", ["דקות", "שעות"], horizontal=True,
                            key=f"gran_{tk}_{sd}")

            # ── Shared chart layout ───────────────────────────────────────
            _BASE = dict(
                height=290, margin=dict(l=10, r=10, t=35, b=10),
                paper_bgcolor="white", plot_bgcolor="white",
                font=dict(color="#222", size=11),
                xaxis=dict(gridcolor="#e0e0e0", tickformat="%m/%d\n%H:%M"),
                showlegend=False,
            )

            def _add_day_vlines(fig, plot_dt_series):
                for i, day in enumerate(window):
                    day_open = pd.Timestamp(day + " 08:30")
                    if plot_dt_series.min() <= day_open <= plot_dt_series.max() + pd.Timedelta(hours=8):
                        fig.add_vline(x=day_open.value / 1e6,
                                      line_dash="dash", line_color="#aaa", line_width=1,
                                      annotation_text=f"D{i+1}",
                                      annotation_font_color="#555",
                                      annotation_position="top right")

            col_score, col_price = st.columns(2)

            # ── Left: Score Trajectory ────────────────────────────────────
            with col_score:
                ps = sdf[["dt", "Score"]].copy()
                if gran == "שעות":
                    ps = ps.set_index("dt").resample("1h")["Score"].mean().dropna().reset_index()

                fig_s = _go.Figure()
                fig_s.add_trace(_go.Scatter(
                    x=ps["dt"], y=ps["Score"], mode="lines+markers",
                    line=dict(color="#1d6fe8", width=2), marker=dict(size=3),
                    hovertemplate="%{x|%m/%d %H:%M}<br>Score: %{y:.1f}<extra></extra>",
                ))
                # Entry star marker
                fig_s.add_trace(_go.Scatter(
                    x=[ps["dt"].iloc[0]], y=[ps["Score"].iloc[0]],
                    mode="markers", marker=dict(color="orange", size=12, symbol="star"),
                    hovertemplate=f"Entry Score: {ps['Score'].iloc[0]:.1f}<extra></extra>",
                ))
                # Entry score baseline
                if _entry_score is not None:
                    fig_s.add_hline(y=_entry_score, line_dash="dash", line_color="orange",
                                    line_width=1.5,
                                    annotation_text=f"Entry {_entry_score:.0f}",
                                    annotation_position="bottom right",
                                    annotation_font_color="darkorange")
                # Zone bands
                fig_s.add_hrect(y0=80, y1=100, fillcolor="#ffe0e0", opacity=0.3, line_width=0)
                fig_s.add_hrect(y0=60, y1=80,  fillcolor="#e0f0e0", opacity=0.3, line_width=0)
                fig_s.add_hrect(y0=40, y1=60,  fillcolor="#fff8e0", opacity=0.3, line_width=0)
                _add_day_vlines(fig_s, ps["dt"])
                fig_s.update_layout(**{**_BASE,
                    "title": dict(text="Score Trajectory", font=dict(size=13)),
                    "yaxis": dict(gridcolor="#e0e0e0", title="Score", range=[0, 100])})
                st.plotly_chart(fig_s, use_container_width=True, key=f"chart_{tk}_{sd}")

            # ── Right: Price vs TP/SL ─────────────────────────────────────
            with col_price:
                if scan_price and "Price" in sdf.columns:
                    pp = sdf[["dt", "Price"]].dropna().copy()
                    if gran == "שעות":
                        pp = pp.set_index("dt").resample("1h")["Price"].mean().dropna().reset_index()

                    fig_p = _go.Figure()
                    fig_p.add_trace(_go.Scatter(
                        x=pp["dt"], y=pp["Price"], mode="lines+markers",
                        line=dict(color="#1d6fe8", width=2), marker=dict(size=3),
                        hovertemplate="%{x|%m/%d %H:%M}<br>$%{y:.2f}<extra></extra>",
                    ))
                    fig_p.add_hline(y=scan_price, line_dash="dot", line_color="#888",
                                    line_width=1.5,
                                    annotation_text=f"Entry ${scan_price:.2f}",
                                    annotation_position="bottom right",
                                    annotation_font_color="#555")
                    fig_p.add_hline(y=tp_price, line_dash="dot", line_color="green",
                                    line_width=1.5,
                                    annotation_text=f"TP ${tp_price:.2f}",
                                    annotation_position="bottom right",
                                    annotation_font_color="green")
                    fig_p.add_hline(y=sl_price, line_dash="dot", line_color="red",
                                    line_width=1.5,
                                    annotation_text=f"SL ${sl_price:.2f}",
                                    annotation_position="top right",
                                    annotation_font_color="red")
                    _add_day_vlines(fig_p, pp["dt"])
                    fig_p.update_layout(**{**_BASE,
                        "title": dict(text="Price vs TP/SL", font=dict(size=13)),
                        "yaxis": dict(gridcolor="#e0e0e0", title="Price ($)")})
                    st.plotly_chart(fig_p, use_container_width=True, key=f"price_{tk}_{sd}")
                else:
                    st.info("אין נתוני מחיר.")

            # ── Summary text ──────────────────────────────────────────────
            peak_score  = sdf["Score"].max()
            peak_dt     = sdf.loc[sdf["Score"].idxmax(), "dt"]
            final_score = float(sdf["Score"].iloc[-1])
            drop_pct    = (final_score - peak_score) / peak_score * 100 if peak_score else 0
            days_since  = (datetime.now(PERU_TZ).date()
                           - datetime.strptime(sd, "%Y-%m-%d").date()).days

            st.markdown(
                f"📈 **Peak Score:** {peak_score:.0f} ב-{peak_dt.strftime('%m/%d %H:%M')}"
                f" &nbsp;|&nbsp; 📉 **Current Score:** {final_score:.0f}"
                f" &nbsp;|&nbsp; 🔻 {abs(drop_pct):.0f}% מהשיא"
            )
            if scan_price and cur_price:
                _chg_sum = (cur_price - scan_price) / scan_price * 100
                st.markdown(
                    f"💰 **Entry:** ${scan_price:.2f}"
                    f" &nbsp;|&nbsp; **Current:** ${cur_price:.2f}"
                    f" &nbsp;|&nbsp; **Change:** {_chg_sum:+.1f}%"
                )
                st.markdown(
                    f"🎯 **TP10 at** ${tp_price:.2f}"
                    f" &nbsp;|&nbsp; 🛑 **SL at** ${sl_price:.2f}"
                    f" &nbsp;|&nbsp; 📅 **Days since entry:** {days_since}"
                )



def live_trades_page():
    _SCORE_TYPES = ["Score", "Score_B", "Score_C", "Score_D", "Score_E",
                    "Score_F", "Score_G", "Score_H", "Score_I"]
    _SCORE_DESC = {
        "Score":   "Current — balanced weights",
        "Score_B": "Pure pump — no RSI/RelVol",
        "Score_C": "Volatility first — ATRX dominant",
        "Score_D": "Micro-cap pump — MxV dominant",
        "Score_E": "Momentum — how much already pumped",
        "Score_F": "VWAP extension — overextended",
        "Score_G": "RelVol sweet spot — penalizes real moves",
        "Score_H": "RSI-free pure technicals",
        "Score_I": "MxV dominant 50%",
    }
    ENTRY_AMOUNT = 1000.0

    st.title("⚡ Live Trades")
    st.caption("מניות שנכנסו לשורט בזמן אמת — Score ≥70 · TP 10% · SL 10% · כניסה $1,000 לעסקה")

    now_peru = datetime.now(PERU_TZ)

    # ── Buttons ───────────────────────────────────────────────────────────────
    col_btn1, col_btn2, col_btn3, _ = st.columns([1, 1, 1, 4])
    with col_btn1:
        if st.button("🗑️ Clear Closed", help="מעביר עסקאות סגורות (TP/SL) לארכיון — לא נמחק לצמיתות"):
            try:
                gc = _get_gc()
                if not gc:
                    st.error("❌ אין חיבור ל-Google Sheets")
                else:
                    ws = sheets_manager.get_worksheet("live_trades", gc=gc)
                    raw = ws.get_all_values() if ws else []
                    if len(raw) > 1:
                        full_df   = pd.DataFrame(raw[1:], columns=raw[0])
                        open_df   = full_df[full_df["Status"] == "Pending"]
                        closed_df = full_df[full_df["Status"].isin(["TP10", "SL"])]

                        if closed_df.empty:
                            st.info("אין עסקאות סגורות")
                        else:
                            # ── ARCHIVE FIRST — only delete if archive succeeds ──
                            n = sheets_manager.archive_live_trades(gc, closed_df)

                            # Write only open (Pending) trades back to live_trades
                            from auto_scanner import LIVE_TRADES_COLS
                            open_clean = open_df.reindex(columns=LIVE_TRADES_COLS, fill_value="")
                            ws.clear()
                            ws.update("A1", [LIVE_TRADES_COLS] + open_clean.astype(str).values.tolist())
                            st.cache_data.clear()
                            st.success(f"✅ {n} עסקאות הועברו לארכיון (live_trades_archive)")
                            st.rerun()
                    else:
                        st.info("live_trades ריק")
            except Exception as e:
                st.error(f"❌ שגיאה — נתונים לא נמחקו: {e}")
    with col_btn2:
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.rerun()

    # ── Load data ─────────────────────────────────────────────────────────────
    with st.spinner("טוען עסקאות חיות..."):
        df = _cached_live_trades()

    if df.empty:
        st.info("📭 אין עסקאות עדיין — הסורק יכניס מניות שעומדות בקריטריון בזמן ריצה הבאה.")
        st.caption(f"⏱ עדכון אחרון: {now_peru.strftime('%H:%M:%S')} Peru · מתרענן כל 60 שניות")
        return

    # Backward-compat: rows without ScoreType belong to "Score"
    if "ScoreType" not in df.columns:
        df["ScoreType"] = "Score"
    else:
        df["ScoreType"] = df["ScoreType"].fillna("Score").replace("", "Score")

    for col in ["EntryPrice", "CurrentPrice", "TP10_Price", "SL_Price", "PnL_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Change%"] = ((df["CurrentPrice"] - df["EntryPrice"]) / df["EntryPrice"] * 100).round(1)
    df["PnL_$"]   = (df["PnL_pct"].fillna(0) / 100 * ENTRY_AMOUNT).round(2)

    # Round price columns to 2 decimal places
    for _col in ["EntryPrice", "CurrentPrice", "TP10_Price", "SL_Price"]:
        if _col in df.columns:
            df[_col] = df[_col].round(2)

    # ── Download All button (placed in col_btn3 defined above) ───────────────
    with col_btn3:
        _dl_cols = ["ScoreType", "EntryTime", "Ticker", "EntryPrice", "CurrentPrice",
                    "Change%", "TP10_Price", "SL_Price", "Status", "PnL_$"]
        _dl_df = df[[c for c in _dl_cols if c in df.columns]].copy()
        _dl_csv = _dl_df.to_csv(index=False).encode("utf-8")
        _dl_fname = f"live_trades_{now_peru.strftime('%Y-%m-%d')}.csv"
        st.download_button("📥 Download All", data=_dl_csv,
                           file_name=_dl_fname, mime="text/csv")

    # ── Global summary ────────────────────────────────────────────────────────
    g_pending = int((df["Status"] == "Pending").sum())
    g_tp      = int((df["Status"] == "TP10").sum())
    g_sl      = int((df["Status"] == "SL").sum())
    g_closed  = g_tp + g_sl
    g_wr      = g_tp / g_closed * 100 if g_closed > 0 else 0
    g_pnl     = df["PnL_$"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("⏳ Pending",   g_pending)
    c2.metric("✅ TP10 Hits", g_tp)
    c3.metric("❌ SL Hits",   g_sl)
    c4.metric("🎯 Win Rate",  f"{g_wr:.0f}%" if g_closed > 0 else "—")
    c5.metric("💰 Total PnL", f"${g_pnl:+.0f}")

    st.divider()

    # ── Row-color helper ──────────────────────────────────────────────────────
    def _color_row(row):
        s = row.get("Status", "")
        if s == "TP10":    return ["background-color: #1a4a1a; color: #80ff80"] * len(row)
        if s == "SL":      return ["background-color: #4a1a1a; color: #ff8080"] * len(row)
        if s == "Pending": return ["background-color: #3a3a10; color: #ffff80"] * len(row)
        return [""] * len(row)

    DISPLAY_COLS = ["EntryTime", "Ticker", "EntryPrice", "CurrentPrice",
                    "Change%", "TP10_Price", "SL_Price", "Status", "PnL_$"]
    STATUS_ORDER = {"Pending": 0, "TP10": 1, "SL": 2}

    # ── 9 collapsible tables ──────────────────────────────────────────────────
    for score_type in _SCORE_TYPES:
        sub = df[df["ScoreType"] == score_type].copy()
        desc = _SCORE_DESC[score_type]

        n_pending = int((sub["Status"] == "Pending").sum())
        n_tp      = int((sub["Status"] == "TP10").sum())
        n_sl      = int((sub["Status"] == "SL").sum())
        n_closed  = n_tp + n_sl
        wr        = n_tp / n_closed * 100 if n_closed > 0 else 0
        pnl       = sub["PnL_$"].sum() if not sub.empty else 0.0
        wr_label  = f"{wr:.0f}%" if n_closed > 0 else "—"

        expander_label = (
            f"**{score_type}** · {desc} · "
            f"WR: {wr_label} · PnL: ${pnl:+.0f}"
        )

        with st.expander(expander_label, expanded=(score_type == "Score")):
            if sub.empty:
                st.info("אין עסקאות לציון זה עדיין.")
                continue

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("⏳ Pending",   n_pending)
            m2.metric("✅ TP",        n_tp)
            m3.metric("❌ SL",        n_sl)
            m4.metric("🎯 Win Rate",  wr_label)
            m5.metric("💰 PnL",       f"${pnl:+.0f}")

            sub["_sort"] = sub["Status"].map(STATUS_ORDER).fillna(9)
            sub = sub.sort_values(["_sort", "EntryTime"], ascending=[True, False]).drop(columns=["_sort"])
            avail = [c for c in DISPLAY_COLS if c in sub.columns]
            tbl = sub[avail].reset_index(drop=True)
            fmt = {c: "{:.2f}" for c in ["EntryPrice", "CurrentPrice", "TP10_Price", "SL_Price", "PnL_$"] if c in tbl.columns}
            if "Change%" in tbl.columns:
                fmt["Change%"] = "{:.1f}%"
            st.dataframe(tbl.style.apply(_color_row, axis=1).format(fmt), use_container_width=True)

    st.caption(f"⏱ עדכון אחרון: {now_peru.strftime('%H:%M:%S')} Peru · מתרענן כל 60 שניות")
    st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)


def score_comparison_page():
    SCORE_COLS = ["Score", "Score_B", "Score_C", "Score_D", "Score_E", "Score_F", "Score_G", "Score_H", "Score_I"]

    st.title("📊 Score Comparison")
    st.caption("השוואת ביצועים בין 9 נוסחות ציון — על בסיס נתוני Post Analysis")

    # ── 📡 Live section — today's data from timeline_live ─────────────────────
    st.markdown("## 📡 נתונים חיים (היום)")
    st.caption("מניות שנסרקו היום — נתונים מ-timeline_live, מתרענן כל 60 שניות")

    tl_raw = _cached_tl_today()
    today_str = datetime.now(PERU_TZ).strftime("%Y-%m-%d")

    if not tl_raw.empty and "Date" in tl_raw.columns and "Ticker" in tl_raw.columns:
        today_tl = tl_raw[tl_raw["Date"] == today_str].copy()
        if today_tl.empty:
            st.info("📭 אין נתוני timeline_live להיום עדיין.")
        else:
            # Numeric coerce for all score columns + display columns
            for col in SCORE_COLS + ["Price", "RunUp", "REL_VOL"]:
                if col in today_tl.columns:
                    today_tl[col] = pd.to_numeric(today_tl[col], errors="coerce")

            # Peak row per ticker = row with highest Score
            peak_tl = (today_tl.sort_values("Score", ascending=False)
                                .drop_duplicates("Ticker")
                                .reset_index(drop=True))

            # Compute max across all 9 score columns for sorting
            avail_sc = [c for c in SCORE_COLS if c in peak_tl.columns]
            peak_tl["_MaxScore"] = peak_tl[avail_sc].max(axis=1)
            peak_tl = peak_tl.sort_values("_MaxScore", ascending=False).reset_index(drop=True)

            # Display columns
            live_disp_cols = ["Ticker", "Price", "RunUp", "REL_VOL"] + avail_sc
            live_disp_cols = [c for c in live_disp_cols if c in peak_tl.columns]
            live_tbl = peak_tl[live_disp_cols].copy()

            def _color_score(val):
                try:
                    v = float(val)
                except (TypeError, ValueError):
                    return ""
                if v >= 80:   return "background-color: #5a1a1a; color: #ffaaaa"
                if v >= 60:   return "background-color: #5a3a00; color: #ffcc80"
                if v >= 45:   return "background-color: #4a4a00; color: #ffff80"
                return ""

            # Round all numeric display columns
            cols_2dp       = avail_sc + ["Price"]
            cols_2dp_extra = ["RunUp", "REL_VOL"]
            for col in cols_2dp + cols_2dp_extra:
                if col in live_tbl.columns:
                    live_tbl[col] = pd.to_numeric(live_tbl[col], errors="coerce").round(2)

            score_subset = [c for c in avail_sc if c in live_tbl.columns]
            fmt_live = {c: "{:.2f}" for c in cols_2dp + cols_2dp_extra if c in live_tbl.columns}
            styled_live = live_tbl.style.map(_color_score, subset=score_subset).format(fmt_live, na_rep="-")
            st.dataframe(styled_live, use_container_width=True)
            st.caption(f"סה\"כ {len(live_tbl)} מניות היום • ממוין לפי ציון מקסימלי ↓")
    else:
        st.info("📭 timeline_live לא זמין.")

    st.divider()
    st.markdown("## 📊 ניתוח היסטורי")
    st.caption("על בסיס נתוני Post Analysis — מניות עם תוצאה ידועה (TP10_Hit)")

    with st.spinner("טוען נתונים..."):
        df = _cached_post_analysis()

    if df.empty:
        st.info("📭 אין נתוני Post Analysis עדיין.")
        return

    # Numeric coercion for all score columns + outcome columns
    for col in SCORE_COLS + ["TP10_Hit", "MaxDrop%"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Working set: rows with TP10_Hit resolved
    has_outcome = df[df["TP10_Hit"].notna()].copy()

    # ── Section 1: Performance table ──────────────────────────────────────────
    st.subheader("📋 סקשן 1 — טבלת ביצועים")

    perf_rows = []
    for sc in SCORE_COLS:
        if sc not in df.columns:
            continue
        subset = has_outcome[has_outcome[sc] >= 60]
        n = len(subset)
        if n == 0:
            perf_rows.append({"Score": sc, "n (≥60)": 0, "Win Rate": None,
                               "Avg MaxDrop% (winners)": None, "Best Bucket": "—"})
            continue
        win_rate = subset["TP10_Hit"].mean()
        winners  = subset[subset["TP10_Hit"] == 1]
        avg_drop = winners["MaxDrop%"].mean() if not winners.empty else None

        # Best bucket: 10-point ranges that have the highest TP10 rate (min 3 samples)
        subset2 = has_outcome[has_outcome[sc].notna()].copy()
        subset2["_bucket"] = (subset2[sc] // 10 * 10).astype(int)
        bkt = (subset2.groupby("_bucket")
               .agg(n_bkt=("TP10_Hit", "count"), wr_bkt=("TP10_Hit", "mean"))
               .reset_index())
        bkt = bkt[bkt["n_bkt"] >= 3]
        if not bkt.empty:
            best = bkt.loc[bkt["wr_bkt"].idxmax()]
            best_label = f"{int(best['_bucket'])}-{int(best['_bucket'])+10} ({best['wr_bkt']*100:.0f}%, n={int(best['n_bkt'])})"
        else:
            best_label = "—"

        perf_rows.append({
            "Score":                    sc,
            "n (≥60)":                  n,
            "Win Rate":                 round(win_rate * 100, 1),
            "Avg MaxDrop% (winners)":   round(avg_drop, 1) if avg_drop is not None else None,
            "Best Bucket":              best_label,
        })

    perf_df = pd.DataFrame(perf_rows).dropna(subset=["Win Rate"]).sort_values("Win Rate", ascending=False)
    _perf_fmt = {"Win Rate": "{:.1f}", "Avg MaxDrop% (winners)": "{:.1f}", "n (≥60)": "{:.0f}"}
    st.dataframe(
        perf_df.reset_index(drop=True).style.format(_perf_fmt, na_rep="-"),
        use_container_width=True
    )

    st.divider()

    # ── Section 2: Win Rate by bucket (line chart) ────────────────────────────
    st.subheader("📈 סקשן 2 — Win Rate לפי Score Bucket")

    bucket_data = {}
    for sc in SCORE_COLS:
        if sc not in has_outcome.columns:
            continue
        tmp = has_outcome[has_outcome[sc].notna()].copy()
        tmp["_bucket"] = (tmp[sc] // 10 * 10).astype(int)
        bkt = (tmp.groupby("_bucket")
               .agg(wr=("TP10_Hit", "mean"), n=("TP10_Hit", "count"))
               .reset_index())
        bkt = bkt[bkt["n"] >= 3]
        bucket_data[sc] = dict(zip(bkt["_bucket"], bkt["wr"] * 100))

    all_buckets = sorted(set(b for v in bucket_data.values() for b in v))
    if all_buckets:
        chart_df = pd.DataFrame(
            {sc: [bucket_data[sc].get(b, None) for b in all_buckets] for sc in bucket_data},
            index=[f"{b}-{b+10}" for b in all_buckets]
        )
        st.line_chart(chart_df, use_container_width=True)
    else:
        st.info("אין מספיק נתונים לגרף (נדרשים לפחות 3 מניות לכל bucket).")

    st.divider()

    # ── Shared helpers for sections 3a & 3b ───────────────────────────────────
    sc3_all = df.copy()
    for col in SCORE_COLS + ["TP10_Hit", "SL7_Hit_D1", "MaxDrop%"]:
        if col in sc3_all.columns:
            sc3_all[col] = pd.to_numeric(sc3_all[col], errors="coerce")

    def _get_status(row):
        if row.get("TP10_Hit") == 1:   return "✅ TP10"
        if row.get("SL7_Hit_D1") == 1: return "❌ SL"
        return "⏳ Pending"

    sc3_all["Status"] = sc3_all.apply(_get_status, axis=1)

    n_total   = len(sc3_all)
    n_tp10    = int((sc3_all["Status"] == "✅ TP10").sum())
    n_sl      = int((sc3_all["Status"] == "❌ SL").sum())
    n_pending = int((sc3_all["Status"] == "⏳ Pending").sum())
    n_closed  = n_tp10 + n_sl
    win_rate  = round(n_tp10 / n_closed * 100, 1) if n_closed > 0 else 0

    sc3_score_cols = [c for c in SCORE_COLS if c in sc3_all.columns]
    base_disp_cols = ["Ticker", "ScanDate", "Status"] + sc3_score_cols + ["MaxDrop%", "TP10_Hit"]
    base_disp_cols = [c for c in base_disp_cols if c in sc3_all.columns]

    def _row_style(row):
        status = str(row.get("Status", ""))
        if "✅" in status:   bg, fg = "#1a4a1a", "#80ff80"
        elif "❌" in status: bg, fg = "#4a1a1a", "#ff8080"
        elif "⏳" in status: bg, fg = "#3a3a10", "#ffff99"
        else:                bg, fg = "", ""
        style = f"background-color: {bg}; color: {fg}" if bg else ""
        return [style if c not in sc3_score_cols else "" for c in row.index]

    def _score_cell(val):
        try: v = float(val)
        except (TypeError, ValueError): return "color: #888888"
        if v >= 80: return "background-color: #5a1a1a; color: #ffaaaa"
        if v >= 60: return "background-color: #5a3a00; color: #ffcc80"
        if v >= 45: return "background-color: #4a4a00; color: #ffff80"
        return "background-color: #2a2a2a; color: #888888"

    fmt_sc3 = {c: "{:.2f}" for c in sc3_score_cols}

    # ── Section 3a: All stocks ─────────────────────────────────────────────────
    st.subheader("📋 סקשן 3א — כל המניות עם ציונים")
    st.markdown(
        f"**סה\"כ {n_total} מניות** | ✅ {n_tp10} TP10 | ❌ {n_sl} SL | "
        f"⏳ {n_pending} Pending | **Win Rate: {win_rate}%**"
    )

    tbl3a = (sc3_all[base_disp_cols]
             .sort_values("ScanDate", ascending=False)
             .reset_index(drop=True))
    for col in sc3_score_cols:
        tbl3a[col] = pd.to_numeric(tbl3a[col], errors="coerce").round(2)
    if "MaxDrop%" in tbl3a.columns:
        tbl3a["MaxDrop%"] = pd.to_numeric(tbl3a["MaxDrop%"], errors="coerce").round(1)
    if "TP10_Hit" in tbl3a.columns:
        tbl3a["TP10_Hit"] = pd.to_numeric(tbl3a["TP10_Hit"], errors="coerce").round(0).astype("Int64")

    _fmt3a = {**fmt_sc3, **({
        "MaxDrop%": "{:.1f}",
        "TP10_Hit": "{:.0f}",
    })}
    st.dataframe(
        tbl3a.style
             .apply(_row_style, axis=1)
             .map(_score_cell, subset=sc3_score_cols)
             .format(_fmt3a, na_rep="-"),
        use_container_width=True
    )

    st.divider()

    # ── Section 3b: Closed stocks — performance by score ──────────────────────
    st.subheader("🎯 סקשן 3ב — השוואת ביצועים לפי ציון")
    st.caption("רק מניות סגורות (TP10_Hit ידוע) — ממוין לפי Win Rate")

    closed = sc3_all[sc3_all["Status"] != "⏳ Pending"].copy()
    if closed.empty:
        st.info("אין מניות סגורות עדיין.")
    else:
        # Per-score Win Rate table
        wr_rows = []
        for sc in SCORE_COLS:
            if sc not in closed.columns: continue
            sub = closed[closed[sc].notna() & (closed[sc] >= 60)]
            if sub.empty: continue
            wr = sub["TP10_Hit"].mean()
            wr_rows.append({
                "ציון":          sc,
                "n (≥60)":       len(sub),
                "Win Rate %":    round(wr * 100, 1),
                "TP10":          int((sub["TP10_Hit"] == 1).sum()),
                "SL":            int((sub["TP10_Hit"] == 0).sum()),
            })
        if wr_rows:
            wr_df = pd.DataFrame(wr_rows).sort_values("Win Rate %", ascending=False).reset_index(drop=True)
            def _wr_color(val):
                try: v = float(val)
                except: return ""
                if v >= 70: return "background-color: #1a4a1a; color: #80ff80"
                if v >= 50: return "background-color: #3a3a10; color: #ffff80"
                return "background-color: #4a1a1a; color: #ff8080"
            st.dataframe(
                wr_df.style.map(_wr_color, subset=["Win Rate %"]),
                use_container_width=True
            )

        st.caption(f"סה\"כ {len(closed)} מניות סגורות מתוך {n_total}")

        # Closed stocks detail table — wins first, then losses
        tbl3b = (closed[base_disp_cols]
                 .sort_values(["TP10_Hit", "ScanDate"], ascending=[False, False])
                 .reset_index(drop=True))
        for col in sc3_score_cols:
            tbl3b[col] = pd.to_numeric(tbl3b[col], errors="coerce").round(2)
        if "MaxDrop%" in tbl3b.columns:
            tbl3b["MaxDrop%"] = pd.to_numeric(tbl3b["MaxDrop%"], errors="coerce").round(1)
        if "TP10_Hit" in tbl3b.columns:
            tbl3b["TP10_Hit"] = pd.to_numeric(tbl3b["TP10_Hit"], errors="coerce").round(0).astype("Int64")

        _fmt3b = {**fmt_sc3, **({
            "MaxDrop%": "{:.1f}",
            "TP10_Hit": "{:.0f}",
        })}
        st.dataframe(
            tbl3b.style
                 .apply(_row_style, axis=1)
                 .map(_score_cell, subset=sc3_score_cols)
                 .format(_fmt3b, na_rep="-"),
            use_container_width=True
        )

    st.divider()

    # ── Section 4: Who was most right ─────────────────────────────────────────
    st.subheader("🏆 סקשן 4 — מי היה הכי צודק על כל מניה")
    st.caption("לכל מניה עם TP10_Hit ידוע — איזה ציון נתן לה את הציון הגבוה ביותר?")

    avail_scores = [c for c in SCORE_COLS if c in has_outcome.columns]
    if avail_scores:
        tmp = has_outcome[avail_scores + ["TP10_Hit"]].copy().dropna(subset=avail_scores, how="all")
        tmp["_highest_score"] = tmp[avail_scores].idxmax(axis=1)

        winners_sc = tmp[tmp["TP10_Hit"] == 1]["_highest_score"].value_counts().rename("Wins (TP10=1)")
        losers_sc  = tmp[tmp["TP10_Hit"] == 0]["_highest_score"].value_counts().rename("Losses (TP10=0)")

        rank_df = pd.concat([winners_sc, losers_sc], axis=1).fillna(0).astype(int)
        rank_df["Total"] = rank_df.get("Wins (TP10=1)", 0) + rank_df.get("Losses (TP10=0)", 0)
        rank_df["Win% when highest"] = (
            rank_df.get("Wins (TP10=1)", 0) / rank_df["Total"] * 100
        ).round(1)
        rank_df = rank_df.sort_values("Wins (TP10=1)", ascending=False)
        rank_df.index.name = "Score"
        st.dataframe(
            rank_df.style.format({"Win% when highest": "{:.1f}"}, na_rep="-"),
            use_container_width=True
        )
    else:
        st.info("אין עמודות ציון זמינות.")


def dashboard_home_page():
    now_peru  = datetime.now(PERU_TZ)
    today_str = now_peru.strftime("%Y-%m-%d")
    market_open = now_peru.weekday() < 5 and 8*60+30 <= now_peru.hour*60+now_peru.minute <= 15*60

    st.title("🏠 RidingHigh Pro")

    # ── Load data early (all cached — no extra Sheets hits) ───────────────────
    tl = _cached_tl_today()
    lt = _cached_live_trades()

    today_tl = pd.DataFrame()
    if not tl.empty and "Date" in tl.columns:
        today_tl = tl[tl["Date"] == today_str].copy()
        for col in ["Score", "Score_B", "Score_C", "Score_D",
                    "Score_E", "Score_F", "Score_G", "Score_H", "Score_I", "RunUp"]:
            if col in today_tl.columns:
                today_tl[col] = pd.to_numeric(today_tl[col], errors="coerce")

    today_lt = pd.DataFrame()
    if not lt.empty and "EntryTime" in lt.columns:
        today_lt = lt[lt["EntryTime"].astype(str).str.startswith(today_str)].copy()

    # ── Section 1: System Status ───────────────────────────────────────────────
    st.subheader("🖥️ סטטוס מערכת")

    # Last Scan: session_state → timeline_live fallback → "—"
    ls_str = "—"
    for key in ("last_scan_time", "last_scan"):
        val = st.session_state.get(key)
        if val is not None:
            try:
                ls_str = val.strftime("%H:%M")
            except Exception:
                ls_str = str(val)[:5]
            break
    if ls_str == "—" and not today_tl.empty and "ScanTime" in today_tl.columns:
        last_tl = today_tl["ScanTime"].dropna().iloc[-1] if len(today_tl) > 0 else None
        if last_tl:
            ls_str = str(last_tl)[:5]   # "HH:MM"

    col_time, col_market, col_scan = st.columns(3)
    col_time.metric("🕐 שעה (Peru)", now_peru.strftime("%H:%M"), delta=today_str)
    if market_open:
        col_market.success("🟢 שוק פתוח")
    else:
        col_market.error("🔴 שוק סגור")
    col_scan.metric("🔍 Last Scan", ls_str)

    with st.expander("🔍 Quick Health Check", expanded=False):
        if st.button("▶ הרץ בדיקה", key="home_hc_btn"):
            with st.spinner("בודק מערכת..."):
                import health_check as _hc
                lines = _hc.run(quiet=True)
            for line in lines:
                st.text(line)

    st.divider()

    # ── Section 2: Today ──────────────────────────────────────────────────────
    st.subheader("📡 היום")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔭 סריקה**")
        if not today_tl.empty and "Ticker" in today_tl.columns:
            n_tickers = today_tl["Ticker"].nunique()
            peak = (today_tl.sort_values("Score", ascending=False)
                            .drop_duplicates("Ticker")) if "Score" in today_tl.columns else today_tl
            scores = pd.to_numeric(peak.get("Score", pd.Series(dtype=float)), errors="coerce")
            critical = int((scores >= 85).sum())
            high     = int((scores >= 70).sum())
            st.metric("מניות שנסרקו", n_tickers)
            st.metric("Critical ≥85", critical, delta=f"High ≥70: {high}")
        else:
            st.info("אין נתוני סריקה להיום")

    with col2:
        st.markdown("**⚡ Live Trades**")
        if not lt.empty and "Status" in lt.columns:
            # All-time
            tp_all = int((lt["Status"] == "TP10").sum())
            sl_all = int((lt["Status"] == "SL").sum())
            cl_all = tp_all + sl_all
            wr_all = f"{tp_all/cl_all*100:.0f}%" if cl_all > 0 else "—"
            # Today
            if not today_lt.empty and "Status" in today_lt.columns:
                tp_td = int((today_lt["Status"] == "TP10").sum())
                sl_td = int((today_lt["Status"] == "SL").sum())
                cl_td = tp_td + sl_td
                today_str_disp = f"היום: {tp_td}/{cl_td}" if cl_td > 0 else "היום: אין"
            else:
                today_str_disp = "היום: אין"
            pending = int((lt["Status"] == "Pending").sum())
            st.metric("Win Rate (כולל)", wr_all, delta=f"TP:{tp_all}  SL:{sl_all}")
            st.caption(f"{today_str_disp}  |  Pending: {pending}")
        else:
            st.info("אין trades")

    with col3:
        st.markdown("**🏆 Top מניה**")
        if not today_tl.empty and "Score" in today_tl.columns and "Ticker" in today_tl.columns:
            peak_all = (today_tl.sort_values("Score", ascending=False)
                                .drop_duplicates("Ticker"))
            if not peak_all.empty:
                top    = peak_all.iloc[0]
                ticker = str(top.get("Ticker", "—"))
                score  = pd.to_numeric(top.get("Score",  0),    errors="coerce")
                price  = pd.to_numeric(top.get("Price",  None), errors="coerce")
                runup  = pd.to_numeric(top.get("RunUp",  None), errors="coerce")
                price_str = f"${price:.2f}" if pd.notna(price) else None
                runup_str = f"RunUp: {runup:.1f}%" if pd.notna(runup) else None
                st.metric(ticker, f"Score {score:.1f}", delta=price_str)
                if runup_str:
                    st.caption(runup_str)
        else:
            st.info("אין נתונים")

    st.divider()

    # ── Section 3: Historical Summary ─────────────────────────────────────────
    st.subheader("📊 סיכום היסטורי")

    df = _cached_post_analysis()
    if not df.empty:
        for col in ["TP10_Hit", "MaxDrop%", "Score"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        total_stocks  = len(df)
        has_outcome   = df[df["TP10_Hit"].notna()] if "TP10_Hit" in df.columns else pd.DataFrame()
        win_rate_hist = f"{has_outcome['TP10_Hit'].mean()*100:.0f}%" if not has_outcome.empty else "—"
        winners       = has_outcome[has_outcome["TP10_Hit"] == 1] if not has_outcome.empty else pd.DataFrame()
        avg_drop      = winners["MaxDrop%"].mean() if not winners.empty and "MaxDrop%" in winners.columns else None
        avg_drop_str  = f"{avg_drop:.1f}%" if avg_drop is not None and pd.notna(avg_drop) else "—"
        best_score    = df["Score"].max() if "Score" in df.columns else None
        best_score_str = f"{best_score:.1f}" if best_score is not None and pd.notna(best_score) else "—"
        n_days        = df["ScanDate"].nunique() if "ScanDate" in df.columns else "?"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎯 Win Rate",           win_rate_hist, delta=f"{len(has_outcome)} עם תוצאה")
        m2.metric("📋 מניות",              total_stocks,  delta=f"{n_days} ימים")
        m3.metric("📉 Avg Drop (winners)", avg_drop_str)
        m4.metric("🏆 Best Score",         best_score_str)
    else:
        st.info("אין נתוני Post Analysis עדיין")

    st.divider()

    # ── Section 4: Quick Navigation ───────────────────────────────────────────
    st.subheader("🧭 ניווט מהיר")
    nav_targets = [
        ("📊 Live Tracker",     "📊 Live Tracker"),
        ("💼 Portfolio",        "💼 Portfolio Tracker"),
        ("⚡ Live Trades",      "⚡ Live Trades"),
        ("🔬 Post Analysis",    "🔬 Post Analysis"),
        ("📊 Score Comparison", "📊 Score Comparison"),
    ]
    nav_cols = st.columns(len(nav_targets))
    for i, (label, target) in enumerate(nav_targets):
        if nav_cols[i].button(label, use_container_width=True, key=f"home_nav_{i}"):
            st.session_state["nav_page"] = target
            st.rerun()


def main():
    _PAGE_NAMES = [
        "🏠 Home",
        "📊 Live Tracker", "💼 Portfolio Tracker", "⚡ Live Trades",
        "🎯 Portfolio Score Tracker", "📅 Daily Summary", "📦 Timeline Archive",
        "🔬 Post Analysis", "📊 Score Comparison",
    ]

    # Session-state key "nav_page" drives the radio (allows Home buttons to switch pages)
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "🏠 Home"

    page = st.sidebar.radio("🧭 Navigation", _PAGE_NAMES, key="nav_page")

    st.sidebar.divider()
    now_peru = datetime.now(PERU_TZ)
    market_open = now_peru.weekday() < 5 and 8*60+30 <= now_peru.hour*60+now_peru.minute <= 15*60
    market_icon = "🟢" if market_open else "🔴"
    st.sidebar.markdown(
        f"🕐 **{now_peru.strftime('%H:%M')} Peru**  \n"
        f"📅 {now_peru.strftime('%Y-%m-%d')}  \n"
        f"{market_icon} {'שוק פתוח' if market_open else 'שוק סגור'}"
    )
    st.sidebar.divider()
    if st.sidebar.button("🔄 Refresh data", help="Clear all caches and reload from Google Sheets"):
        st.cache_data.clear()
        st.rerun()

    if page == "🏠 Home":
        dashboard_home_page()
    elif page == "📊 Live Tracker":
        main_page()
    elif page == "💼 Portfolio Tracker":
        portfolio_tracker_page()
    elif page == "⚡ Live Trades":
        live_trades_page()
    elif page == "📅 Daily Summary":
        daily_summary_page()
    elif page == "📦 Timeline Archive":
        timeline_archive_page()
    elif page == "🎯 Portfolio Score Tracker":
        score_tracker_page()
    elif page == "🔬 Post Analysis":
        post_analysis_page()
    else:
        score_comparison_page()

if __name__ == "__main__":
    main()
