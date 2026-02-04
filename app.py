# market.py
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

# Intentar importar investpy
try:
    import investpy
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False

# ────────────────────────────────────────────────
# FUNCIONS AUXILIARS - DATOS REALES
# ────────────────────────────────────────────────

def get_economic_calendar():
    """Obtiene el calendario economico de hoy y manana."""
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
            
            importance_map = {
                'high': 'High',
                'medium': 'Medium', 
                'low': 'Low'
            }
            impact = importance_map.get(row['importance'].lower(), '(),(), 'Medium')
            
            events.append({
                "time(), 'Medium')
            
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
        {"time": "14:15", "event": "ADP Nonfarm", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

# ─── CRIPTOMONEDAS REALES CON YFINANCE ───
@st.cache_data(ttl=300)
def get_crypto_prices():
    """
    Obtiene precios reales de criptomonedas usando yfinance.
    Mas estable que CoinGecko API.
    """
    try": time_es,
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

# ─── CRIPTOMONEDAS REALES CON YFINANCE ───
@st.cache_data(ttl=300)
def get_crypto_prices():
    """
    Obtiene precios reales de criptomonedas usando yfinance.
    Mas estable que CoinGecko API.
    """
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
                print(f"Error en {symbol}: {e}")
                continue
        
        if not cryptos:
            return get_fallback_crypto_prices()
            
        return cryptos
        
    except Exception as e:
        print(f"Error general crypto: {e}")
        return get_fallback_crypto_prices()

def get_fallback_crypto_prices():
    """Datos simulados como fallback"""
    return [
        {"symbol": "BTC", "name": "Bitcoin", "price": "104,231.50", "change": "+2.4%", "is_positive": True},
        {"symbol": "ETH", "name": "Ethereum", "price": "3,120.12", "change": "-1.1%", "is_positive": False},
        {"symbol": "BNB", "name": "BNB", "price": "685.45", "change": "+0.8%", "is_positive": True},
        {"symbol": "SOL", "name": "Solana", "price": "245.88", "change": "+5.7%", "is_positive": True},
        {"symbol": "XRP", "name": "XRP", "price": "3.15", "change": "-2.3%", "is_positive": False},
    ]

# ─── REDDIT REAL - SCRAPING DESDE BUZZTICKR ───
@st.cache_data(ttl=300)
def get_reddit_buzz():
    """
    Scrapea la tabla 'Overall Top 10' de tickers mas mencionados en Reddit
    desde https://www.buzztickr.com/reddit-buzz/
    """
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        top_10_tickers = []
        
        # Estrategia 1: Buscar por texto "Overall Top 10"
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
        
        # Estrategia 2: Buscar todos los enlaces de ticker
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
        
        # Estrategia 3: Extraer tickers del texto completo
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
        print(f"Error scraping Reddit Buzz: {e}")
        return get_fallback_reddit_tickers()

def get_fallback_reddit_tickers():
    """Tickers fallback cuando falla el scraping"""
    return {
        'tickers': ["MSFT", "NVDA", "TSLA", "AAPL", "AMZN", "GOOGL", "META", "AMD", "PLTR", "GME"],
        'source': 'Fallback',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }

# ─── TICKER FINANCIERO CON FUTUROS Y DATOS EN TIEMPO REAL ───
@st.cache_data(ttl=60)
def get_financial_ticker_data():
    """
    Obtiene datos para el ticker/prompter financiero:
    - Indices: SPX, NDX, DJI, RUT, N225, DAX
    - Commodities: Oro, Plata, Petroleo
    - FX: EUR/USD, USD/JPY
    - MAG7 Futuros
    - Crypto: BTC, ETH
    """
    ticker_data = []
    
    # Indices principales
    indices = {
        'ES=F': 'S&P 500 FUT',
        'NQ=F': 'NASDAQ FUT',
        'YM=F': 'DOW FUT',
        'RTY=F': 'RUSSELL FUT',
        '^N225': 'NIKKEI',
        '^GDAXI': 'DAX',
        '^FTSE': 'FTSE 100',
    }
    
    # Commodities
    commodities = {
        'GC=F': 'GOLD',
        'SI=F': 'SILVER',
        'CL=F': 'CRUDE OIL',
        'NG=F': 'NAT GAS',
    }
    
    # MAG7 para futuros (usando acciones como proxy)
    mag7 = {
        'AAPL': 'AAPL',
        'MSFT': 'MSFT',
        'GOOGL': 'GOOGL',
        'AMZN': 'AMZN',
        'NVDA': 'NVDA',
        'META': 'META',
        'TSLA': 'TSLA',
    }
    
    # Crypto
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
                
                # Formatear precio
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
    """Genera el HTML del ticker financiero animado"""
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
    
    ticker_html = f'''
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
            0% {{
                transform: translateX(0);
            }}
            100% {{
                transform: translateX(-50%);
            }}
        }}
    </style>
    '''
    
    return ticker_html

# ─── SECTORES REALES CON YFINANCE ───
@st.cache_data(ttl=600)
def get_sector_performance():
    """
    Obtiene rendimiento real de sectores usando ETFs representativos.
    """
    try:
        sector_etfs = {
            'TECH': 'XLK',
            'FINL': 'XLF',
            'HLTH': 'XLV',
            'ENER': 'XLE',
            'CONS': 'XLY',
            'UTIL': 'XLU',
            'INDU': 'XLI',
            'MATR': 'XLB',
            'STPL': 'XLP',
            'REAL': 'XLRE',
            'TELE': 'XLC',
        }
        
        sectors_data = []
        
        for name, symbol in sector_etfs.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((current - prev) / prev) * 100
                    
                    sectors_data.append((name, change))
                    
                time.sleep(0.1)
                
            except Exception as e:
                continue
        
        if not sectors_data:
            return get_fallback_sectors()
            
        return sectors_data
        
    except Exception as e:
        return get_fallback_sectors()

def get_fallback_sectors():
    """Datos de sectores simulados"""
    return [
        ("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), 
        ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)
    ]

def get_earnings_calendar():
    """Obtiene earnings reales usando yfinance si es posible"""
    try:
        earnings_tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'NVDA', 'META', 'NFLX']
        earnings_data = []
        
        for ticker in earnings_tickers[:4]:
            try:
                stock = yf.Ticker(ticker)
                calendar = stock.calendar
                if calendar is not None and not calendar.empty:
                    earnings_date = calendar.index[0] if hasattr(calendar, 'index') else None
                    if earnings_date:
                        date_str = earnings_date.strftime('%b %d') if isinstance(earnings_date, datetime) else str(earnings_date)
                        earnings_data.append((ticker, date_str, "TBD", "High"))
            except:
                continue
                
        if earnings_data:
            return earnings_data
            
    except Exception as e:
        print(f"Error earnings: {e}")
    
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("GOOGL", "Feb 06", "Before Bell", "High"),
        ("TSLA", "Feb 07", "After Market", "High"),
    ]

def get_insider_trading():
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K"),
        ("TSLA", "DIR", "SELL", "$2.1M"),
    ]

def get_fallback_news():
    return [
        {"time": "19:45", "title": "Tesla supera expectatives i puja un 8% despres del tancament", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "18:30", "title": "El PIB dels EUA creix un 2,3% al darrer trimestre", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "16:15", "title": "Apple presenta resultats record gracies a serveis", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "14:00", "title": "La inflacio subjacent a la zona euro es modera al 2,7%", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "12:30", "title": "Microsoft Cloud supera els 30.000 milions en ingressos", "impact": "Alto", "color": "#f23645", "link": "#"},
    ]

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    
    if not api_key:
        return get_fallback_news()

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()

        news_list = []
        for item in data[:8]:
            title = item.get("headline", "Sense titol")
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"

            lower = title.lower()
            if any(k in lower for k in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "employment"]):
                impact = "Alto"
                color = "#f23645"
            else:
                impact = "Moderado"
                color = "#ff9800"

            news_list.append({
                "time": time_str,
                "title": title,
                "impact": impact,
                "color": color,
                "linklink": "#"},
        {"time": "18:30", "title": "El PIB dels EUA creix un 2,3% al darrer trimestre", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "16:15", "title": "Apple presenta resultats record gracies a serveis", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "14:00", "title": "La inflacio subjacent a la zona euro es modera al 2,7%", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "12:30", "title": "Microsoft Cloud supera els 30.000 milions en ingressos", "impact": "Alto", "color": "#f23645", "link": "#"},
    ]

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    
    if not api_key:
        return get_fallback_news()

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()

        news_list = []
        for item in data[:8]:
            title = item.get("headline", "Sense titol")
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"

            lower = title.lower()
            if any(k in lower for k in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "employment"]):
                impact = "Alto"
                color = "#f23645"
            else:
                impact = "Moderado"
                color = "#ff9800"

            news_list.append({
                "time": time_str,
                "title": title,
                "impact": impact,
                "color": color,
                "link": link
            })
        return news_list if news_list else get_fallback_news()
    except Exception as e:
        return get_fallback_news()


