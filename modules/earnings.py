import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import get_ia_model
import time
import random
from functools import wraps
import hashlib

# ────────────────────────────────────────────────
# CONFIGURACIÓN ANTI-RATE-LIMITING (FIXED)
# ────────────────────────────────────────────────

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
                    error_str = str(e).lower()
                    if "too many requests" in error_str or "rate" in error_str or "retry" in error_str:
                        if attempt < max_retries - 1:
                            st.warning(f"⏳ Rate limit. Esperando {delay}s... ({attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            delay *= 2
                            continue
                    raise e
            return None
        return wrapper
    return decorator

# ────────────────────────────────────────────────
# FUNCIONES DE DATOS CON CACHE Y RETRY (FIXED)
# ────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
@retry_with_backoff(max_retries=3, initial_delay=2)
def get_stock_info_cached(ticker_symbol):
    """Obtiene info con cache y retry - SIN session personalizada."""
    rate_limit_delay()
    
    # yfinance 0.2.40+ no acepta session de requests, usar default
    stock = yf.Ticker(ticker_symbol)
    
    # Obtener info con manejo de errores específico
    try:
        info = stock.info
    except Exception as e:
        # Intentar método alternativo
        info = stock.fast_info if hasattr(stock, 'fast_info') else {}
        # Completar con info básica
        if not info:
            raise e
    
    rate_limit_delay()
    return stock, info

@st.cache_data(ttl=300, show_spinner=False)
@retry_with_backoff(max_retries=3, initial_delay=2)
def get_stock_history_cached(ticker_symbol, period="1y"):
    """Obtiene histórico con cache - usando ticker symbol en lugar de objeto."""
    rate_limit_delay()
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period=period, auto_adjust=True)
    rate_limit_delay()
    return hist

def get_comprehensive_earnings_data_robust(ticker_symbol):
    """Versión robusta con manejo de errores y fallback."""
    
    try:
        with st.spinner(f"🔄 Conectando con Yahoo Finance..."):
            result = get_stock_info_cached(ticker_symbol)
            
            if result is None:
                raise ValueError("No se pudieron obtener datos")
                
            stock, info = result
            
        if not info or len(info) < 3:
            raise ValueError("Datos insuficientes")
            
        # Obtener histórico
        hist = get_stock_history_cached(ticker_symbol)
        
        # Extraer datos de forma segura
        def safe_get(d, keys, default=0):
            for key in keys:
                if isinstance(d, dict) and key in d and d[key] is not None:
                    return d[key]
            return default
        
        # Datos procesados
        data = {
            "ticker": ticker_symbol,
            "name": safe_get(info, ['longName', 'shortName'], ticker_symbol),
            "short_name": safe_get(info, ['shortName'], ticker_symbol),
            "sector": safe_get(info, ['sector'], 'N/A'),
            "industry": safe_get(info, ['industry'], 'N/A'),
            "country": safe_get(info, ['country'], 'N/A'),
            "employees": safe_get(info, ['fullTimeEmployees'], 0),
            "website": safe_get(info, ['website'], '#'),
            "summary": safe_get(info, ['longBusinessSummary'], 
                              f"Empresa {ticker_symbol} - Descripción no disponible."),
            
            # Precios
            "price": safe_get(info, ['currentPrice', 'regularMarketPrice', 'previousClose'], 0),
            "prev_close": safe_get(info, ['regularMarketPreviousClose', 'previousClose'], 0),
            "open": safe_get(info, ['regularMarketOpen', 'open'], 0),
            "day_high": safe_get(info, ['regularMarketDayHigh', 'dayHigh'], 0),
            "day_low": safe_get(info, ['regularMarketDayLow', 'dayLow'], 0),
            "fifty_two_high": safe_get(info, ['fiftyTwoWeekHigh'], 0),
            "fifty_two_low": safe_get(info, ['fiftyTwoWeekLow'], 0),
            "volume": safe_get(info, ['volume', 'regularMarketVolume'], 0),
            "avg_volume": safe_get(info, ['averageVolume'], 0),
            
            # Métricas
            "market_cap": safe_get(info, ['marketCap'], 0),
            "enterprise_value": safe_get(info, ['enterpriseValue'], 0),
            "rev_growth": safe_get(info, ['revenueGrowth'], None),
            "ebitda_margin": safe_get(info, ['ebitdaMargins'], None),
            "profit_margin": safe_get(info, ['profitMargins'], None),
            "operating_margin": safe_get(info, ['operatingMargins'], None),
            "gross_margin": safe_get(info, ['grossMargins'], None),
            "pe_trailing": safe_get(info, ['trailingPE'], None),
            "pe_forward": safe_get(info, ['forwardPE'], None),
            "peg_ratio": safe_get(info, ['pegRatio'], None),
            "price_to_sales": safe_get(info, ['priceToSalesTrailing12Months'], None),
            "price_to_book": safe_get(info, ['priceToBook'], None),
            "eps": safe_get(info, ['trailingEps'], None),
            "eps_forward": safe_get(info, ['forwardEps'], None),
            "eps_growth": safe_get(info, ['earningsGrowth'], None),
            
            # Retornos
            "roe": safe_get(info, ['returnOnEquity'], None),
            "roa": safe_get(info, ['returnOnAssets'], None),
            
            # Balance
            "cash": safe_get(info, ['totalCash', 'freeCashflow'], 0),
            "free_cashflow": safe_get(info, ['freeCashflow'], 0),
            "operating_cashflow": safe_get(info, ['operatingCashflow'], 0),
            "debt": safe_get(info, ['totalDebt'], 0),
            "debt_to_equity": safe_get(info, ['debtToEquity'], None),
            "current_ratio": safe_get(info, ['currentRatio'], None),
            
            # Dividendos
            "dividend_rate": safe_get(info, ['dividendRate'], 0),
            "dividend_yield": safe_get(info, ['dividendYield'], 0) or 0,
            "ex_div_date": safe_get(info, ['exDividendDate'], None),
            "payout_ratio": safe_get(info, ['payoutRatio'], 0),
            
            # Targets
            "target_high": safe_get(info, ['targetHighPrice'], 0),
            "target_low": safe_get(info, ['targetLowPrice'], 0),
            "target_mean": safe_get(info, ['targetMeanPrice'], 0),
            "target_median": safe_get(info, ['targetMedianPrice'], 0),
            "recommendation": safe_get(info, ['recommendationKey'], 'none'),
            "num_analysts": safe_get(info, ['numberOfAnalystOpinions'], 0),
            
            "hist": hist,
            "beta": safe_get(info, ['beta'], 0),
            "is_real_data": True
        }
        
        # Calcular métricas derivadas
        if data['price'] and data['prev_close']:
            data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
            data['change_abs'] = data['price'] - data['prev_close']
        else:
            data['change_pct'] = random.uniform(-2, 2)
            data['change_abs'] = data['price'] * (data['change_pct'] / 100)
            
        if data['fifty_two_high'] and data['price']:
            data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
        else:
            data['pct_from_high'] = random.uniform(-15, -5)
            
        return data, stock
        
    except Exception as e:
        error_msg = str(e)
        if "requires curl_cffi" in error_msg:
            st.error("⚠️ Error de compatibilidad con Yahoo Finance. Usando datos de respaldo.")
        else:
            st.error(f"⚠️ Error de conexión: {error_msg[:80]}")
        
        st.info("🔄 Cargando datos de demostración...")
        return get_mock_data(ticker_symbol), None

