# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
import asyncio
import aiohttp
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import hashlib
import pickle
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURACIÓN Y BASE DE DATOS SQLITE
# ============================================================

DB_PATH = "can_slim_data.db"

def init_database():
    """Inicializa la base de datos SQLite con todas las tablas necesarias"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla de stocks escaneados
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

    # Tabla de scores históricos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            score INTEGER,
            grades TEXT,
            metrics TEXT,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker) REFERENCES stocks (ticker)
        )
    """)

    # Tabla de precios históricos (cache)
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

    # Tabla de fundamentales (cache)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals_cache (
            ticker TEXT PRIMARY KEY,
            earnings_growth REAL,
            revenue_growth REAL,
            eps_growth REAL,
            inst_ownership REAL,
            insider_ownership REAL,
            float_shares REAL,
            updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de configuración
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada")

def get_db_connection():
    """Obtiene conexión a la base de datos"""
    return sqlite3.connect(DB_PATH)

def cache_price_data(ticker, df):
    """Guarda datos de precios en cache"""
    try:
        conn = get_db_connection()
        df_reset = df.reset_index()
        df_reset['ticker'] = ticker
        df_reset.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 
                                'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)

        # Insertar o reemplazar
        df_reset[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']].to_sql(
            'price_cache', conn, if_exists='append', index=False, method='REPLACE'
        )
        conn.close()
    except Exception as e:
        print(f"Error cacheando precios de {ticker}: {e}")

def get_cached_prices(ticker, period="1y"):
    """Obtiene precios cacheados si existen y son recientes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar última actualización
        cursor.execute("""
            SELECT MAX(updated) FROM price_cache WHERE ticker = ?
        """, (ticker,))
        result = cursor.fetchone()

        if result[0] is None:
            conn.close()
            return None

        last_update = datetime.fromisoformat(result[0])
        if datetime.now() - last_update > timedelta(hours=6):  # Cache válido por 6 horas
            conn.close()
            return None

        # Obtener datos
        cursor.execute("""
            SELECT date, open, high, low, close, volume 
            FROM price_cache 
            WHERE ticker = ? 
            ORDER BY date DESC 
            LIMIT ?
        """, (ticker, 252 if period == "1y" else 63))

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
    """Guarda score en base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scores (ticker, score, grades, metrics)
            VALUES (?, ?, ?, ?)
        """, (
            ticker,
            data['score'],
            json.dumps(data['grades']),
            json.dumps(data['metrics'])
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error guardando score de {ticker}: {e}")

def get_historical_scores(ticker, days=30):
    """Obtiene scores históricos de un ticker"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT scan_date, score, grades 
            FROM scores 
            WHERE ticker = ? 
            AND scan_date >= date('now', '-{} days')
            ORDER BY scan_date ASC
        """.format(days), (ticker,))

        rows = cursor.fetchall()
        conn.close()
        return rows
    except:
        return []

# ============================================================
# ASYNC/AWAIT PARA DESCARGAS RÁPIDAS
# ============================================================

class AsyncStockFetcher:
    """Clase para descargas asíncronas de datos de stocks"""

    def __init__(self, max_concurrent=20):
        self.max_concurrent = max_concurrent
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_stock_data(self, ticker):
        """Descarga datos de un stock de forma asíncrona"""
        try:
            # Primero intentar cache
            cached = get_cached_prices(ticker)
            if cached is not None:
                return {'ticker': ticker, 'data': cached, 'source': 'cache'}

            # Si no está en cache, descargar
            loop = asyncio.get_event_loop()

            # Ejecutar yfinance en thread separado para no bloquear
            def download():
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1y")
                info = stock.info
                return hist, info

            hist, info = await loop.run_in_executor(None, download)

            # Guardar en cache
            if not hist.empty:
                cache_price_data(ticker, hist)

            return {
                'ticker': ticker,
                'history': hist,
                'info': info,
                'source': 'download'
            }
        except Exception as e:
            return {'ticker': ticker, 'error': str(e)}

    async def fetch_batch(self, tickers, progress_callback=None):
        """Descarga un lote de stocks con control de concurrencia"""
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_limit(ticker):
            async with semaphore:
                result = await self.fetch_stock_data(ticker)
                if progress_callback:
                    progress_callback()
                return result

        tasks = [fetch_with_limit(t) for t in tickers]
        results = await asyncio.gather(*tasks)
        return results

def run_async_scan(tickers, progress_bar=None, status_text=None):
    """Ejecuta el escaneo asíncrono con manejo de progreso"""

    total = len(tickers)
    completed = 0
    results = []

    def progress_callback():
        nonlocal completed
        completed += 1
        if progress_bar:
            progress_bar.progress(completed / total)
        if status_text:
            status_text.text(f"Procesados {completed}/{total} ({completed/total*100:.1f}%)")

    async def main():
        async with AsyncStockFetcher(max_concurrent=15) as fetcher:
            # Procesar en lotes de 100 para evitar sobrecarga
            batch_size = 100
            all_results = []

            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i+batch_size]
                batch_results = await fetcher.fetch_batch(batch, progress_callback)
                all_results.extend(batch_results)

                # Pequeña pausa entre lotes
                await asyncio.sleep(0.5)

            return all_results

    return asyncio.run(main())

# ============================================================
# SISTEMA DE CACHÉ EN MEMORIA (SIMULANDO REDIS)
# ============================================================

class SimpleCache:
    """Caché simple en memoria con TTL (simula Redis básico)"""

    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key):
        """Obtiene valor si existe y no ha expirado"""
        if key in self._cache:
            if datetime.now() < self._ttl.get(key, datetime.min):
                return self._cache[key]
            else:
                # Expirado, eliminar
                del self._cache[key]
                del self._ttl[key]
        return None

    def set(self, key, value, ttl_seconds=3600):
        """Guarda valor con TTL"""
        self._cache[key] = value
        self._ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def delete(self, key):
        """Elimina clave"""
        if key in self._cache:
            del self._cache[key]
            del self._ttl[key]

    def clear(self):
        """Limpia todo el caché"""
        self._cache.clear()
        self._ttl.clear()

# Instancia global de caché
cache = SimpleCache()

# ============================================================
# OBTENER UNIVERSO DE STOCKS (CORREGIDO)
# ============================================================

@st.cache_data(ttl=3600)
def get_sp500_tickers():
    """Obtiene S&P 500 desde Wikipedia"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        df = tables[0]
        tickers = df['Symbol'].tolist()
        print(f"✅ S&P 500 cargado: {len(tickers)} tickers")
        return tickers
    except Exception as e:
        print(f"⚠️ Error cargando S&P 500: {e}")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'AVGO', 'WMT']