def get_fed_liquidity():
    api_key = st.secrets.get("FRED_API_KEY", None)
    
    if not api_key:
        return "ERROR", "#888", "API Key no configurada", "N/A", "N/A"
    
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc"
    try:
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
                    status = "QT"
                    color = "#f23645"
                    desc = "Quantitative Tightening"
                elif change > 100:
                    status = "QE"
                    color = "#00ffad"
                    desc = "Quantitative Easing"
                else:
                    status = "STABLE"
                    color = "#ff9800"
                    desc = "Balance sheet stable"
                return status, color, desc, f"{latest_val/1000:.1f}T", date_latest
        return "ERROR", "#888", "API temporalment no disponible", "N/A", "N/A"
    except:
        return "N/A", "#888", "Sense connexio a FRED", "N/A", "N/A"


# ────────────────────────────────────────────────
# RENDER DEL DASHBOARD
# ────────────────────────────────────────────────

def render():
    # CSS global
    st.markdown("""
    <style>
        .tooltip-container {
            position: absolute;
            top: 50%;
            right: 12px;
            transform: translateY(-50%);
            cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 140%;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }

        .fng-legend {
            display: flex;
            justify-content: space-between;
            width: 100%;
            margin-top: 12px;
            font-size: 0.65rem;
            color: #ccc;
            text-align: center;
            padding: 0 10px;
        }
        .fng-legend-item {
            flex: 1;
            padding: 0 4px;
        }
        .fng-color-box {
            width: 100%;
            height: 6px;
            margin-bottom: 4px;
            border-radius: 3px;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .news-item {
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            transition: background 0.2s;
        }
        .news-item:hover {
            background: #0c0e12;
        }
        .news-item:last-child {
            border-bottom: none;
        }
        .impact-badge {
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .news-link {
            color: #00ffad;
            text-decoration: none;
            font-size: 0.85rem;
        }
        .news-link:hover {
            text-decoration: underline;
        }
        
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
        }
        .group-header {
            background: #0c0e12;
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .group-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        .group-content {
            padding: 0;
        }
    </style>
    """, unsafe_allow_html=True)

    # TICKER FINANCIERO ANIMADO EN LA PARTE SUPERIOR
    ticker_html = generate_ticker_html()
    components.html(ticker_html, height=50, scrolling=False)
    
    st.markdown('<h1 style="margin-top:20px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    H = "340px"

    # FILA 1
    col1, col2, col3 = st.columns(3)

    with col1:
        indices_html = ""
        for t, n in [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]:
            idx_val, idx_change = get_market_index(t)
            color = "#00ffad" if idx_change >= 0 else "#f23645"
            indices_html += f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{idx_val:,.2f}</div><div style="color:{color}; font-size:11px; font-weight:bold;">{idx_change:+.2f}%</div></div>
            </div>'''
        
        tooltip = "Rendiment en temps real dels principals indexs borsaris dels EUA."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events = get_economic_calendar()
        
        impact_colors = {
            'High': '#f23645',
            'Medium': '#ff9800',
            'Low': '#4caf50'
        }
        
        events_html = ""
        for ev in events:
            imp_color = impact_colors.get(ev['imp'], '#888')
            events_html += f'''
            <div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:10px; width:45px; font-family:monospace;">{ev["time"]}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:11px; font-weight:500; line-height:1.3;">{ev["event"]}</div>
                    <div style="color:{imp_color}; font-size:8px; font-weight:bold; text-transform:uppercase; margin-top:3px;">
                        ● {ev["imp"]} IMPACT
                    </div>
                </div>
                <div style="text-align:right; min-width:50px;">
                    <div style="color:white; font-size:11px; font-weight:bold;">{ev["val"]}</div>
                    <div style="color:#444; font-size:9px;">P: {ev["prev"]}</div>
                </div>
            </div>'''
            
        tooltip = "Calendari economic en temps real (hora espanyola CET/CEST). Dades d'investpy."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Calendari Economic</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        reddit_data = get_reddit_buzz()
        tickers = reddit_data.get('tickers', [])
        
        reddit_html_items = []
        for i, ticker in enumerate(tickers[:10], 1):
            rank_bg = "#f23645" if i <= 3 else "#1a1e26"
            rank_color = "white" if i <= 3 else "#888"
            trend_text = "HOT 🔥" if i <= 3 else "Trending"
            trend_bg = "rgba(242, 54, 69, 0.2)" if i <= 3 else "rgba(0, 255, 173, 0.1)"
            trend_color = "#f23645" if i <= 3 else "#00ffad"
            
            item_html = f'''
            <div style="display: flex; align-items: center; padding: 12px 15px; border-bottom: 1px solid #1a1e26; transition: background 0.2s;">
                <div style="width: 28px; height: 28px; border-radius: 50%; background: {rank_bg}; display: flex; align-items: center; justify-content: center; color: {rank_color}; font-weight: bold; font-size:  font-size: 12px; margin font-size: 12px; margin-right: 12px;">{i}</div>
                <div style="flex: 1;">
                    <div style="color: #00ffad; font-weight: bold; font-size: 14px;">${ticker}</div>
                    <div style="color: #666; font-size: 10px; margin-top: 2px;">Buzzing on Reddit</div>
                </div>
                <div style="color: {trend_color}; font-size: 11px; font-weight: bold; background: {trend_bg}; padding: 4px 8px; border-radius: 4px;">{trend_text}</div>
            </div>
            '''
            reddit_html_items.append(item_html)
        
        reddit_content = "".join(reddit_html_items)
        badge_text = f"Top {len(tickers)}"
        tooltip_text = f"Top 10 tickers mes mencionats a Reddit (scraping de BuzzTickr). Actualitzat: {reddit_data.get('timestamp', 'now')}"
        
        reddit_html_full = f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}

.container {{
    border: 1px solid #1a1e26;
    border-radius: 10px;
    overflow: hidden;
    background: #11141a;
    width: 100%;
}}

.header {{
    background: #0c0e12;
    padding: 12px 15px;
    border-bottom: 1px solid #1a1e26;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.title {{
    color: white;
    font-size: 14px;
    font-weight: bold;
}}

.badge {{
    background: #2a3f5f;
    color: #00ffad;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}}

.tooltip-container {{
    position: relative;
    cursor: help;
}}

.tooltip-icon {{
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #1a1e26;
    border: 2px solid #555;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
 font-size: 12px; margin-right: 12px;">{i}</div>
                <div style="flex: 1;">
                    <div style="color: #00ffad; font-weight: bold; font-size: 14px;">${ticker}</div>
                    <div style="color: #666; font-size: 10px; margin-top: 2px;">Buzzing on Reddit</div>
                </div>
                <div style="color: {trend_color}; font-size: 11px; font-weight: bold; background: {trend_bg}; padding: 4px 8px; border-radius: 4px;">{trend_text}</div>
            </div>
            '''
            reddit_html_items.append(item_html)
        
        reddit_content = "".join(reddit_html_items)
        badge_text = f"Top {len(tickers)}"
        tooltip_text = f"Top 10 tickers mes mencionats a Reddit (scraping de BuzzTickr). Actualitzat: {reddit_data.get('timestamp', 'now')}"
        
        reddit_html_full = f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}

