# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import plotly.graph_objects as go
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURACIÓN Y BASE DE DATOS SQLITE
# ============================================================

DB_PATH = "can_slim_data.db"

def init_database():
    """Inicializa la base de datos SQLite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                sector TEXT,
                industry TEXT,
                market_cap REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                score INTEGER,
                grades TEXT,
                metrics TEXT,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_cache (
                ticker TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (ticker, date)
            )
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error inicializando DB: {e}")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def cache_price_data(ticker, df):
    try:
        conn = get_db_connection()
        df_reset = df.reset_index()
        df_reset['ticker'] = ticker
        df_reset.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 
                                'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)

        for _, row in df_reset.iterrows():
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO price_cache (ticker, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (ticker, str(row['date']), row['open'], row['high'], 
                      row['low'], row['close'], row['volume']))
            except:
                continue

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error cacheando {ticker}: {e}")

def get_cached_prices(ticker, period="1y"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(updated) FROM price_cache WHERE ticker = ?", (ticker,))
        result = cursor.fetchone()

        if result[0] is None:
            conn.close()
            return None

        last_update = datetime.fromisoformat(result[0])
        if datetime.now() - last_update > timedelta(hours=6):
            conn.close()
            return None

        limit = 252 if period == "1y" else 63
        cursor.execute("""
            SELECT date, open, high, low, close, volume 
            FROM price_cache 
            WHERE ticker = ? 
            ORDER BY date DESC 
            LIMIT ?
        """, (ticker, limit))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        return df
    except:
        return None

def save_score(ticker, data):
    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO scores (ticker, score, grades, metrics)
            VALUES (?, ?, ?, ?)
        """, (ticker, data['score'], json.dumps(data['grades']), json.dumps(data['metrics'])))
        conn.commit()
        conn.close()
    except:
        pass

# ============================================================
# CACHÉ EN MEMORIA SIMPLE
# ============================================================

class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key):
        if key in self._cache:
            if datetime.now() < self._ttl.get(key, datetime.min):
                return self._cache[key]
            else:
                del self._cache[key]
                if key in self._ttl:
                    del self._ttl[key]
        return None

    def set(self, key, value, ttl_seconds=3600):
        self._cache[key] = value
        self._ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def clear(self):
        self._cache.clear()
        self._ttl.clear()

cache = SimpleCache()

# ============================================================
# OBTENER UNIVERSO DE STOCKS
# ============================================================

@st.cache_data(ttl=3600)
def get_sp500_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        df = tables[0]
        return df['Symbol'].tolist()
    except:
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'AVGO', 'WMT']

@st.cache_data(ttl=3600)
def get_nasdaq100_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
        tables = pd.read_html(url)
        for table in tables:
            if 'Ticker' in table.columns:
                return table['Ticker'].tolist()
    except:
        pass
    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'PEP', 'COST']

@st.cache_data(ttl=3600)
def get_russell2000_tickers():
    return [
        'PLTR', 'SNOW', 'CRWD', 'OKTA', 'ZS', 'NET', 'DDOG', 'S', 'PANW', 'FTNT',
        'CYBR', 'QLYS', 'VRNS', 'TENB', 'SPLK', 'ESTC', 'FSLY', 'CFLT', 'SUMO', 'ZUO',
        'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'FSR', 'GOEV', 'WKHS', 'BLNK', 'CHPT',
        'ENPH', 'SEDG', 'RUN', 'NOVA', 'SPWR', 'BE', 'PLUG', 'FCEL', 'BLDP', 'GPRE',
        'MRNA', 'BNTX', 'NVAX', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'BLUE', 'SRPT', 'VRTX',
        'SQ', 'PYPL', 'SOFI', 'AFRM', 'UPST', 'HOOD', 'COIN', 'RBLX', 'U', 'DOCN',
        'MSTR', 'RIOT', 'MARA', 'HUT', 'BITF', 'CLSK', 'ARBK', 'CORZ', 'BTBT', 'WULF',
        'TTWO', 'EA', 'MTTR', 'VRM', 'W', 'CHWY', 'PTON', 'DASH',
        'ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ICLN', 'QCLN', 'PBW', 'TAN', 'LIT'
    ]

def get_all_universe_tickers(include_sp500=True, include_nasdaq=True, include_russell=True):
    all_tickers = []

    if include_sp500:
        sp500 = get_sp500_tickers()
        all_tickers.extend(sp500)
        print(f"S&P 500: {len(sp500)}")

    if include_nasdaq:
        nasdaq = get_nasdaq100_tickers()
        nasdaq_unique = [t for t in nasdaq if t not in all_tickers]
        all_tickers.extend(nasdaq_unique)
        print(f"NASDAQ 100: {len(nasdaq_unique)} nuevos")

    if include_russell:
        russell = get_russell2000_tickers()
        russell_unique = [t for t in russell if t not in all_tickers]
        all_tickers.extend(russell_unique)
        print(f"Russell/Growth: {len(russell_unique)} nuevos")

    print(f"Total únicos: {len(all_tickers)}")
    return all_tickers

