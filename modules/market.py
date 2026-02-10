# -*- coding: utf-8 -*-
import streamlit as st
from datetime import datetime, timedelta
from config import get_market_index, get_cnn_fear_greed
import requests
import streamlit.components.v1 as components
import time
import yfinance as yf
from bs4 import BeautifulSoup
import pandas as pd
import re
from collections import Counter

try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')

def get_economic_calendar():
    if not INVESTPY_AVAILABLE:
        return get_fallback_economic_calendar()
    try:
        from_date = datetime.now().strftime('%d/%m/%Y')
        to_date = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
        calendar = investpy.economic_calendar(
            time_zone='GMT', time_filter='time_only',
            from_date=from_date, to_date=to_date,
            countries=['united states', 'euro zone'],
            importances=['high', 'medium', 'low']
        )
        events = []
        for _, row in calendar.head(10).iterrows():
            time_str = row['time']
            if time_str and time_str != '':
                try:
                    hour, minute = map(int, time_str.split(':'))
                    hour_es = (hour + 1) % 24
                    time_es = f"{hour_es:02d}:{minute:02d}"
                except:
                    time_es = time_str
            else:
                time_es = "TBD"
            importance_map = {'high': 'High', 'medium': 'Medium', 'low': 'Low'}
            impact = importance_map.get(row['importance'].lower(), 'Medium')
            events.append({
                "time": time_es, "event": row['event'], "imp": impact,
                "val": row.get('actual', '-'), "prev": row.get('previous', '-')
            })
        return events if events else get_fallback_economic_calendar()
    except:
        return get_fallback_economic_calendar()

def get_fallback_economic_calendar():
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

@st.cache_data(ttl=300)
def get_crypto_prices():
    try:
        crypto_symbols = {
            'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'BNB-USD': 'BNB',
            'SOL-USD': 'Solana', 'XRP-USD': 'XRP', 'ADA-USD': 'Cardano'
        }
        cryptos = []
        for symbol, name in crypto_symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    price_str = f"{current_price:,.2f}" if current_price >= 1 else f"{current_price:.4f}"
                    cryptos.append({
                        'symbol': symbol.replace('-USD', ''), 'name': name,
                        'price': price_str, 'change': f"{change_pct:+.2f}%",
                        'is_positive': change_pct >= 0
                    })
                    time.sleep(0.1)
            except:
                continue
        return cryptos if cryptos else get_fallback_crypto_prices()
    except:
        return get_fallback_crypto_prices()

def get_fallback_crypto_prices():
    return [
        {"symbol": "BTC", "name": "Bitcoin", "price": "68,984.88", "change": "-1.62%", "is_positive": False},
        {"symbol": "ETH", "name": "Ethereum", "price": "2,018.46", "change": "-4.05%", "is_positive": False},
        {"symbol": "BNB", "name": "BNB", "price": "618.43", "change": "-2.76%", "is_positive": False},
        {"symbol": "SOL", "name": "Solana", "price": "84.04", "change": "-3.07%", "is_positive": False},
        {"symbol": "XRP", "name": "XRP", "price": "1.40", "change": "-2.22%", "is_positive": False},
        {"symbol": "ADA", "name": "Cardano", "price": "0.52", "change": "-4.20%", "is_positive": False},
    ]

@st.cache_data(ttl=300)
def get_reddit_buzz():
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        top_10_tickers = []
        headers_elements = soup.find_all(['h2', 'h3', 'h4', 'div', 'span'])
        for header in headers_elements:
            header_text = header.get_text(strip=True).lower()
            if 'overall' in header_text and 'top' in header_text:
                parent = header.find_parent()
                if parent:
                    links = parent.find_all('a', href=re.compile(r'/reddit-buzz/\?ticker='))
                    for link in links[:10]:
                        ticker = link.get_text(strip=True).upper()
                        if ticker and ticker not in top_10_tickers and len(ticker) <= 5:
                            top_10_tickers.append(ticker)
        if not top_10_tickers:
            all_links = soup.find_all('a', href=re.compile(r'/reddit-buzz/\?ticker=[A-Z]+'))
            seen = set()
            for link in all_links:
                ticker = link.get_text(strip=True).upper()
                if ticker and ticker not in seen and len(ticker) <= 5 and ticker.isalpha():
                    top_10_tickers.append(ticker)
                    seen.add(ticker)
                    if len(top_10_tickers) >= 10:
                        break
        if not top_10_tickers:
            return get_fallback_reddit_tickers()
        return {
            'tickers': top_10_tickers[:10], 'source': 'BuzzTickr',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
    except:
        return get_fallback_reddit_tickers()

def get_fallback_reddit_tickers():
    return {
        'tickers': ["MSFT", "NVDA", "TSLA", "AAPL", "AMZN", "GOOGL", "META", "AMD", "PLTR", "GME"],
        'source': 'Fallback', 'timestamp': datetime.now().strftime('%H:%M:%S')
    }

@st.cache_data(ttl=60)
def get_financial_ticker_data():
    ticker_data = []
    all_symbols = {
        'ES=F': 'S&P 500 FUT', 'NQ=F': 'NASDAQ FUT', 'YM=F': 'DOW FUT', 'RTY=F': 'RUSSELL FUT',
        '^N225': 'NIKKEI', '^GDAXI': 'DAX', '^FTSE': 'FTSE 100',
        'GC=F': 'GOLD', 'SI=F': 'SILVER', 'CL=F': 'CRUDE OIL', 'NG=F': 'NAT GAS',
        'AAPL': 'AAPL', 'MSFT': 'MSFT', 'GOOGL': 'GOOGL', 'AMZN': 'AMZN',
        'NVDA': 'NVDA', 'META': 'META', 'TSLA': 'TSLA',
        'BTC-USD': 'BTC', 'ETH-USD': 'ETH'
    }
    for symbol, name in all_symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100
                price_str = f"{current:,.2f}" if current >= 100 else f"{current:.3f}"
                ticker_data.append({
                    'name': name, 'price': price_str,
                    'change': change_pct, 'is_positive': change_pct >= 0
                })
            time.sleep(0.05)
        except:
            continue
    return ticker_data

def generate_ticker_html():
    data = get_financial_ticker_data()
    if not data:
        data = [
            {'name': 'S&P 500 FUT', 'price': '5,890.25', 'change': 0.45, 'is_positive': True},
            {'name': 'NASDAQ FUT', 'price': '21,150.80', 'change': -0.23, 'is_positive': False},
            {'name': 'DOW FUT', 'price': '42,890.15', 'change': 0.67, 'is_positive': True},
            {'name': 'NIKKEI', 'price': '38,750.50', 'change': 1.24, 'is_positive': True},
            {'name': 'DAX', 'price': '21,340.75', 'change': -0.15, 'is_positive': False},
            {'name': 'GOLD', 'price': '2,865.40', 'change': 0.89, 'is_positive': True},
            {'name': 'SILVER', 'price': '32.45', 'change': 1.56, 'is_positive': True},
            {'name': 'CRUDE OIL', 'price': '73.85', 'change': -1.23, 'is_positive': False},
            {'name': 'BTC', 'price': '68,984.88', 'change': -1.62, 'is_positive': False},
            {'name': 'ETH', 'price': '2,018.46', 'change': -4.05, 'is_positive': False},
        ]
    ticker_items = []
    for item in data:
        color = "#00ffad" if item['is_positive'] else "#f23645"
        arrow = "▲" if item['is_positive'] else "▼"
        ticker_items.append(
            f'<span style="margin-right: 40px; white-space: nowrap;">'
            f'<span style="color: #fff; font-weight: bold;">{item["name"]}</span> '
            f'<span style="color: #ccc;">{item["price"]}</span> '
            f'<span style="color: {color};">{arrow} {item["change"]:+.2f}%</span>'
            f'</span>'
        )
    items_html = "".join(ticker_items)
    all_items = items_html + items_html
    return f"""
    <div style="background: linear-gradient(90deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%); border-bottom: 2px solid #2a3f5f; padding: 12px 0; overflow: hidden;">
        <div style="display: inline-block; white-space: nowrap; animation: ticker-scroll 30s linear infinite; padding-left: 100%;">{all_items}</div>
    </div>
    <style>@keyframes ticker-scroll {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}</style>
    """

@st.cache_data(ttl=300)
def get_sector_performance(timeframe="1D"):
    try:
        sector_etfs = {
            'XLK': ('Technology', 'Tecnología'), 
            'XLF': ('Financials', 'Financieros'),
            'XLV': ('Healthcare', 'Salud'), 
            'XLE': ('Energy', 'Energía'),
            'XLY': ('Consumer Disc.', 'Consumo Discrecional'), 
            'XLU': ('Utilities', 'Utilidades'),
            'XLI': ('Industrials', 'Industriales'), 
            'XLB': ('Materials', 'Materiales'),
            'XLP': ('Consumer Staples', 'Consumo Básico'), 
            'XLRE': ('Real Estate', 'Bienes Raíces'),
            'XLC': ('Communication', 'Comunicaciones')
        }

        period_map = {"1D": "2d", "3D": "5d", "1W": "10d", "1M": "1mo"}
        period = period_map.get(timeframe, "2d")
        sectors_data = []

        for symbol, (name_en, name_es) in sector_etfs.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if len(hist) >= 2:
                    if timeframe == "1D":
                        current, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                    elif timeframe == "3D":
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-4] if len(hist) >= 4 else hist['Close'].iloc[0]
                    elif timeframe == "1W":
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-6] if len(hist) >= 6 else hist['Close'].iloc[0]
                    else:
                        current, prev = hist['Close'].iloc[-1], hist['Close'].iloc[0]

                    change = ((current - prev) / prev) * 100
                    sectors_data.append({
                        'code': symbol, 
                        'name': name_en, 
                        'name_es': name_es,
                        'change': change
                    })
                time.sleep(0.05)
            except:
                continue

        return sectors_data if sectors_data else get_fallback_sectors(timeframe)
    except:
        return get_fallback_sectors(timeframe)