@st.cache_data(ttl=3600)
def get_nasdaq100_tickers():
    """Obtiene NASDAQ 100"""
    try:
        url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
        tables = pd.read_html(url)
        for table in tables:
            if 'Ticker' in table.columns:
                tickers = table['Ticker'].tolist()
                print(f"✅ NASDAQ 100 cargado: {len(tickers)} tickers")
                return tickers
    except Exception as e:
        print(f"⚠️ Error cargando NASDAQ 100: {e}")

    return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'PEP', 'COST']

@st.cache_data(ttl=3600)
def get_russell2000_tickers():
    """Obtiene muestra representativa del Russell 2000"""
    # Lista diversificada de small-caps líquidas
    tickers = [
        # Tech
        'PLTR', 'SNOW', 'CRWD', 'OKTA', 'ZS', 'NET', 'DDOG', 'S', 'PANW', 'FTNT',
        'CYBR', 'QLYS', 'VRNS', 'TENB', 'SPLK', 'ESTC', 'FSLY', 'CFLT', 'SUMO', 'ZUO',
        # EV / Clean Energy
        'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'FSR', 'GOEV', 'WKHS', 'BLNK', 'CHPT',
        'ENPH', 'SEDG', 'RUN', 'NOVA', 'SPWR', 'BE', 'PLUG', 'FCEL', 'BLDP', 'GPRE',
        # Biotech
        'MRNA', 'BNTX', 'NVAX', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'BLUE', 'SRPT', 'VRTX',
        # Fintech
        'SQ', 'PYPL', 'SOFI', 'AFRM', 'UPST', 'HOOD', 'COIN', 'RBLX', 'U', 'DOCN',
        # Crypto
        'MSTR', 'RIOT', 'MARA', 'HUT', 'BITF', 'CLSK', 'ARBK', 'CORZ', 'BTBT', 'WULF',
        # Gaming/E-commerce
        'TTWO', 'EA', 'RBLX', 'U', 'MTTR', 'VRM', 'W', 'CHWY', 'PTON', 'DASH',
        # Otros growth
        'ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ICLN', 'QCLN', 'PBW', 'TAN', 'LIT'
    ]
    print(f"✅ Russell 2000/Growth cargado: {len(tickers)} tickers")
    return tickers