# ============================================================
# CÁLCULO CAN SLIM (PARALELO CON THREADS)
# ============================================================

def calculate_can_slim_metrics(ticker):
    try:
        # Verificar cache
        cache_key = f"metrics_{ticker}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Intentar cache de precios
        hist = get_cached_prices(ticker)

        if hist is None:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y")
            if not hist.empty:
                cache_price_data(ticker, hist)
        else:
            stock = yf.Ticker(ticker)
            info = stock.info

        if hist.empty or len(hist) < 50:
            return None

        market_cap = info.get('marketCap', 0) / 1e9
        current_price = hist['Close'].iloc[-1]

        # Métricas
        earnings_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
        revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
        eps_growth = info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0

        high_52w = hist['High'].max()
        pct_from_high = ((current_price - high_52w) / high_52w) * 100
        is_new_high = pct_from_high > -5

        avg_volume_20 = hist['Volume'].rolling(20).mean().iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1

        # RS Rating
        try:
            spy_data = cache.get('spy_history')
            if spy_data is None:
                spy = yf.Ticker("SPY").history(period="1y")
                cache.set('spy_history', spy, ttl_seconds=1800)
            else:
                spy = spy_data

            stock_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
            spy_return = (spy['Close'].iloc[-1] / spy['Close'].iloc[0] - 1) * 100
            rs_rating = 50 + (stock_return - spy_return) * 2
            rs_rating = max(0, min(100, rs_rating))
        except:
            rs_rating = 50

        inst_ownership = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0

        # Market direction
        market_bullish = cache.get('market_bullish')
        if market_bullish is None:
            try:
                spy_current = yf.Ticker("SPY").history(period="5d")
                sma20 = spy_current['Close'].rolling(20).mean().iloc[-1] if len(spy_current) >= 20 else spy_current['Close'].mean()
                market_bullish = spy_current['Close'].iloc[-1] > sma20
                cache.set('market_bullish', market_bullish, ttl_seconds=3600)
            except:
                market_bullish = True

        # Scoring
        score = 0
        grades = {}

        if earnings_growth > 50: score += 15; grades['C'] = 'A'
        elif earnings_growth > 25: score += 12; grades['C'] = 'A'
        elif earnings_growth > 15: score += 8; grades['C'] = 'B'
        elif earnings_growth > 0: score += 4; grades['C'] = 'C'
        else: grades['C'] = 'D'

        if eps_growth > 50: score += 15; grades['A'] = 'A'
        elif eps_growth > 25: score += 12; grades['A'] = 'A'
        elif eps_growth > 15: score += 8; grades['A'] = 'B'
        elif eps_growth > 0: score += 4; grades['A'] = 'C'
        else: grades['A'] = 'D'

        if pct_from_high > -3: score += 15; grades['N'] = 'A'
        elif pct_from_high > -10: score += 12; grades['N'] = 'A'
        elif pct_from_high > -20: score += 8; grades['N'] = 'B'
        else: grades['N'] = 'C'

        if volume_ratio > 2: score += 15; grades['S'] = 'A'
        elif volume_ratio > 1.5: score += 12; grades['S'] = 'A'
        elif volume_ratio > 1: score += 8; grades['S'] = 'B'
        else: grades['S'] = 'C'

        if rs_rating > 85: score += 15; grades['L'] = 'A'
        elif rs_rating > 75: score += 12; grades['L'] = 'A'
        elif rs_rating > 65: score += 8; grades['L'] = 'B'
        else: grades['L'] = 'C'

        if inst_ownership > 60: score += 10; grades['I'] = 'A'
        elif inst_ownership > 40: score += 8; grades['I'] = 'B'
        elif inst_ownership > 20: score += 4; grades['I'] = 'C'
        else: grades['I'] = 'D'

        if market_bullish: score += 15; grades['M'] = 'A'
        else: score += 5; grades['M'] = 'C'

        result = {
            'ticker': ticker,
            'name': info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
            'market_cap': market_cap,
            'price': current_price,
            'score': score,
            'grades': grades,
            'metrics': {
                'earnings_growth': earnings_growth,
                'revenue_growth': revenue_growth,
                'eps_growth': eps_growth,
                'pct_from_high': pct_from_high,
                'volume_ratio': volume_ratio,
                'rs_rating': rs_rating,
                'inst_ownership': inst_ownership,
                'is_new_high': is_new_high
            }
        }

        cache.set(cache_key, result, ttl_seconds=1800)
        save_score(ticker, result)
        return result
    except Exception as e:
        return None