def get_fallback_sectors(timeframe="1D"):
    base = [
        ("XLK", "Technology", +6.02), ("XLF", "Financials", +0.99), 
        ("XLV", "Healthcare", +1.01), ("XLE", "Energy", +2.30),
        ("XLY", "Consumer Disc.", +1.13), ("XLU", "Utilities", +1.68),
        ("XLI", "Industrials", +3.26), ("XLB", "Materials", +3.91), 
        ("XLP", "Consumer Staples", +0.20), ("XLRE", "Real Estate", +3.33), 
        ("XLC", "Communication", +1.08)
    ]
    mult = {"1D": 1, "3D": 2.5, "1W": 4, "1M": 8}.get(timeframe, 1)
    return [{'code': c, 'name': n, 'name_es': n, 'change': v * mult} for c, n, v in base]

@st.cache_data(ttl=300)
def get_vix_term_structure():
    try:
        try:
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="5d")
            if len(vix_hist) >= 3:
                current_spot = vix_hist['Close'].iloc[-1]
                prev_spot = vix_hist['Close'].iloc[-2]
                spot_2days = vix_hist['Close'].iloc[-3]
            else:
                current_spot = 17.45
                prev_spot = 17.36
                spot_2days = 20.37
        except:
            current_spot = 17.45
            prev_spot = 17.36
            spot_2days = 20.37

        months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
        base_year = datetime.now().year

        current_curve = [current_spot]
        prev_curve = [prev_spot]
        two_days_curve = [spot_2days]

        is_contango = current_spot < 20

        for i in range(1, 9):
            if is_contango:
                current_curve.append(current_spot + (i * 0.9) + (i * i * 0.08))
                prev_curve.append(prev_spot + (i * 0.85) + (i * i * 0.07))
                two_days_curve.append(spot_2days + (i * 0.5) + (i * i * 0.05))
            else:
                current_curve.append(current_spot - (i * 0.3))
                prev_curve.append(prev_spot - (i * 0.25))
                two_days_curve.append(spot_2days - (i * 0.2))

        vix_data = []
        for i, month in enumerate(months):
            year = base_year if i < 10 else base_year + 1
            vix_data.append({
                'month': f"{month} {year}",
                'current': round(current_curve[i], 2),
                'previous': round(prev_curve[i], 2),
                'two_days': round(two_days_curve[i], 2)
            })

        if current_curve[-1] > current_curve[0]:
            state = "Contango"
            state_desc = "Typical in calm markets - Conducive to dip buying"
            state_color = "#00ffad"
            explanation = ("<b>Contango:</b> Futures price > Spot price. "
                         "The market expects volatility to decrease over time. "
                         "This is the normal state in calm markets. "
                         "Investors pay a premium for future protection, expecting volatility to mean revert lower.")
        else:
            state = "Backwardation"
            state_desc = "Market stress detected - Caution advised"
            state_color = "#f23645"
            explanation = ("<b>Backwardation:</b> Futures price < Spot price. "
                         "The market expects volatility to increase. "
                         "Immediate hedging demand drives up short-term volatility. "
                         "This signals fear of upcoming market moves.")

        return {
            'data': vix_data,
            'current_spot': current_spot,
            'prev_spot': prev_spot,
            'spot_2days': spot_2days,
            'state': state,
            'state_desc': state_desc,
            'state_color': state_color,
            'explanation': explanation,
            'is_contango': is_contango
        }
    except Exception as e:
        return get_fallback_vix_structure()

def get_fallback_vix_structure():
    return {
        'data': [
            {'month': 'Feb 2026', 'current': 17.45, 'previous': 17.36, 'two_days': 20.37},
            {'month': 'Mar 2026', 'current': 18.35, 'previous': 18.21, 'two_days': 20.87},
            {'month': 'Apr 2026', 'current': 19.25, 'previous': 19.06, 'two_days': 21.37},
            {'month': 'May 2026', 'current': 20.15, 'previous': 19.91, 'two_days': 21.87},
            {'month': 'Jun 2026', 'current': 21.05, 'previous': 20.76, 'two_days': 22.37},
            {'month': 'Jul 2026', 'current': 21.95, 'previous': 21.61, 'two_days': 22.87},
            {'month': 'Aug 2026', 'current': 22.85, 'previous': 22.46, 'two_days': 23.37},
            {'month': 'Sep 2026', 'current': 23.75, 'previous': 23.31, 'two_days': 23.87},
        ],
        'current_spot': 17.45,
        'prev_spot': 17.36,
        'spot_2days': 20.37,
        'state': 'Contango',
        'state_desc': 'Typical in calm markets - Conducive to dip buying',
        'state_color': '#00ffad',
        'explanation': 'Futures price > Spot. Market expects lower volatility ahead.',
        'is_contango': True
    }

