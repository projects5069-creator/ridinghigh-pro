#!/usr/bin/env python3
"""
RidingHigh Pro v14.6 - Score 7 Metrics
- Timeline Archive exported as proper grid (pivot) per date
- New "Analysis Export" with Timeline Summary for AI analysis
- Full export unchanged except Timeline Archive fix
"""

import streamlit as st
import os

# ──────────────────────────────────────────────────────────────
# Streamlit Cloud secrets bridge (Issue #9 + #N21)
# Copy required keys from st.secrets → os.environ so that downstream
# modules (alpaca_provider, gspread auth, etc.) which read from
# os.environ.get() find their credentials in Cloud deployment too.
# Idempotent: silently skips when running locally (st.secrets empty).
# ──────────────────────────────────────────────────────────────
try:
    _SECRETS_BRIDGE_KEYS = [
        "ALPACA_API_KEY_ID",
        "ALPACA_SECRET_KEY",
        "ALPACA_BASE_URL",
        "ALPACA_DATA_URL",
        "ALPACA_PAPER",
        "DATA_PROVIDER",
    ]
    for _k in _SECRETS_BRIDGE_KEYS:
        if _k in st.secrets and not os.environ.get(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

import pandas as pd
import math
import time
import plotly.express as px
from finvizfinance.screener.overview import Overview
from datetime import datetime, time as dt_time, timedelta
import pytz
import pytz
from data_logger import DataLogger
from ta.momentum import RSIIndicator
from data_provider import get_data_provider, get_fundamentals_provider
from ta.volatility import AverageTrueRange
import shutil
from gsheets_sync import save_snapshot_to_sheets, save_timeline_to_sheets, save_portfolio_to_sheets, load_portfolio_from_sheets, load_timeline_dates_from_sheets, load_timeline_from_sheets
import sheets_manager
import json
from formulas import (
    calculate_mxv,
    calculate_runup,
    calculate_atrx,
    validate_atrx,
    calculate_gap,
    calculate_vwap_dist,
    calculate_rel_vol,
    calculate_float_pct,
    normalize_mxv,
    normalize_atrx,
)
from auto_scanner import calculate_score
from utils import (
    parse_market_cap,
    parse_volume,
    is_market_hours,
)
from config import (
    MIN_SCORE_DISPLAY,
    CRITICAL_SCORE,
    TRADE_ENTRY_MIN_SCORE,
    POSITION_SIZE_USD,
    TP_THRESHOLD_FRAC,
    SL_THRESHOLD_FRAC,
    DATA_CUTOFF_DATE,
)

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
    
    # parse_market_cap and parse_volume imported from utils

    def get_market_cap_smart(self, ticker, price, finviz_mc=None):
        """Wrapper around utils.get_market_cap_smart that injects dashboard-specific
        callbacks (cache file persistence + history lookup).
        Issue #9 Phase 2 — unified with auto_scanner via utils.py.
        """
        from utils import get_market_cap_smart as _unified_mc

        def _cache_set(t, mc):
            self.market_cap_cache[t] = int(mc)
            self.save_to_cache_file(t, mc)

        market_cap = _unified_mc(
            ticker,
            price=price,
            finviz_mc=finviz_mc,
            shares_cache=self.shares_cache,
            cache_get=self.load_from_cache_file,
            cache_set=_cache_set,
            history_lookup=self.get_from_history_all_days,
        )
        return market_cap
    
    def preload_market_caps(self, finviz_df, progress_callback=None):
        if finviz_df is None or finviz_df.empty:
            return
        
        total = len(finviz_df)
        
        for idx, row in finviz_df.iterrows():
            ticker = row['Ticker']
            
            if progress_callback:
                progress_callback(idx + 1, total, ticker)
            
            finviz_mc = parse_market_cap(row.get('Market Cap', None))
            price = float(row.get('Price', 0))
            
            market_cap = self.get_market_cap_smart(ticker, price, finviz_mc)
            
            time.sleep(0.3)
    
    def analyze_ticker_from_yahoo(self, ticker):
        """Issue #9 Phase 2 — was yfinance, now uses data_provider."""
        try:
            provider = get_data_provider()
            full_hist = provider.get_daily_bars(ticker, days=60)

            if full_hist.empty or len(full_hist) < 2:
                return None

            try:
                fund = get_fundamentals_provider().get_fundamentals(ticker) or {}
            except Exception:
                fund = {}

            current = full_hist.iloc[-1]
            previous = full_hist.iloc[-2]

            price = current['close']
            change = ((current['close'] - previous['close']) / previous['close']) * 100
            volume = current['volume']

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

            if not full_hist.empty and len(full_hist) >= 2:
                try:
                    if len(full_hist) >= 14:
                        rsi_indicator = RSIIndicator(close=full_hist['close'], window=14)
                        rsi_values = rsi_indicator.rsi()
                        if not rsi_values.empty and not pd.isna(rsi_values.iloc[-1]):
                            rsi = rsi_values.iloc[-1]
                except:
                    rsi = 50

                try:
                    if len(full_hist) >= 14:
                        atr_indicator = AverageTrueRange(
                            high=full_hist['high'],
                            low=full_hist['low'],
                            close=full_hist['close'],
                            window=14
                        )
                        atr_values = atr_indicator.average_true_range()
                        if not atr_values.empty and not pd.isna(atr_values.iloc[-1]):
                            atr = atr_values.iloc[-1]
                        else:
                            atr = current['high'] - current['low']
                    else:
                        atr = current['high'] - current['low']
                    atrx = validate_atrx(calculate_atrx(current["high"], current["low"], atr), atr, price)
                except:
                    atr = 0
                    atrx = 0

                try:
                    avg_volume = fund.get('average_volume') or volume
                    if avg_volume > 0:
                        rel_vol = calculate_rel_vol(volume, avg_volume)
                    else:
                        if len(full_hist) >= 20:
                            avg_vol_20 = full_hist['volume'].tail(20).mean()
                        else:
                            avg_vol_20 = full_hist['volume'].mean()
                        rel_vol = calculate_rel_vol(volume, avg_vol_20)
                except:
                    rel_vol = 1.0

                try:
                    if current['open'] > 0:
                        run_up = calculate_runup(price, current['open'])
                except:
                    run_up = 0

                try:
                    gap = calculate_gap(current['open'], previous['close'])
                except:
                    gap = 0

                try:
                    vwap_dist = calculate_vwap_dist(price, current['high'], current['low'])
                except:
                    vwap_dist = 0

                try:
                    high_today = current['high']
                    price_to_high = ((price - high_today) / high_today) * 100 if high_today > 0 else 0
                except:
                    price_to_high = 0

                try:
                    high_52w = float(full_hist['high'].max())
                    price_to_52w_high = ((price - high_52w) / high_52w) * 100 if high_52w > 0 else 0
                except:
                    price_to_52w_high = 0

                if shares_outstanding == 0:
                    try:
                        shares_outstanding = fund.get('shares_outstanding') or 0
                        if shares_outstanding == 0:
                            shares_outstanding = int(market_cap / price) if price > 0 else 0
                    except:
                        shares_outstanding = int(market_cap / price) if price > 0 else 0

                try:
                    float_shares = fund.get('float_shares') or 0
                    float_pct = calculate_float_pct(float_shares, shares_outstanding)
                except:
                    float_pct = 0

            mxv = calculate_mxv(market_cap, price, volume)

            try:
                change = ((price - previous['close']) / previous['close']) * 100 if previous['close'] > 0 else 0
            except:
                change = 0
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
                'change': change,
            }

            score = calculate_score(metrics)
            
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
            
            volume = parse_volume(finviz_row.get('Volume', None))
            if volume is None or volume == 0:
                return None
            
            finviz_mc = parse_market_cap(finviz_row.get('Market Cap', None))
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
            
            # Issue #9 Phase 2 — was yfinance
            try:
                provider = get_data_provider()
                hist = provider.get_daily_bars(ticker, days=60)

                if not hist.empty and len(hist) >= 2:
                    try:
                        fund = get_fundamentals_provider().get_fundamentals(ticker) or {}
                    except Exception:
                        fund = {}

                    current = hist.iloc[-1]
                    previous = hist.iloc[-2]

                    try:
                        if len(hist) >= 14:
                            rsi_indicator = RSIIndicator(close=hist['close'], window=14)
                            rsi_values = rsi_indicator.rsi()
                            if not rsi_values.empty and not pd.isna(rsi_values.iloc[-1]):
                                rsi = rsi_values.iloc[-1]
                    except:
                        rsi = 50

                    try:
                        if len(hist) >= 14:
                            atr_indicator = AverageTrueRange(
                                high=hist['high'],
                                low=hist['low'],
                                close=hist['close'],
                                window=14
                            )
                            atr_values = atr_indicator.average_true_range()
                            if not atr_values.empty and not pd.isna(atr_values.iloc[-1]):
                                atr = atr_values.iloc[-1]
                            else:
                                atr = current['high'] - current['low']
                        else:
                            atr = current['high'] - current['low']
                        atrx = validate_atrx(calculate_atrx(current["high"], current["low"], atr), atr, price)
                    except:
                        atr = 0
                        atrx = 0

                    try:
                        avg_volume = fund.get('average_volume') or volume
                        if avg_volume > 0:
                            rel_vol = calculate_rel_vol(volume, avg_volume)
                        else:
                            if len(hist) >= 20:
                                avg_vol_20 = hist['volume'].tail(20).mean()
                            else:
                                avg_vol_20 = hist['volume'].mean()
                            rel_vol = calculate_rel_vol(volume, avg_vol_20)
                    except:
                        rel_vol = 1.0

                    try:
                        if current['open'] > 0:
                            run_up = calculate_runup(price, current['open'])
                    except:
                        run_up = 0

                    try:
                        gap = calculate_gap(current['open'], previous['close'])
                    except:
                        gap = 0

                    try:
                        vwap_dist = calculate_vwap_dist(price, current['high'], current['low'])
                    except:
                        vwap_dist = 0

                    try:
                        high_today = current['high']
                        price_to_high = ((price - high_today) / high_today) * 100 if high_today > 0 else 0
                    except:
                        price_to_high = 0

                    try:
                        high_52w = float(hist['high'].max())
                        price_to_52w_high = ((price - high_52w) / high_52w) * 100 if high_52w > 0 else 0
                    except:
                        price_to_52w_high = 0

                    if shares_outstanding == 0:
                        try:
                            shares_outstanding = fund.get('shares_outstanding') or 0
                            if shares_outstanding == 0:
                                shares_outstanding = int(market_cap / price) if price > 0 else 0
                        except:
                            shares_outstanding = int(market_cap / price) if price > 0 else 0

                    try:
                        float_shares = fund.get('float_shares') or 0
                        float_pct = calculate_float_pct(float_shares, shares_outstanding)
                    except:
                        float_pct = 0
            
            except:
                if shares_outstanding == 0:
                    shares_outstanding = int(market_cap / price) if price > 0 else 0
            
            mxv = calculate_mxv(market_cap, price, volume)

            try:
                change = ((price - previous['Close']) / previous['Close']) * 100 if previous['Close'] > 0 else 0
            except:
                change = 0
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
                'change': change,
            }

            score = calculate_score(metrics)
            
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
        
        high_score_stocks = [r for r in results if r['Score'] >= MIN_SCORE_DISPLAY]
        
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
            
            # Issue #9 Phase 2 — was yfinance
            provider = get_data_provider()
            for idx, row in df.iterrows():
                ticker = row['Ticker']
                buy_price = row['BuyPrice']

                try:
                    bar = provider.get_latest_bar(ticker)

                    if bar:
                        current_price = float(bar['close'])
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