def scan_with_threads(tickers, min_score, progress_bar, status_text, max_workers=10):
    """Escaneo paralelo usando ThreadPoolExecutor (no requiere aiohttp)"""
    results = []
    completed = 0
    total = len(tickers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {executor.submit(calculate_can_slim_metrics, t): t for t in tickers}

        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            completed += 1

            try:
                result = future.result()
                if result and result['score'] >= min_score:
                    results.append(result)
            except:
                pass

            if progress_bar:
                progress_bar.progress(completed / total)
            if status_text:
                status_text.text(f"Procesados {completed}/{total} ({completed/total*100:.1f}%) - Encontrados: {len(results)}")

    return results

# ============================================================
# VISUALIZACIONES
# ============================================================

def create_score_gauge(score):
    color = "#00ffad" if score >= 80 else "#ff9800" if score >= 60 else "#f23645"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Score", 'font': {'size': 14, 'color': 'white'}},
        number={'font': {'size': 36, 'color': color}},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'bgcolor': "#0c0e12",
            'steps': [
                {'range': [0, 60], 'color': "rgba(242, 54, 69, 0.2)"},
                {'range': [60, 80], 'color': "rgba(255, 152, 0, 0.2)"},
                {'range': [80, 100], 'color': "rgba(0, 255, 173, 0.2)"}
            ]
        }
    ))

    fig.update_layout(paper_bgcolor="#0c0e12", font={'color': "white"}, height=200, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# ============================================================
# RENDER PRINCIPAL
# ============================================================

def render():
    init_database()

    st.markdown("""
    <style>
    .main { background: #0c0e12; color: white; }
    .stApp { background: #0c0e12; }
    h1, h2, h3 { color: white !important; }
    .stProgress > div > div > div > div { background-color: #00ffad; }
    .stButton>button { background-color: #00ffad; color: #0c0e12; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #00ffad;">🎯 CAN SLIM Scanner Pro v2.1</h1>
        <p style="color: #888;">SQLite + ThreadPool | Sin dependencias externas</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Configuración")

        st.subheader("Universos")
        include_sp500 = st.checkbox("S&P 500", value=True)
        include_nasdaq = st.checkbox("NASDAQ 100", value=True)
        include_russell = st.checkbox("Russell 2000 + Growth", value=True)

        st.subheader("Filtros")
        min_score = st.slider("Score mínimo", 0, 100, 40)
        max_results = st.number_input("Máx resultados", 5, 100, 20)

        st.subheader("Rendimiento")
        max_workers = st.slider("Workers paralelos", 1, 20, 10, 
                               help="Más workers = más rápido pero más riesgo de rate limiting")
        use_cache = st.checkbox("Usar Cache", value=True)

        if st.button("🗑️ Limpiar Cache"):
            cache.clear()
            st.success("Cache limpiado")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write(f"DB: {DB_PATH} | Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    with col3:
        scan_button = st.button("🔍 ESCANEAR UNIVERSO", use_container_width=True)

    if scan_button:
        tickers = get_all_universe_tickers(include_sp500, include_nasdaq, include_russell)
        st.info(f"📊 Universo total: **{len(tickers)}** activos únicos")

        progress_bar = st.progress(0)
        status_text = st.empty()

        start_time = datetime.now()

        candidates = scan_with_threads(tickers[:500], min_score, progress_bar, status_text, max_workers)  # Limitar a 500

        elapsed = (datetime.now() - start_time).total_seconds()
        progress_bar.empty()
        status_text.empty()

        candidates.sort(key=lambda x: x['score'], reverse=True)

        st.success(f"✅ Escaneo completado en {elapsed:.1f}s | {len(candidates)} candidatos encontrados")

        if candidates:
            st.subheader("🏆 Top Candidatos")
            cols = st.columns(min(3, len(candidates)))
            for i, col in enumerate(cols):
                if i < len(candidates):
                    c = candidates[i]
                    with col:
                        st.plotly_chart(create_score_gauge(c['score']), use_container_width=True, key=f"gauge_{i}")
                        st.markdown(f"**{c['ticker']}** - {c['name'][:20]}")
                        grades_str = ''.join([f"{k}:{v}" for k, v in c['grades'].items()])
                        st.markdown(f"Grades: {grades_str}")

            st.subheader("📋 Resultados Detallados")
            df_data = []
            for c in candidates[:max_results]:
                df_data.append({
                    'Ticker': c['ticker'],
                    'Nombre': c['name'][:25],
                    'Score': c['score'],
                    **c['grades'],
                    'EPS Growth': f"{c['metrics']['earnings_growth']:.1f}%",
                    'RS Rating': f"{c['metrics']['rs_rating']:.0f}",
                    'Sector': c['sector']
                })

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, height=400)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar CSV", csv, "can_slim_results.csv", "text/csv")
        else:
            st.warning("No se encontraron candidatos. Intenta reducir el score mínimo.")
            st.info("💡 Tip: Prueba con score mínimo = 30")

if __name__ == "__main__":
    render()