def generate_vix_chart_html(vix_data):
    data = vix_data['data']
    months = [d['month'].split()[0] for d in data]
    current_levels = [d['current'] for d in data]
    prev_levels = [d['previous'] for d in data]
    two_days_levels = [d['two_days'] for d in data]

    chart_width, chart_height, padding = 340, 180, 35

    all_values = current_levels + prev_levels + two_days_levels
    min_level, max_level = min(all_values) - 0.5, max(all_values) + 0.5
    level_range = max_level - min_level

    def get_coords(values, color, is_dashed=False):
        points = []
        for i, level in enumerate(values):
            x = padding + (i / (len(values) - 1)) * (chart_width - 2 * padding)
            y = chart_height - padding - ((level - min_level) / level_range) * (chart_height - 2 * padding)
            points.append((x, y, level))

        points_str = " ".join([f"{x},{y}" for x, y, _ in points])
        dash_attr = 'stroke-dasharray="4,3"' if is_dashed else ''

        circles = ""
        for x, y, level in points:
            circles += f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" stroke="white" stroke-width="1"/>'

        return f'<polyline points="{points_str}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {dash_attr}/>{circles}'

    current_line = get_coords(current_levels, "#3b82f6", False)
    prev_line = get_coords(prev_levels, "#f97316", True)
    two_days_line = get_coords(two_days_levels, "#6b7280", True)

    y_axis = ""
    for i in range(5):
        val = min_level + (level_range * i / 4)
        y_pos = chart_height - padding - (i / 4) * (chart_height - 2 * padding)
        y_axis += f'<text x="{padding-8}" y="{y_pos+3}" text-anchor="end" fill="#666" font-size="9">{val:.1f}</text>'
        y_axis += f'<line x1="{padding}" y1="{y_pos}" x2="{chart_width-padding}" y2="{y_pos}" stroke="#1a1e26" stroke-width="1"/>'

    x_labels = ""
    for i, month in enumerate(months):
        x = padding + (i / (len(months) - 1)) * (chart_width - 2 * padding)
        x_labels += f'<text x="{x}" y="{chart_height-8}" text-anchor="middle" fill="#666" font-size="8">{month}</text>'

    legend_y = 15
    legend = f"""
    <rect x="{chart_width-175}" y="5" width="170" height="50" fill="#0c0e12" stroke="#1a1e26" rx="4"/>
    <line x1="{chart_width-170}" y1="{legend_y+5}" x2="{chart_width-155}" y2="{legend_y+5}" stroke="#3b82f6" stroke-width="2"/>
    <text x="{chart_width-150}" y="{legend_y+8}" fill="#888" font-size="8">Current (2/10): {vix_data['current_spot']:.2f}</text>

    <line x1="{chart_width-170}" y1="{legend_y+20}" x2="{chart_width-155}" y2="{legend_y+20}" stroke="#f97316" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="{chart_width-150}" y="{legend_y+23}" fill="#888" font-size="8">Previous (2/9): {vix_data['prev_spot']:.2f}</text>

    <line x1="{chart_width-170}" y1="{legend_y+35}" x2="{chart_width-155}" y2="{legend_y+35}" stroke="#6b7280" stroke-width="2" stroke-dasharray="4,3"/>
    <text x="{chart_width-150}" y="{legend_y+38}" fill="#888" font-size="8">2 Days Ago (2/8): {vix_data['spot_2days']:.2f}</text>
    """

    return f"""
    <div style="width: 100%; height: 200px; background: #0c0e12; border-radius: 8px; padding: 8px;">
        <svg width="100%" height="100%" viewBox="0 0 {chart_width} {chart_height}" preserveAspectRatio="xMidYMid meet">
            {y_axis}
            {two_days_line}
            {prev_line}
            {current_line}
            {x_labels}
            {legend}
            <text x="15" y="{chart_height/2}" text-anchor="middle" fill="#888" font-size="9" transform="rotate(-90, 15, {chart_height/2})">VIX Level</text>
        </svg>
    </div>
    """

@st.cache_data(ttl=300)
def get_crypto_fear_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and len(data['data']) > 0:
                item = data['data'][0]
                value = int(item['value'])
                classification = item['value_classification']
                timestamp = int(item['timestamp'])
                update_time = datetime.fromtimestamp(timestamp).strftime('%H:%M')

                return {
                    'value': value,
                    'classification': classification,
                    'timestamp': update_time,
                    'source': 'alternative.me'
                }

        return get_fallback_crypto_fear_greed()
    except:
        return get_fallback_crypto_fear_greed()

def get_fallback_crypto_fear_greed():
    return {
        'value': 50,
        'classification': 'Neutral',
        'timestamp': get_timestamp(),
        'source': 'alternative.me'
    }

@st.cache_data(ttl=600)
def get_earnings_calendar():
    try:
        mega_caps = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 
            'BRK-B', 'AVGO', 'WMT', 'JPM', 'V', 'MA', 'UNH', 'HD',
            'PG', 'JNJ', 'BAC', 'LLY', 'MRK', 'KO', 'PEP', 'ABBV',
            'COST', 'TMO', 'ADBE', 'NFLX', 'AMD', 'CRM', 'ACN'
        ]

        earnings_list = []

        for ticker in mega_caps[:15]:
            try:
                stock = yf.Ticker(ticker)
                calendar = stock.calendar

                if calendar is not None and not calendar.empty:
                    info = stock.info
                    market_cap = info.get('marketCap', 0) / 1e9

                    if market_cap >= 100:
                        next_earnings = calendar.index[0]
                        hour = next_earnings.hour if hasattr(next_earnings, 'hour') else 16
                        time_str = "Before Bell" if hour < 12 else "After Market"

                        days_until = (next_earnings - pd.Timestamp.now()).days

                        if days_until >= -1 and days_until <= 30:
                            earnings_list.append({
                                'ticker': ticker,
                                'date': next_earnings.strftime('%b %d'),
                                'time': time_str,
                                'impact': 'High',
                                'market_cap': f"${market_cap:.0f}B",
                                'days': days_until
                            })

                time.sleep(0.1)
            except:
                continue

        earnings_list.sort(key=lambda x: x['days'])

        if earnings_list:
            return earnings_list[:6]

        return get_fallback_earnings()
    except:
        return get_fallback_earnings()

def get_fallback_earnings():
    return [
        {"ticker": "AAPL", "date": "Feb 05", "time": "After Market", "impact": "High", "market_cap": "$3.4T"},
        {"ticker": "AMZN", "date": "Feb 05", "time": "After Market", "impact": "High", "market_cap": "$2.1T"},
        {"ticker": "GOOGL", "date": "Feb 06", "time": "Before Bell", "impact": "High", "market_cap": "$2.3T"},
        {"ticker": "META", "date": "Feb 07", "time": "After Market", "impact": "High", "market_cap": "$1.8T"},
    ]