# _get_gc: use sheets_manager._get_gc() (supports st.secrets + env var + local file)
def _get_gc():
    return sheets_manager._get_gc()

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
        df = pd.DataFrame(data[1:], columns=data[0])
        if "ScanTime" in df.columns:
            df["ScanTime"] = df["ScanTime"].astype(str).str.zfill(5)
        return df
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
        df = pd.DataFrame(data[1:], columns=data[0])
        if "ScanTime" in df.columns:
            df["ScanTime"] = df["ScanTime"].astype(str).str.zfill(5)
        return df
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
def _cached_ticker_follow_up() -> pd.DataFrame:
    """Load ticker_follow_up sheet. Cached 60s.
    Issue #39 — minute-by-minute D1-D3 follow-up data per ticker.
    """
    try:
        gc = sheets_manager._get_gc()
        if not gc:
            return pd.DataFrame()
        ws = sheets_manager.get_worksheet("ticker_follow_up", gc=gc)
        if not ws:
            return pd.DataFrame()
        data = ws.get_all_values()
        if len(data) <= 1:
            return pd.DataFrame()
        return pd.DataFrame(data[1:], columns=data[0])
    except Exception:
        return pd.DataFrame()


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

# is_market_hours imported from utils

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

        time_above_60 = int((scores >= MIN_SCORE_DISPLAY).sum())

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
            critical = len([r for r in results if r['Score'] >= CRITICAL_SCORE])
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
                'EntryScore': f"{entry_s:.2f}" if r['Score'] >= MIN_SCORE_DISPLAY else "—",
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
            if score >= CRITICAL_SCORE:
                return ['background-color: #800020; color: white; font-weight: bold'] * len(row)
            elif score >= MIN_SCORE_DISPLAY:
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
                if v >= MIN_SCORE_DISPLAY:
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
                if score >= CRITICAL_SCORE:
                    return 'background-color: #800020; color: white; font-weight: bold'
                elif score >= MIN_SCORE_DISPLAY:
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
            if score >= CRITICAL_SCORE:
                return ['background-color: #800020; color: white; font-weight: bold'] * len(row)
            elif score >= MIN_SCORE_DISPLAY:
                return ['background-color: #cc0000; color: white'] * len(row)
            elif score >= 40:
                return ['background-color: #ff6600; color: white'] * len(row)
            else:
                return ['background-color: #ffcc00; color: black'] * len(row)
        except:
            return [''] * len(row)
    
    METRIC_COLS = [
        "Ticker",
        "Price", "Volume", "MarketCap", "Change",
        "Score",
        "MxV", "RunUp", "REL_VOL", "RSI", "ATRX", "Gap",
        "TypicalPriceDist", "PriceToHigh", "PriceTo52WHigh", "Float%",
        "Open_price", "PrevClose", "High_today", "Low_today",
        "TypicalPrice", "ATR14_raw", "Week52High",
        "SharesOutstanding", "AvgVolume", "FloatShares",
    ]
    display_cols = [c for c in METRIC_COLS if c in df.columns]
    df = df[display_cols].copy()

    for col in df.columns:
        if col != "Ticker":
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.sort_values("Score", ascending=False, ignore_index=True) if "Score" in df.columns else df

    # Column-specific format dict (rules: Score=2dp, MxV=0dp int, %=1dp, REL_VOL=1dp, others=2dp)
    _fmt_map = {
        "Score":              "{:.2f}",
        "Price":              "{:.2f}",
        "Volume":             "{:,.0f}",
        "MarketCap":          "{:,.0f}",
        "Change":             "{:.1f}",
        "MxV":                "{:.0f}",
        "RunUp":              "{:.1f}",
        "REL_VOL":            "{:.1f}",
        "RSI":                "{:.1f}",
        "ATRX":               "{:.1f}",
        "Gap":                "{:.1f}",
        "TypicalPriceDist":   "{:.1f}",
        "PriceToHigh":        "{:.2f}",
        "PriceTo52WHigh":     "{:.2f}",
        "Float%":             "{:.1f}",
        "Open_price":         "{:.2f}",
        "PrevClose":          "{:.2f}",
        "High_today":         "{:.2f}",
        "Low_today":          "{:.2f}",
        "TypicalPrice":       "{:.2f}",
        "ATR14_raw":          "{:.4f}",
        "Week52High":         "{:.2f}",
        "SharesOutstanding":  "{:,.0f}",
        "AvgVolume":          "{:,.0f}",
        "FloatShares":        "{:,.0f}",
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
    st.caption("Minute-by-minute data per ticker — D0 scans + D1-D3 follow-up + D1-D5 OHLC")
    system_health_bar()

    try:
        tl_df = _cached_timeline_live()
        fu_df = _cached_ticker_follow_up()
        pa_df = _cached_post_analysis()
        if tl_df.empty:
            st.warning("⚠️ No timeline data yet")
            return
        dates = sorted(tl_df["Date"].unique().tolist(), reverse=True)
    except Exception as e:
        st.error(f"Error: {e}")
        return

    if not dates:
        st.warning("⚠️ No timeline data yet")
        return

    # Controls
    col_date, col_ticker = st.columns([1, 2])
    with col_date:
        selected_date = st.selectbox("📆 Date", dates, index=0)

    day_df = tl_df[tl_df["Date"] == selected_date].copy()
    tickers_today = sorted(day_df["Ticker"].unique().tolist()) if "Ticker" in day_df.columns else []

    with col_ticker:
        options = ["— All tickers (overview) —"] + tickers_today
        selected_ticker = st.selectbox(f"🎯 Ticker ({len(tickers_today)} available)", options, index=0)

    # ── Case A: no ticker → pivot overview ────────────────────────────────────
    if selected_ticker == "— All tickers (overview) —":
        st.subheader(f"All tickers — {selected_date}")

        day_df["Score"] = pd.to_numeric(day_df.get("Score", 0), errors="coerce")
        if "ScanTime" in day_df.columns:
            pivot = day_df.pivot_table(index="Ticker", columns="ScanTime", values="Score", aggfunc="last")
            pivot = pivot[sorted(pivot.columns, reverse=True)].round(2)
        else:
            pivot = day_df.set_index("Ticker") if "Ticker" in day_df.columns else day_df

        if pivot.empty:
            st.error("No data for this date")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Stocks Tracked", len(pivot))
        with col2:
            st.metric("Time Points", len(pivot.columns))

        def color_score(val):
            try:
                score = float(val)
                if score >= CRITICAL_SCORE:
                    return 'background-color: #800020; color: white; font-weight: bold'
                elif score >= MIN_SCORE_DISPLAY:
                    return 'background-color: #cc0000; color: white'
                elif score >= 50:
                    return 'background-color: #ff6600; color: white'
                else:
                    return 'background-color: #ffcc00; color: black'
            except:
                return ''

        styled = pivot.style.map(color_score).format("{:.2f}")
        st.dataframe(styled, use_container_width=True, height=600)

        csv = pivot.to_csv()
        st.download_button("📥 Download CSV", csv, f"timeline_{selected_date}.csv", "text/csv")
        return

    # ── Case B: specific ticker → 3-section detail view ───────────────────────
    ticker = selected_ticker
    st.subheader(f"{ticker} — Full detail")

    _numeric_cols = ["Price", "Volume", "MarketCap", "Score", "MxV", "RunUp", "REL_VOL",
                     "Change", "RSI", "ATRX", "Gap", "TypicalPriceDist", "PriceToHigh",
                     "PriceTo52WHigh", "Float%", "Open_price", "PrevClose", "High_today",
                     "Low_today", "TypicalPrice", "ATR14_raw", "Week52High",
                     "SharesOutstanding", "AvgVolume", "FloatShares"]

    # ── Section 1: D0 scans ──────────────────────────────────────────────────
    st.markdown(f"### D0 — Scan day ({selected_date})")
    st.caption("Minute-by-minute scans during market hours")

    t_df = day_df[day_df["Ticker"] == ticker].copy()
    if not t_df.empty:
        if "ScanTime" in t_df.columns:
            t_df = t_df.sort_values("ScanTime", ascending=False).reset_index(drop=True)
        for col in _numeric_cols:
            if col in t_df.columns:
                t_df[col] = pd.to_numeric(t_df[col], errors='coerce')
        st.metric("Scans today", len(t_df))
        st.dataframe(t_df, use_container_width=True, height=300)
    else:
        st.info(f"No D0 data for {ticker} on {selected_date}")

    # ── Section 2: D1-D3 follow-up ──────────────────────────────────────────
    st.markdown("### D1-D3 — Follow-up tracking")
    st.caption("Post-pump minute-by-minute tracking for 3 trading days")

    if fu_df.empty or "Ticker" not in fu_df.columns:
        st.info("No follow-up data yet (populates next trading day)")
    else:
        fu_ticker = fu_df[(fu_df["Ticker"] == ticker) &
                          (fu_df["ScanDate"].astype(str).str[:10] == selected_date)].copy()
        if fu_ticker.empty:
            st.info(f"No follow-up rows for {ticker} scanned on {selected_date} yet")
        else:
            for col in _numeric_cols + ["FollowDay"]:
                if col in fu_ticker.columns:
                    fu_ticker[col] = pd.to_numeric(fu_ticker[col], errors='coerce')
            fu_ticker = fu_ticker.sort_values(["FollowDay", "Date", "ScanTime"],
                                              ascending=[True, True, False])
            c1, c2, c3 = st.columns(3)
            for day, col_ph in zip([1, 2, 3], [c1, c2, c3]):
                day_rows = fu_ticker[fu_ticker["FollowDay"] == day]
                col_ph.metric(f"D{day} rows", len(day_rows))
            st.dataframe(fu_ticker, use_container_width=True, height=400)

    # ── Section 3: D1-D5 OHLC summary ──────────────────────────────────────
    st.markdown("### D1-D5 OHLC summary")
    st.caption("Daily OHLC from post_analysis")

    if pa_df.empty or "Ticker" not in pa_df.columns:
        st.info("No post_analysis data yet")
    else:
        pa_ticker = pa_df[(pa_df["Ticker"] == ticker) &
                          (pa_df["ScanDate"].astype(str).str[:10] == selected_date)].copy()
        if pa_ticker.empty:
            st.info(f"No post_analysis entry for {ticker} on {selected_date}")
        else:
            ohlc_cols = [c for c in pa_ticker.columns if
                         c.startswith(("D0_", "D1_", "D2_", "D3_", "D4_", "D5_")) or
                         c in ("Ticker", "ScanDate", "ScanPrice", "MaxDrop%", "TP10_Hit",
                               "TP15_Hit", "TP20_Hit", "BestDay")]
            show_cols = [c for c in ohlc_cols if c in pa_ticker.columns]
            if show_cols:
                st.dataframe(pa_ticker[show_cols], use_container_width=True, height=200)
            else:
                st.dataframe(pa_ticker, use_container_width=True, height=200)

@st.cache_data(ttl=3600)
def _fetch_live_prices(tickers: tuple) -> dict:
    """Fetch latest prices via data_provider. Cached 1 hour.
    Issue #9 Phase 2 — was yfinance batch download.
    Performance note: loops one-at-a-time. ~50ms per ticker via Alpaca.
    For 100 tickers ≈ 5s, but cached 1hr so amortized cost is negligible.
    """
    tickers = list(tickers)
    if not tickers:
        return {}

    from data_provider import get_data_provider
    provider = get_data_provider()
    result = {}
    for ticker in tickers:
        try:
            bar = provider.get_latest_bar(ticker)
            if bar:
                result[ticker] = round(float(bar["close"]), 2)
        except Exception:
            continue
    return result


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

    # Issue #9 Phase 2 — was yfinance batch download per d1_date
    from data_provider import get_data_provider
    from datetime import datetime as _dt
    provider = get_data_provider()
    result = {}
    for d1_date, ticker_scan_pairs in d1_to_tickers.items():
        # Compute days_since_d1 to know how many bars to fetch
        try:
            if isinstance(d1_date, str):
                d1_dt = _dt.strptime(d1_date[:10], "%Y-%m-%d").date()
            else:
                d1_dt = d1_date
            days_back = (_dt.now().date() - d1_dt).days + 5  # buffer for weekends
        except Exception:
            days_back = 30  # safe default

        for ticker, scan_date in ticker_scan_pairs:
            key = f"{ticker}_{scan_date}"
            try:
                hist = provider.get_daily_bars(ticker, days=days_back)
                if hist.empty:
                    continue
                # Filter to >= d1_date (provider returns lowercase columns)
                hist = hist[hist.index >= str(d1_dt)] if hasattr(hist.index, 'astype') else hist
                if hist.empty:
                    continue
                h = round(float(hist["high"].dropna().max()), 2)
                l = round(float(hist["low"].dropna().min()),  2)
                result[key] = {"high": h, "low": l}
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
    POSITION = POSITION_SIZE_USD
    TP_PCT   = TP_THRESHOLD_FRAC   # from config.py
    SL_PCT   = SL_THRESHOLD_FRAC   # from config.py
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
        f"$1,000 short · TP 10% · SL 10% &nbsp;&nbsp;|&nbsp;&nbsp; "
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
    min_score  = MIN_SCORE_DISPLAY

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
        # Issue #9 Phase 2 — was yfinance batch download
        from data_provider import get_data_provider
        provider = get_data_provider()
        tickers = df["Ticker"].unique().tolist()
        try:
            current_price = {}
            for ticker in tickers:
                try:
                    bar = provider.get_latest_bar(ticker)
                    if bar:
                        current_price[ticker] = round(float(bar["close"]), 2)
                except Exception:
                    continue
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

    # ── Dynamic Score section removed (Issue #34 — transitioning to single Score v2) ──

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
            if sd < DATA_CUTOFF_DATE:   # תיעוד score_tracker רק מ-DATA_CUTOFF_DATE
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
                        _tp_price   = round(_scan_price * (1 - TP_THRESHOLD_FRAC), 2)
                        _sl_price   = round(_scan_price * (1 + SL_THRESHOLD_FRAC), 2)
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
    ENTRY_AMOUNT = POSITION_SIZE_USD

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
                if v >= MIN_SCORE_DISPLAY:   return "background-color: #5a3a00; color: #ffcc80"
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
        subset = has_outcome[has_outcome[sc] >= MIN_SCORE_DISPLAY]
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
    for col in SCORE_COLS + ["TP10_Hit", "SL_Hit_D5", "MaxDrop%"]:
        if col in sc3_all.columns:
            sc3_all[col] = pd.to_numeric(sc3_all[col], errors="coerce")

    def _get_status(row):
        if row.get("TP10_Hit") == 1:   return "✅ TP10"
        if row.get("SL_Hit_D5") == 1: return "❌ SL"
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
        if v >= MIN_SCORE_DISPLAY: return "background-color: #5a3a00; color: #ffcc80"
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
            sub = closed[closed[sc].notna() & (closed[sc] >= MIN_SCORE_DISPLAY)]
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
                if v >= TRADE_ENTRY_MIN_SCORE: return "background-color: #1a4a1a; color: #80ff80"
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


def system_overview_page():
    """🖥️ דף מבט-על מקיף — ארכיטקטורה, צינור נתונים, ציון, בריאות, runbook.
    
    כל סעיף ב-expander לקריאה נקייה.
    מקור: PK v2.0 (docs/RidingHigh_Pro_PK_v2.md) + קוד חי.
    """
    now_peru = datetime.now(PERU_TZ)
    today_str = now_peru.strftime("%Y-%m-%d")
    market_open = now_peru.weekday() < 5 and 8*60+30 <= now_peru.hour*60+now_peru.minute <= 15*60

    st.title("🖥️ סטטוס מערכת — מבט כולל")

    # ── Top bar: live status ────────────────────────────────────────────────
    sb1, sb2, sb3, sb4 = st.columns(4)
    sb1.metric("🕐 Peru", now_peru.strftime("%H:%M"))
    if market_open:
        sb2.success("🟢 שוק פתוח")
    else:
        sb2.error("🔴 שוק סגור")
    sb3.metric("📅 תאריך", today_str)
    sb4.metric("📍 Owner", "Lima, Peru")

    st.caption(
        f"מסמך מקור: `docs/RidingHigh_Pro_PK_v2.md` (PK v2.0, 36 sections + 4 appendices) · "
        f"עודכן: 2026-05-02"
    )

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # 1. TL;DR — תמיד פתוח
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("### ⚡ TL;DR")
    st.info(
        "**RidingHigh Pro** — מערכת אוטומטית לחקר shorts במניות אמריקאיות. "
        "סורקת FINVIZ כל דקה, מנקדת 0-100 לפי 7 metrics, "
        "מסמלצת short trade של $1,000 (TP=−10%, SL=+10%), עוקבת 5 ימי מסחר. "
        "**שלב 1: איסוף נתונים, ללא כסף אמיתי.**"
    )

    # Load data once for all sections
    pa_df = _cached_post_analysis()
    v2_records = 0
    v2_days = 0
    v2_winrate = None
    if not pa_df.empty:
        for col in ["TP10_Hit", "MaxDrop%", "Score"]:
            if col in pa_df.columns:
                pa_df[col] = pd.to_numeric(pa_df[col], errors="coerce")
        if "score_version" in pa_df.columns:
            v2_df = pa_df[pa_df["score_version"] == "v2"].copy()
            v2_records = len(v2_df)
            if "ScanDate" in v2_df.columns:
                v2_days = v2_df["ScanDate"].nunique()
            v2_with_outcome = v2_df[v2_df["TP10_Hit"].notna()] if "TP10_Hit" in v2_df.columns else pd.DataFrame()
            v2_winrate = v2_with_outcome["TP10_Hit"].mean() * 100 if not v2_with_outcome.empty else None

    # Phase 1 progress
    target_records = 100
    target_days = 30
    progress_records = min(v2_records / target_records, 1.0) if target_records else 0
    progress_days = min(v2_days / target_days, 1.0) if target_days else 0

    p1, p2, p3 = st.columns(3)
    p1.metric("📊 רשומות v2", f"{v2_records}/{target_records}", delta=f"{progress_records*100:.0f}%")
    p2.metric("📆 ימי מסחר v2", f"{v2_days}/{target_days}", delta=f"{progress_days*100:.0f}%")
    p3.metric("🎯 TP10 v2", f"{v2_winrate:.1f}%" if v2_winrate else "—")

    st.caption(
        "🎯 **קריטריוני יציאה לשלב 2:** ≥100 רשומות v2 · ≥30 ימי מסחר · "
        "TP10 hit rate יציב (±3%) · 18/18 health checks ירוקים 7 ימים"
    )

    st.divider()
    st.markdown("### 📚 פירוט מלא — לחץ לפתיחה")

    # ═══════════════════════════════════════════════════════════════════════
    # 2. Mental Model
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🧠 מודל מנטלי — *fishing fleet that doesn't fish*"):
        st.markdown("""
> **"RidingHigh Pro is like a fishing fleet that doesn't fish."**

צי דייגים שמטיל רשתות בכל דקה אבל לא תופס דגים — מצלם, שוקל, מודד, ומשחרר.
חודשים אחר כך, הרישומים יחשפו אילו תבניות מנבאות בצורה אמינה איזה דגים שווה לתפוס.

**רק כשהתבניות יוכחו סטטיסטית — ה-boats יתחילו לתפוס בפועל.**

המודל המנטלי מרמז:
- מהירות תפיסה פחות חשובה משלמות הרישום
- "השלל" הוא הנתונים, לא הכסף
- סבלנות היא מבנית
- Score היא השערה, לא פסק דין
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 3. Architecture — פירוט מלא
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🏗️ ארכיטקטורת המערכת — 7 שכבות עם פירוט"):
        st.markdown("""
המערכת בנויה ב-7 שכבות, כל אחת עם תפקיד מובחן.
שכבה גבוהה תלויה בשכבה נמוכה, אך לא להפך.
        """)

        layers_detail = [
            {
                "num": "7",
                "name": "Visualization (תצוגה)",
                "desc": "המסך שאתה רואה כרגע. Streamlit dashboard עם 8 דפים:",
                "files": [
                    "**dashboard.py** (4,111 שורות) — הקובץ העיקרי",
                    "  • 🏠 Home — סיכום היום",
                    "  • 💼 Portfolio Tracker — trades פעילים",
                    "  • 🔬 Post Analysis — מניות עם Score≥60 + 5 ימי מעקב",
                    "  • ⚡ Live Trades — trades בזמן אמת",
                    "  • 📈 Score Tracker — מסע Score של מניה ביום",
                    "  • 📅 Daily Summary — סיכום יומי",
                    "  • 📦 Timeline Archive — ארכיון timeline_live",
                    "  • 🖥️ System Overview (זה הדף הזה)",
                ],
            },
            {
                "num": "6",
                "name": "Maintenance & Automation (תחזוקה)",
                "desc": "סקריפטים שרצים אוטומטית לתחזק את המערכת:",
                "files": [
                    "**monthly_rotation.py** — מעבר לחודש חדש (1 בחודש 00:01 Peru)",
                    "**prepare_next_month.py** — יוצר תיקייה+9 sheets לחודש הבא",
                    "**warm_oauth_token.py** — מרענן OAuth token כל 3 ימים",
                    "**backup_manager.py** — CSV backup 3 פעמים ביום",
                    "**mark_score_version.py** — one-shot tagger v1/v2 (רץ פעם אחת)",
                ],
            },
            {
                "num": "5",
                "name": "Health & Audit (ניטור)",
                "desc": "המערכת בודקת את עצמה אוטומטית:",
                "files": [
                    "**health_audit.py** (1,377 שורות) — 18 בדיקות, 3×/יום, email על CRITICAL",
                    "**code_auditor.py** — drift detection (formulas duplicates, hardcoded values)",
                    "**daily_audit.py** — בדיקה יומית יותר מקיפה",
                    "**morning_health_check.py** — smoke test לפני שוק",
                    "**health_check.py** — הכפתור 'Quick Health Check' בHome",
                ],
            },
            {
                "num": "4",
                "name": "Collection & Enrichment (איסוף)",
                "desc": "אחרי סגירת השוק — אוסף ומעבד נתוני 5 ימים:",
                "files": [
                    "**post_analysis_collector.py** (v5) — לכל מניה עם Score≥60: D1-D5 OHLC",
                    "**enrich_post_analysis.py** — נתוני intraday (TP10 בתוך היום, peak score)",
                    "**enrich_data.py** — fundamentals enrichment",
                    "**backfill_ohlc.py** — ממלא D1-D5 חסרים מימים קודמים",
                    "**backfill_fundamentals.py** — sector, industry, float, וכו'",
                ],
            },
            {
                "num": "3",
                "name": "Engine (מנוע)",
                "desc": "הלב של המערכת — הסקאנר:",
                "files": [
                    "**auto_scanner.py** (1,317 שורות) — מכיל 7 פונקציות מרכזיות:",
                    "  • `run_scan()` — סריקה כל דקה",
                    "  • `analyze_ticker()` — ניתוח מניה אחת",
                    "  • `run_eod()` — EOD snapshot ב-16:00",
                    "  • `update_portfolio_live()` — עדכון פוזיציות",
                    "  • `update_ticker_follow_up()` — מעקב 5 ימים",
                    "  • `update_live_trades()` — סימולציה של trades",
                    "  • `sync_score_tracker()` — דגימה כל 5 דקות",
                ],
            },
            {
                "num": "2",
                "name": "Data Providers (ספקי נתונים)",
                "desc": "abstraction layer — מאחורי הקלעים בוחר Alpaca או yfinance:",
                "files": [
                    "**data_provider.py** — abstract base class",
                    "**providers/alpaca_provider.py** — PRIMARY (paper trading)",
                    "**providers/yfinance_provider.py** — FALLBACK + fundamentals",
                    "**validate_providers.py** — A/B comparison tool",
                    "ENV: `DATA_PROVIDER=alpaca` · `ALPACA_PAPER=true`",
                ],
            },
            {
                "num": "1",
                "name": "Foundation (תשתית)",
                "desc": "אבני בניין — נטען על ידי כל היתר:",
                "files": [
                    "**config.py** — Single source of truth (weights, caps, thresholds)",
                    "**formulas.py** (470 שורות) — 18 פונקציות חישוב מטריקות",
                    "**utils.py** — helpers (time, parsing, market hours)",
                    "**sheets_manager.py** — Google Sheets I/O + monthly rotation",
                    "**gsheets_sync.py** — post_analysis save/load",
                ],
            },
        ]

        for layer in layers_detail:
            st.markdown(f"#### Layer {layer['num']}: {layer['name']}")
            st.markdown(f"_{layer['desc']}_")
            for f in layer['files']:
                st.markdown(f"- {f}")
            st.markdown("")

        st.markdown("---")
        st.markdown("**עקרונות ארכיטקטוניים:**")
        st.markdown("""
1. **No formula duplication** — כל מטריקה ב-`formulas.py` בלבד
2. **Provider abstraction** — Code לא יודע אם Alpaca או yfinance
3. **Config centralization** — כל threshold ב-`config.py`
4. **Read-once, write-once** — אין מקבילות לאותו sheet
5. **Idempotent maintenance** — חזרה על rotation/OAuth/backup בטוחה
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 4. Data Pipeline
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🔄 צינור הנתונים — מה קורה בכל שלב"):
        st.code("""
FINVIZ (כל דקה, 08:30-15:00 Peru)
   ↓ pre-market screener filter
cron-job.org → GitHub Actions (auto_scan.yml)
   ↓ trigger every minute
auto_scanner.py · run_scan()
   ├─ 1. is_market_hours() — אם לא, יציאה
   ├─ 2. fetch_finviz() — מביא רשימת מניות מ-FINVIZ
   ├─ 3. for each ticker:
   │     ├─ analyze_ticker() — חישוב 7 metrics
   │     │     ├─ provider.get_daily_bars(252) — Alpaca
   │     │     ├─ get_fundamentals() — yfinance
   │     │     ├─ RSI(14), ATR(14), AvgVolume(20)
   │     │     └─ calculate_score(metrics) → 0-100
   │     └─ append to results
   ├─ 4. sort by Score descending
   ├─ 5. write to timeline_live (every scan)
   ├─ 6. if 14:59 → daily_snapshot + portfolio + daily_summary
   ├─ 7. update_portfolio_live() — TP/SL tracking
   ├─ 8. update_live_trades() — minute-by-minute simulation
   └─ 9. sync_score_tracker() — every 5 min sample

[16:05 Peru — אחרי סגירת שוק] post_analysis.yml:
   ↓
1. auto_scanner.py --eod
   ├─ קריאת timeline_live של היום
   ├─ סינון Score≥70 → portfolio
   └─ daily_summary (סיכום יומי)
2. post_analysis_collector.py
   ├─ לכל מניה ב-portfolio
   ├─ provider.get_daily_bars() — D1-D5 OHLC
   └─ TP10_Hit, MaxDrop%, SL_Hit_D5
3. enrich_post_analysis.py
   ├─ intraday data (5-min bars)
   ├─ IntraDay_TP10
   └─ peak score during day
4. backfill_ohlc.py
   └─ ממלא D1-D5 חסרים מימים קודמים

→ post_analysis sheet (THE research dataset)
   ↓
dashboard.py reads → displays in 8 pages
        """, language="text")

    # ═══════════════════════════════════════════════════════════════════════
    # 5. Daily Timeline — פירוט מלא
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("⏱️ לוח זמנים יומי — מה קורה בכל שעה (פירוט מלא)"):
        st.markdown("""
**כל הזמנים ב-Peru (UTC-5, ללא DST).** מערכת רצה 24/7, אבל הסקאנר רק 08:30-15:00 בימי מסחר.
        """)

        timeline_full = [
            {
                "time": "00:01",
                "icon": "🌙",
                "title": "Monthly Rotation (1 בחודש בלבד)",
                "what": "monthly_rotation.py מעדכן `sheets_config.json` שהחודש הנוכחי הוא הפעיל",
                "why": "כותבים בorder יודעים לאיזה sheet לכתוב",
                "frequency": "פעם בחודש (1 לחודש)",
            },
            {
                "time": "00:05",
                "icon": "🌙",
                "title": "Prepare Next Month (1 בחודש בלבד)",
                "what": "prepare_next_month.py יוצר תיקייה חדשה ב-Drive + 9 sheets ריקים לחודש הבא",
                "why": "ב-31 בחודש (מחר), הסיבוב יעבור לחודש שכבר הוכן",
                "frequency": "פעם בחודש (1 לחודש)",
            },
            {
                "time": "06:00",
                "icon": "🩺",
                "title": "Health Audit #1 — Pre-market",
                "what": "מריץ 18 בדיקות (code, data, config) → כותב ל-Health-Audit Sheet → שולח email",
                "why": "וידוא שהמערכת תקינה לפני פתיחת השוק",
                "frequency": "כל יום, כולל סוף שבוע",
            },
            {
                "time": "07:00",
                "icon": "🔑",
                "title": "Warm OAuth Token (כל 3 ימים)",
                "what": "warm_oauth_token.py מרענן את ה-Google OAuth refresh token",
                "why": "Google מבטל refresh tokens אחרי 7 ימי חוסר פעילות (apps in Testing OAuth)",
                "frequency": "כל 3 ימים",
            },
            {
                "time": "08:30",
                "icon": "🟢",
                "title": "NYSE OPEN — Auto Scanner Starts",
                "what": "cron-job.org יתחיל לטריגר את `auto_scan.yml` כל דקה",
                "why": "תחילת חלון המסחר של NYSE",
                "frequency": "Mon-Fri",
            },
            {
                "time": "08:30-15:00",
                "icon": "⚡",
                "title": "Auto Scan — כל דקה (~390 פעמים ביום)",
                "what": (
                    "1. fetch FINVIZ pre-market screener\n"
                    "2. לכל מניה — calculate 7 metrics + Score v2\n"
                    "3. כתיבה ל-`timeline_live` (כל סריקה)\n"
                    "4. עדכון `portfolio_live` (TP/SL real-time tracking)\n"
                    "5. עדכון `live_trades` (minute-by-minute simulation)\n"
                    "6. כל 5 דקות — דגימה ל-`score_tracker`\n"
                    "7. עדכון `ticker_follow_up` (5-day journey)"
                ),
                "why": "איסוף נתוני pump candidates בזמן אמת",
                "frequency": "כל דקה במהלך שוק (Mon-Fri 08:30-15:00)",
            },
            {
                "time": "12:00",
                "icon": "🩺",
                "title": "Health Audit #2 — Mid-day",
                "what": "אותן 18 בדיקות, באמצע יום המסחר",
                "why": "תפיסה של בעיות שיכולות להופיע במהלך היום",
                "frequency": "כל יום",
            },
            {
                "time": "14:59",
                "icon": "📸",
                "title": "Daily Snapshot",
                "what": (
                    "מתוך `auto_scanner.run_scan()`:\n"
                    "1. כתיבה ל-`daily_snapshots` — best score per ticker\n"
                    "2. כתיבה ל-`portfolio` — מניות עם Score≥70\n"
                    "3. כתיבה ל-`daily_summary` — סיכום יומי"
                ),
                "why": "לפני סגירת השוק — לתפוס את ה-state הסופי",
                "frequency": "Mon-Fri 14:59",
            },
            {
                "time": "15:00",
                "icon": "🔴",
                "title": "NYSE CLOSE",
                "what": "סקאנר ימשיך לרוץ עד שאחת ה-cron-job.org dispatches תזהה שהשוק סגור",
                "why": "סוף יום המסחר",
                "frequency": "Mon-Fri",
            },
            {
                "time": "15:07-16:30",
                "icon": "💼",
                "title": "Backups (3 פעמים)",
                "what": "backup_manager.py — CSV של post_analysis → GitHub artifact (90-day retention)",
                "why": "שכבת גיבוי שלישית (אחרי git + Sheets)",
                "frequency": "Mon-Fri, 3 פעמים מהשוק 15:07/16:00/16:30",
            },
            {
                "time": "16:05",
                "icon": "📊",
                "title": "Post-Analysis Pipeline (4 שלבים)",
                "what": (
                    "**שלב 1:** auto_scanner.py --eod — EOD snapshot\n"
                    "**שלב 2:** post_analysis_collector.py — D1-D5 OHLC לכל מניה\n"
                    "**שלב 3:** enrich_post_analysis.py — intraday TP10, D0_Drop%\n"
                    "**שלב 4:** backfill_ohlc.py — ממלא D1-D5 חסרים מימים קודמים"
                ),
                "why": "יצירת ה-research dataset העיקרי (post_analysis sheet)",
                "frequency": "Mon-Fri 16:05 (1 שעה אחרי סגירת שוק)",
            },
            {
                "time": "22:00",
                "icon": "🩺",
                "title": "Health Audit #3 — EOD",
                "what": "אותן 18 בדיקות, אחרי שכל ה-pipelines של היום הסתיימו",
                "why": "לוודא ש-post_analysis fill rate הצליח",
                "frequency": "כל יום, כולל סוף שבוע",
            },
        ]

        for evt in timeline_full:
            st.markdown(f"#### {evt['icon']} `{evt['time']}` — {evt['title']}")
            st.markdown(f"**מה:** {evt['what']}")
            st.markdown(f"**למה:** {evt['why']}")
            st.markdown(f"**תדירות:** {evt['frequency']}")
            st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════
    # 6. 9 Sheets Architecture
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🗄️ ארכיטקטורת ה-Sheets — 9 לחודש × 3 חודשים = 27 קבצים"):
        st.markdown("""
המערכת משתמשת ב-9 Google Sheets לכל חודש. בכל זמן נתון יש 3 חודשים פעילים בו-זמנית
(החודש הנוכחי, החודש הבא שכבר נוצר, וחודש קודם לקריאה היסטורית).
        """)

        sheets_full = pd.DataFrame([
            {"Sheet": "timeline_live", "כותב": "auto_scanner.run_scan()", "תדירות": "כל דקה",
             "מה נכתב": "ScanTime, Ticker, Price, Score, MxV, RunUp, REL_VOL, ATRX, RSI, VWAP, Volume, MarketCap, Float, ScanChange",
             "שורות/חודש": "~250-300K"},
            {"Sheet": "daily_snapshots", "כותב": "auto_scanner (best/ticker/day)", "תדירות": "EOD scan (14:59)",
             "מה נכתב": "Best score per ticker per day — סנפשוט יומי",
             "שורות/חודש": "~15-20/day"},
            {"Sheet": "daily_summary", "כותב": "auto_scanner.run_eod()", "תדירות": "scan + EOD",
             "מה נכתב": "סיכום יומי — TotalScans, UniqueStocks, AvgScore, TopScore, BestTicker",
             "שורות/חודש": "~50-60/day"},
            {"Sheet": "post_analysis", "כותב": "post_analysis_collector.py", "תדירות": "16:05 Peru",
             "מה נכתב": "המחקר הראשי: לכל מניה Score≥60, D0-D5 OHLC, TP10_Hit, MaxDrop%, fundamentals",
             "שורות/חודש": "~5-15/day"},
            {"Sheet": "portfolio", "כותב": "auto_scanner.update_live_trades", "תדירות": "כל דקה",
             "מה נכתב": "PositionKey, Date, Ticker, Score, BuyPrice, Status (Open/TP/SL)",
             "שורות/חודש": "~5-15/day"},
            {"Sheet": "portfolio_live", "כותב": "auto_scanner.update_portfolio_live", "תדירות": "כל דקה",
             "מה נכתב": "Live tracking: EntryPrice, TP10_Price, SL_Price, RunningHigh, RunningLow, Status",
             "שורות/חודש": "~5-20 active"},
            {"Sheet": "score_tracker", "כותב": "auto_scanner.sync_score_tracker", "תדירות": "כל 5 דקות",
             "מה נכתב": "דגימה של score: Ticker, ScanDate, ScanTime, Score, Price",
             "שורות/חודש": "~800-1000/day"},
            {"Sheet": "live_trades", "כותב": "auto_scanner.update_live_trades", "תדירות": "כל דקה",
             "מה נכתב": "Minute-by-minute trades simulation",
             "שורות/חודש": "~800-1000/day"},
            {"Sheet": "ticker_follow_up", "כותב": "auto_scanner.update_ticker_follow_up", "תדירות": "כל דקה (5 ימים)",
             "מה נכתב": "מעקב 5 ימים אחרי הסריקה: D0/D1/D2/D3/D4/D5 prices, drops",
             "שורות/חודש": "~5-15/day"},
        ])
        st.dataframe(sheets_full, hide_index=True, use_container_width=True)

        st.markdown("**Special-purpose sheets** (מחוץ ל-monthly rotation):")
        st.markdown("""
- **RidingHigh-Health-Audit** — תוצאות 18 בדיקות בריאות (3 tabs: History, Latest, Failed)
- **RidingHigh-Pro-System-Reference** — Master backup של PK v2.0
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 7. Score v2 — פירוט מלא לכל מטריקה
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🧮 Score v2 — פירוט מלא של כל המטריקות והנוסחאות"):
        st.markdown("""
Score הוא מספר 0-100 שמשקלל 7 metrics. **סכום המשקלים בדיוק 100.**
מקור הקוד: `formulas.calculate_score()` ב-`formulas.py` שורה 1034.
        """)

        # MxV
        st.markdown("### 1️⃣ MxV — Market Cap vs Volume (משקל: 25%)")
        st.markdown("**מה זה:** מודד את היחס בין market cap למחזור הדולרי. ערכים שליליים = פאמפ עוצמתי.")
        st.markdown("**הנוסחה:**")
        st.code("MxV = (MarketCap - Price × Volume) / MarketCap × 100", language="text")
        st.markdown("""
**איך זה משנה לshorts:**
- כשמחזור דולרי גבוה ביחס למחזור הרגיל של המניה (low cap × huge volume) → MxV שלילי מאוד
- ככל ש-MxV יותר שלילי → סיגנל פאמפ חזק יותר → ציון גבוה יותר
- **רק ערכים שליליים מקבלים נקודות** (פאמפ = ירידה אחר כך)
        """)
        st.markdown("**Cap לציון:** 200 — `score = min(|MxV| / 200, 1) × 25`")
        st.markdown("**דוגמה:** MarketCap=$100M · Price=$5 · Volume=50M → MxV = (100M − 250M)/100M × 100 = **−150%** → score: 150/200 × 25 = **18.75 נקודות**")
        st.markdown("---")

        # RunUp
        st.markdown("### 2️⃣ RunUp — Intraday Rise (משקל: 25%)")
        st.markdown("**מה זה:** העלייה האחוזית מ-Open עד המחיר הנוכחי באותו יום.")
        st.markdown("**הנוסחה:**")
        st.code("RunUp = (Price - Open) / Open × 100", language="text")
        st.markdown("""
**איך זה משנה לshorts:**
- מניה שעלתה הרבה היום היא candidate לתיקון מחר
- **רק ערכים חיוביים מקבלים נקודות**
- Cap 30%: עליות מעבר ל-30% לא מוסיפות עוד ציון
        """)
        st.markdown("**Cap לציון:** 30% — `score = min(RunUp / 30, 1) × 25`")
        st.markdown("**דוגמה:** Open=$10 · Price=$13 → RunUp = 30% → score: **25 נקודות מלאות**")
        st.markdown("---")

        # ATRX
        st.markdown("### 3️⃣ ATRX — Volatility Expansion (משקל: 20%)")
        st.markdown("**מה זה:** טווח היום (high-low) חלקי ATR14 — כפולה של תנודתיות הממוצע.")
        st.markdown("**הנוסחה:**")
        st.code("ATRX = (High_today - Low_today) / ATR14", language="text")
        st.markdown("""
**איך זה משנה לshorts:**
- ATRX > 1 → היום תנודתי משמעותית מהממוצע
- ATRX > 3 → תנודתיות חריגה
- מניות עם תנודתיות גבוהה נוטות לחזור לממוצע

**ATR14:** Average True Range של 14 הימים האחרונים — מדד תקני לתנודתיות.
        """)
        st.markdown("**Cap לציון:** 5x — `score = min(ATRX / 5, 1) × 20`")
        st.markdown("**דוגמה:** High=$10, Low=$8, ATR14=$1 → ATRX = 2.0 → score: 2/5 × 20 = **8 נקודות**")
        st.markdown("---")

        # RSI
        st.markdown("### 4️⃣ RSI — Extreme Overbought (משקל: 10%)")
        st.markdown("**מה זה:** Relative Strength Index של 14 ימים. מודד momentum.")
        st.markdown("**הנוסחה:** RSI(14) — קלאסי מ-`ta` library")
        st.markdown("""
**שלבים (אחרי מחקר 22/4/2026):**
- RSI ≥ 90 → **10 נקודות מלאות** (extreme overbought, 100% TP20)
- RSI ≥ 85 → 7 נקודות
- RSI ≥ 80 → 4 נקודות
- RSI < 80 → **0 נקודות**

**שינוי קריטי:** היה bell curve 50-70, אבל המחקר הראה שדווקא RSI 50-70 = הזון הכי חלש.
RSI 90+ = TP20 hit rate 100%.
        """)
        st.markdown("---")

        # VWAP / Typical Price
        st.markdown("### 5️⃣ VWAP / TypicalPriceDist (משקל: 10%)")
        st.markdown("**מה זה:** מרחק אחוזי של המחיר מ-Typical Price = (High+Low+Close)/3.")
        st.markdown("**הנוסחה:**")
        st.code("TypicalPrice = (High + Low + Close) / 3\nDist = (Price / TypicalPrice - 1) × 100", language="text")
        st.markdown("""
**הערה חשובה:** זו לא VWAP אמיתית — VWAP אמיתית דורשת tick-by-tick data שאין לנו.
Typical Price הוא TA proxy סטנדרטי לדוחות יומיים.
        """)
        st.markdown("**Cap:** 8% — רק ערכים חיוביים (price מעל typical) → `min(Dist / 8, 1) × 10`")
        st.markdown("---")

        # ScanChange
        st.markdown("### 6️⃣ ScanChange% — Change Since Previous Close (משקל: 5%)")
        st.markdown("**מה זה:** % השינוי מ-Close של אתמול עד המחיר בזמן הסריקה.")
        st.markdown("**הנוסחה:**")
        st.code("ScanChange = (Price - PrevClose) / PrevClose × 100", language="text")
        st.markdown("**Cap:** 60% — רק חיוביים. `min(ScanChange / 60, 1) × 5`")
        st.markdown("---")

        # REL_VOL
        st.markdown("### 7️⃣ REL_VOL — Relative Volume (משקל: 5%)")
        st.markdown("**מה זה:** מחזור היום לעומת ממוצע 20 ימים.")
        st.markdown("**הנוסחה:**")
        st.code("REL_VOL = Volume_today / AvgVolume(20d)", language="text")
        st.markdown("""
**Hard cap:** 100x (גם ב-raw data) — מנע outliers מ-yfinance שראינו בעבר 26,794x.
        """)
        st.markdown("**Cap לציון:** 15x — `min(REL_VOL / 15, 1) × 5`")
        st.markdown("---")

        # Tiers
        st.markdown("### 🎨 רמות הציון (Tiers)")
        tcol1, tcol2, tcol3, tcol4 = st.columns(4)
        tcol1.error("🔴 **Critical** ≥85")
        tcol2.warning("🟠 **High** 60-84")
        tcol3.info("🟡 **Medium** 40-59")
        tcol4.success("⚪ **Low** <40")

        st.markdown(f"""
**ספי פעולה:**
- `MIN_SCORE_DISPLAY = {MIN_SCORE_DISPLAY}` — מינימום להצגה ב-dashboard
- `TRADE_ENTRY_MIN_SCORE = {TRADE_ENTRY_MIN_SCORE}` — מינימום לכניסה ל-portfolio simulation
- `CRITICAL_SCORE = {CRITICAL_SCORE}` — סיגנל הכי חזק

**מקור:** `config.py` — `SCORE_WEIGHTS_V2` ו-`SCORE_CAPS_V2`
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 8. Trade Simulation
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("💼 סימולציית מסחר — איך זה עובד והאם להשאיר"):
        st.markdown(f"""
**הסימולציה רצה אקטיבית ויש לה ערך מחקרי גדול.** היא לא מחליפה Alpaca paper trading
עתידי — היא משלימה אותו.

### למה שתי שכבות?

**🧪 סימולציה פנימית (פעיל היום):**
- ✅ גמישה — אפשר לשנות TP/SL/window בקלות
- ✅ זריזה — backtest מיידי על נתונים היסטוריים
- ✅ multiple strategies במקביל
- ❌ פחות מציאותי — בלי slippage, fills, spread

**📈 Alpaca paper (עתיד — Phase מתקדם):**
- ✅ מציאותי — fills, slippage, spread כמו real trading
- ✅ הכנה ל-real money (Phase 4)
- ❌ פחות גמיש — אסטרטגיה אחת בלבד
- ❌ Sequential — לא במקביל

**ההמלצה:** משאירים את שתי השכבות. כעת רק סימולציה פנימית. בעתיד — מוסיפים Alpaca paper.

### איך הסימולציה עובדת

**Position Size:** ${POSITION_SIZE_USD:,} per trade · **TP:** −{TP_THRESHOLD_FRAC*100:.0f}% · **SL:** +{SL_THRESHOLD_FRAC*100:.0f}% · **חלון:** 5 ימי מסחר

```
לכל מניה עם Score ≥ {TRADE_ENTRY_MIN_SCORE}:
  Entry:    BORROW & SELL at ScanPrice (סוף היום)
            ↓
            wait up to 5 trading days (D1-D5)
            ↓
  Watch every minute (live_trades) and EOD (portfolio):
    IF intraday_low ≤ entry × 0.90  →  TP10 HIT  (WIN, +$100)
    IF intraday_high ≥ entry × 1.10 →  SL HIT    (LOSS, −$100)
    IF day 5 ends with neither      →  TIMEOUT (close at D5 close)

SL ALWAYS overrides TP אם שניהם נפגעו באותו bar (שמרני).
```

### איפה רואים את זה?

- **💼 Portfolio Tracker** — רשימת trades פעילים עם status
- **⚡ Live Trades** — מעקב minute-by-minute
- **🔬 Post Analysis** — מה קרה אחרי 5 ימים
- **📈 Score Tracker** — איך Score השתנה ביום הסריקה
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 9. 18 Health Checks — פירוט מלא
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🩺 18 Health Checks — פירוט מלא של כל בדיקה"):
        st.markdown("""
המערכת בודקת את עצמה אוטומטית 3 פעמים ביום (06:00, 12:00, 22:00 Peru).
תוצאות נכתבות ל-Health Audit Sheet ונשלחים emails על CRITICAL.

מקור: `health_audit.py` (1,377 שורות).
        """)

        st.markdown("### 📁 Code Integrity (3 בדיקות)")
        checks_code = [
            {"id": "C1", "name": "duplicate_functions",
             "what": "סריקת כל קבצי .py למציאת פונקציות שמוגדרות בשני מקומות או יותר",
             "fail": "WARNING — מצאה פונקציה כפולה (חוץ מ-calculate_score, run, now_peru)"},
            {"id": "C2", "name": "hardcoded_thresholds",
             "what": "חיפוש regex של 0.07, 0.10, >=60, >=70 בקבצי .py מחוץ ל-config.py",
             "fail": "WARNING — מצאה ערך שצריך להיות ב-config.py"},
            {"id": "C3", "name": "imports_consistency",
             "what": "וידוא ש-dashboard.py מייבא מ-formulas.py ומ-config.py",
             "fail": "CRITICAL אם dashboard.py חסר · WARNING אם imports חסרים"},
        ]
        for c in checks_code:
            st.markdown(f"**{c['id']} — {c['name']}**")
            st.markdown(f"  - **מה בודק:** {c['what']}")
            st.markdown(f"  - **כשנכשל:** {c['fail']}")

        st.markdown("### 📊 Data Freshness (3 בדיקות)")
        checks_fresh = [
            {"id": "D1", "name": "timeline_freshness",
             "what": "תאריך השורה האחרונה ב-timeline_live חייב להיות ≤24 שעות בימי מסחר",
             "fail": "CRITICAL אם > 24h בלי כתיבה ביום מסחר · WARNING אם sheet ריק"},
            {"id": "D2", "name": "post_analysis_completeness",
             "what": "פוסט-אנליסיס מלא לכל יום מסחר עם רשומות (TP10_Hit לא ריק)",
             "fail": "WARNING על gap של D1-D5 חסרים"},
            {"id": "D3", "name": "github_actions_health",
             "what": "API call ל-GitHub: בודק 95%+ workflows הצליחו ב-50 הריצות האחרונות",
             "fail": "PASSED ≥95% · WARNING ≥80% · CRITICAL <80%"},
        ]
        for c in checks_fresh:
            st.markdown(f"**{c['id']} — {c['name']}**")
            st.markdown(f"  - **מה בודק:** {c['what']}")
            st.markdown(f"  - **כשנכשל:** {c['fail']}")

        st.markdown("### 🔢 Data Quality (4 בדיקות)")
        checks_qual = [
            {"id": "Q1", "name": "score_range",
             "what": "כל הציונים ב-post_analysis בטווח [0, 100]",
             "fail": "CRITICAL אם נמצא score < 0 או > 100"},
            {"id": "Q2", "name": "required_columns",
             "what": "Schema integrity: timeline_live חייב Date/ScanTime/Ticker/Price/Score · post_analysis חייב Ticker/ScanDate/Score",
             "fail": "WARNING על עמודה חסרה · CRITICAL אם sheet לא מוגדר"},
            {"id": "Q3", "name": "duplicate_post_analysis_rows",
             "what": "לכל זוג (Ticker, ScanDate) ב-post_analysis צריך להיות שורה אחת בלבד",
             "fail": "WARNING על כפילויות"},
            {"id": "Q4", "name": "outliers",
             "what": "REL_VOL > 100 (cap should prevent) · ScanPrice ≤ 0",
             "fail": "WARNING על outliers"},
        ]
        for c in checks_qual:
            st.markdown(f"**{c['id']} — {c['name']}**")
            st.markdown(f"  - **מה בודק:** {c['what']}")
            st.markdown(f"  - **כשנכשל:** {c['fail']}")

        st.markdown("### ⚙️ Config Consistency (3 בדיקות)")
        checks_cfg = [
            {"id": "X1", "name": "sheets_config_current_month",
             "what": "sheets_config.json מכיל entry לחודש הנוכחי (Peru time)",
             "fail": "CRITICAL — חסר חודש = sheets לא יעבדו"},
            {"id": "X2", "name": "score_weights_sum",
             "what": "סכום SCORE_WEIGHTS_V2 ב-config.py בדיוק 100 (או 1.0)",
             "fail": "CRITICAL — סכום שונה = ציון שבור"},
            {"id": "X3", "name": "critical_files",
             "what": "כל הקבצים החיוניים קיימים: auto_scanner.py, formulas.py, config.py, וכו'",
             "fail": "CRITICAL — קובץ חסר"},
        ]
        for c in checks_cfg:
            st.markdown(f"**{c['id']} — {c['name']}**")
            st.markdown(f"  - **מה בודק:** {c['what']}")
            st.markdown(f"  - **כשנכשל:** {c['fail']}")

        st.markdown("### 🔐 Repo Health (2 בדיקות)")
        checks_repo = [
            {"id": "R1", "name": "uncommitted_count",
             "what": "(local only) מספר נמוך של קבצים לא-committed",
             "fail": "WARNING על cleanup מומלץ"},
            {"id": "R2", "name": "gitignore_enforcement",
             "what": "גילוי שקבצים רגישים כמו google_credentials.json נמצאים ב-.gitignore",
             "fail": "CRITICAL — secrets exposed"},
        ]
        for c in checks_repo:
            st.markdown(f"**{c['id']} — {c['name']}**")
            st.markdown(f"  - **מה בודק:** {c['what']}")
            st.markdown(f"  - **כשנכשל:** {c['fail']}")

        st.markdown("### 🌐 Provider/Stuck Checks (3 בדיקות)")
        checks_prov = [
            {"id": "16", "name": "rel_vol_stuck",
             "what": "האם REL_VOL נתקע (200 שורות אחרונות אותו ערך)",
             "fail": "WARNING — likely provider issue"},
            {"id": "17", "name": "fundamentals_provider",
             "what": "fundamentals provider מחזיר נתונים תקפים ל-AAPL (test ticker)",
             "fail": "CRITICAL אם provider לא מגיב או מחזיר נתונים שבורים"},
            {"id": "18", "name": "daily_bars_provider",
             "what": "Alpaca/yfinance מחזיר daily bars תקינים",
             "fail": "CRITICAL אם provider לא נגיש"},
        ]
        for c in checks_prov:
            st.markdown(f"**{c['id']} — {c['name']}**")
            st.markdown(f"  - **מה בודק:** {c['what']}")
            st.markdown(f"  - **כשנכשל:** {c['fail']}")

        st.markdown("---")
        st.markdown("""
**Severity levels:**
- 🟢 **PASSED** — בדיקה עברה
- 🟡 **WARNING** — חריגה לא קריטית, גורם לemail צהוב
- 🔴 **CRITICAL** — בעיה חמורה, email אדום + alert מיידי
- ⚪ **INFO** — מידע בלבד (e.g., bypass ב-no Sheets access)

**email schedule:**
- אימיילים נשלחים גם כש-PASSED (heartbeat) — חוסר אימייל = מערכת שבורה
- 🔴 בנושא = נדרשת התערבות מיידית
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 10. 7 Workflows
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("⚙️ 7 GitHub Actions Workflows — פירוט מלא"):
        wf_data = [
            {
                "name": "auto_scan.yml",
                "cron": "* * * * *",
                "peru": "כל דקה",
                "purpose": "הסקאנר המרכזי — `python auto_scanner.py`",
                "steps": "Filter market hours → fetch FINVIZ → analyze → write 6 sheets",
                "timeout": "8 דקות",
                "env": "Alpaca + Google + ALPACA_PAPER=true",
            },
            {
                "name": "post_analysis.yml",
                "cron": "5 21 * * 1-5",
                "peru": "16:05 Mon-Fri",
                "purpose": "Daily research collector (4 שלבים)",
                "steps": "EOD snapshot → 5-day OHLC → enrich intraday → backfill gaps",
                "timeout": "15 דקות",
                "env": "Alpaca + Google",
            },
            {
                "name": "health_audit.yml",
                "cron": "0 11,17 * * *  +  0 3 * * *",
                "peru": "06:00, 12:00, 22:00 כל יום",
                "purpose": "18 בדיקות בריאות + email alerts",
                "steps": "run health_audit.py → write to Sheet → send email",
                "timeout": "10 דקות",
                "env": "Google + Alpaca + Gmail SMTP",
            },
            {
                "name": "backup.yml",
                "cron": "7 13-21 * * 1-5  +  7 20 * * 1-5  +  30 21 * * 1-5",
                "peru": "08:07-16:30 Mon-Fri (3 פעמים)",
                "purpose": "CSV backups → GH artifact (90-day retention)",
                "steps": "backup_manager.py → upload artifact",
                "timeout": "10 דקות",
                "env": "Google",
            },
            {
                "name": "monthly_rotation.yml",
                "cron": "1 5 1 * *",
                "peru": "00:01 ב-1 לחודש",
                "purpose": "מעבר לחודש פעיל חדש",
                "steps": "monthly_rotation.py → commit sheets_config.json",
                "timeout": "10 דקות",
                "env": "Google + write permissions",
            },
            {
                "name": "prepare_next_month.yml",
                "cron": "5 5 1 * *",
                "peru": "00:05 ב-1 לחודש",
                "purpose": "יצירת תיקייה+9 sheets לחודש הבא (אחרי rotation)",
                "steps": "prepare_next_month.py → commit config",
                "timeout": "—",
                "env": "Google OAuth + write permissions",
            },
            {
                "name": "warm_oauth_token.yml",
                "cron": "0 12 */3 * *",
                "peru": "07:00 כל 3 ימים",
                "purpose": "מניעת ביטול OAuth refresh token (7-day timeout)",
                "steps": "warm_oauth_token.py → email if fails",
                "timeout": "—",
                "env": "Google OAuth + Gmail SMTP",
            },
        ]

        for wf in wf_data:
            st.markdown(f"#### `{wf['name']}`")
            c1, c2 = st.columns(2)
            c1.markdown(f"**Cron:** `{wf['cron']}`")
            c2.markdown(f"**Peru time:** {wf['peru']}")
            st.markdown(f"**מטרה:** {wf['purpose']}")
            st.markdown(f"**שלבים:** {wf['steps']}")
            c3, c4 = st.columns(2)
            c3.caption(f"Timeout: {wf['timeout']}")
            c4.caption(f"Env: {wf['env']}")
            st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════
    # 11. Glossary
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("📖 מונחון — מה כל מונח אומר"):
        glossary = [
            ("D0", "יום הסריקה (היום שהסיגנל קרה)"),
            ("D1, D2, ... D5", "1-5 ימי מסחר אחרי D0 (מדלגים על סופי שבוע וחגים)"),
            ("Table A", "סימולציה עם entry ב-ScanPrice (EOD של D0) — תאורטית"),
            ("Table B", "סימולציה עם entry ב-D1_Open — מציאותית, כוללת gap risk"),
            ("TP / TP10", "Take Profit ב-−10% מהentry (short win)"),
            ("SL", "Stop Loss ב-+10% מהentry (short loss)"),
            ("MxV", "Market cap minus dollar volume — מודד illiquidity"),
            ("RunUp", "אחוז עלייה מ-Open עד הnowprice"),
            ("ATRX", "טווח היום (High-Low) חלקי ATR14 — כפולה של תנודתיות הממוצע"),
            ("REL_VOL", "מחזור היום חלקי ממוצע 20 ימים (capped 100)"),
            ("VWAP", "מרחק % מ-Typical Price = (H+L+C)/3"),
            ("ScanChange%", "אחוז שינוי מ-Close הקודם בזמן הסריקה"),
            ("Float%", "מחזור כ-% של float shares — turnover"),
            ("Score", "מספר 0-100 ממוצע משוקלל של 7 metrics (Score v2)"),
            ("v1 / v2", "v1 = formula ישנה (לפני 11.4) · v2 = formula נוכחית"),
            ("Critical / High / Med / Low", "tiers של Score: 85+/60-84/40-59/<40"),
            ("TRADE_ENTRY_MIN_SCORE", "70 — מינימום ל-portfolio simulation"),
            ("MIN_SCORE_DISPLAY", "60 — מינימום להצגה ב-dashboards"),
            ("EOD", "End of Day — תהליך אחרי סגירת השוק (16:00-16:30 Peru)"),
            ("Phase 1/2/3/4", "שלבי המערכת — איסוף → dynamic TP → entry timing → real money"),
            ("Paper trading", "trades מסומלצים ב-Alpaca ללא כסף אמיתי"),
            ("SIP / IEX", "U.S. market data feeds (SIP=consolidated, IEX=single venue)"),
            ("PK", "Project Knowledge — מסמך המקור עליו Claude קורא בכל סשן"),
            ("ADR", "Architecture Decision Record — תיעוד החלטות טכניות"),
        ]
        for term, definition in glossary:
            st.markdown(f"**{term}** — {definition}")

    # ═══════════════════════════════════════════════════════════════════════
    # 12. Disaster Recovery
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("💾 התאוששות מאסון (DR Plan)"):
        st.markdown("""
### יעדי שירות
- **RPO (Recovery Point Objective):** איבוד נתונים מקסימלי = **1 יום מסחר**
- **RTO (Recovery Time Objective):** השבתה מקסימלית = **48 שעות** (סוף שבוע אחד)

### תרחישי אסון

#### 🖥️ Scenario 1: המק שלך מת
- **השפעה:** אפס על המערכת הרצה. רק כלים מקומיים לא זמינים.
- **התאוששות:** מק חדש → `git clone` → העתק `google_credentials.json` → `pip install -r requirements.txt`
- **RTO:** ~2 שעות

#### 📊 Scenario 2: Sheet נמחק בטעות
- **השפעה:** איבוד נתונים בתהליך, גיבויים חלקיים.
- **התאוששות:** Drive trash (30 ימים) → CSV backup ב-`backups/` → GitHub artifacts
- **RTO:** 4-8 שעות

#### 🔐 Scenario 3: GitHub Actions מבוטל / repo נמחק
- **השפעה:** אין אוטומציה. נתונים קיימים נשמרים ב-Sheets.
- **התאוששות:** local clone → `git push <new-url>` → re-add secrets → enable Actions
- **RTO:** 4 שעות

#### 🚫 Scenario 4: חשבון Google מושעה
- **השפעה:** קטסטרופלי. Sheets, Drive, OAuth — הכל אבוד.
- **התאוששות:** restore account או חדש → service account חדש → re-create sheets → CSV backups (≤90 ימים)
- **RTO:** 24-48 שעות
- **Data loss:** הכל שלא גובה ל-CSV. עד שבועות של נתוני in-Sheets לא נתפסים.

#### 📈 Scenario 5: חשבון Alpaca מושעה
- **השפעה:** Provider abstraction מתערב — yfinance fallback.
- **התאוששות:** Alpaca paper account חדש → update env vars
- **RTO:** 1 שעה
- **Data loss:** אין

### מה בכל שכבת גיבוי
| Asset | Primary | Backup | Tertiary |
|-------|---------|--------|----------|
| Code | GitHub repo | Local clone | — |
| post_analysis | Google Sheets | CSV in `backups/` | GH artifacts (90-day) |
| Other sheets | Google Sheets | Manual export | — |
| Secrets | GitHub Secrets | (TBD: 1Password) | — |
| OAuth token | Auto-refreshed every 3d | Manual via `get_oauth_token.py` | — |
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 13. Operational Runbook
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🚨 Operational Runbook — מה לעשות אם משהו נשבר"):
        st.markdown("""
### 🔴 אימייל Health Audit מציג CRITICAL

**אבחון:**
1. פתח את האימייל — זהה איזו בדיקה נכשלה
2. פתח את **RidingHigh-Health-Audit Sheet** → "Failed" tab
3. הסתכל על "Latest" tab למצב מערכת מלא

**טיפול בבעיות נפוצות:**
- `D1 timeline_freshness` → סקאנר עצר. בדוק GH Actions tab ב-repo. הרץ `auto_scan.yml` ידנית.
- `D2 post_analysis_completeness` → collector נכשל אתמול. הרץ `python post_analysis_collector.py` מקומית.
- `Q1 score_range` → נתונים שבורים. בדוק את ה-ticker/date מהאימייל.
- `X2 score_weights_sum` → ערכי `config.py` נשברו. `cat config.py | grep -A 10 SCORE_WEIGHTS_V2`
- `X3 critical_files` → קובץ ליבה נמחק. בדוק `git log` של ה-commits האחרונים.

### 🔑 אימייל "OAuth Token EXPIRED"

**שלבים:**
1. SSH/local למק
2. `cd ~/RidingHighPro && python3 get_oauth_token.py`
3. תהליך browser → grant → token נשמר
4. עתק תוכן הtoken JSON
5. עדכן GitHub Secret `GOOGLE_OAUTH_TOKEN_JSON`
6. הפעל `warm_oauth_token.yml` ידנית
7. המתן ל-health audit הבא

### 📭 אין אימיילים

**אבחון:**
1. בדוק spam folder
2. חפש "RidingHigh" ב-Gmail "All Mail"
3. בדוק `health_audit.yml` ב-GH Actions tab — האם יש runs?
4. אם הruns מצליחים אבל אין email: secret `GMAIL_APP_PASS` בוטל. צור App Password חדש.

### 🐌 Sheets Quota Exceeded (נדיר)

**טיפול:**
1. המתן 100 שניות (חלון quota)
2. נסה את הפעולה שוב ידנית
3. אם חוזר על עצמו: הקטן refresh frequency של dashboard.

### 📭 post_analysis חסר רשומות היום

**אבחון:**
- בדוק daily_summary — האם בכלל היו מניות היום?
- אם היו: הרץ `python post_analysis_collector.py`
- ואז: `python backfill_ohlc.py`

### 🔄 Dashboard מציג נתונים ישנים

**טיפול:**
1. לחץ "🗑️ Clear Local Cache" ב-sidebar
2. לחץ "🔄 Refresh data"
3. אם עדיין ישן: בדוק את ה-sheet ישירות ב-Drive

### Manual interventions
| משימה | פקודה |
|------|--------|
| הרץ סקאנר עכשיו | `python3 auto_scanner.py` (מקומית) |
| הרץ EOD עכשיו | `python3 auto_scanner.py --eod` |
| הרץ health audit עכשיו | `python3 health_audit.py --local` |
| post-analysis לתאריך מסוים | `python3 post_analysis_collector.py --date 2026-04-30` |
| Backfill OHLC | `python3 backfill_ohlc.py` |
| Audit code drift | `python3 code_auditor.py` |
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 14. External Dependencies
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🔗 תלויות חיצוניות"):
        deps_data = pd.DataFrame([
            {"שירות": "FINVIZ", "תפקיד": "Pre-market filter (single point of failure)", "Tier": "Free scrape", "SLA": "אין"},
            {"שירות": "Alpaca", "תפקיד": "Verification prices, D1-D5 OHLC", "Tier": "Free paper", "SLA": "best effort"},
            {"שירות": "yfinance", "תפקיד": "Fundamentals + fallback prices", "Tier": "Free public", "SLA": "אין"},
            {"שירות": "Google Sheets", "תפקיד": "All operational data storage", "Tier": "Free", "SLA": "99.9%"},
            {"שירות": "GitHub Actions", "תפקיד": "7 workflows automation", "Tier": "Free ~3000 min/mo", "SLA": "varies"},
            {"שירות": "cron-job.org", "תפקיד": "Triggers auto_scan every minute", "Tier": "Free", "SLA": "אין"},
            {"שירות": "Streamlit Cloud", "תפקיד": "Dashboard hosting (זה האתר)", "Tier": "Free", "SLA": "best effort"},
            {"שירות": "Gmail SMTP", "תפקיד": "Health audit email alerts", "Tier": "Free", "SLA": "high"},
        ])
        st.dataframe(deps_data, hide_index=True, use_container_width=True)

        st.markdown("**עלות חודשית כוללת: $0**")

        st.markdown("""
### Single points of failure
1. **FINVIZ** — אין fallback אוטומטי לscreener
2. **GitHub** — קוד, secrets, automation הכל שם
3. **Google account** — Sheets, Drive, OAuth מחוברים לחשבון אחד

אלה risks מקובלים למערכת single-operator.
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 15. Master Backups
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🛡️ גיבויים — Triple safety net"):
        bk1, bk2, bk3 = st.columns(3)
        with bk1:
            st.markdown("**📦 GitHub Repo**")
            st.markdown("[`projects5069-creator/ridinghigh-pro`](https://github.com/projects5069-creator/ridinghigh-pro)")
            st.caption("Source of truth · Git history קבועה")
        with bk2:
            st.markdown("**☁️ Google Sheet Master**")
            st.markdown("[System Reference Sheet](https://docs.google.com/spreadsheets/d/1SuHj0joCfT7kAoSEvrqepJJcUG8uBU5J4zmxkx9e3J0)")
            st.caption("PK v2.0 mirror · sync via `sync_pk_to_sheet.py`")
        with bk3:
            st.markdown("**💼 CSV Backups**")
            st.markdown("GitHub Actions artifacts (90-day retention)")
            st.caption("3×/יום במהלך שוק · backup_manager.py")

    # ═══════════════════════════════════════════════════════════════════════
    # 16. Roadmap
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🗺️ Roadmap — Phase 1 → 4"):
        st.markdown("""
### Phase 1 — Data Accumulation [פעיל, ~50%]
- ✅ מערכת רצה יומית
- ✅ 18 health checks חיים
- ✅ Score v2 פעיל
- ✅ Provider abstraction (Alpaca + yfinance)
- ⏳ 100 רשומות v2 (כעת: ~50)
- ⏳ 30 ימי מסחר v2 (כעת: ~14)

### Phase 2 — Dynamic TP via ATRX [מתוכנן]
- מטרה: TP threshold לכל מניה לפי ATRX (high-vol stocks need wider TP)
- דורש: Phase 1 exit criteria מולאו
- הערכה: סוף מאי 2026

### Phase 3 — Entry Timing Optimization [מתוכנן]
- מטרה: minute-level data לזיהוי entry timing אופטימלי
- דורש: Phase 2 stable 4 שבועות

### Phase 4 — Real Money Execution [GATED, אין תאריך]
- מטרה: `ALPACA_PAPER=false`, deploy small position size
- Gate criteria:
  - Phase 3 מראה edge מאומת על תנאי שוק שונים
  - Independent statistical review
  - החלטה על capital allocation
  - Risk limits hardcoded
        """)

    # ═══════════════════════════════════════════════════════════════════════
    # 17. Anti-Drift Contract
    # ═══════════════════════════════════════════════════════════════════════
    with st.expander("🤝 Anti-Drift Maintenance Contract"):
        st.markdown("""
**חוזה מחייב על Claude בכל סשן עתידי:**

כשClaude עוזר במשימה ש-:
1. מוסיפה / משנה / מסירה Python file ב-repo
2. מוסיפה / משנה / מסירה workflow ב-`.github/workflows/`
3. מוסיפה / משנה / מסירה sheet ב-`sheets_config.json`
4. מוסיפה / משנה / מסירה constant ב-`config.py`
5. מוסיפה / משנה / מסירה metric, formula, או weight
6. מוסיפה / משנה / מסירה health check
7. מוסיפה / משנה / מסירה email alert או schedule
8. מוסיפה / משנה / מסירה phase, KPI, או known issue
9. סוגרת או פותחת issue ב-`OPEN_ISSUES.md`

**אז, לפני git commit/push הסופי, Claude חייב:**
- ✓ לזהות אילו סעיפי PK מושפעים
- ✓ לעדכן את הסעיפים עם המציאות החדשה
- ✓ להגדיל גרסה (v2.0 → v2.0.1 patch · → v2.1 minor)
- ✓ להוסיף שורת changelog ב-§1
- ✓ להריץ `python3 sync_pk_to_sheet.py` לעדכון Sheet master
- ✓ להודיע לעמיחי ("עדכנתי PK §X לשקף Y")
        """)

    st.divider()

    # ═══ Footer ═══════════════════════════════════════════════════════════════
    st.caption(
        f"🌍 **Owner:** Amihay Levy · Lima, Peru (UTC-5, no DST) · "
        f"📅 **PK v2.0:** 2026-05-02 · "
        f"📚 **Full reference:** `docs/RidingHigh_Pro_PK_v2.md` (2,052 שורות, 36+4 sections)"
    )




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

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🔭 סריקה**")
        if not today_tl.empty and "Ticker" in today_tl.columns:
            n_tickers = today_tl["Ticker"].nunique()
            peak = (today_tl.sort_values("Score", ascending=False)
                            .drop_duplicates("Ticker")) if "Score" in today_tl.columns else today_tl
            scores = pd.to_numeric(peak.get("Score", pd.Series(dtype=float)), errors="coerce")
            critical = int((scores >= CRITICAL_SCORE).sum())
            high     = int((scores >= TRADE_ENTRY_MIN_SCORE).sum())
            st.metric("מניות שנסרקו", n_tickers)
            st.metric(f"Critical ≥{CRITICAL_SCORE}", critical, delta=f"High ≥{TRADE_ENTRY_MIN_SCORE}: {high}")
        else:
            st.info("אין נתוני סריקה להיום")

    with col2:
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


def main():
    _PAGE_NAMES = [
        "🏠 Home",
        "💼 Portfolio Tracker",
        "🔬 Post Analysis",
        "📈 Score Tracker",
        "📅 Daily Summary",
        "📦 Timeline Archive",
        "🖥️ System Overview",
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
    elif page == "💼 Portfolio Tracker":
        portfolio_tracker_page()
    elif page == "🔬 Post Analysis":
        post_analysis_page()
    elif page == "📈 Score Tracker":
        score_tracker_page()
    elif page == "📅 Daily Summary":
        daily_summary_page()
    elif page == "📦 Timeline Archive":
        timeline_archive_page()
    elif page == "🖥️ System Overview":
        system_overview_page()

if __name__ == "__main__":
    main()
