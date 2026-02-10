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

# ============================================================
# FUNCIONES AUXILIARES - DATOS REALES
# ============================================================

def get_economic_calendar():
    if not INVESTPY_AVAILABLE:
        return get_fallback_economic_calendar()

    try:
        from_date = datetime.now().strftime('%d/%m/%Y')
        to_date = (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')

        calendar = investpy.economic_calendar(
            time_zone='GMT',
            time_filter='time_only',
            from_date=from_date,
            to_date=to_date,
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
                "time": time_es,
                "event": row['event'],
                "imp": impact,
                "val": row.get('actual', '-'),
                "prev": row.get('previous', '-')
            })

        return events if events else get_fallback_economic_calendar()

    except Exception as e:
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
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum', 
            'BNB-USD': 'BNB',
            'SOL-USD': 'Solana',
            'XRP-USD': 'XRP'
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

                    if current_price >= 1000:
                        price_str = f"{current_price:,.2f}"
                    elif current_price >= 1:
                        price_str = f"{current_price:,.2f}"
                    else:
                        price_str = f"{current_price:.4f}"

                    change_str = f"{change_pct:+.2f}%"
                    is_positive = change_pct >= 0

                    cryptos.append({
                        'symbol': symbol.replace('-USD', ''),
                        'name': name,
                        'price': price_str,
                        'change': change_str,
                        'is_positive': is_positive
                    })

                    time.sleep(0.2)

            except Exception as e:
                continue

        if not cryptos:
            return get_fallback_crypto_prices()

        return cryptos

    except Exception as e:
        return get_fallback_crypto_prices()

def get_fallback_crypto_prices():
    return [
        {"symbol": "BTC", "name": "Bitcoin", "price": "104,231.50", "change": "+2.4%", "is_positive": True},
        {"symbol": "ETH", "name": "Ethereum", "price": "3,120.12", "change": "-1.1%", "is_positive": False},
        {"symbol": "BNB", "name": "BNB", "price": "685.45", "change": "+0.8%", "is_positive": True},
        {"symbol": "SOL", "name": "Solana", "price": "245.88", "change": "+5.7%", "is_positive": True},
        {"symbol": "XRP", "name": "XRP", "price": "3.15", "change": "-2.3%", "is_positive": False},
    ]

@st.cache_data(ttl=300)
def get_reddit_buzz():
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

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
                if (ticker and ticker not in seen and len(ticker) <= 5 
                    and ticker.isalpha() and len(ticker) >= 1):
                    top_10_tickers.append(ticker)
                    seen.add(ticker)
                    if len(top_10_tickers) >= 10:
                        break

        if not top_10_tickers:
            text = soup.get_text()
            ticker_matches = re.findall(r'\$([A-Z]{1,5})\b', text)
            ticker_counts = Counter(ticker_matches)
            exclude = {'A', 'I', 'EL', 'LA', 'DE', 'EN', 'ES', 'SE', 'AL', 'DEL', 'LAS', 'LOS', 'USD', 'CEO', 'CFO', 'CTO', 'AI', 'IPO', 'ETF', 'EPS', 'GDP', 'FED', 'SPY', 'QQQ'}
            filtered = [(t, c) for t, c in ticker_counts.most_common(20) if t not in exclude and len(t) >= 1]
            top_10_tickers = [t for t, c in filtered[:10]]

        if not top_10_tickers:
            return get_fallback_reddit_tickers()

        return {
            'tickers': top_10_tickers[:10],
            'source': 'BuzzTickr',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }

    except Exception as e:
        return get_fallback_reddit_tickers()

def get_fallback_reddit_tickers():
    return {
        'tickers': ["MSFT", "NVDA", "TSLA", "AAPL", "AMZN", "GOOGL", "META", "AMD", "PLTR", "GME"],
        'source': 'Fallback',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }

@st.cache_data(ttl=60)
def get_financial_ticker_data():
    ticker_data = []

    indices = {
        'ES=F': 'S&P 500 FUT',
        'NQ=F': 'NASDAQ FUT',
        'YM=F': 'DOW FUT',
        'RTY=F': 'RUSSELL FUT',
        '^N225': 'NIKKEI',
        '^GDAXI': 'DAX',
        '^FTSE': 'FTSE 100',
    }

    commodities = {
        'GC=F': 'GOLD',
        'SI=F': 'SILVER',
        'CL=F': 'CRUDE OIL',
        'NG=F': 'NAT GAS',
    }

    mag7 = {
        'AAPL': 'AAPL',
        'MSFT': 'MSFT',
        'GOOGL': 'GOOGL',
        'AMZN': 'AMZN',
        'NVDA': 'NVDA',
        'META': 'META',
        'TSLA': 'TSLA',
    }

    cryptos = {
        'BTC-USD': 'BTC',
        'ETH-USD': 'ETH',
    }

    all_symbols = {**indices, **commodities, **mag7, **cryptos}

    for symbol, name in all_symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")

            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change_pct = ((current - prev) / prev) * 100

                if current >= 1000:
                    price_str = f"{current:,.2f}"
                elif current >= 100:
                    price_str = f"{current:,.2f}"
                else:
                    price_str = f"{current:.3f}"

                ticker_data.append({
                    'name': name,
                    'price': price_str,
                    'change': change_pct,
                    'is_positive': change_pct >= 0
                })

            time.sleep(0.05)

        except Exception as e:
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
            {'name': 'BTC', 'price': '104,231.50', 'change': 2.45, 'is_positive': True},
            {'name': 'ETH', 'price': '3,120.80', 'change': -0.85, 'is_positive': False},
            {'name': 'AAPL', 'price': '228.50', 'change': 1.25, 'is_positive': True},
            {'name': 'MSFT', 'price': '425.80', 'change': -0.45, 'is_positive': False},
            {'name': 'NVDA', 'price': '138.25', 'change': 3.45, 'is_positive': True},
            {'name': 'TSLA', 'price': '380.50', 'change': -2.15, 'is_positive': False},
        ]

    ticker_items = []
    for item in data:
        color = "#00ffad" if item['is_positive'] else "#f23645"
        arrow = "▲" if item['is_positive'] else "▼"
        change_str = f"{item['change']:+.2f}%"

        ticker_items.append(
            f'<span style="margin-right: 40px; white-space: nowrap;">'
            f'<span style="color: #fff; font-weight: bold;">{item["name"]}</span> '
            f'<span style="color: #ccc;">{item["price"]}</span> '
            f'<span style="color: {color};">{arrow} {change_str}</span>'
            f'</span>'
        )

    items_html = "".join(ticker_items)
    all_items = items_html + items_html

    ticker_html = f"""
    <div style="
        background: linear-gradient(90deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%);
        border-bottom: 2px solid #2a3f5f;
        padding: 12px 0;
        overflow: hidden;
        position: relative;
        width: 100%;
    ">
        <div style="
            display: inline-block;
            white-space: nowrap;
            animation: ticker-scroll 30s linear infinite;
            padding-left: 100%;
        ">
            {all_items}
        </div>
    </div>
    <style>
        @keyframes ticker-scroll {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
    </style>
    """

    return ticker_html
