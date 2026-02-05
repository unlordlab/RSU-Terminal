import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from config import get_ia_model, get_cnn_fear_greed
import requests
from bs4 import BeautifulSoup
import time
import random
from functools import wraps

# ────────────────────────────────────────────────
# CONFIGURACIÓN ANTI-RATE-LIMITING
# ────────────────────────────────────────────────

# Session compartida para reusar conexiones
_SESSION = None

def get_session():
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        _SESSION.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    return _SESSION

def rate_limit_delay():
    """Delay aleatorio entre requests."""
    time.sleep(random.uniform(0.5, 1.5))

def retry_with_backoff(max_retries=3, initial_delay=2):
    """Decorador para retry con backoff exponencial."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "Too Many Requests" in str(e) or "rate" in str(e).lower():
                        if attempt < max_retries - 1:
                            st.warning(f"⏳ Rate limit detectado. Esperando {delay}s... (intento {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            delay *= 2  # Backoff exponencial
                        else:
                            raise e
                    else:
                        raise e
            return None
        return wrapper
    return decorator

# ────────────────────────────────────────────────
# FUNCIONES DE DATOS CON CACHE Y RETRY
# ────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)  # Cache 5 minutos
@retry_with_backoff(max_retries=3, initial_delay=2)
def get_stock_info_cached(ticker_symbol):
    """Obtiene info con cache y retry."""
    rate_limit_delay()
    
    # Crear ticker con session
    stock = yf.Ticker(ticker_symbol, session=get_session())
    
    # Obtener info
    info = stock.info
    
    # Pequeño delay adicional
    rate_limit_delay()
    
    return stock, info

@st.cache_data(ttl=300, show_spinner=False)
@retry_with_backoff(max_retries=3, initial_delay=2)
def get_stock_history_cached(stock, period="1y"):
    """Obtiene histórico con cache."""
    rate_limit_delay()
    hist = stock.history(period=period, auto_adjust=True)
    rate_limit_delay()
    return hist

@st.cache_data(ttl=600, show_spinner=False)
@retry_with_backoff(max_retries=2, initial_delay=1)
def get_calendar_cached(stock):
    """Obtiene calendario earnings."""
    try:
        return stock.calendar
    except:
        return None

@st.cache_data(ttl=600, show_spinner=False)
@retry_with_backoff(max_retries=2, initial_delay=1)
def get_recommendations_cached(stock):
    """Obtiene recomendaciones."""
    try:
        return stock.recommendations
    except:
        return None

def get_comprehensive_earnings_data_robust(ticker_symbol):
    """Versión robusta con manejo de errores y fallback."""
    
    try:
        # Intentar obtener datos reales
        with st.spinner(f"🔄 Conectando con Yahoo Finance..."):
            stock, info = get_stock_info_cached(ticker_symbol)
            
        if not info or len(info) < 5:
            raise ValueError("Datos insuficientes")
            
        # Obtener histórico
        hist = get_stock_history_cached(stock)
        
        # Datos procesados
        data = {
            "ticker": ticker_symbol,
            "name": info.get('longName') or info.get('shortName', ticker_symbol),
            "short_name": info.get('shortName', ticker_symbol),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "country": info.get('country', 'N/A'),
            "employees": info.get('fullTimeEmployees', 0),
            "website": info.get('website', '#'),
            "summary": info.get('longBusinessSummary', ''),
            
            # Precios
            "price": info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0),
            "prev_close": info.get('regularMarketPreviousClose', 0),
            "open": info.get('regularMarketOpen', 0),
            "day_high": info.get('regularMarketDayHigh', 0),
            "day_low": info.get('regularMarketDayLow', 0),
            "fifty_two_high": info.get('fiftyTwoWeekHigh', 0),
            "fifty_two_low": info.get('fiftyTwoWeekLow', 0),
            "volume": info.get('volume', 0),
            "avg_volume": info.get('averageVolume', 0),
            
            # Métricas
            "market_cap": info.get('marketCap', 0),
            "enterprise_value": info.get('enterpriseValue', 0),
            "rev_growth": info.get('revenueGrowth'),
            "ebitda_margin": info.get('ebitdaMargins'),
            "profit_margin": info.get('profitMargins'),
            "operating_margin": info.get('operatingMargins'),
            "gross_margin": info.get('grossMargins'),
            "pe_trailing": info.get('trailingPE'),
            "pe_forward": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_sales": info.get('priceToSalesTrailing12Months'),
            "price_to_book": info.get('priceToBook'),
            "eps": info.get('trailingEps'),
            "eps_forward": info.get('forwardEps'),
            "eps_growth": info.get('earningsGrowth'),
            
            # Retornos
            "roe": info.get('returnOnEquity'),
            "roa": info.get('returnOnAssets'),
            
            # Balance
            "cash": info.get('totalCash', 0),
            "free_cashflow": info.get('freeCashflow', 0),
            "operating_cashflow": info.get('operatingCashflow', 0),
            "debt": info.get('totalDebt', 0),
            "debt_to_equity": info.get('debtToEquity'),
            "current_ratio": info.get('currentRatio'),
            
            # Dividendos
            "dividend_rate": info.get('dividendRate', 0),
            "dividend_yield": info.get('dividendYield', 0) if info.get('dividendYield') else 0,
            "ex_div_date": info.get('exDividendDate'),
            "payout_ratio": info.get('payoutRatio', 0),
            
            # Targets
            "target_high": info.get('targetHighPrice', 0),
            "target_low": info.get('targetLowPrice', 0),
            "target_mean": info.get('targetMeanPrice', 0),
            "target_median": info.get('targetMedianPrice', 0),
            "recommendation": info.get('recommendationKey', 'none'),
            "num_analysts": info.get('numberOfAnalystOpinions', 0),
            
            "hist": hist,
            "beta": info.get('beta', 0),
            "is_real_data": True
        }
        
        # Calcular métricas derivadas
        if data['price'] and data['prev_close']:
            data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
            data['change_abs'] = data['price'] - data['prev_close']
        else:
            data['change_pct'] = 0
            data['change_abs'] = 0
            
        if data['fifty_two_high'] and data['price']:
            data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
        else:
            data['pct_from_high'] = 0
            
        return data, stock
        
    except Exception as e:
        st.error(f"⚠️ Error de conexión: {str(e)[:100]}")
        st.info("🔄 Intentando cargar datos de respaldo...")
        
        # Fallback a datos mock realistas
        return get_mock_data(ticker_symbol), None

def get_mock_data(ticker):
    """Datos de respaldo realistas para demostración."""
    
    # Datos aproximados de grandes empresas (pueden no ser 100% actuales pero son representativos)
    mock_db = {
        "AAPL": {
            "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics",
            "price": 185.50, "market_cap": 2.8e12, "rev_growth": 0.02, "pe_forward": 28.5,
            "eps": 6.15, "dividend_yield": 0.005, "roe": 1.60
        },
        "MSFT": {
            "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software",
            "price": 420.30, "market_cap": 3.1e12, "rev_growth": 0.15, "pe_forward": 32.0,
            "eps": 11.80, "dividend_yield": 0.007, "roe": 0.45
        },
        "GOOGL": {
            "name": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet Content",
            "price": 175.20, "market_cap": 2.1e12, "rev_growth": 0.13, "pe_forward": 22.5,
            "eps": 6.50, "dividend_yield": 0.0, "roe": 0.30
        },
        "AMZN": {
            "name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "Internet Retail",
            "price": 185.00, "market_cap": 1.9e12, "rev_growth": 0.12, "pe_forward": 42.0,
            "eps": 4.20, "dividend_yield": 0.0, "roe": 0.18
        },
        "NVDA": {
            "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors",
            "price": 875.50, "market_cap": 2.15e12, "rev_growth": 2.10, "pe_forward": 35.0,
            "eps": 12.90, "dividend_yield": 0.0003, "roe": 0.70
        },
        "META": {
            "name": "Meta Platforms Inc.", "sector": "Communication Services", "industry": "Internet Content",
            "price": 505.20, "market_cap": 1.3e12, "rev_growth": 0.25, "pe_forward": 24.0,
            "eps": 18.50, "dividend_yield": 0.0, "roe": 0.35
        },
        "TSLA": {
            "name": "Tesla Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers",
            "price": 195.30, "market_cap": 620e9, "rev_growth": 0.08, "pe_forward": 65.0,
            "eps": 3.50, "dividend_yield": 0.0, "roe": 0.22
        },
        "NFLX": {
            "name": "Netflix Inc.", "sector": "Communication Services", "industry": "Entertainment",
            "price": 625.80, "market_cap": 270e9, "rev_growth": 0.15, "pe_forward": 28.0,
            "eps": 18.20, "dividend_yield": 0.0, "roe": 0.28
        }
    }
    
    # Si no está en la base, generar datos sintéticos realistas
    if ticker not in mock_db:
        import hashlib
        seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
        base_price = 50 + (seed % 950)
        
        mock_db[ticker] = {
            "name": f"{ticker} Corp.",
            "sector": "Technology",
            "industry": "Software",
            "price": base_price,
            "market_cap": base_price * 1e9 * random.uniform(0.5, 5),
            "rev_growth": random.uniform(-0.1, 0.5),
            "pe_forward": random.uniform(15, 50),
            "eps": base_price / random.uniform(15, 40),
            "dividend_yield": random.choice([0, 0, 0, 0.02, 0.04]),
            "roe": random.uniform(0.05, 0.40)
        }
    
    mock = mock_db[ticker]
    
    data = {
        "ticker": ticker,
        "name": mock["name"],
        "short_name": ticker,
        "sector": mock["sector"],
        "industry": mock["industry"],
        "country": "United States",
        "employees": random.randint(10000, 200000),
        "website": "#",
        "summary": f"{mock['name']} es una empresa líder en {mock['industry']} con presencia global. "
                  f"Datos mostrados son aproximados para demostración debido a limitaciones de API.",
        
        "price": mock["price"],
        "prev_close": mock["price"] * random.uniform(0.98, 1.02),
        "open": mock["price"] * random.uniform(0.99, 1.01),
        "day_high": mock["price"] * 1.02,
        "day_low": mock["price"] * 0.98,
        "fifty_two_high": mock["price"] * 1.3,
        "fifty_two_low": mock["price"] * 0.7,
        "volume": random.randint(10e6, 100e6),
        "avg_volume": random.randint(15e6, 80e6),
        
        "market_cap": mock["market_cap"],
        "enterprise_value": mock["market_cap"] * 1.1,
        "rev_growth": mock["rev_growth"],
        "ebitda_margin": random.uniform(0.20, 0.45),
        "profit_margin": random.uniform(0.10, 0.35),
        "operating_margin": random.uniform(0.15, 0.40),
        "gross_margin": random.uniform(0.40, 0.80),
        "pe_trailing": mock["pe_forward"] * random.uniform(0.9, 1.1),
        "pe_forward": mock["pe_forward"],
        "peg_ratio": mock["pe_forward"] / (mock["rev_growth"] * 100) if mock["rev_growth"] > 0 else 2.0,
        "price_to_sales": random.uniform(3, 15),
        "price_to_book": random.uniform(2, 10),
        "eps": mock["eps"],
        "eps_forward": mock["eps"] * 1.15,
        "eps_growth": mock["rev_growth"] * 1.2,
        
        "roe": mock["roe"],
        "roa": mock["roe"] * 0.6,
        
        "cash": mock["market_cap"] * 0.05,
        "free_cashflow": mock["market_cap"] * 0.03,
        "operating_cashflow": mock["market_cap"] * 0.04,
        "debt": mock["market_cap"] * 0.15,
        "debt_to_equity": random.uniform(20, 80),
        "current_ratio": random.uniform(1.0, 3.0),
        
        "dividend_rate": mock["price"] * mock["dividend_yield"],
        "dividend_yield": mock["dividend_yield"],
        "ex_div_date": None,
        "payout_ratio": random.uniform(0.1, 0.6) if mock["dividend_yield"] > 0 else 0,
        
        "target_high": mock["price"] * 1.3,
        "target_low": mock["price"] * 0.8,
        "target_mean": mock["price"] * 1.1,
        "target_median": mock["price"] * 1.1,
        "recommendation": random.choice(['buy', 'strong_buy', 'hold']),
        "num_analysts": random.randint(20, 50),
        
        "hist": pd.DataFrame(),  # Vacío para gráfico
        "beta": random.uniform(0.8, 2.0),
        "is_real_data": False,
        "change_pct": random.uniform(-3, 3),
        "change_abs": 0,
        "pct_from_high": random.uniform(-20, -5)
    }
    
    data["change_abs"] = data["price"] * (data["change_pct"] / 100)
    
    return data

# ────────────────────────────────────────────────
# RESTO DE FUNCIONES (igual que antes, omitidas por brevedad)
# ────────────────────────────────────────────────

def format_value(value, prefix="", suffix="", decimals=2):
    if value is None or value == 0:
        return "N/A"
    if isinstance(value, (int, float)):
        if abs(value) >= 1e12:
            return f"{prefix}{value/1e12:.{decimals}f}T{suffix}"
        elif abs(value) >= 1e9:
            return f"{prefix}{value/1e9:.{decimals}f}B{suffix}"
        elif abs(value) >= 1e6:
            return f"{prefix}{value/1e6:.{decimals}f}M{suffix}"
        elif abs(value) >= 1e3:
            return f"{prefix}{value/1e3:.{decimals}f}K{suffix}"
        else:
            return f"{prefix}{value:.{decimals}f}{suffix}"
    return str(value)

def format_percentage(value, decimals=2):
    if value is None:
        return "N/A", "#888"
    if isinstance(value, float):
        color = "#00ffad" if value >= 0 else "#f23645"
        return f"{value:.{decimals}f}%", color
    return str(value), "#888"

def get_recommendation_color(rec):
    colors = {
        'strong_buy': '#00ffad', 'buy': '#4caf50', 'hold': '#ff9800',
        'sell': '#f23645', 'strong_sell': '#d32f2f', 'none': '#888'
    }
    return colors.get(rec, '#888')

def get_recommendation_text(rec):
    translations = {
        'strong_buy': 'COMPRA FUERTE', 'buy': 'COMPRA', 'hold': 'MANTENER',
        'sell': 'VENDER', 'strong_sell': 'VENTA FUERTE', 'none': 'SIN DATOS'
    }
    return translations.get(rec, rec.upper())

# [Aquí irían las funciones de renderizado... manteniendo las mismas que en la versión anterior]
# render_header, render_price_stats, render_fundamental_metrics, render_chart, etc.

def render_header(data):
    change_color = "#00ffad" if data['change_pct'] >= 0 else "#f23645"
    arrow = "▲" if data['change_pct'] >= 0 else "▼"
    data_source = "🔴 DEMO" if not data.get('is_real_data', True) else "🟢 REAL"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 5px;">
            <span style="background: #2a3f5f; color: #00ffad; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                {data['sector']} • {data_source}
            </span>
        </div>
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">
            {data['name']} <span style="color: #00ffad; font-size: 1.3rem;">({data['ticker']})</span>
        </h1>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: right;">
            <div style="color: white; font-size: 2.8rem; font-weight: bold;">
                ${data['price']:,.2f}
            </div>
            <div style="color: {change_color}; font-size: 1.2rem; font-weight: bold;">
                {arrow} {data['change_pct']:+.2f}%
            </div>
            <div style="color: #666; font-size: 11px;">
                Cap: {format_value(data['market_cap'], '$')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if not data.get('is_real_data', True):
        st.warning("⚠️ **Modo Demostración**: Mostrando datos aproximados. Los precios pueden no ser 100% actuales debido a limitaciones de la API gratuita.")

def render_fundamental_metrics(data):
    st.markdown("### 📊 Métricas Fundamentales")
    
    cols = st.columns(4)
    metrics = [
        ("Crec. Ingresos", data['rev_growth'], "%", True),
        ("Margen EBITDA", data['ebitda_margin'], "%", True),
        ("ROE", data['roe'], "%", True),
        ("P/E Forward", format_value(data['pe_forward'], '', 'x', 1), "#00ffad"),
    ]
    
    for col, (label, value, suffix, is_good) in zip(cols, metrics):
        with col:
            if isinstance(value, str):
                formatted, color = value, suffix
            else:
                formatted, color = format_percentage(value) if suffix == "%" else (format_value(value, '', suffix), "#00ffad")
            
            st.markdown(f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 15px; text-align: center;">
                <div style="color: #666; font-size: 10px; text-transform: uppercase;">{label}</div>
                <div style="color: {color if isinstance(color, str) else '#00ffad'}; font-size: 1.4rem; font-weight: bold;">{formatted}</div>
            </div>
            """, unsafe_allow_html=True)