.container {{
    border: 1px solid #1a1e26;
    border-radius: 10px;
    overflow: hidden;
    background: #11141a;
    width: 100%;
}}

.header {{
    background: #0c0e12;
    padding: 12px 15px;
    border-bottom: 1px solid #1a1e26;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.title {{
    color: white;
    font-size: 14px;
    font-weight: bold;
}}

.badge {{
    background: #2a3f5f;
    color: #00ffad;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}}

.tooltip-container {{
    position: relative;
    cursor: help;
}}

.tooltip-icon {{
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #1a1e26;
    border: 2px solid #555;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
    font-size: 16px;
    font-weight: bold;
}}

.tooltip-text {{
    visibility: hidden;
    width: 260260px;
    background-color: #1e222d;
    color: #eee;
    text-align: left;
    padding: 10px 12px;
    border-radius: 6px;
    position: absolute;
    z-index: 999;
    top: 35px;
    right: -10px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    border: 1px solid #444;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}}

.tooltip-container:hover .tooltip-text {{
    visibility: visible;
    opacity: 1;
}}

.content {{
    background: #11141a;
    height: 340px;
    overflow-y: auto;
}}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="title">Reddit Social Pulse</div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span class="badge">{badge_text}</span>
            <div class="tooltip-container">
                <div class="tooltip-icon">?</div>
                <div class="tooltip-text">{tooltip_text}</div>
            </div>
        </div>
    </div>
    <div class="content">
        {reddit_content}
    </div>
</div>
</body>
</html>'''
        
        components.html(reddit_html_full, height=400, scrolling=False)

    # FILA 2
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val_display = "N/D"
            label = "ERROR DE CONNEXIO"
            col = "#888"
            bar_width = 50
            extra = " (refresca)"
        else:
            val_display = val
            bar_width = val
            if val <= 24:
                label, col = "EXTREME FEAR", "#d32f2f"
            elif val <= 44:
                label, col = "FEAR", "#f57c00"
            elif val <= 55:
                label, col = "NEUTRAL", "#ff9800"
            elif val <= 75:
                label, col = "GREED", "#4caf50"
            else:
                label, col = "EXTREME GREED", "#00ffad"
            extra = ""

        tooltip = "Index CNN Fear & Greed – mesura el sentiment del mercat."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'

        st.markdown(f'''<div class="group-container">
            <div class="group-header">
                <p class="group-title">Fear & Greed Index</p>
                {info_icon}
            </div>
            <div class="group-content" style="background:#11141a; height:{H}; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px 15px;">
                <div style="font-size:4.2rem; font-weight:bold; color:{col};">{val_display}</div>
                <div style="color:white; font-size:1.1rem; letter-spacing:1.5px; font-weight:bold; margin:12px 0;">{label}{extra}</div>
                <div style="width:88%; background:#0c0e12; height:14px; border-radius:7px; margin:18px 0 12px 0; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{bar_width}%; background:linear-gradient(to right, {col}, {col}aa); height:100%; transition:width 0.8s ease;"></div>
                </div>
                <div class="fng-legend">
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Extreme Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Fear</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Greed</div></div>
                    <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Extreme Greed</div></div>
                </div>
            </div>
        </div>''', unsafe_allow_html=True)

    with c2:
        sectors = get_sector_performance()
        sectors_html = ""
        for n, p in sectors:
            bg_color = "#00ffad11" if p >= 0 else "#f2364511"
            border_color = "#00ffad44" if p >= 0 else "#f2364544"
            text_color = "#00ffad" if p >= 0 else "#f23645"
            sectors_html += f'<div style="background:{bg_color}; border:1px solid {border_color}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{text_color}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>'
        
        tooltip = "Rendiment diari dels principals sectors del mercat (ETFs) via yfinance."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        try:
            cryptos = get_crypto_prices()
        except:
            cryptos = get_fallback_crypto_prices()
        
        tooltip_text = "Preus reals de criptomonedes via yfinance (Bitcoin, Ethereum, etc)."
        
        crypto_items_html = []
        for crypto in cryptos[:5]:
            try:
                symbol = str(crypto.get('symbol', 'N/A'))
                name = str(crypto.get('name', 'Unknown'))
                price = str(crypto.get('price', '0.00'))
                change = str(crypto.get('change', '0%'))
                is_positive = crypto.get('is_positive', True)
                
                color = "#00ffad" if is_positive else "#f23645"
                
                item_html = (
                    '<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">'
                    '<div style="display:flex; align-items:center; gap:10px;">'
                    '<div style="color:white; font-weight:bold; font-size:13px;">' + symbol + '</div>'
                    '<div style="color:#555; font-size:9px;">' + name + '</div>'
                    '</div>'
                    '<div style="text-align:right;">'
                    '<div style="color:white; font-size:13px; font-weight:bold;">$' + price + '</div>'
                    '<div style="color:' + color + '; font-size:11px; font-weight:bold;">' + change + '</div>'
                    '</div>'
                    '</div>'
                )
                crypto_items_html.append(item_html)
            except Exception as e:
                continue
        
        crypto_content = "".join(crypto_items_html)
        
        crypto_html_full = '''<!DOCTYPE html>
<html>
<head>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

.container {
    border: 1px solid #1a1e26;
    border-radius: 10px;
    overflow: hidden;
    background: #11141a;
    width: 100%;
}

.header {
    background: #0c0e12;
    padding: 12px 15px;
    border-bottom: 1px solid #1a1e26;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.title {
    color: white;
    font-size: 14px;
    font-weight: bold;
}

.tooltip-container {
    position: relative;
    cursor: help;
}

.tooltip-icon {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #1a1e26;
    border: 2px solid #555;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
    font-size: 16px;
    font-weight: bold;
}

.tooltip-text {
    visibility: hidden;
    width: 260px;
    background-color: #1e222d;
    color: #eee;
    text-align: left;
    padding: 10px 12px;
    border-radius: 6px;
    position: absolute;
    z-index: 999;
    top: 35px;
    right: -10px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    border: 1px solid #444;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.tooltip-container:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}

.content {
    background: #11141a;
    height: 340px;
    overflow-y: auto;
    padding: 15px;
}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="title">Crypto Pulse</div>
        <div class="tooltip-container">
            <div class="tooltip-icon">?</div>
            <div class="tooltip-text">''' + tooltip_text + '''</div>
        </div>
    </div>
    <div class="content">
        ''' + crypto_content + '''
    </div>
</div>
</body>
</html>'''
        
        components.html(crypto_html_full, height=400, scrolling=False)

    # FILA 3
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    with f3c1:
        earnings = get_earnings_calendar()
        earn_html = ""
        for t, d, tm, i in earnings:
            impact_color = "#f23645" if i == "High" else "#888"
            earn_html += f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</div><div style="color:#444; font-size:9px; font-weight:bold;">{d}</div></div>
            <div style="text-align:right;"><div style="color:#888; font-size:9px;">{tm}</div><span style="color:{impact_color}; font-size:8px; font-weight:bold;">● {i}</span></div>
            </div>'''
        
        tooltip = "Calendari de publicacio de resultats d'empreses importants aquesta setmana."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        insiders = get_insider_trading()
        insider_html = ""
        for t, p, ty, a in insiders:
            type_color = "#00ffad" if ty == "BUY" else "#f23645"
            insider_html += f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
            <div><div style="color:white; font-weight:bold; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div>
            <div style="text-align:right;"><div style="color:{type_color}; font-weight:bold; font-size:10px;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div>
            </div>'''
        
        tooltip = "Compres i vendes recents d'accions per part de directius i insiders."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news = fetch_finnhub_news()
        
        tooltip_text = "Noticies d'alt impacte obtingudes via Finnhub API."
        
        news_items_html = []
        for item in news:
            safe_title = item['title'].replace('"', '&quot;').replace("'", '&#39;')
            time_val = item['time']
            impact_val = item['impact']
            color_val = item['color']
            link_val = item['link']
            
            news_item = (
                '<div style="padding: 12px 15px; border-bottom: 1px solid #1a1e26;">'
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">'
                '<span style="color:#888;font-size:0.78rem;font-family:monospace;">' + time_val + '</span>'
                '<span style="padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; background-color:' + color_val + '22;color:' + color_val + ';">' + impact_val + '</span>'
                '</div>'
                '<div style="color:white;font-size:0.92rem;line-height:1.35;margin-bottom:8px;">' + safe_title + '</div>'
                '<a href="' + link_val + '" target="_blank" style="color: #00ffad; text-decoration: none; font-size: 0.85rem;">→ Llig la noticia completa</a>'
                '</div>'
            )
            news_items_html.append(news_item)
        
        news_content = "".join(news_items_html)
        
        full_html = '''<!DOCTYPE html>
<html>
<head>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

.container {
    border: 1px solid #1a1e26;
    border-radius: 10px;
    overflow: hidden;
    background: #11141a;
    width: 100%;
}

.header {
    background: #0c0e12;
    padding: 12px 15px;
    border-bottom: 1px solid #1a1e26;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.title {
    color: white;
    font-size: 14px;
    font-weight: bold;
}

.tooltip-container {
    position: relative;
    cursor: help;
}

.tooltip-icon {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #1a1e26;
    border: 2px solid #555;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
    font-size: 16px;
    font-weight: bold;
}

.tooltip-text {
    visibility: hidden;
    width: 260px;
    background-color: #1e222d;
    color: #eee;
    text-align: left;
    padding: 10px 12px;
    border-radius: 6px;
    position: absolute;
    z-index: 999;
    top: 35px;
    right: -10px;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    border: 1px solid #444;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.tooltip-container:hover .tooltip-text {
    visibility: visible;
    opacity: 1;
}

.content {
    background: #11141a;
    height: 340px;
    overflow-y: auto;
}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="title">Noticies d'Alt Impacte</div>
        <div class="tooltip-container">
            <div class="tooltip-icon">?</div>
            <div class="tooltip-text">''' + tooltip_text + '''</div>
        </div>
    </div>
    <div class="content">
        ''' + news_content + '''
    </div>
</div>
</body>
</html>'''
        
        components.html(full_html, height=400, scrolling=False)

    # FILA 4
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)

    with f4c1:
        vix = get_market_index("^VIX")
        vix_color = "#00ffad" if vix[1] >= 0 else "#f23645"
        vix_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:4.2rem; font-weight:bold; color:white;">{vix[0]:.2f}</div>
                <div style="color:#f23645; font-size:1.4rem; font-weight:bold;">VIX INDEX</div>
                <div style="color:{vix_color}; font-size:1.2rem; font-weight:bold;">{vix[1]:+.2f}%</div>
                <div style="color:#555; font-size:0.9rem; margin-top:15px;">Volatility Index</div>
            </div>
        '''
        tooltip = "Index de volatilitat CBOE (VIX) – mesura la por esperada al mercat."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">VIX Index</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{vix_html}</div></div>', unsafe_allow_html=True)

    with f4c2:
        status, color, desc, assets, date = get_fed_liquidity()
        fed_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:5rem; font-weight:bold; color:{color};">{status}</div>
                <div style="color:white; font-size:1.3rem; font-weight:bold; margin:10px 0;">{desc}</div>
                <div style="background:#0c0e12; padding:12px 20px; border-radius:8px; border:1px solid #1a1e26;">
                    <div style="font-size:1.8rem; color:white;">{assets}</div>
                    <div style="color:#888; font-size:0.9rem;">Total Assets (FED)</div>
                </div>
                <div style="color:#555; font-size:0.8rem; margin-top:12px;">Actualitzat: {date}</div>
            </div>
        '''
        tooltip = "Politica de liquiditat de la FED: expansio (QE) / contraccio (QT) segons balanc."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">FED Liquidity Policy</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{fed_html}</div></div>', unsafe_allow_html=True)

    with f4c3:
        tnx = get_market_index("^TNX")
        tnx_color = "#00ffad" if tnx[1] >= 0 else "#f23645"
        tnx_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:4.2rem; font-weight:bold; color:white;">{tnx[0]:.2f}%</div>
                <div style="color:white; font-size:1.4rem; font-weight:bold;">10Y TREASURY</div>
                <div style="color:{tnx_color}; font-size:1.2rem; font-weight:bold;">{tnx[1]:+.2f}%</div>
                <div style="color:#555; font-size:0.9rem; margin-top:15px;">US 10-Year Yield</div>
            </div>
        '''
        tooltip = "Rendiment del bo del Tresor dels EUA a 10 anys."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">10Y Treasury Yield</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{tnx_html}</div></div>', unsafe_allow_html=True)