@st.cache_data(ttl=600)
def get_insider_trading():
    try:
        api_key = st.secrets.get("FMP_API_KEY", None)

        if not api_key:
            return get_fallback_insider()

        symbols = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'META', 'GOOGL', 'AMZN', 'NFLX', 'AMD', 'CRM']
        all_trades = []

        for symbol in symbols:
            try:
                url = f"https://financialmodelingprep.com/api/v4/insider-trading?symbol={symbol}&limit=3&apikey={api_key}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    for trade in data:
                        transaction_type = trade.get('transactionType', '')
                        if 'P' in transaction_type:
                            trans = "BUY"
                        elif 'S' in transaction_type:
                            trans = "SELL"
                        else:
                            continue

                        shares = trade.get('securitiesTransacted', 0)
                        price = trade.get('price', 0)
                        amount = shares * price

                        if amount > 50000:
                            all_trades.append({
                                'ticker': symbol,
                                'insider': trade.get('reportingName', 'Executive')[:20],
                                'position': trade.get('typeOfOwner', 'Officer')[:15],
                                'type': trans,
                                'amount': f"${amount/1e6:.1f}M" if amount >= 1e6 else f"${amount/1e3:.0f}K",
                                'date': trade.get('transactionDate', 'Recent')
                            })
            except Exception as e:
                continue

        if all_trades:
            all_trades.sort(key=lambda x: float(x['amount'].replace('$','').replace('M','').replace('K','').replace(',','')), reverse=True)
            return all_trades[:6]

        return get_fallback_insider()

    except Exception as e:
        return get_fallback_insider()

def get_fallback_insider():
    return [
        {"ticker": "NVDA", "insider": "Jensen Huang", "position": "CEO", "type": "SELL", "amount": "$12.5M"},
        {"ticker": "TSLA", "insider": "Elon Musk", "position": "CEO", "type": "SELL", "amount": "$45.1M"},
        {"ticker": "META", "insider": "Mark Zuckerberg", "position": "CEO", "type": "SELL", "amount": "$28.3M"},
        {"ticker": "MSFT", "insider": "Satya Nadella", "position": "CEO", "type": "SELL", "amount": "$8.2M"},
        {"ticker": "AAPL", "insider": "Tim Cook", "position": "CEO", "type": "SELL", "amount": "$5.4M"},
        {"ticker": "AMZN", "insider": "Andy Jassy", "position": "CEO", "type": "SELL", "amount": "$3.1M"},
    ]

@st.cache_data(ttl=600)
def get_market_breadth():
    try:
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="6mo")
        if len(spy_hist) > 50:
            current = spy_hist['Close'].iloc[-1]
            sma50 = spy_hist['Close'].rolling(50).mean().iloc[-1]
            sma200 = spy_hist['Close'].rolling(200).mean().iloc[-1]
            deltas = spy_hist['Close'].diff()
            gains = deltas.where(deltas > 0, 0).rolling(14).mean()
            losses = (-deltas.where(deltas < 0, 0)).rolling(14).mean()
            rs = gains / losses
            rsi = 100 - (100 / (1 + rs.iloc[-1])) if not pd.isna(rs.iloc[-1]) else 50
            return {
                'price': current, 'sma50': sma50, 'sma200': sma200,
                'above_sma50': current > sma50, 'above_sma200': current > sma200,
                'golden_cross': sma50 > sma200, 'rsi': rsi,
                'trend': 'ALCISTA' if sma50 > sma200 else 'BAJISTA',
                'strength': 'FUERTE' if (current > sma50 and current > sma200) else 'DÉBIL'
            }
        return get_fallback_market_breadth()
    except:
        return get_fallback_market_breadth()

def get_fallback_market_breadth():
    return {
        'price': 695.50, 'sma50': 686.61, 'sma200': float('nan'),
        'above_sma50': True, 'above_sma200': False, 'golden_cross': False,
        'rsi': 59.2, 'trend': 'BAJISTA', 'strength': 'DÉBIL'
    }

def get_fallback_news():
    return [
        {"time": "19:45", "title": "Tesla supera expectatives de benefici", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "18:30", "title": "El PIB dels EUA creix un 2,3% en l'últim trimestre", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "16:15", "title": "Apple presenta resultats rècord gràcies a l'iPhone", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "14:00", "title": "La inflació subjacent es modera al 3,2%", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "12:30", "title": "Microsoft Cloud supera els 30.000M en ingressos", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "11:15", "title": "La Fed manté els tipus d'interès sense canvis", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "10:00", "title": "Amazon anuncia nova divisió d'intel·ligència artificial", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "09:30", "title": "NVIDIA presenta nous xips per a centres de dades", "impact": "Alto", "color": "#f23645", "link": "#"},
    ]

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    if not api_key:
        return get_fallback_news()
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=12)
        data = r.json()
        news_list = []
        for item in data[:8]:
            title = item.get("headline", "Sense titol")
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"
            lower = title.lower()
            impact, color = ("Alto", "#f23645") if any(k in lower for k in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "rate", "outlook"]) else ("Moderado", "#ff9800")
            news_list.append({"time": time_str, "title": title, "impact": impact, "color": color, "link": link})
        return news_list if news_list else get_fallback_news()
    except:
        return get_fallback_news()

def get_fed_liquidity():
    api_key = st.secrets.get("FRED_API_KEY", None)
    if not api_key:
        return "STABLE", "#ff9800", "API Key no configurada", "N/A", "N/A"
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            if len(observations) >= 2:
                latest_val = float(observations[0]['value'])
                prev_val = float(observations[1]['value'])
                date_latest = observations[0]['date']
                change = latest_val - prev_val
                if change < -100:
                    return "QT", "#f23645", "Quantitative Tightening", f"{latest_val/1000:.1f}T", date_latest
                elif change > 100:
                    return "QE", "#00ffad", "Quantitative Easing", f"{latest_val/1000:.1f}T", date_latest
                else:
                    return "STABLE", "#ff9800", "Balance sheet stable", f"{latest_val/1000:.1f}T", date_latest
        return "ERROR", "#888", "API no disponible", "N/A", "N/A"
    except:
        return "N/A", "#888", "Sense connexio", "N/A", "N/A"