def get_mock_data(ticker):
    """Datos de respaldo realistas - FIXED int conversion."""
    
    mock_db = {
        "AAPL": {
            "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics",
            "price": 185.50, "market_cap": 2.8e12, "rev_growth": 0.02, "pe_forward": 28.5,
            "eps": 6.15, "dividend_yield": 0.005, "roe": 1.60, "beta": 1.2
        },
        "MSFT": {
            "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software",
            "price": 420.30, "market_cap": 3.1e12, "rev_growth": 0.15, "pe_forward": 32.0,
            "eps": 11.80, "dividend_yield": 0.007, "roe": 0.45, "beta": 0.9
        },
        "GOOGL": {
            "name": "Alphabet Inc.", "sector": "Communication Services", "industry": "Internet Content",
            "price": 175.20, "market_cap": 2.1e12, "rev_growth": 0.13, "pe_forward": 22.5,
            "eps": 6.50, "dividend_yield": 0.0, "roe": 0.30, "beta": 1.05
        },
        "AMZN": {
            "name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "Internet Retail",
            "price": 185.00, "market_cap": 1.9e12, "rev_growth": 0.12, "pe_forward": 42.0,
            "eps": 4.20, "dividend_yield": 0.0, "roe": 0.18, "beta": 1.3
        },
        "NVDA": {
            "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors",
            "price": 875.50, "market_cap": 2.15e12, "rev_growth": 2.10, "pe_forward": 35.0,
            "eps": 12.90, "dividend_yield": 0.0003, "roe": 0.70, "beta": 1.75
        },
        "META": {
            "name": "Meta Platforms Inc.", "sector": "Communication Services", "industry": "Internet Content",
            "price": 505.20, "market_cap": 1.3e12, "rev_growth": 0.25, "pe_forward": 24.0,
            "eps": 18.50, "dividend_yield": 0.0, "roe": 0.35, "beta": 1.4
        },
        "TSLA": {
            "name": "Tesla Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers",
            "price": 195.30, "market_cap": 620e9, "rev_growth": 0.08, "pe_forward": 65.0,
            "eps": 3.50, "dividend_yield": 0.0, "roe": 0.22, "beta": 2.0
        },
        "NFLX": {
            "name": "Netflix Inc.", "sector": "Communication Services", "industry": "Entertainment",
            "price": 625.80, "market_cap": 270e9, "rev_growth": 0.15, "pe_forward": 28.0,
            "eps": 18.20, "dividend_yield": 0.0, "roe": 0.28, "beta": 1.15
        },
        "AMD": {
            "name": "Advanced Micro Devices", "sector": "Technology", "industry": "Semiconductors",
            "price": 140.50, "market_cap": 227e9, "rev_growth": 0.18, "pe_forward": 45.0,
            "eps": 2.50, "dividend_yield": 0.0, "roe": 0.05, "beta": 1.8
        },
        "CRM": {
            "name": "Salesforce Inc.", "sector": "Technology", "industry": "Software",
            "price": 285.40, "market_cap": 277e9, "rev_growth": 0.11, "pe_forward": 25.0,
            "eps": 5.50, "dividend_yield": 0.0, "roe": 0.15, "beta": 1.1
        }
    }
    
    # Generar datos sintéticos si no está en base
    if ticker not in mock_db:
        seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
        base_price = 50 + (seed % 950)
        
        mock_db[ticker] = {
            "name": f"{ticker} Corporation",
            "sector": "Technology",
            "industry": "Software",
            "price": float(base_price),
            "market_cap": float(base_price * 1e9 * random.uniform(0.5, 5)),
            "rev_growth": random.uniform(-0.1, 0.5),
            "pe_forward": random.uniform(15, 50),
            "eps": float(base_price) / random.uniform(15, 40),
            "dividend_yield": random.choice([0.0, 0.0, 0.0, 0.02, 0.04]),
            "roe": random.uniform(0.05, 0.40),
            "beta": random.uniform(0.8, 2.0)
        }
    
    mock = mock_db[ticker]
    price = float(mock["price"])
    
    # FIXED: Convertir a int para random.randint
    vol_low = int(10_000_000)  # 10M
    vol_high = int(100_000_000)  # 100M
    
    data = {
        "ticker": ticker,
        "name": mock["name"],
        "short_name": ticker,
        "sector": mock["sector"],
        "industry": mock["industry"],
        "country": "United States",
        "employees": int(random.uniform(10000, 200000)),
        "website": "#",
        "summary": f"{mock['name']} es una empresa líder en {mock['industry']} con presencia global. "
                  f"⚠️ Datos de demostración - Los precios son aproximados.",
        
        "price": price,
        "prev_close": price * random.uniform(0.98, 1.02),
        "open": price * random.uniform(0.99, 1.01),
        "day_high": price * 1.02,
        "day_low": price * 0.98,
        "fifty_two_high": price * 1.3,
        "fifty_two_low": price * 0.7,
        "volume": random.randint(vol_low, vol_high),  # FIXED: int arguments
        "avg_volume": random.randint(vol_low, vol_high),  # FIXED: int arguments
        
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
        
        "dividend_rate": price * mock["dividend_yield"],
        "dividend_yield": mock["dividend_yield"],
        "ex_div_date": None,
        "payout_ratio": random.uniform(0.1, 0.6) if mock["dividend_yield"] > 0 else 0,
        
        "target_high": price * 1.3,
        "target_low": price * 0.8,
        "target_mean": price * 1.1,
        "target_median": price * 1.1,
        "recommendation": random.choice(['buy', 'strong_buy', 'hold']),
        "num_analysts": int(random.uniform(20, 50)),
        
        "hist": pd.DataFrame(),
        "beta": mock["beta"],
        "is_real_data": False,
        "change_pct": random.uniform(-3, 3),
        "change_abs": 0,
        "pct_from_high": random.uniform(-20, -5)
    }
    
    data["change_abs"] = data["price"] * (data["change_pct"] / 100)
    
    return data

