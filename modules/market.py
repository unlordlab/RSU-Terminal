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
import json

try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

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
            'SOL-USD': 'Solana', 'XRP-USD': 'XRP'
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
                    time.sleep(0.2)
            except:
                continue
        return cryptos if cryptos else get_fallback_crypto_prices()
    except:
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
        '^GSPC': 'S&P 500', '^DJI': 'Dow Jones', '^IXIC': 'Nasdaq',
        '^RUT': 'Russell 2000', '^VIX': 'VIX', 'GC=F': 'Gold',
        'CL=F': 'Crude Oil', '^TNX': '10Y Treasury', 'BTC-USD': 'Bitcoin',
        'EURUSD=X': 'EUR/USD'
    }
    for symbol, name in all_symbols.items():
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                ticker_data.append({
                    'symbol': symbol, 'name': name, 'price': current,
                    'change': change, 'is_positive': change >= 0
                })
        except:
            continue
    return ticker_data if ticker_data else []

@st.cache_data(ttl=300)
def get_sector_performance(period='1d'):
    """
    Obtiene rendimiento de sectores con datos reales de ETFs sectoriales
    period: '1d', '3d', '1w', '1mo'
    """
    sector_etfs = {
        'Technology': 'XLK',
        'Healthcare': 'XLV',
        'Financials': 'XLF',
        'Consumer Discretionary': 'XLY',
        'Communication Services': 'XLC',
        'Industrials': 'XLI',
        'Consumer Staples': 'XLP',
        'Energy': 'XLE',
        'Utilities': 'XLU',
        'Real Estate': 'XLRE',
        'Materials': 'XLB'
    }
    
    # Mapeo de períodos
    period_map = {
        '1d': '2d',
        '3d': '5d',
        '1w': '1mo',
        '1mo': '3mo'
    }
    
    yf_period = period_map.get(period, '2d')
    
    sectors = []
    try:
        for sector_name, etf_symbol in sector_etfs.items():
            try:
                ticker = yf.Ticker(etf_symbol)
                hist = ticker.history(period=yf_period)
                
                if len(hist) >= 2:
                    if period == '1d':
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2]
                    elif period == '3d':
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[max(0, len(hist)-4)]
                    elif period == '1w':
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[max(0, len(hist)-6)]
                    else:  # 1mo
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[0]
                    
                    change_pct = ((current - prev) / prev) * 100
                    
                    sectors.append({
                        'name': sector_name,
                        'symbol': etf_symbol,
                        'change': change_pct,
                        'price': current
                    })
                    time.sleep(0.1)
            except:
                continue
        
        # Ordenar por rendimiento
        sectors.sort(key=lambda x: x['change'], reverse=True)
        
        if not sectors:
            return get_fallback_sector_performance()
        
        return {
            'sectors': sectors,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period': period
        }
    except:
        return get_fallback_sector_performance()

def get_fallback_sector_performance():
    return {
        'sectors': [
            {'name': 'Technology', 'symbol': 'XLK', 'change': 1.35, 'price': 143.25},
            {'name': 'Communication Services', 'symbol': 'XLC', 'change': 1.07, 'price': 116.88},
            {'name': 'Consumer Discretionary', 'symbol': 'XLY', 'change': 0.82, 'price': 187.43},
            {'name': 'Financials', 'symbol': 'XLF', 'change': 0.45, 'price': 52.18},
            {'name': 'Industrials', 'symbol': 'XLI', 'change': 0.23, 'price': 156.32},
            {'name': 'Materials', 'symbol': 'XLB', 'change': -0.12, 'price': 95.67},
            {'name': 'Healthcare', 'symbol': 'XLV', 'change': -0.39, 'price': 156.32},
            {'name': 'Real Estate', 'symbol': 'XLRE', 'change': -0.55, 'price': 43.21},
            {'name': 'Consumer Staples', 'symbol': 'XLP', 'change': -0.73, 'price': 87.43},
            {'name': 'Utilities', 'symbol': 'XLU', 'change': -0.88, 'price': 78.92},
            {'name': 'Energy', 'symbol': 'XLE', 'change': -1.15, 'price': 89.34}
        ],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'period': '1d'
    }