def render():
    # CSS Global - Tooltips CENTRADOS en el módulo
    st.markdown("""
    <style>
    /* Tooltips CENTRADOS - flotan en el centro del módulo */
    .tooltip-wrapper {
        position: static;
        display: inline-block;
    }
    .tooltip-btn {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: #1a1e26;
        border: 2px solid #555;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #aaa;
        font-size: 14px;
        font-weight: bold;
        cursor: help;
    }
    .tooltip-content {
        display: none;
        position: fixed;
        width: 300px;
        background-color: #1e222d;
        color: #eee;
        text-align: left;
        padding: 15px;
        border-radius: 10px;
        z-index: 99999;
        font-size: 12px;
        border: 2px solid #3b82f6;
        box-shadow: 0 15px 40px rgba(0,0,0,0.9);
        line-height: 1.5;

        /* CENTRADO EN LA PANTALLA */
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);

        white-space: normal;
        word-wrap: break-word;
    }

    /* Mostrar tooltip en hover */
    .tooltip-wrapper:hover .tooltip-content {
        display: block;
    }

    /* Timestamp */
    .update-timestamp {
        text-align: center;
        color: #555;
        font-size: 10px;
        padding: 6px 0;
        font-family: 'Courier New', monospace;
        border-top: 1px solid #1a1e26;
        background: #0c0e12;
        flex-shrink: 0;
    }

    /* Contenedores - altura 340px */
    .module-container { 
        border: 1px solid #1a1e26; 
        border-radius: 10px; 
        overflow: hidden; 
        background: #11141a; 
        height: 340px;
        display: flex;
        flex-direction: column;
        margin-bottom: 0;
    }
    .module-header { 
        background: #0c0e12; 
        padding: 10px 12px; 
        border-bottom: 1px solid #1a1e26; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        flex-shrink: 0;
    }
    .module-title { 
        margin: 0; 
        color: white; 
        font-size: 13px; 
        font-weight: bold; 
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .module-content { 
        flex: 1;
        overflow-y: auto;
        padding: 10px;
    }

    /* Sector rotation */
    .sector-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
        height: 100%;
    }
    .sector-item {
        background: #0c0e12;
        border: 1px solid #1a1e26;
        border-radius: 6px;
        padding: 8px 4px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .sector-code { color: #666; font-size: 9px; font-weight: bold; margin-bottom: 2px; }
    .sector-name { color: white; font-size: 10px; font-weight: 600; margin-bottom: 4px; line-height: 1.2; }
    .sector-change { font-size: 11px; font-weight: bold; }

    /* Select nativo */
    .sector-select {
        background: #1a1e26;
        color: white;
        border: 1px solid #2a3f5f;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
        cursor: pointer;
    }
    .sector-select:hover { border-color: #3b82f6; }

    /* Fear & Greed */
    .fng-legend { display: flex; justify-content: space-between; width: 100%; margin-top: 10px; font-size: 0.6rem; color: #888; text-align: center; }
    .fng-legend-item { flex: 1; padding: 0 2px; }
    .fng-color-box { width: 100%; height: 4px; margin-bottom: 3px; border-radius: 2px; }

    /* Columnas */
    .stColumns { gap: 0.5rem !important; }
    .stColumn { padding: 0 0.25rem !important; }
    .element-container { margin-bottom: 0.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # Ticker
    ticker_html = generate_ticker_html()
    components.html(ticker_html, height=50, scrolling=False)
    st.markdown('<h1 style="margin-top:15px; text-align:center; margin-bottom:15px; font-size: 1.5rem;">Market Dashboard</h1>', unsafe_allow_html=True)

    # FILA 1
    col1, col2, col3 = st.columns(3)

    with col1:
        indices_html = ""
        for t, n in [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]:
            idx_val, idx_change = get_market_index(t)
            color = "#00ffad" if idx_change >= 0 else "#f23645"
            indices_html += f'''<div style="background:#0c0e12; padding:10px 12px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:12px;">{n}</div><div style="color:#555; font-size:9px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:12px;">{idx_val:,.2f}</div><div style="color:{color}; font-size:10px; font-weight:bold;">{idx_change:+.2f}%</div></div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Market Indices</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Rendiment en temps real dels principals indexs borsaris dels EUA.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 12px;">{indices_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        events = get_economic_calendar()
        impact_colors = {'High': '#f23645', 'Medium': '#ff9800', 'Low': '#4caf50'}
        events_html = ""
        for ev in events[:6]:
            imp_color = impact_colors.get(ev['imp'], '#888')
            events_html += f'''<div style="padding:8px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:9px; width:40px; font-family:monospace;">{ev["time"]}</div>
                <div style="flex-grow:1; margin-left:8px;">
                    <div style="color:white; font-size:10px; font-weight:500; line-height:1.2;">{ev["event"]}</div>
                    <div style="color:{imp_color}; font-size:7px; font-weight:bold; text-transform:uppercase; margin-top:2px;">● {ev["imp"]}</div>
                </div>
                <div style="text-align:right; min-width:45px;">
                    <div style="color:white; font-size:10px; font-weight:bold;">{ev["val"]}</div>
                </div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Calendari Economic</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Calendari economic en temps real (hora espanyola CET/CEST).</div>
                </div>
            </div>
            <div class="module-content">{events_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        reddit_data = get_reddit_buzz()
        tickers = reddit_data.get('tickers', [])
        reddit_html_items = []
        for i, ticker in enumerate(tickers[:8], 1):
            rank_bg = "#f23645" if i <= 3 else "#1a1e26"
            rank_color = "white" if i <= 3 else "#888"
            trend_text = "HOT 🔥" if i <= 3 else "Trending"
            trend_bg = "rgba(242, 54, 69, 0.2)" if i <= 3 else "rgba(0, 255, 173, 0.1)"
            trend_color = "#f23645" if i <= 3 else "#00ffad"
            item_html = f'''<div style="display: flex; align-items: center; padding: 8px 12px; border-bottom: 1px solid #1a1e26;">
                <div style="width: 24px; height: 24px; border-radius: 50%; background: {rank_bg}; display: flex; align-items: center; justify-content: center; color: {rank_color}; font-weight: bold; font-size: 10px; margin-right: 10px;">{i}</div>
                <div style="flex: 1;"><div style="color: #00ffad; font-weight: bold; font-size: 12px;">${ticker}</div><div style="color: #666; font-size: 8px;">Buzzing on Reddit</div></div>
                <div style="color: {trend_color}; font-size: 9px; font-weight: bold; background: {trend_bg}; padding: 2px 6px; border-radius: 3px;">{trend_text}</div>
            </div>'''
            reddit_html_items.append(item_html)
        reddit_content = "".join(reddit_html_items)

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Reddit Social Pulse</div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="background: #2a3f5f; color: #00ffad; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">Top {len(tickers)}</span>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Top 10 tickers mes mencionats a Reddit.</div>
                    </div>
                </div>
            </div>
            <div class="module-content" style="padding: 0;">{reddit_content}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)


    # FILA 2
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val_display, label, col, bar_width = "50", "NEUTRAL", "#ff9800", 50
        else:
            val_display = val
            bar_width = val
            if val <= 24: label, col = "EXTREME FEAR", "#d32f2f"
            elif val <= 44: label, col = "FEAR", "#f57c00"
            elif val <= 55: label, col = "NEUTRAL", "#ff9800"
            elif val <= 75: label, col = "GREED", "#4caf50"
            else: label, col = "EXTREME GREED", "#00ffad"

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Fear & Greed Index</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Index CNN Fear & Greed – mesura el sentiment del mercat.</div>
                </div>
            </div>
            <div class="module-content" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:15px;">
                <div style="font-size:3.5rem; font-weight:bold; color:{col};">{val_display}</div>
                <div style="color:white; font-size:1rem; letter-spacing:1px; font-weight:bold; margin:8px 0;">{label}</div>
                <div style="width:90%; background:#0c0e12; height:12px; border-radius:6px; margin:10px 0; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{bar_width}%; background:{col}; height:100%;"></div>
                </div>
                <div class="fng-legend">
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Extreme<br>Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Greed</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Extreme<br>Greed</div></div>
                </div>
            </div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    # SECTOR ROTATION - CON SELECT FUNCIONAL
    with c2:
        if 'sector_tf' not in st.session_state:
            st.session_state.sector_tf = "1 Day"

        tf_options = ["1 Day", "3 Days", "1 Week", "1 Month"]
        tf_map = {"1 Day": "1D", "3 Days": "3D", "1 Week": "1W", "1 Month": "1M"}

        # Crear opciones HTML
        options_html = ""
        for opt in tf_options:
            selected = "selected" if opt == st.session_state.sector_tf else ""
            options_html += f'<option value="{opt}" {selected}>{opt}</option>'

        tf_code = tf_map.get(st.session_state.sector_tf, "1D")
        sectors = get_sector_performance(tf_code)

        sectors_html = ""
        for sector in sectors:
            code, name, change = sector['code'], sector['name'], sector['change']

            if change >= 2: 
                bg_color, border_color, text_color = "#00ffad22", "#00ffad", "#00ffad"
            elif change >= 0.5: 
                bg_color, border_color, text_color = "#00ffad18", "#00ffad", "#00ffad"
            elif change >= 0: 
                bg_color, border_color, text_color = "#00ffad10", "#00ffad88", "#00ffad"
            elif change >= -0.5: 
                bg_color, border_color, text_color = "#f2364510", "#f2364588", "#f23645"
            elif change >= -2: 
                bg_color, border_color, text_color = "#f2364518", "#f23645", "#f23645"
            else: 
                bg_color, border_color, text_color = "#f2364522", "#f23645", "#f23645"

            sectors_html += f'''
            <div class="sector-item" style="background:{bg_color}; border-color:{border_color};">
                <div class="sector-code">{code}</div>
                <div class="sector-name">{name}</div>
                <div class="sector-change" style="color:{text_color};">{change:+.2f}%</div>
            </div>'''

        # HTML con select nativo - USANDO st.query_params PARA FUNCIONALIDAD
        header_html = f'''
        <div class="module-container">
            <div class="module-header" style="justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="module-title">Sector Rotation</div>
                    <div class="tooltip-wrapper">
                        <div class="tooltip-btn">?</div>
                        <div class="tooltip-content">Rendiment dels sectors via ETFs sectorials.</div>
                    </div>
                </div>
                <select class="sector-select" id="sector-select" onchange="updateSector(this.value)">
                    {options_html}
                </select>
            </div>
            <div class="module-content" style="padding: 8px;">
                <div class="sector-grid">{sectors_html}</div>
            </div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        <script>
            function updateSector(value) {{
                // Enviar a Streamlit usando query params
                const url = new URL(window.location);
                url.searchParams.set('sector_tf', value);
                window.history.pushState({{}}, '', url);
                window.location.reload();
            }}
            // Restaurar selección
            const urlParams = new URLSearchParams(window.location.search);
            const savedValue = urlParams.get('sector_tf');
            if (savedValue) {{
                document.getElementById('sector-select').value = savedValue;
            }}
        </script>
        '''
        st.markdown(header_html, unsafe_allow_html=True)

        # Manejar el cambio desde query params
        if 'sector_tf' in st.query_params:
            new_tf = st.query_params['sector_tf']
            if new_tf != st.session_state.sector_tf and new_tf in tf_options:
                st.session_state.sector_tf = new_tf
                st.rerun()

    with c3:
        crypto_fg = get_crypto_fear_greed()
        val = crypto_fg['value']

        if val <= 24: label, col = "EXTREME FEAR", "#d32f2f"
        elif val <= 44: label, col = "FEAR", "#f57c00"
        elif val <= 55: label, col = "NEUTRAL", "#ff9800"
        elif val <= 75: label, col = "GREED", "#4caf50"
        else: label, col = "EXTREME GREED", "#00ffad"

        bar_width = val

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Crypto Fear & Greed</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Crypto Fear & Greed Index – mesura el sentiment del mercat de criptomonedes.</div>
                </div>
            </div>
            <div class="module-content" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:15px;">
                <div style="font-size:3.5rem; font-weight:bold; color:{col};">{val}</div>
                <div style="color:white; font-size:1rem; letter-spacing:1px; font-weight:bold; margin:8px 0;">{label}</div>
                <div style="width:90%; background:#0c0e12; height:12px; border-radius:6px; margin:10px 0; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{bar_width}%; background:{col}; height:100%;"></div>
                </div>
                <div class="fng-legend">
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Extreme<br>Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Greed</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Extreme<br>Greed</div></div>
                </div>
            </div>
            <div class="update-timestamp">Updated: {crypto_fg['timestamp']} • {crypto_fg['source']}</div>
        </div>
        ''', unsafe_allow_html=True)


    # FILA 3
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    with f3c1:
        earnings = get_earnings_calendar()
        earn_html = ""
        for item in earnings:
            impact_color = "#f23645" if item['impact'] == "High" else "#888"
            earn_html += f'''<div style="background:#0c0e12; padding:8px; border-radius:6px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:#00ffad; font-weight:bold; font-size:11px;">{item['ticker']}</div><div style="color:#555; font-size:8px;">{item['date']}</div></div>
            <div style="text-align:center; flex:1; margin:0 8px;">
                <div style="color:#666; font-size:8px;">{item['time']}</div>
                <div style="color:#888; font-size:9px;">{item['market_cap']}</div>
            </div>
            <div style="text-align:right;"><span style="color:{impact_color}; font-size:8px; font-weight:bold;">● {item['impact']}</span></div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Earnings Calendar</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Earnings de mega-cap companies (>$100B).</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{earn_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with f3c2:
        insiders = get_insider_trading()
        insider_html = ""
        for item in insiders:
            type_color = "#00ffad" if item['type'] == "BUY" else "#f23645"
            insider_html += f'''<div style="background:#0c0e12; padding:8px; border-radius:6px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
            <div><div style="color:white; font-weight:bold; font-size:10px;">{item['ticker']}</div><div style="color:#555; font-size:8px;">{item['position']}</div></div>
            <div style="text-align:right;"><div style="color:{type_color}; font-weight:bold; font-size:9px;">{item['type']}</div><div style="color:#888; font-size:8px;">{item['amount']}</div></div>
            </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Insider Tracker</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Insider trading activity (> $50k) via SEC Form 4.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 10px;">{insider_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with f3c3:
        news = fetch_finnhub_news()
        news_items_html = []
        for item in news[:8]:
            safe_title = item['title'].replace('"', '&quot;').replace("'", '&#39;')
            news_item = (
                '<div style="padding: 8px 12px; border-bottom: 1px solid #1a1e26;">'
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:3px;">'
                '<span style="color:#888;font-size:0.7rem;font-family:monospace;">' + item['time'] + '</span>'
                '<span style="padding: 1px 6px; border-radius: 8px; font-size: 0.65rem; font-weight: bold; background-color:' + item['color'] + '22;color:' + item['color'] + ';">' + item['impact'] + '</span>'
                '</div>'
                '<div style="color:white;font-size:0.8rem;line-height:1.2;margin-bottom:4px;">' + safe_title + '</div>'
                '<a href="' + item['link'] + '" target="_blank" style="color: #00ffad; text-decoration: none; font-size: 0.75rem;">→ Llegir més</a>'
                '</div>'
            )
            news_items_html.append(news_item)
        news_content = "".join(news_items_html)

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">Noticies d'Alt Impacte</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Noticies d'alt impacte via Finnhub API.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 0; overflow-y: auto;">{news_content}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    # FILA 4
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)

    with f4c1:
        vix = get_market_index("^VIX")
        vix_color = "#00ffad" if vix[1] >= 0 else "#f23645"
        vix_html = f'''<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
            <div style="font-size:3rem; font-weight:bold; color:white;">{vix[0]:.2f}</div>
            <div style="color:#f23645; font-size:1rem; font-weight:bold; margin-top:5px;">VIX INDEX</div>
            <div style="color:{vix_color}; font-size:0.9rem; font-weight:bold;">{vix[1]:+.2f}%</div>
            <div style="color:#555; font-size:0.75rem; margin-top:10px;">Volatility Index</div>
        </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">VIX Index</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Index de volatilitat CBOE (VIX).</div>
                </div>
            </div>
            <div class="module-content" style="padding: 15px;">{vix_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)

    with f4c2:
        status, color, desc, assets, date = get_fed_liquidity()
        fed_html = f'''<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
            <div style="font-size:3.5rem; font-weight:bold; color:{color};">{status}</div>
            <div style="color:white; font-size:1rem; font-weight:bold; margin:8px 0;">{desc}</div>
            <div style="background:#0c0e12; padding:10px 16px; border-radius:6px; border:1px solid #1a1e26;">
                <div style="font-size:1.4rem; color:white;">{assets}</div>
                <div style="color:#888; font-size:0.75rem;">Total Assets</div>
            </div>
        </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">FED Liquidity Policy</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Politica de liquiditat de la FED via FRED.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 15px;">{fed_html}</div>
            <div class="update-timestamp">Updated: {date}</div>
        </div>
        ''', unsafe_allow_html=True)

    with f4c3:
        tnx = get_market_index("^TNX")
        tnx_color = "#00ffad" if tnx[1] >= 0 else "#f23645"
        tnx_html = f'''<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
            <div style="font-size:3rem; font-weight:bold; color:white;">{tnx[0]:.2f}%</div>
            <div style="color:white; font-size:1rem; font-weight:bold; margin-top:5px;">10Y TREASURY</div>
            <div style="color:{tnx_color}; font-size:0.9rem; font-weight:bold;">{tnx[1]:+.2f}%</div>
            <div style="color:#555; font-size:0.75rem; margin-top:10px;">US 10-Year Yield</div>
        </div>'''

        st.markdown(f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">10Y Treasury Yield</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">Rendiment del bo del Tresor dels EUA a 10 anys.</div>
                </div>
            </div>
            <div class="module-content" style="padding: 15px;">{tnx_html}</div>
            <div class="update-timestamp">Updated: {get_timestamp()}</div>
        </div>
        ''', unsafe_allow_html=True)


    # FILA 5 - Módulos HTML
    st.write("")
    f5c1, f5c2, f5c3 = st.columns(3)

    # Market Breadth
    with f5c1:
        breadth = get_market_breadth()
        trend_color = "#00ffad" if breadth['trend'] == 'ALCISTA' else "#f23645"
        strength_color = "#00ffad" if breadth['strength'] == 'FUERTE' else "#ff9800"
        sma50_color = "#00ffad" if breadth['above_sma50'] else "#f23645"
        sma200_color = "#00ffad" if breadth['above_sma200'] else "#f23645"
        golden_color = "#00ffad" if breadth['golden_cross'] else "#f23645"
        golden_text = "GOLDEN CROSS ✓" if breadth['golden_cross'] else "DEATH CROSS ✗"
        rsi = breadth['rsi']
        if rsi > 70: rsi_color, rsi_text = "#f23645", "OVERBOUGHT"
        elif rsi < 30: rsi_color, rsi_text = "#00ffad", "OVERSOLD"
        else: rsi_color, rsi_text = "#ff9800", "NEUTRAL"

        tooltip_text = "Market Breadth: SMA50/200, Golden/Death Cross, RSI(14)"
        timestamp_str = get_timestamp()

        breadth_html = f'''<!DOCTYPE html><html><head><style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .container {{ border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; background: #11141a; width: 100%; height: 340px; display: flex; flex-direction: column; }}
        .header {{ background: #0c0e12; padding: 10px 12px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }}
        .title {{ color: white; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
        .tooltip-wrapper {{ position: static; display: inline-block; }}
        .tooltip-btn {{ width: 24px; height: 24px; border-radius: 50%; background: #1a1e26; border: 2px solid #555; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 14px; font-weight: bold; cursor: help; }}
        .tooltip-content {{ display: none; position: fixed; width: 300px; background-color: #1e222d; color: #eee; text-align: left; padding: 15px; border-radius: 10px; z-index: 99999; font-size: 12px; border: 2px solid #3b82f6; box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5; left: 50%; top: 50%; transform: translate(-50%, -50%); white-space: normal; word-wrap: break-word; }}
        .tooltip-wrapper:hover .tooltip-content {{ display: block; }}
        .content {{ background: #11141a; flex: 1; overflow-y: auto; padding: 10px; }}
        .metric-box {{ background: #0c0e12; border: 1px solid #1a1e26; border-radius: 6px; padding: 8px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }}
        .metric-label {{ color: #888; font-size: 10px; }}
        .metric-value {{ font-size: 13px; font-weight: bold; }}
        .rsi-gauge {{ width: 100%; height: 14px; background: linear-gradient(to right, #00ffad 0%, #ff9800 50%, #f23645 100%); border-radius: 7px; position: relative; margin: 6px 0; }}
        .rsi-marker {{ position: absolute; top: -3px; width: 3px; height: 20px; background: white; border-radius: 2px; transform: translateX(-50%); }}
        .update-timestamp {{ text-align: center; color: #555; font-size: 10px; padding: 6px 0; font-family: 'Courier New', monospace; border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0; }}
        </style></head><body>
        <div class="container">
            <div class="header">
                <div class="title">Market Breadth</div>
                <div class="tooltip-wrapper">
                    <div class="tooltip-btn">?</div>
                    <div class="tooltip-content">{tooltip_text}</div>
                </div>
            </div>
            <div class="content">
                <div class="metric-box">
                    <span class="metric-label">SPY Price</span>
                    <span class="metric-value" style="color: white;">${breadth['price']:.2f}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">SMA 50</span>
                    <span class="metric-value" style="color: {sma50_color};">${breadth['sma50']:.2f}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">SMA 200</span>
                    <span class="metric-value" style="color: {sma200_color};">${breadth['sma200']:.2f}</span>
                </div>
                <div class="metric-box" style="border-color: {golden_color}44; background: {golden_color}11;">
                    <span class="metric-label">Signal</span>
                    <span class="metric-value" style="color: {golden_color};">{golden_text}</span>
                </div>
                <div style="margin-top: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                        <span class="metric-label">RSI (14)</span>
                        <span style="color: {rsi_color}; font-size: 11px; font-weight: bold;">{rsi:.1f} - {rsi_text}</span>
                    </div>
                    <div class="rsi-gauge">
                        <div class="rsi-marker" style="left: {min(rsi, 100)}%;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 8px; color: #555; margin-top: 2px;">
                        <span>0</span><span>30</span><span>50</span><span>70</span><span>100</span>
                    </div>
                </div>
                <div style="margin-top: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                    <div class="metric-box" style="text-align: center; margin-bottom: 0; padding: 6px;">
                        <div class="metric-label">Trend</div>
                        <div style="color: {trend_color}; font-size: 11px; font-weight: bold;">{breadth['trend']}</div>
                    </div>
                    <div class="metric-box" style="text-align: center; margin-bottom: 0; padding: 6px;">
                        <div class="metric-label">Strength</div>
                        <div style="color: {strength_color}; font-size: 11px; font-weight: bold;">{breadth['strength']}</div>
                    </div>
                </div>
            </div>
            <div class="update-timestamp">Updated: {timestamp_str}</div>
        </div>
        </body></html>'''
        components.html(breadth_html, height=340, scrolling=False)


    # VIX Term Structure
    with f5c2:
        vix_data = get_vix_term_structure()
        state_color = vix_data['state_color']
        state_bg = f"{state_color}15"
        chart_html = generate_vix_chart_html(vix_data)
        tooltip_text = f"VIX Term Structure: {vix_data['state']}. {vix_data['explanation']}"
        data_points = vix_data['data']
        slope_pct = ((data_points[-1]['current'] - data_points[0]['current']) / data_points[0]['current']) * 100 if len(data_points) >= 2 else 0
        timestamp_str = get_timestamp()

        vix_html_full = f"""
<!DOCTYPE html><html><head><style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
.container {{ border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; background: #11141a; width: 100%; height: 340px; display: flex; flex-direction: column; }}
.header {{ background: #0c0e12; padding: 10px 12px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; position: relative; }}
.title {{ color: white; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }}
.state-badge {{ background: {state_bg}; color: {state_color}; padding: 4px 10px; border-radius: 10px; font-size: 10px; font-weight: bold; border: 1px solid {state_color}33; position: absolute; left: 50%; transform: translateX(-50%); }}
.tooltip-wrapper {{ position: static; display: inline-block; }}
.tooltip-btn {{ width: 22px; height: 22px; border-radius: 50%; background: #1a1e26; border: 1px solid #444; display: flex; align-items: center; justify-content: center; color: #888; font-size: 12px; font-weight: bold; cursor: help; }}
.tooltip-content {{ display: none; position: fixed; width: 300px; background-color: #1e222d; color: #eee; text-align: left; padding: 15px; border-radius: 10px; z-index: 99999; font-size: 12px; border: 2px solid #3b82f6; box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5; left: 50%; top: 50%; transform: translate(-50%, -50%); white-space: normal; word-wrap: break-word; }}
.tooltip-wrapper:hover .tooltip-content {{ display: block; }}
.content {{ background: #11141a; flex: 1; overflow-y: auto; padding: 10px; }}
.spot-box {{ display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 6px; padding: 10px 14px; margin-bottom: 10px; }}
.spot-label {{ color: #888; font-size: 10px; font-weight: 500; }}
.spot-value {{ color: white; font-size: 20px; font-weight: bold; }}
.spot-change {{ color: {state_color}; font-size: 10px; font-weight: bold; margin-top: 2px; }}
.chart-wrapper {{ background: #0c0e12; border: 1px solid #1a1e26; border-radius: 6px; padding: 8px; margin-bottom: 8px; }}
.insight-box {{ background: {state_bg}; border: 1px solid {state_color}22; border-radius: 6px; padding: 8px 10px; }}
.insight-title {{ color: {state_color}; font-weight: bold; font-size: 11px; margin-bottom: 2px; }}
.insight-desc {{ color: #aaa; font-size: 10px; line-height: 1.3; }}
.update-timestamp {{ text-align: center; color: #555; font-size: 10px; padding: 6px 0; font-family: 'Courier New', monospace; border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0; }}
</style></head><body>
<div class="container">
    <div class="header">
        <div class="title">VIX Term Structure</div>
        <span class="state-badge">{vix_data['state']}</span>
        <div class="tooltip-wrapper">
            <div class="tooltip-btn">?</div>
            <div class="tooltip-content">{tooltip_text}</div>
        </div>
    </div>
    <div class="content">
        <div class="spot-box">
            <div>
                <div class="spot-label">VIX Spot</div>
                <div class="spot-change">{slope_pct:+.1f}% vs Far Month</div>
            </div>
            <div class="spot-value">{vix_data['current_spot']:.2f}</div>
        </div>
        <div class="chart-wrapper">
            {chart_html}
        </div>
        <div class="insight-box">
            <div class="insight-title">● {vix_data['state']}</div>
            <div class="insight-desc">{vix_data['state_desc']}</div>
        </div>
    </div>
    <div class="update-timestamp">Updated: {timestamp_str}</div>
</div>
</body></html>
"""
        components.html(vix_html_full, height=340, scrolling=False)

    # Crypto Pulse
    with f5c3:
        try:
            cryptos = get_crypto_prices()
        except:
            cryptos = get_fallback_crypto_prices()

        crypto_items_html = []
        for crypto in cryptos[:6]:
            symbol = str(crypto.get('symbol', 'N/A'))
            name = str(crypto.get('name', 'Unknown'))
            price = str(crypto.get('price', '0.00'))
            change = str(crypto.get('change', '0%'))
            color = "#00ffad" if crypto.get('is_positive', True) else "#f23645"
            item_html = (
                '<div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 6px; padding: 8px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">'
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<div style="color: #00ffad; font-weight: bold; font-size: 12px;">' + symbol + '</div>'
                '<div style="color: #555; font-size: 9px;">' + name + '</div></div>'
                '<div style="text-align: right;">'
                '<div style="color: white; font-size: 12px; font-weight: bold;">$' + price + '</div>'
                '<div style="color: ' + color + '; font-size: 10px; font-weight: bold;">' + change + '</div></div></div>'
            )
            crypto_items_html.append(item_html)
        crypto_content = "".join(crypto_items_html)
        timestamp_str = get_timestamp()

        crypto_html_full = '''<!DOCTYPE html><html><head><style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .container { border: 1px solid #1a1e26; border-radius: 10px; overflow: hidden; background: #11141a; width: 100%; height: 340px; display: flex; flex-direction: column; }
        .header { background: #0c0e12; padding: 10px 12px; border-bottom: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        .title { color: white; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
        .tooltip-wrapper { position: static; display: inline-block; }
        .tooltip-btn { width: 24px; height: 24px; border-radius: 50%; background: #1a1e26; border: 2px solid #555; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 14px; font-weight: bold; cursor: help; }
        .tooltip-content { display: none; position: fixed; width: 300px; background-color: #1e222d; color: #eee; text-align: left; padding: 15px; border-radius: 10px; z-index: 99999; font-size: 12px; border: 2px solid #3b82f6; box-shadow: 0 15px 40px rgba(0,0,0,0.9); line-height: 1.5; left: 50%; top: 50%; transform: translate(-50%, -50%); white-space: normal; word-wrap: break-word; }
        .tooltip-wrapper:hover .tooltip-content { display: block; }
        .content { background: #11141a; flex: 1; overflow-y: auto; padding: 10px; }
        .update-timestamp { text-align: center; color: #555; font-size: 10px; padding: 6px 0; font-family: 'Courier New', monospace; border-top: 1px solid #1a1e26; background: #0c0e12; flex-shrink: 0; }
        </style></head><body><div class="container">
        <div class="header"><div class="title">Crypto Pulse</div><div class="tooltip-wrapper"><div class="tooltip-btn">?</div><div class="tooltip-content">Preus reals de criptomonedes via Yahoo Finance.</div></div></div>
        <div class="content">''' + crypto_content + '''</div>
        <div class="update-timestamp">Updated: ''' + timestamp_str + '''</div>
        </div></body></html>'''
        components.html(crypto_html_full, height=340, scrolling=False)

if __name__ == "__main__":
    render()