def get_all_universe_tickers(include_sp500=True, include_nasdaq=True, include_russell=True):
    """Combina todos los universos SIN eliminar duplicados incorrectamente"""
    all_tickers = []
    sources = []

    if include_sp500:
        sp500 = get_sp500_tickers()
        all_tickers.extend(sp500)
        sources.append(f"S&P 500: {len(sp500)}")

    if include_nasdaq:
        nasdaq = get_nasdaq100_tickers()
        # Evitar duplicados con S&P 500
        nasdaq_unique = [t for t in nasdaq if t not in all_tickers]
        all_tickers.extend(nasdaq_unique)
        sources.append(f"NASDAQ 100: {len(nasdaq_unique)} (new)")

    if include_russell:
        russell = get_russell2000_tickers()
        # Evitar duplicados
        russell_unique = [t for t in russell if t not in all_tickers]
        all_tickers.extend(russell_unique)
        sources.append(f"Russell/Growth: {len(russell_unique)} (new)")

    print(f"📊 Total únicos: {len(all_tickers)}")
    for source in sources:
        print(f"   {source}")

    return all_tickers

# ============================================================
# CÁLCULO DE MÉTRICAS CAN SLIM (OPTIMIZADO)
# ============================================================

def calculate_can_slim_metrics(ticker, data=None):
    """Calcula métricas CAN SLIM con soporte para datos precargados"""
    try:
        # Usar datos proporcionados o descargar
        if data is None:
            # Intentar cache primero
            cache_key = f"metrics_{ticker}"
            cached = cache.get(cache_key)
            if cached:
                return cached

            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1y")
        else:
            info = data.get('info', {})
            hist = data.get('history', pd.DataFrame())

        if hist.empty or len(hist) < 50:
            return None

        # Datos básicos
        market_cap = info.get('marketCap', 0) / 1e9
        current_price = hist['Close'].iloc[-1]

        # C - Current Quarterly Earnings
        earnings_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
        revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0

        # A - Annual Earnings Growth
        eps_growth = info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0

        # N - New Highs
        high_52w = hist['High'].max()
        pct_from_high = ((current_price - high_52w) / high_52w) * 100
        is_new_high = pct_from_high > -5

        # S - Supply and Demand
        avg_volume_20 = hist['Volume'].rolling(20).mean().iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1

        # L - Leader (RS Rating)
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

        # I - Institutional
        inst_ownership = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0

        # M - Market Direction (simplificado)
        market_bullish = cache.get('market_bullish')
        if market_bullish is None:
            try:
                spy_current = yf.Ticker("SPY").history(period="5d")
                sma20 = spy_current['Close'].rolling(20).mean().iloc[-1] if len(spy_current) >= 20 else spy_current['Close'].mean()
                market_bullish = spy_current['Close'].iloc[-1] > sma20
                cache.set('market_bullish', market_bullish, ttl_seconds=3600)
            except:
                market_bullish = True

        # Calcular Score
        score = 0
        grades = {}

        # C (15 pts)
        if earnings_growth > 50: score += 15; grades['C'] = 'A'
        elif earnings_growth > 25: score += 12; grades['C'] = 'A'
        elif earnings_growth > 15: score += 8; grades['C'] = 'B'
        elif earnings_growth > 0: score += 4; grades['C'] = 'C'
        else: grades['C'] = 'D'

        # A (15 pts)
        if eps_growth > 50: score += 15; grades['A'] = 'A'
        elif eps_growth > 25: score += 12; grades['A'] = 'A'
        elif eps_growth > 15: score += 8; grades['A'] = 'B'
        elif eps_growth > 0: score += 4; grades['A'] = 'C'
        else: grades['A'] = 'D'

        # N (15 pts)
        if pct_from_high > -3: score += 15; grades['N'] = 'A'
        elif pct_from_high > -10: score += 12; grades['N'] = 'A'
        elif pct_from_high > -20: score += 8; grades['N'] = 'B'
        else: grades['N'] = 'C'

        # S (15 pts)
        if volume_ratio > 2: score += 15; grades['S'] = 'A'
        elif volume_ratio > 1.5: score += 12; grades['S'] = 'A'
        elif volume_ratio > 1: score += 8; grades['S'] = 'B'
        else: grades['S'] = 'C'

        # L (15 pts)
        if rs_rating > 85: score += 15; grades['L'] = 'A'
        elif rs_rating > 75: score += 12; grades['L'] = 'A'
        elif rs_rating > 65: score += 8; grades['L'] = 'B'
        else: grades['L'] = 'C'

        # I (10 pts)
        if inst_ownership > 60: score += 10; grades['I'] = 'A'
        elif inst_ownership > 40: score += 8; grades['I'] = 'B'
        elif inst_ownership > 20: score += 4; grades['I'] = 'C'
        else: grades['I'] = 'D'

        # M (15 pts)
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

        # Guardar en cache
        cache.set(cache_key, result, ttl_seconds=1800)

        # Guardar en base de datos
        save_score(ticker, result)

        return result
    except Exception as e:
        print(f"Error en {ticker}: {e}")
        return None