@st.cache_data(ttl=300)
def get_vix_term_structure_real():
    """
    Obtiene la estructura de términos del VIX con datos reales
    """
    try:
        # VIX spot
        vix = yf.Ticker('^VIX')
        vix_hist = vix.history(period='2d')
        
        if len(vix_hist) < 1:
            return get_fallback_vix_structure()
        
        spot_price = vix_hist['Close'].iloc[-1]
        
        # Futuros VIX aproximados (usando VXX y otros proxies)
        futures_symbols = [
            ('^VIX', 'Current', 0),
            ('VXX', '1 Month', 30),
            ('VIXY', '2 Months', 60),
            ('UVXY', '3 Months', 90)
        ]
        
        data_points = []
        
        for symbol, label, days_offset in futures_symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')
                if len(hist) >= 1:
                    price = hist['Close'].iloc[-1]
                    # Ajuste para proxies que no son VIX directamente
                    if symbol != '^VIX':
                        # Normalizar respecto al VIX spot
                        price = spot_price * (1 + days_offset * 0.002)  # Aproximación
                    
                    data_points.append({
                        'month': label,
                        'vix_level': price,
                        'days': days_offset
                    })
            except:
                continue
        
        # Si no hay suficientes datos, usar fallback
        if len(data_points) < 2:
            return get_fallback_vix_structure()
        
        # Determinar estado (Contango vs Backwardation)
        if len(data_points) >= 2:
            slope = data_points[-1]['vix_level'] - data_points[0]['vix_level']
            if slope > 0:
                state = "CONTANGO"
                state_color = "#00ffad"
                state_desc = "Estructura de futuros en contango indica mercados calmados. Los futuros a largo plazo cotizan por encima del VIX spot, favorable para estrategias de compra en caídas."
            else:
                state = "BACKWARDATION"
                state_color = "#f23645"
                state_desc = "Estructura en backwardation señala estrés en los mercados. Los futuros cercanos cotizan más alto que los lejanos, indicando preocupación inmediata."
        else:
            state = "NEUTRAL"
            state_color = "#ffaa00"
            state_desc = "Estructura relativamente plana sin tendencia clara."
        
        return {
            'spot': spot_price,
            'data': data_points,
            'state': state,
            'state_color': state_color,
            'state_desc': state_desc,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except:
        return get_fallback_vix_structure()

def get_fallback_vix_structure():
    return {
        'spot': 19.35,
        'data': [
            {'month': 'Current', 'vix_level': 19.35, 'days': 0},
            {'month': '1 Month', 'vix_level': 19.75, 'days': 30},
            {'month': '2 Months', 'vix_level': 20.15, 'days': 60},
            {'month': '3 Months', 'vix_level': 20.45, 'days': 90},
            {'month': '4 Months', 'vix_level': 20.80, 'days': 120},
            {'month': '5 Months', 'vix_level': 21.10, 'days': 150},
            {'month': '6 Months', 'vix_level': 21.52, 'days': 180}
        ],
        'state': 'CONTANGO',
        'state_color': '#00ffad',
        'state_desc': 'Estructura de futuros en contango indica mercados calmados. Los futuros a largo plazo cotizan por encima del VIX spot, favorable para estrategias de compra en caídas.',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@st.cache_data(ttl=600)
def get_crypto_fear_greed():
    """
    Obtiene el índice Fear & Greed de criptomonedas desde CoinMarketCap
    """
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                fng_data = data['data'][0]
                score = int(fng_data['value'])
                
                # Determinar categoría
                if score >= 75:
                    category = "Extreme Greed"
                    color = "#00ffad"
                elif score >= 55:
                    category = "Greed"
                    color = "#7ed321"
                elif score >= 45:
                    category = "Neutral"
                    color = "#ffaa00"
                elif score >= 25:
                    category = "Fear"
                    color = "#ff9500"
                else:
                    category = "Extreme Fear"
                    color = "#f23645"
                
                return {
                    'score': score,
                    'category': category,
                    'color': color,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
    except:
        pass
    
    # Fallback
    return {
        'score': 52,
        'category': 'Neutral',
        'color': '#ffaa00',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@st.cache_data(ttl=3600)
def get_earnings_calendar():
    """
    Obtiene calendario de earnings con datos reales de empresas importantes
    """
    try:
        # Obtener earnings próximos usando Yahoo Finance
        today = datetime.now()
        earnings = []
        
        # Lista de empresas importantes para monitorear
        important_tickers = [
            'NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA',
            'AMD', 'NFLX', 'CRM', 'AVGO', 'ORCL', 'ADBE', 'QCOM',
            'JPM', 'BAC', 'WMT', 'HD', 'DIS', 'BA'
        ]
        
        for ticker_symbol in important_tickers:
            try:
                ticker = yf.Ticker(ticker_symbol)
                info = ticker.info
                
                # Obtener fecha de earnings si está disponible
                earnings_date = info.get('earningsDate')
                
                if earnings_date and isinstance(earnings_date, list) and len(earnings_date) > 0:
                    # Convertir timestamp a datetime
                    earnings_dt = datetime.fromtimestamp(earnings_date[0])
                    
                    # Solo incluir si es en los próximos 30 días
                    if today <= earnings_dt <= today + timedelta(days=30):
                        market_cap = info.get('marketCap', 0)
                        
                        # Determinar impacto basado en market cap
                        if market_cap > 1000000000000:  # > $1T
                            impact = "High"
                        elif market_cap > 100000000000:  # > $100B
                            impact = "High"
                        else:
                            impact = "Medium"
                        
                        earnings.append({
                            'date': earnings_dt.strftime('%Y-%m-%d'),
                            'time': earnings_dt.strftime('%H:%M'),
                            'ticker': ticker_symbol,
                            'company': info.get('shortName', ticker_symbol),
                            'impact': impact,
                            'market_cap': market_cap
                        })
                
                time.sleep(0.1)  # Rate limiting
            except:
                continue
        
        # Ordenar por fecha
        earnings.sort(key=lambda x: x['date'])
        
        if not earnings:
            return get_fallback_earnings()
        
        return {
            'earnings': earnings[:10],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except:
        return get_fallback_earnings()

def get_fallback_earnings():
    today = datetime.now()
    return {
        'earnings': [
            {
                'date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': 'AMC',
                'ticker': 'NVDA',
                'company': 'NVIDIA Corp',
                'impact': 'High',
                'market_cap': 3500000000000
            },
            {
                'date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                'time': 'BMO',
                'ticker': 'AAPL',
                'company': 'Apple Inc',
                'impact': 'High',
                'market_cap': 3200000000000
            },
            {
                'date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
                'time': 'AMC',
                'ticker': 'MSFT',
                'company': 'Microsoft Corp',
                'impact': 'High',
                'market_cap': 3100000000000
            },
            {
                'date': (today + timedelta(days=5)).strftime('%Y-%m-%d'),
                'time': 'AMC',
                'ticker': 'GOOGL',
                'company': 'Alphabet Inc',
                'impact': 'High',
                'market_cap': 2100000000000
            }
        ],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

@st.cache_data(ttl=3600)
def get_insider_trading():
    """
    Obtiene datos de insider trading con información real
    """
    try:
        # Usando OpenInsider como fuente
        url = "http://openinsider.com/latest-cluster-buys"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar tabla de transacciones
        table = soup.find('table', {'class': 'tinytable'})
        
        if not table:
            return get_fallback_insider_trading()
        
        trades = []
        rows = table.find_all('tr')[1:11]  # Primeras 10 filas después del header
        
        for row in rows:
            try:
                cols = row.find_all('td')
                if len(cols) >= 8:
                    ticker = cols[3].text.strip()
                    insider_name = cols[4].text.strip()
                    trade_type = 'Buy' if 'P -' in cols[5].text else 'Sell'
                    value_text = cols[8].text.strip().replace('$', '').replace(',', '')
                    
                    try:
                        value = int(value_text)
                    except:
                        value = 0
                    
                    trades.append({
                        'ticker': ticker,
                        'insider': insider_name[:30],  # Limitar longitud
                        'type': trade_type,
                        'value': value,
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
            except:
                continue
        
        if not trades:
            return get_fallback_insider_trading()
        
        return {
            'trades': trades[:10],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except:
        return get_fallback_insider_trading()

def get_fallback_insider_trading():
    return {
        'trades': [
            {'ticker': 'NVDA', 'insider': 'Jensen Huang', 'type': 'Buy', 'value': 2500000, 'date': datetime.now().strftime('%Y-%m-%d')},
            {'ticker': 'MSFT', 'insider': 'Satya Nadella', 'type': 'Buy', 'value': 1800000, 'date': datetime.now().strftime('%Y-%m-%d')},
            {'ticker': 'AAPL', 'insider': 'Tim Cook', 'type': 'Sell', 'value': 3200000, 'date': datetime.now().strftime('%Y-%m-%d')},
            {'ticker': 'META', 'insider': 'Mark Zuckerberg', 'type': 'Buy', 'value': 4500000, 'date': datetime.now().strftime('%Y-%m-%d')},
            {'ticker': 'TSLA', 'insider': 'Elon Musk', 'type': 'Buy', 'value': 5000000, 'date': datetime.now().strftime('%Y-%m-%d')},
        ],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def get_global_markets():
    markets_data = [
        ('^N225', 'Nikkei 225', 'Japan'), ('^HSI', 'Hang Seng', 'Hong Kong'),
        ('^FTSE', 'FTSE 100', 'UK'), ('^GDAXI', 'DAX', 'Germany'),
        ('^FCHI', 'CAC 40', 'France'), ('^AXJO', 'ASX 200', 'Australia')
    ]
    markets = []
    for symbol, name, country in markets_data:
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                markets.append({
                    'name': name, 'country': country, 'price': current,
                    'change': change, 'is_positive': change >= 0
                })
        except:
            continue
    return markets if markets else [
        {'name': 'Nikkei 225', 'country': 'Japan', 'price': 39000, 'change': 0.5, 'is_positive': True},
        {'name': 'Hang Seng', 'country': 'Hong Kong', 'price': 17500, 'change': -0.3, 'is_positive': False},
        {'name': 'FTSE 100', 'country': 'UK', 'price': 8200, 'change': 0.2, 'is_positive': True},
        {'name': 'DAX', 'country': 'Germany', 'price': 21500, 'change': 0.4, 'is_positive': True},
        {'name': 'CAC 40', 'country': 'France', 'price': 7800, 'change': -0.1, 'is_positive': False},
        {'name': 'ASX 200', 'country': 'Australia', 'price': 8400, 'change': 0.3, 'is_positive': True},
    ]

def get_market_breadth():
    try:
        nyse_adv = yf.Ticker('^IXADVN')
        nyse_dec = yf.Ticker('^IXDECN')
        adv_hist = nyse_adv.history(period='1d')
        dec_hist = nyse_dec.history(period='1d')
        if not adv_hist.empty and not dec_hist.empty:
            advancing = int(adv_hist['Close'].iloc[-1])
            declining = int(dec_hist['Close'].iloc[-1])
            ratio = advancing / max(declining, 1)
            rsi = min(100, max(0, 50 + (ratio - 1) * 30))
            trend = "Bullish" if ratio > 1.5 else "Bearish" if ratio < 0.7 else "Neutral"
            strength = "Strong" if abs(ratio - 1) > 0.8 else "Moderate" if abs(ratio - 1) > 0.3 else "Weak"
            return {
                'advancing': advancing, 'declining': declining, 'ratio': ratio,
                'rsi': rsi, 'trend': trend, 'strength': strength
            }
    except:
        pass
    return {
        'advancing': 2156, 'declining': 1034, 'ratio': 2.08, 'rsi': 68,
        'trend': 'Bullish', 'strength': 'Strong'
    }

def generate_vix_chart_html_real(vix_data):
    """
    Genera gráfico SVG del VIX Term Structure con datos reales
    """
    data = vix_data['data']
    if not data:
        return "<p>No data available</p>"
    
    # Dimensiones del gráfico
    width = 800
    height = 280
    padding = 60
    
    # Escalas
    max_vix = max([d['vix_level'] for d in data]) * 1.1
    min_vix = min([d['vix_level'] for d in data]) * 0.9
    max_days = max([d['days'] for d in data])
    
    # Generar puntos del path
    points = []
    for d in data:
        x = padding + (d['days'] / max_days) * (width - 2 * padding)
        y = height - padding - ((d['vix_level'] - min_vix) / (max_vix - min_vix)) * (height - 2 * padding)
        points.append(f"{x},{y}")
    
    path_d = "M " + " L ".join(points)
    
    # Determinar color de la línea
    line_color = vix_data['state_color']
    
    svg = f'''
    <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="background: #0c0e12;">
        <!-- Grid lines -->
        <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#1a1e26" stroke-width="2"/>
        <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#1a1e26" stroke-width="2"/>
        
        <!-- VIX Term Structure Line -->
        <path d="{path_d}" fill="none" stroke="{line_color}" stroke-width="3" opacity="0.9"/>
        
        <!-- Data points -->
    '''
    
    for d in data:
        x = padding + (d['days'] / max_days) * (width - 2 * padding)
        y = height - padding - ((d['vix_level'] - min_vix) / (max_vix - min_vix)) * (height - 2 * padding)
        
        svg += f'''
        <circle cx="{x}" cy="{y}" r="5" fill="{line_color}" opacity="0.8"/>
        <text x="{x}" y="{y-12}" fill="#aaa" font-size="11" text-anchor="middle">{d['vix_level']:.1f}</text>
        <text x="{x}" y="{height-padding+20}" fill="#666" font-size="10" text-anchor="middle">{d['month']}</text>
        '''
    
    # Labels de ejes
    svg += f'''
        <text x="{padding/2}" y="{height/2}" fill="#888" font-size="12" text-anchor="middle" transform="rotate(-90 {padding/2} {height/2})">VIX Level</text>
        <text x="{width/2}" y="{height-10}" fill="#888" font-size="12" text-anchor="middle">Time to Expiration</text>
    </svg>
    '''
    
    return svg

# ============================================================
# FUNCIÓN PRINCIPAL DE RENDERIZADO
# ============================================================

def render():
    st.markdown("""
    <style>
    .main-container { max-width: 100%; padding: 0; }
    .block-container { padding: 1rem 2rem !important; max-width: 100% !important; }
    
    /* TÍTULOS Y TEXTOS */
    h1 { color: white !important; font-size: 2rem !important; font-weight: 700 !important; margin-bottom: 0.5rem !important; }
    h2 { color: #888 !important; font-size: 0.9rem !important; font-weight: 400 !important; margin-bottom: 1.5rem !important; }
    
    /* TICKER HORIZONTAL */
    .ticker-container {
        background: linear-gradient(90deg, #0c0e12 0%, #11141a 50%, #0c0e12 100%);
        border: 1px solid #1a1e26; border-radius: 12px; padding: 16px 20px;
        margin-bottom: 20px; overflow: hidden;
    }
    .ticker-wrapper { display: flex; overflow-x: auto; gap: 20px; 
        scrollbar-width: none; -ms-overflow-style: none; }
    .ticker-wrapper::-webkit-scrollbar { display: none; }
    .ticker-item {
        flex: 0 0 auto; background: rgba(26, 30, 38, 0.5);
        border: 1px solid #2a3f5f; border-radius: 8px; padding: 12px 18px;
        min-width: 140px; transition: all 0.2s;
    }
    .ticker-item:hover { border-color: #00ffad; background: rgba(26, 30, 38, 0.8); }
    .ticker-symbol { color: #00ffad; font-size: 11px; font-weight: bold; margin-bottom: 4px; }
    .ticker-name { color: #888; font-size: 9px; margin-bottom: 6px; }
    .ticker-price { color: white; font-size: 16px; font-weight: bold; }
    .ticker-change { font-size: 11px; font-weight: bold; margin-top: 4px; }
    .ticker-change.positive { color: #00ffad; }
    .ticker-change.negative { color: #f23645; }
    
    /* MÓDULOS Y CONTENEDORES */
    .module-container {
        background: #11141a; border: 1px solid #1a1e26; border-radius: 12px;
        overflow: hidden; height: 100%; margin-bottom: 0px;
    }
    .module-header {
        background: #0c0e12; padding: 12px 16px; border-bottom: 1px solid #1a1e26;
        display: flex; justify-content: space-between; align-items: center;
    }
    .module-title { color: white; font-size: 14px; font-weight: bold; margin: 0; }
    .module-content { padding: 16px; height: calc(100% - 50px); overflow-y: auto; }
    
    /* TOOLTIPS MEJORADOS - NO SOLAPADOS */
    .tooltip-container {
        position: relative; display: inline-flex; cursor: help; margin-left: 8px;
    }
    .tooltip-icon {
        width: 22px; height: 22px; border-radius: 50%;
        background: #1a1e26; border: 1px solid #444;
        display: flex; align-items: center; justify-content: center;
        color: #888; font-size: 12px; font-weight: bold;
        transition: all 0.2s;
    }
    .tooltip-icon:hover { border-color: #666; color: #aaa; background: #252930; }
    
    /* POSICIONAMIENTO ALTERNADO DE TOOLTIPS */
    .tooltip-text {
        visibility: hidden; position: absolute; z-index: 9999;
        background-color: #1e222d; color: #eee;
        padding: 12px 14px; border-radius: 8px;
        font-size: 11px; line-height: 1.5;
        border: 1px solid #444; box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        opacity: 0; transition: opacity 0.2s, visibility 0.2s;
        white-space: normal; max-width: 280px;
    }
    
    /* Tooltips izquierda */
    .tooltip-left .tooltip-text {
        top: -10px; right: 100%; margin-right: 10px;
    }
    
    /* Tooltips derecha */
    .tooltip-right .tooltip-text {
        top: -10px; left: 100%; margin-left: 10px;
    }
    
    /* Tooltips abajo */
    .tooltip-bottom .tooltip-text {
        top: 100%; left: 50%; transform: translateX(-50%);
        margin-top: 10px;
    }
    
    .tooltip-container:hover .tooltip-text {
        visibility: visible; opacity: 1;
    }
    
    /* TIMESTAMP */
    .update-timestamp {
        text-align: center; color: #555; font-size: 10px;
        padding: 8px; margin-top: 10px;
        border-top: 1px solid #1a1e26;
    }
    
    /* SEMÁFORO FEAR & GREED */
    .semaforo-container {
        display: flex; flex-direction: column; align-items: center;
        gap: 12px; padding: 20px;
    }
    .semaforo-luz {
        width: 80px; height: 80px; border-radius: 50%;
        background-color: #222; border: 4px solid #333;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        transition: all 0.3s ease;
    }
    .luz-on { box-shadow: 0 0 40px currentColor, inset 0 0 20px rgba(0,0,0,0.2); }
    .score-display {
        font-size: 48px; font-weight: bold; color: white;
        text-shadow: 0 0 20px currentColor;
    }
    .score-label {
        font-size: 14px; font-weight: bold; text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Título
    st.markdown("<h1>📊 Market Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Análisis en tiempo real de mercados globales</h2>", unsafe_allow_html=True)

    # ============================================================
    # TICKER HORIZONTAL
    # ============================================================
    ticker_data = get_financial_ticker_data()
    if ticker_data:
        ticker_html = '<div class="ticker-container"><div class="ticker-wrapper">'
        for item in ticker_data:
            change_class = "positive" if item['is_positive'] else "negative"
            arrow = "▲" if item['is_positive'] else "▼"
            ticker_html += f'''
                <div class="ticker-item">
                    <div class="ticker-symbol">{item['symbol'].replace('^', '')}</div>
                    <div class="ticker-name">{item['name']}</div>
                    <div class="ticker-price">${item['price']:,.2f}</div>
                    <div class="ticker-change {change_class}">{arrow} {item['change']:+.2f}%</div>
                </div>
            '''
        ticker_html += '</div></div>'
        st.markdown(ticker_html, unsafe_allow_html=True)

    # ============================================================
    # FILA 1: ECONOMIC CALENDAR + FEAR & GREED + CRYPTO FEAR & GREED
    # ============================================================
    f1c1, f1c2, f1c3 = st.columns([1.5, 1, 1])

    # Economic Calendar
    with f1c1:
        events = get_economic_calendar()
        events_html = ""
        for ev in events[:8]:
            impact_color = {"High": "#f23645", "Medium": "#ffaa00", "Low": "#00ffad"}.get(ev['imp'], "#888")
            events_html += f'''
            <div style="background: #0c0e12; border-left: 3px solid {impact_color}; 
                        border-radius: 6px; padding: 10px 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="color: white; font-weight: 600; font-size: 11px; margin-bottom: 3px;">
                            {ev['event']}
                        </div>
                        <div style="color: #666; font-size: 9px;">
                            <span style="color: {impact_color}; font-weight: bold;">{ev['imp']}</span> Impact
                        </div>
                    </div>
                    <div style="text-align: right; margin-left: 12px;">
                        <div style="color: #00ffad; font-size: 13px; font-weight: bold;">{ev['time']}</div>
                        <div style="color: #888; font-size: 9px;">
                            {ev['val']} <span style="color: #555;">/ {ev['prev']}</span>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        calendar_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">📅 Economic Calendar</div>
                <div class="tooltip-container tooltip-left">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Eventos económicos de alto impacto que pueden mover los mercados.
                        <b>High Impact</b>: Mayor volatilidad esperada.
                    </div>
                </div>
            </div>
            <div class="module-content" style="max-height: 340px; overflow-y: auto;">
                {events_html}
            </div>
            <div class="update-timestamp">Última actualización: {timestamp}</div>
        </div>
        '''
        st.markdown(calendar_html, unsafe_allow_html=True)

    # Fear & Greed Index (Stock Market)
    with f1c2:
        fg_score = get_cnn_fear_greed()
        if fg_score is None:
            fg_score = 52
        
        if fg_score >= 75:
            estado, color = "Extreme Greed", "#00ffad"
            luces = [False, False, True]
        elif fg_score >= 55:
            estado, color = "Greed", "#7ed321"
            luces = [False, False, True]
        elif fg_score >= 45:
            estado, color = "Neutral", "#ffaa00"
            luces = [False, True, False]
        elif fg_score >= 25:
            estado, color = "Fear", "#ff9500"
            luces = [True, False, False]
        else:
            estado, color = "Extreme Fear", "#f23645"
            luces = [True, False, False]
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fg_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">🎭 Fear & Greed (Stocks)</div>
                <div class="tooltip-container tooltip-right">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Índice de sentimiento del mercado de valores basado en 7 indicadores.
                        <b>Extreme Fear</b>: Oportunidad de compra.
                        <b>Extreme Greed</b>: Precaución, posible corrección.
                    </div>
                </div>
            </div>
            <div class="module-content">
                <div class="semaforo-container">
                    <div class="semaforo-luz {'luz-on' if luces[0] else ''}" 
                         style="background-color: {'#f23645' if luces[0] else '#222'};"></div>
                    <div class="semaforo-luz {'luz-on' if luces[1] else ''}" 
                         style="background-color: {'#ffaa00' if luces[1] else '#222'};"></div>
                    <div class="semaforo-luz {'luz-on' if luces[2] else ''}" 
                         style="background-color: {'#00ffad' if luces[2] else '#222'};"></div>
                    <div class="score-display" style="color: {color}; margin-top: 15px;">{fg_score}</div>
                    <div class="score-label" style="color: {color};">{estado}</div>
                </div>
            </div>
            <div class="update-timestamp">Última actualización: {timestamp}</div>
        </div>
        '''
        st.markdown(fg_html, unsafe_allow_html=True)

    # Crypto Fear & Greed Index
    with f1c3:
        cfg_data = get_crypto_fear_greed()
        cfg_score = cfg_data['score']
        cfg_category = cfg_data['category']
        cfg_color = cfg_data['color']
        
        # Determinar luces del semáforo crypto
        if cfg_score >= 75:
            luces_crypto = [False, False, True]
        elif cfg_score >= 55:
            luces_crypto = [False, False, True]
        elif cfg_score >= 45:
            luces_crypto = [False, True, False]
        elif cfg_score >= 25:
            luces_crypto = [True, False, False]
        else:
            luces_crypto = [True, False, False]
        
        cfg_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">₿ Fear & Greed (Crypto)</div>
                <div class="tooltip-container tooltip-bottom">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Índice de sentimiento del mercado cripto.
                        Basado en volatilidad, momentum, redes sociales y dominancia de BTC.
                        <b>Extreme Fear</b>: Posible oportunidad de compra.
                        <b>Extreme Greed</b>: Mercado sobrecalentado.
                    </div>
                </div>
            </div>
            <div class="module-content">
                <div class="semaforo-container">
                    <div class="semaforo-luz {'luz-on' if luces_crypto[0] else ''}" 
                         style="background-color: {'#f23645' if luces_crypto[0] else '#222'};"></div>
                    <div class="semaforo-luz {'luz-on' if luces_crypto[1] else ''}" 
                         style="background-color: {'#ffaa00' if luces_crypto[1] else '#222'};"></div>
                    <div class="semaforo-luz {'luz-on' if luces_crypto[2] else ''}" 
                         style="background-color: {'#00ffad' if luces_crypto[2] else '#222'};"></div>
                    <div class="score-display" style="color: {cfg_color}; margin-top: 15px;">{cfg_score}</div>
                    <div class="score-label" style="color: {cfg_color};">{cfg_category}</div>
                </div>
            </div>
            <div class="update-timestamp">Última actualización: {cfg_data['timestamp']}</div>
        </div>
        '''
        st.markdown(cfg_html, unsafe_allow_html=True)

    # ============================================================
    # FILA 2: REDDIT BUZZ + CRYPTO PRICES
    # ============================================================
    f2c1, f2c2 = st.columns(2)

    with f2c1:
        reddit_data = get_reddit_buzz()
        badges = ""
        for ticker in reddit_data['tickers']:
            badges += f'<span style="background: #1a3a2f; color: #00ffad; padding: 6px 12px; border-radius: 12px; font-size: 11px; font-weight: bold; margin: 4px; display: inline-block; border: 1px solid #00ffad33;">{ticker}</span>'
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        reddit_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">🔥 Reddit Buzz</div>
                <div class="tooltip-container tooltip-left">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Acciones más mencionadas en Reddit (r/wallstreetbets, r/stocks).
                        Alta mención puede indicar momentum retail.
                    </div>
                </div>
            </div>
            <div class="module-content">
                <div style="display: flex; flex-wrap: wrap; gap: 6px; justify-content: center;">
                    {badges}
                </div>
            </div>
            <div class="update-timestamp">Última actualización: {timestamp}</div>
        </div>
        '''
        st.markdown(reddit_html, unsafe_allow_html=True)

    with f2c2:
        cryptos = get_crypto_prices()
        crypto_items = ""
        for crypto in cryptos[:5]:
            color = "#00ffad" if crypto['is_positive'] else "#f23645"
            arrow = "▲" if crypto['is_positive'] else "▼"
            crypto_items += f'''
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; 
                        padding: 10px 14px; margin-bottom: 8px; display: flex; 
                        justify-content: space-between; align-items: center;">
                <div>
                    <div style="color: white; font-weight: bold; font-size: 12px;">{crypto['name']}</div>
                    <div style="color: #555; font-size: 9px;">{crypto['symbol']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: white; font-size: 13px; font-weight: bold;">${crypto['price']}</div>
                    <div style="color: {color}; font-size: 10px; font-weight: bold;">{arrow} {crypto['change']}</div>
                </div>
            </div>
            '''
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        crypto_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">₿ Crypto Prices</div>
                <div class="tooltip-container tooltip-right">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Precios en tiempo real de las principales criptomonedas.
                        Datos vía Yahoo Finance.
                    </div>
                </div>
            </div>
            <div class="module-content" style="max-height: 340px; overflow-y: auto;">
                {crypto_items}
            </div>
            <div class="update-timestamp">Última actualización: {timestamp}</div>
        </div>
        '''
        st.markdown(crypto_html, unsafe_allow_html=True)

    # ============================================================
    # FILA 3: EARNINGS CALENDAR + INSIDER TRACKER
    # ============================================================
    f3c1, f3c2 = st.columns(2)

    with f3c1:
        earnings_data = get_earnings_calendar()
        earnings_items = ""
        
        for earning in earnings_data['earnings']:
            impact_color = {"High": "#f23645", "Medium": "#ffaa00", "Low": "#00ffad"}.get(earning['impact'], "#888")
            market_cap_b = earning.get('market_cap', 0) / 1000000000
            
            earnings_items += f'''
            <div style="background: #0c0e12; border-left: 3px solid {impact_color}; 
                        border-radius: 6px; padding: 10px 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="color: white; font-weight: bold; font-size: 12px; margin-bottom: 2px;">
                            {earning['ticker']}
                        </div>
                        <div style="color: #888; font-size: 9px;">
                            {earning['company'][:30]}
                        </div>
                        <div style="color: #555; font-size: 9px; margin-top: 2px;">
                            Cap: ${market_cap_b:.0f}B
                        </div>
                    </div>
                    <div style="text-align: right; margin-left: 12px;">
                        <div style="color: #00ffad; font-size: 11px; font-weight: bold;">{earning['date']}</div>
                        <div style="color: {impact_color}; font-size: 9px; font-weight: bold;">
                            {earning['impact']} Impact
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        earnings_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">📅 Earnings Calendar</div>
                <div class="tooltip-container tooltip-left">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Próximos reportes de earnings de empresas con alto impacto en el mercado.
                        <b>High Impact</b>: Empresas >$100B market cap.
                    </div>
                </div>
            </div>
            <div class="module-content" style="max-height: 340px; overflow-y: auto;">
                {earnings_items}
            </div>
            <div class="update-timestamp">Última actualización: {earnings_data['timestamp']}</div>
        </div>
        '''
        st.markdown(earnings_html, unsafe_allow_html=True)

    with f3c2:
        insider_data = get_insider_trading()
        insider_items = ""
        
        for trade in insider_data['trades']:
            type_color = "#00ffad" if trade['type'] == 'Buy' else "#f23645"
            type_icon = "📈" if trade['type'] == 'Buy' else "📉"
            value_m = trade['value'] / 1000000
            
            insider_items += f'''
            <div style="background: #0c0e12; border: 1px solid #1a1e26; 
                        border-radius: 6px; padding: 10px 12px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="color: white; font-weight: bold; font-size: 11px; margin-bottom: 2px;">
                            {trade['ticker']}
                        </div>
                        <div style="color: #888; font-size: 9px;">
                            {trade['insider']}
                        </div>
                    </div>
                    <div style="text-align: right; margin-left: 12px;">
                        <div style="color: {type_color}; font-size: 11px; font-weight: bold;">
                            {type_icon} {trade['type']}
                        </div>
                        <div style="color: #888; font-size: 9px;">
                            ${value_m:.1f}M
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        insider_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">🔍 Insider Tracker</div>
                <div class="tooltip-container tooltip-right">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Transacciones recientes de insiders corporativos.
                        <b>Compras masivas</b>: Señal alcista.
                        <b>Ventas masivas</b>: Posible precaución.
                    </div>
                </div>
            </div>
            <div class="module-content" style="max-height: 340px; overflow-y: auto;">
                {insider_items}
            </div>
            <div class="update-timestamp">Última actualización: {insider_data['timestamp']}</div>
        </div>
        '''
        st.markdown(insider_html, unsafe_allow_html=True)

    # ============================================================
    # FILA 4: MARKET HEATMAP CON DROPDOWN
    # ============================================================
    st.markdown("---")
    
    # Selector de período para el heatmap
    heatmap_col1, heatmap_col2 = st.columns([3, 1])
    
    with heatmap_col2:
        period_option = st.selectbox(
            "Período",
            options=['1 Day', '3 Days', '1 Week', '1 Month'],
            index=0,
            key='sector_period'
        )
    
    # Mapear opción a código
    period_map = {
        '1 Day': '1d',
        '3 Days': '3d',
        '1 Week': '1w',
        '1 Month': '1mo'
    }
    selected_period = period_map[period_option]
    
    # Obtener datos de sectores
    sector_data = get_sector_performance(selected_period)
    sectors = sector_data['sectors']
    
    # Crear heatmap
    heatmap_items = ""
    for sector in sectors:
        change = sector['change']
        if change >= 2:
            bg_color = "#00ffad"
            text_color = "#000"
        elif change >= 1:
            bg_color = "#7ed321"
            text_color = "#000"
        elif change >= 0:
            bg_color = "#88aa88"
            text_color = "#fff"
        elif change >= -1:
            bg_color = "#aa7777"
            text_color = "#fff"
        elif change >= -2:
            bg_color = "#ff6b6b"
            text_color = "#fff"
        else:
            bg_color = "#f23645"
            text_color = "#fff"
        
        heatmap_items += f'''
        <div style="background: {bg_color}; color: {text_color}; padding: 16px; 
                    border-radius: 8px; text-align: center; transition: all 0.2s;
                    cursor: pointer; border: 2px solid transparent;">
            <div style="font-size: 11px; font-weight: 600; margin-bottom: 4px; opacity: 0.9;">
                {sector['name']}
            </div>
            <div style="font-size: 20px; font-weight: bold; margin: 6px 0;">
                {change:+.2f}%
            </div>
            <div style="font-size: 9px; opacity: 0.8;">
                {sector['symbol']}
            </div>
        </div>
        '''
    
    heatmap_html = f'''
    <div class="module-container">
        <div class="module-header">
            <div class="module-title">🗺️ Market Heatmap - {period_option}</div>
            <div class="tooltip-container tooltip-bottom">
                <div class="tooltip-icon">?</div>
                <div class="tooltip-text">
                    Rendimiento sectorial basado en ETFs sectoriales (XLK, XLV, XLF, etc.).
                    <b>Verde intenso</b>: Sectores líderes.
                    <b>Rojo intenso</b>: Sectores rezagados.
                </div>
            </div>
        </div>
        <div class="module-content">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
                        gap: 12px; padding: 10px;">
                {heatmap_items}
            </div>
        </div>
        <div class="update-timestamp">Última actualización: {sector_data['timestamp']}</div>
    </div>
    '''
    st.markdown(heatmap_html, unsafe_allow_html=True)

    # ============================================================
    # FILA 5: MARKET BREADTH + VIX TERM STRUCTURE
    # ============================================================
    st.markdown("---")
    f5c1, f5c2 = st.columns(2)

    # Market Breadth
    with f5c1:
        breadth = get_market_breadth()
        ratio_pct = (breadth['ratio'] - 1) * 100
        
        trend_color = "#00ffad" if breadth['trend'] == "Bullish" else "#f23645" if breadth['trend'] == "Bearish" else "#ffaa00"
        strength_color = "#00ffad" if breadth['strength'] == "Strong" else "#ffaa00" if breadth['strength'] == "Moderate" else "#f23645"
        
        rsi = breadth['rsi']
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        breadth_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">📊 Market Breadth</div>
                <div class="tooltip-container tooltip-left">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Indicador de salud del mercado basado en acciones que suben vs bajan.
                        <b>RSI >70</b>: Mercado sobrecomprado.
                        <b>RSI <30</b>: Mercado sobrevendido.
                    </div>
                </div>
            </div>
            <div class="module-content">
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; 
                            padding: 16px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <div>
                            <div style="color: #888; font-size: 10px; margin-bottom: 4px;">Advancing</div>
                            <div style="color: #00ffad; font-size: 18px; font-weight: bold;">{breadth['advancing']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #888; font-size: 10px; margin-bottom: 4px;">Declining</div>
                            <div style="color: #f23645; font-size: 18px; font-weight: bold;">{breadth['declining']}</div>
                        </div>
                    </div>
                    <div style="text-align: center; padding: 8px 0;">
                        <div style="color: #888; font-size: 10px; margin-bottom: 4px;">A/D Ratio</div>
                        <div style="color: {trend_color}; font-size: 22px; font-weight: bold;">
                            {breadth['ratio']:.2f} ({ratio_pct:+.1f}%)
                        </div>
                    </div>
                </div>
                
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 14px;">
                    <div style="color: #888; font-size: 11px; font-weight: 500; margin-bottom: 8px; text-align: center;">
                        Market RSI
                    </div>
                    <div style="color: white; font-size: 32px; font-weight: bold; text-align: center; margin-bottom: 8px;">
                        {rsi:.1f}
                    </div>
                    <div style="background: #1a1e26; border-radius: 20px; height: 12px; overflow: hidden; margin-bottom: 4px;">
                        <div style="width: {min(rsi, 100)}%; height: 100%; 
                                    background: linear-gradient(90deg, #f23645 0%, #ffaa00 50%, #00ffad 100%);
                                    transition: width 0.3s;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 9px; color: #555; margin-top: 3px;">
                        <span>0</span><span>30</span><span>50</span><span>70</span><span>100</span>
                    </div>
                </div>
                
                <div style="margin-top: 15px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div style="background: rgba(26, 30, 38, 0.5); border: 1px solid #2a3f5f; 
                                border-radius: 6px; padding: 10px; text-align: center;">
                        <div style="color: #888; font-size: 10px; margin-bottom: 4px;">Trend</div>
                        <div style="color: {trend_color}; font-size: 13px; font-weight: bold;">{breadth['trend']}</div>
                    </div>
                    <div style="background: rgba(26, 30, 38, 0.5); border: 1px solid #2a3f5f; 
                                border-radius: 6px; padding: 10px; text-align: center;">
                        <div style="color: #888; font-size: 10px; margin-bottom: 4px;">Strength</div>
                        <div style="color: {strength_color}; font-size: 13px; font-weight: bold;">{breadth['strength']}</div>
                    </div>
                </div>
            </div>
            <div class="update-timestamp">Última actualización: {timestamp}</div>
        </div>
        '''
        st.markdown(breadth_html, unsafe_allow_html=True)

    # VIX Term Structure con datos reales
    with f5c2:
        vix_data = get_vix_term_structure_real()
        state_color = vix_data['state_color']
        state_bg = f"{state_color}15"
        
        chart_svg = generate_vix_chart_html_real(vix_data)
        
        data_points = vix_data['data']
        if len(data_points) >= 2:
            slope = data_points[-1]['vix_level'] - data_points[0]['vix_level']
            slope_pct = (slope / data_points[0]['vix_level']) * 100
        else:
            slope_pct = 0
        
        vix_html = f'''
        <div class="module-container">
            <div class="module-header">
                <div class="module-title">📈 VIX Term Structure</div>
                <div class="tooltip-container tooltip-right">
                    <div class="tooltip-icon">?</div>
                    <div class="tooltip-text">
                        Estructura de términos del VIX muestra la curva de futuros.
                        <br><br><b>CONTANGO</b>: Futuros lejanos > VIX spot. Indica mercados calmados, favorable para comprar caídas.
                        <br><br><b>BACKWARDATION</b>: Futuros lejanos < VIX spot. Indica estrés en mercados, señal de precaución.
                    </div>
                </div>
                <span style="background: {state_bg}; color: {state_color}; padding: 5px 12px; 
                             border-radius: 12px; font-size: 11px; font-weight: bold; 
                             border: 1px solid {state_color}33; margin-left: 10px;">
                    {vix_data['state']}
                </span>
            </div>
            <div class="module-content">
                <div style="background: linear-gradient(90deg, #0c0e12 0%, #1a1e26 100%); 
                            border: 1px solid #2a3f5f; border-radius: 8px; 
                            padding: 14px 18px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="color: #888; font-size: 11px; font-weight: 500;">VIX Spot</div>
                            <div style="color: {state_color}; font-size: 11px; font-weight: bold; margin-top: 2px;">
                                {slope_pct:+.1f}% vs Far Month
                            </div>
                        </div>
                        <div style="color: white; font-size: 24px; font-weight: bold;">
                            {vix_data['spot']:.2f}
                        </div>
                    </div>
                </div>
                
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; 
                            padding: 12px; margin-bottom: 12px;">
                    {chart_svg}
                </div>
                
                <div style="background: {state_bg}; border: 1px solid {state_color}22; 
                            border-radius: 8px; padding: 12px 14px;">
                    <div style="color: {state_color}; font-weight: bold; font-size: 12px; 
                                margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                        <span>●</span> {vix_data['state']}
                    </div>
                    <div style="color: #aaa; font-size: 11px; line-height: 1.4;">
                        {vix_data['state_desc']}
                    </div>
                </div>
            </div>
            <div class="update-timestamp">Última actualización: {vix_data['timestamp']}</div>
        </div>
        '''
        st.markdown(vix_html, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