def render_chart_simple(data):
    """Gráfico simplificado o mensaje si no hay datos históricos."""
    if data['hist'].empty:
        st.info("📊 Gráfico histórico no disponible en modo demostración")
        return
    
    hist = data['hist']
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index, open=hist['Open'], high=hist['High'],
        low=hist['Low'], close=hist['Close'],
        increasing_line_color='#00ffad', decreasing_line_color='#f23645'
    )])
    
    fig.update_layout(
        template="plotly_dark", plot_bgcolor='#0c0e12', paper_bgcolor='#11141a',
        font=dict(color='white'), xaxis_rangeslider_visible=False,
        height=350, margin=dict(l=30, r=30, t=30, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_outlook_real(data):
    st.markdown("### 🔮 Perspectivas y Desafíos")
    
    positive_points = []
    challenge_points = []
    
    if data['rev_growth'] and data['rev_growth'] > 0.1:
        positive_points.append(f"Crecimiento robusto ({data['rev_growth']:.1%})")
    elif data['rev_growth'] and data['rev_growth'] < 0:
        challenge_points.append("Contracción de ingresos")
    
    if data['free_cashflow'] and data['free_cashflow'] > 0:
        positive_points.append("Generación positiva de caja")
    
    if data['roe'] and data['roe'] > 0.15:
        positive_points.append(f"ROE elevado ({data['roe']:.1%})")
    
    if data['debt_to_equity'] and data['debt_to_equity'] < 50:
        positive_points.append("Balance poco apalancado")
    elif data['debt_to_equity'] and data['debt_to_equity'] > 100:
        challenge_points.append("Alto apalancamiento")
    
    while len(positive_points) < 3:
        positive_points.append("Posición establecida en el sector")
    while len(challenge_points) < 3:
        challenge_points.append("Competencia del sector")
    
    col1, col2 = st.columns(2)
    
    with col1:
        points = "".join([f"<li style='margin-bottom: 8px;'>{p}</li>" for p in positive_points[:4]])
        st.markdown(f"""
        <div style="background: rgba(0,255,173,0.1); border: 1px solid #00ffad44; border-radius: 12px; padding: 20px;">
            <h4 style="color: #00ffad; margin-bottom: 15px;">📈 Perspectivas Positivas</h4>
            <ul style="color: #ccc; padding-left: 20px;">{points}</ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        points = "".join([f"<li style='margin-bottom: 8px;'>{c}</li>" for c in challenge_points[:4]])
        st.markdown(f"""
        <div style="background: rgba(242,54,69,0.1); border: 1px solid #f2364544; border-radius: 12px; padding: 20px;">
            <h4 style="color: #f23645; margin-bottom: 15px;">⚠️ Desafíos Pendientes</h4>
            <ul style="color: #ccc; padding-left: 20px;">{points}</ul>
        </div>
        """, unsafe_allow_html=True)

def render_ai_analysis(data):
    st.markdown("### 🤖 Análisis Inteligente")
    
    model, name, err = get_ia_model()
    if not model:
        st.info("IA no configurada. Análisis manual disponible.")
        return
    
    prompt = f"""
    Análisis de {data['name']} ({data['ticker']}):
    Precio: ${data['price']:.2f}, Market Cap: {format_value(data['market_cap'], '$')},
    Crecimiento: {format_value(data['rev_growth'], '', '%', 1)}, 
    ROE: {format_value(data['roe'], '', '%', 1)}, P/E: {format_value(data['pe_forward'], '', 'x', 1)}
    
    Proporciona:
    1. Resumen ejecutivo (2-3 líneas)
    2. 3 Fortalezas clave
    3. 3 Riesgos principales
    4. Veredicto: Compra/Mantener/Vender
    
    Responde en español, formato markdown.
    """
    
    try:
        with st.spinner("Analizando..."):
            response = model.generate_content(prompt)
            st.markdown(f"""
            <div style="background: #1a1e26; border: 1px solid #2a3f5f; border-radius: 10px; padding: 20px;">
                {response.text}
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error IA: {e}")

# ────────────────────────────────────────────────
# RENDER PRINCIPAL
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; }
        .stTextInput > div > div > input {
            background-color: #1a1e26; color: white; border: 1px solid #2a3f5f;
            border-radius: 8px; padding: 12px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%);
            color: #0c0e12; border: none; border-radius: 8px;
            padding: 12px 30px; font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Análisis de Earnings")
    st.markdown('<div style="color: #888; margin-bottom: 20px;">Datos fundamentales con respaldo automático</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input("Ticker", value="NVDA").upper().strip()
    with col2:
        st.write("")
        st.write("")
        if st.button("🔍 Analizar", use_container_width=True):
            pass  # Trigger rerun

    if ticker:
        # Limpiar cache si es necesario (botón opcional)
        if st.sidebar.button("🧹 Limpiar Caché"):
            st.cache_data.clear()
            st.success("Caché limpiado")
        
        data, stock = get_comprehensive_earnings_data_robust(ticker)
        
        if data:
            render_header(data)
            render_fundamental_metrics(data)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                render_chart_simple(data)
            with col2:
                st.markdown("#### 📋 Sobre la empresa")
                st.markdown(f"<div style='color: #aaa; font-size: 13px;'>{data['summary'][:300]}...</div>", unsafe_allow_html=True)
                
                st.markdown("#### 💰 Finanzas")
                st.markdown(f"""
                - **Efectivo:** {format_value(data['cash'], '$')}
                - **Deuda:** {format_value(data['debt'], '$')}
                - **FCF:** {format_value(data['free_cashflow'], '$')}
                - **Ratio Deuda/Pat:** {format_value(data['debt_to_equity'], '', '%', 1)}
                """)
            
            st.markdown("---")
            render_outlook_real(data)
            st.markdown("---")
            render_ai_analysis(data)
            
            st.markdown("""
            <div style="text-align: center; color: #444; font-size: 11px; margin-top: 30px;">
                Datos: Yahoo Finance | Análisis: Capyfin IA
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