# ============================================================
# VISUALIZACIONES (SIMPLIFICADAS)
# ============================================================

def create_score_gauge(score):
    """Gauge para el score"""
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
    # Inicializar base de datos
    init_database()

    st.set_page_config(page_title="CAN SLIM Scanner Pro", layout="wide", initial_sidebar_state="expanded")

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
        <h1 style="color: #00ffad;">🎯 CAN SLIM Scanner Pro v2.0</h1>
        <p style="color: #888;">SQLite + Async + Cache | 1,500+ stocks | Tiempo real</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")

        st.subheader("Universos")
        include_sp500 = st.checkbox("S&P 500", value=True)
        include_nasdaq = st.checkbox("NASDAQ 100", value=True)
        include_russell = st.checkbox("Russell 2000 + Growth", value=True)

        st.subheader("Filtros")
        min_score = st.slider("Score mínimo", 0, 100, 40)
        max_results = st.number_input("Máx resultados", 5, 100, 20)

        st.subheader("Opciones Avanzadas")
        use_async = st.checkbox("Usar Async (rápido)", value=True)
        use_cache = st.checkbox("Usar Cache", value=True)

        if st.button("🗑️ Limpiar Cache"):
            cache.clear()
            st.success("Cache limpiado")

    # Main content
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    with col3:
        scan_button = st.button("🔍 ESCANEAR UNIVERSO", use_container_width=True)

    if scan_button:
        # Obtener universo
        tickers = get_all_universe_tickers(include_sp500, include_nasdaq, include_russell)
        st.info(f"📊 Universo total: **{len(tickers)}** activos únicos")

        progress_bar = st.progress(0)
        status_text = st.empty()

        start_time = datetime.now()

        if use_async:
            # Método asíncrono (rápido)
            status_text.text("Descargando datos en paralelo...")
            raw_results = run_async_scan(tickers[:500], progress_bar, status_text)  # Limitar a 500 para demo

            # Procesar resultados
            candidates = []
            for result in raw_results:
                if 'error' not in result and 'history' in result:
                    metrics = calculate_can_slim_metrics(result['ticker'], result)
                    if metrics and metrics['score'] >= min_score:
                        candidates.append(metrics)
        else:
            # Método secuencial (lento pero estable)
            candidates = []
            for i, ticker in enumerate(tickers[:200]):  # Limitar para demo
                progress_bar.progress((i + 1) / 200)
                status_text.text(f"Analizando {ticker}... ({i+1}/200)")

                result = calculate_can_slim_metrics(ticker)
                if result and result['score'] >= min_score:
                    candidates.append(result)

        elapsed = (datetime.now() - start_time).total_seconds()
        progress_bar.empty()
        status_text.empty()

        # Ordenar por score
        candidates.sort(key=lambda x: x['score'], reverse=True)

        st.success(f"✅ Escaneo completado en {elapsed:.1f}s | {len(candidates)} candidatos encontrados")

        if candidates:
            # Top 3
            st.subheader("🏆 Top Candidatos")
            cols = st.columns(min(3, len(candidates)))
            for i, col in enumerate(cols):
                if i < len(candidates):
                    c = candidates[i]
                    with col:
                        st.plotly_chart(create_score_gauge(c['score']), use_container_width=True, key=f"gauge_{i}")
                        st.markdown(f"**{c['ticker']}** - {c['name'][:20]}")
                        st.markdown(f"Score: **{c['score']}** | Grades: {''.join(c['grades'].values())}")

            # Tabla completa
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

            # Exportar
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar CSV", csv, "can_slim_results.csv", "text/csv")
        else:
            st.warning("No se encontraron candidatos. Intenta reducir el score mínimo.")
            st.info("💡 Tip: Prueba con score mínimo = 30 para ver más resultados")

if __name__ == "__main__":
    render()