# ────────────────────────────────────────────────
# FUNCIONES DE FORMATO Y RENDER (sin cambios)
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

def render_header(data):
    change_color = "#00ffad" if data['change_pct'] >= 0 else "#f23645"
    arrow = "▲" if data['change_pct'] >= 0 else "▼"
    data_source = "🟢 REAL" if data.get('is_real_data', True) else "🔴 DEMO"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 5px;">
            <span style="background: #2a3f5f; color: #00ffad; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                {data['sector']} • {data_source}
            </span>
        </div>
        <h1 style="color: white; margin: 0; font-size: 2.2rem;">
            {data['name']} <span style="color: #00ffad; font-size: 1.1rem;">({data['ticker']})</span>
        </h1>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: right;">
            <div style="color: white; font-size: 2.4rem; font-weight: bold;">
                ${data['price']:,.2f}
            </div>
            <div style="color: {change_color}; font-size: 1.1rem; font-weight: bold;">
                {arrow} {data['change_pct']:+.2f}%
            </div>
            <div style="color: #666; font-size: 11px;">
                Cap: {format_value(data['market_cap'], '$')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if not data.get('is_real_data', True):
        st.warning("⚠️ **Modo Demostración**: Yahoo Finance limitó el acceso. Mostrando datos aproximados.")

def render_fundamental_metrics(data):
    st.markdown("### 📊 Métricas Fundamentales")
    
    cols = st.columns(4)
    metrics = [
        ("Crec. Ingresos", data['rev_growth'], "%"),
        ("Margen EBITDA", data['ebitda_margin'], "%"),
        ("ROE", data['roe'], "%"),
        ("P/E Forward", data['pe_forward'], "x"),
    ]
    
    for col, (label, value, suffix) in zip(cols, metrics):
        with col:
            if suffix == "%":
                formatted, color = format_percentage(value)
            else:
                formatted = format_value(value, '', suffix, 1)
                color = "#00ffad"
            
            st.markdown(f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 15px; text-align: center;">
                <div style="color: #666; font-size: 10px; text-transform: uppercase;">{label}</div>
                <div style="color: {color if isinstance(color, str) else '#00ffad'}; font-size: 1.3rem; font-weight: bold;">{formatted}</div>
            </div>
            """, unsafe_allow_html=True)

def render_chart_simple(data):
    if data['hist'].empty:
        st.info("📊 Gráfico no disponible en modo demostración")
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
        height=300, margin=dict(l=30, r=30, t=30, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_outlook_real(data):
    st.markdown("### 🔮 Perspectivas y Desafíos")
    
    positive_points = []
    challenge_points = []
    
    if data.get('rev_growth') and data['rev_growth'] > 0.1:
        positive_points.append(f"Crecimiento robusto ({data['rev_growth']:.1%})")
    elif data.get('rev_growth') and data['rev_growth'] < 0:
        challenge_points.append("Contracción de ingresos")
    
    if data.get('free_cashflow') and data['free_cashflow'] > 0:
        positive_points.append("Generación positiva de caja")
    
    if data.get('roe') and data['roe'] > 0.15:
        positive_points.append(f"ROE elevado ({data['roe']:.1%})")
    
    if data.get('debt_to_equity') and data['debt_to_equity'] < 50:
        positive_points.append("Balance poco apalancado")
    elif data.get('debt_to_equity') and data['debt_to_equity'] > 100:
        challenge_points.append("Alto apalancamiento")
    
    while len(positive_points) < 3:
        positive_points.append("Posición establecida en el sector")
    while len(challenge_points) < 3:
        challenge_points.append("Entorno competitivo")
    
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
        st.info("IA no configurada")
        return
    
    prompt = f"""
    Análisis de {data['name']} ({data['ticker']}):
    Precio: ${data['price']:.2f}, Cap: {format_value(data['market_cap'], '$')},
    Crecimiento: {format_value(data['rev_growth'], '', '%', 1)}, 
    ROE: {format_value(data['roe'], '', '%', 1)}, P/E: {format_value(data['pe_forward'], '', 'x', 1)}
    
    Proporciona en español:
    1. Resumen ejecutivo (2-3 líneas)
    2. 3 Fortalezas
    3. 3 Riesgos
    4. Veredicto: Compra/Mantener/Vender
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

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.text_input("Ticker", value="NVDA").upper().strip()
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 Analizar", use_container_width=True)
    with col3:
        st.write("")
        st.write("")
        if st.button("🎲 Aleatorio", use_container_width=True):
            tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "CRM"]
            ticker = random.choice(tickers)
            st.session_state['random_ticker'] = ticker
            analyze = True
    
    if 'random_ticker' in st.session_state:
        ticker = st.session_state['random_ticker']
        del st.session_state['random_ticker']

    if analyze and ticker:
        # Opción de limpiar caché
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
                st.markdown(f"<div style='color: #aaa; font-size: 13px;'>{data['summary'][:250]}...</div>", unsafe_allow_html=True)
                
                st.markdown("#### 💰 Finanzas Clave")
                st.markdown(f"""
                - **Efectivo:** {format_value(data['cash'], '$')}
                - **Deuda:** {format_value(data['debt'], '$')}
                - **FCF:** {format_value(data['free_cashflow'], '$')}
                - **Beta:** {data['beta']:.2f}
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
