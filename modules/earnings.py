

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
import requests

# ────────────────────────────────────────────────
# CONFIGURACIÓN ANTI-RATE-LIMITING
# ────────────────────────────────────────────────

def rate_limit_delay():
    """Delay aleatorio entre requests."""
    time.sleep(random.uniform(0.3, 0.8))

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
                    if any(x in error_str for x in ["too many requests", "rate", "retry", "serialize"]):
                        if attempt < max_retries - 1:
                            st.warning(f"⏳ Reintentando... ({attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            delay *= 2
                            continue
                    raise e
            return None
        return wrapper
    return decorator

# ────────────────────────────────────────────────
# OBTENCIÓN DE DATOS SIN CACHE PROBLEMATICO
# ────────────────────────────────────────────────

def get_yfinance_data_simple(ticker_symbol):
    """
    Obtiene datos de yfinance sin usar cache en tuplas complejas.
    Retorna solo datos serializables (dict, no objetos yf).
    """
    try:
        rate_limit_delay()
        
        # Crear ticker
        ticker = yf.Ticker(ticker_symbol)
        
        # Obtener info
        try:
            info = ticker.info
        except:
            # Fallback a fast_info si info falla
            try:
                info = dict(ticker.fast_info)
            except:
                info = {}
        
        if not info:
            return None
            
        # Obtener histórico
        try:
            hist = ticker.history(period="6mo", auto_adjust=True)
            hist_dict = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            } if not hist.empty else None
        except:
            hist_dict = None
        
        # Retornar solo datos serializables (dict)
        return {
            'info': info,
            'history': hist_dict,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error yfinance: {e}")
        return None

def get_alternative_data_finnhub(ticker, api_key):
    """
    Obtiene datos alternativos desde Finnhub como respaldo.
    """
    if not api_key:
        return None
        
    try:
        base_url = "https://finnhub.io/api/v1"
        headers = {"X-Finnhub-Token": api_key}
        
        # Quote (precio actual)
        quote_resp = requests.get(
            f"{base_url}/quote", 
            params={"symbol": ticker}, 
            headers=headers,
            timeout=10
        )
        quote = quote_resp.json() if quote_resp.status_code == 200 else {}
        
        # Company profile
        profile_resp = requests.get(
            f"{base_url}/stock/profile2",
            params={"symbol": ticker},
            headers=headers,
            timeout=10
        )
        profile = profile_resp.json() if profile_resp.status_code == 200 else {}
        
        # Basic financials
        metrics_resp = requests.get(
            f"{base_url}/stock/metric",
            params={"symbol": ticker, "metric": "all"},
            headers=headers,
            timeout=10
        )
        metrics = metrics_resp.json().get('metric', {}) if metrics_resp.status_code == 200 else {}
        
        if not quote or not profile:
            return None
            
        # Mapear a formato compatible
        return {
            'info': {
                'longName': profile.get('name', ticker),
                'sector': profile.get('finnhubIndustry', 'N/A'),
                'industry': profile.get('industry', 'N/A'),
                'country': profile.get('country', 'N/A'),
                'website': profile.get('weburl', '#'),
                'longBusinessSummary': profile.get('description', ''),
                'currentPrice': quote.get('c', 0),
                'previousClose': quote.get('pc', 0),
                'open': quote.get('o', 0),
                'dayHigh': quote.get('h', 0),
                'dayLow': quote.get('l', 0),
                'marketCap': profile.get('marketCapitalization', 0) * 1e6 if profile.get('marketCapitalization') else 0,
                'volume': quote.get('v', 0),
                'beta': metrics.get('beta', 0),
                'peTrailing': metrics.get('peTTM', None),
                'peForward': metrics.get('peNormalizedAnnual', None),
                'dividendYield': metrics.get('dividendYieldIndicatedAnnual', 0),
                'roe': metrics.get('roeTTM', None),
                'revenueGrowth': metrics.get('revenueGrowth5Y', None),
                'debtToEquity': metrics.get('totalDebtToTotalEquityAnnual', None),
            },
            'history': None,  # Finnhub requiere llamada separada para candles
            'source': 'finnhub'
        }
        
    except Exception as e:
        print(f"Error Finnhub: {e}")
        return None

def get_comprehensive_earnings_data_robust(ticker_symbol):
    """Obtiene datos usando múltiples fuentes con fallback."""
    
    # Intentar yfinance primero
    yf_data = get_yfinance_data_simple(ticker_symbol)
    
    if yf_data and yf_data.get('info'):
        source = "Yahoo Finance"
        info = yf_data['info']
        hist_data = yf_data['history']
        is_real = True
    else:
        # Fallback a Finnhub
        api_key = st.secrets.get("FINNHUB_API_KEY", None)
        if api_key:
            fh_data = get_alternative_data_finnhub(ticker_symbol, api_key)
            if fh_data:
                source = "Finnhub"
                info = fh_data['info']
                hist_data = None
                is_real = True
            else:
                return get_mock_data(ticker_symbol), "mock"
        else:
            st.warning("⚠️ Yahoo Finance limitado y Finnhub no configurado.")
            return get_mock_data(ticker_symbol), "mock"
    
    # Procesar datos
    def safe_get(d, keys, default=0):
        for key in keys:
            if isinstance(d, dict) and key in d and d[key] is not None:
                return d[key]
        return default
    
    # Reconstruir DataFrame de histórico si existe
    hist_df = pd.DataFrame()
    if hist_data:
        try:
            hist_df = pd.DataFrame({
                'Open': hist_data['open'],
                'High': hist_data['high'],
                'Low': hist_data['low'],
                'Close': hist_data['close'],
                'Volume': hist_data['volume']
            }, index=pd.to_datetime(hist_data['dates']))
        except:
            pass
    
    price = safe_get(info, ['currentPrice', 'regularMarketPrice', 'previousClose'], 0)
    prev_close = safe_get(info, ['previousClose', 'regularMarketPreviousClose'], price)
    
    data = {
        "ticker": ticker_symbol,
        "name": safe_get(info, ['longName', 'shortName', 'name'], ticker_symbol),
        "sector": safe_get(info, ['sector', 'finnhubIndustry'], 'N/A'),
        "industry": safe_get(info, ['industry'], 'N/A'),
        "country": safe_get(info, ['country'], 'N/A'),
        "employees": safe_get(info, ['fullTimeEmployees'], 0),
        "website": safe_get(info, ['website', 'weburl'], '#'),
        "summary": safe_get(info, ['longBusinessSummary', 'description'], 
                          f"Empresa {ticker_symbol}"),
        
        "price": price,
        "prev_close": prev_close,
        "open": safe_get(info, ['open', 'regularMarketOpen'], price),
        "day_high": safe_get(info, ['dayHigh', 'regularMarketDayHigh', 'h'], price * 1.01),
        "day_low": safe_get(info, ['dayLow', 'regularMarketDayLow', 'l'], price * 0.99),
        "fifty_two_high": safe_get(info, ['fiftyTwoWeekHigh', '52WeekHigh'], price * 1.2),
        "fifty_two_low": safe_get(info, ['fiftyTwoWeekLow', '52WeekLow'], price * 0.8),
        "volume": safe_get(info, ['volume', 'regularMarketVolume', 'v'], 0),
        "avg_volume": safe_get(info, ['averageVolume', 'avgVolume'], 0),
        
        "market_cap": safe_get(info, ['marketCap', 'marketCapitalization'], 0),
        "enterprise_value": safe_get(info, ['enterpriseValue'], 0),
        "rev_growth": safe_get(info, ['revenueGrowth', 'revenueGrowth5Y'], None),
        "ebitda_margin": safe_get(info, ['ebitdaMargins'], None),
        "profit_margin": safe_get(info, ['profitMargins', 'netProfitMargin'], None),
        "operating_margin": safe_get(info, ['operatingMargins'], None),
        "gross_margin": safe_get(info, ['grossMargins'], None),
        "pe_trailing": safe_get(info, ['trailingPE', 'peTrailing', 'peTTM'], None),
        "pe_forward": safe_get(info, ['forwardPE', 'peForward', 'peNormalizedAnnual'], None),
        "peg_ratio": safe_get(info, ['pegRatio'], None),
        "price_to_sales": safe_get(info, ['priceToSalesTrailing12Months'], None),
        "price_to_book": safe_get(info, ['priceToBook'], None),
        "eps": safe_get(info, ['trailingEps'], None),
        "eps_forward": safe_get(info, ['forwardEps'], None),
        "eps_growth": safe_get(info, ['earningsGrowth'], None),
        
        "roe": safe_get(info, ['returnOnEquity', 'roeTTM'], None),
        "roa": safe_get(info, ['returnOnAssets'], None),
        
        "cash": safe_get(info, ['totalCash', 'freeCashflow'], 0),
        "free_cashflow": safe_get(info, ['freeCashflow'], 0),
        "operating_cashflow": safe_get(info, ['operatingCashflow'], 0),
        "debt": safe_get(info, ['totalDebt'], 0),
        "debt_to_equity": safe_get(info, ['debtToEquity', 'totalDebtToTotalEquityAnnual'], None),
        "current_ratio": safe_get(info, ['currentRatio'], None),
        
        "dividend_rate": safe_get(info, ['dividendRate'], 0),
        "dividend_yield": (safe_get(info, ['dividendYield'], 0) or 0) / 100 if safe_get(info, ['dividendYield'], 0) and safe_get(info, ['dividendYield'], 0) > 1 else safe_get(info, ['dividendYield'], 0) or 0,
        "ex_div_date": safe_get(info, ['exDividendDate'], None),
        "payout_ratio": safe_get(info, ['payoutRatio'], 0),
        
        "target_high": safe_get(info, ['targetHighPrice'], price * 1.2),
        "target_low": safe_get(info, ['targetLowPrice'], price * 0.8),
        "target_mean": safe_get(info, ['targetMeanPrice'], price),
        "target_median": safe_get(info, ['targetMedianPrice'], price),
        "recommendation": safe_get(info, ['recommendationKey'], 'none'),
        "num_analysts": safe_get(info, ['numberOfAnalystOpinions'], 0),
        
        "hist": hist_df,
        "beta": safe_get(info, ['beta'], 0),
        "is_real_data": is_real,
        "data_source": source
    }
    
    # Calcular cambios
    if data['price'] and data['prev_close'] and data['prev_close'] != 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
        data['change_abs'] = data['price'] - data['prev_close']
    else:
        data['change_pct'] = 0
        data['change_abs'] = 0
        
    if data['fifty_two_high'] and data['price'] and data['fifty_two_high'] != 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    else:
        data['pct_from_high'] = 0
    
    return data, source

def get_mock_data(ticker):
    """Datos de demostración realistas."""
    
    mock_db = {
        "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 185.50, "market_cap": 2.8e12, "rev_growth": 0.02, "pe_forward": 28.5, "eps": 6.15, "dividend_yield": 0.005, "roe": 0.30, "beta": 1.2},
        "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "price": 420.30, "market_cap": 3.1e12, "rev_growth": 0.15, "pe_forward": 32.0, "eps": 11.80, "dividend_yield": 0.007, "roe": 0.38, "beta": 0.9},
        "GOOGL": {"name": "Alphabet Inc.", "sector": "Communication Services", "price": 175.20, "market_cap": 2.1e12, "rev_growth": 0.13, "pe_forward": 22.5, "eps": 6.50, "dividend_yield": 0.0, "roe": 0.27, "beta": 1.05},
        "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "price": 185.00, "market_cap": 1.9e12, "rev_growth": 0.12, "pe_forward": 42.0, "eps": 4.20, "dividend_yield": 0.0, "roe": 0.16, "beta": 1.3},
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "price": 875.50, "market_cap": 2.15e12, "rev_growth": 2.10, "pe_forward": 35.0, "eps": 12.90, "dividend_yield": 0.0003, "roe": 0.55, "beta": 1.75},
        "META": {"name": "Meta Platforms Inc.", "sector": "Communication Services", "price": 505.20, "market_cap": 1.3e12, "rev_growth": 0.25, "pe_forward": 24.0, "eps": 18.50, "dividend_yield": 0.0, "roe": 0.28, "beta": 1.4},
        "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Cyclical", "price": 195.30, "market_cap": 620e9, "rev_growth": 0.08, "pe_forward": 65.0, "eps": 3.50, "dividend_yield": 0.0, "roe": 0.18, "beta": 2.0},
        "NFLX": {"name": "Netflix Inc.", "sector": "Communication Services", "price": 625.80, "market_cap": 270e9, "rev_growth": 0.15, "pe_forward": 28.0, "eps": 18.20, "dividend_yield": 0.0, "roe": 0.25, "beta": 1.15},
        "AMD": {"name": "Advanced Micro Devices", "sector": "Technology", "price": 140.50, "market_cap": 227e9, "rev_growth": 0.18, "pe_forward": 45.0, "eps": 2.50, "dividend_yield": 0.0, "roe": 0.05, "beta": 1.8},
        "CRM": {"name": "Salesforce Inc.", "sector": "Technology", "price": 285.40, "market_cap": 277e9, "rev_growth": 0.11, "pe_forward": 25.0, "eps": 5.50, "dividend_yield": 0.0, "roe": 0.12, "beta": 1.1}
    }
    
    if ticker not in mock_db:
        seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
        base_price = 50 + (seed % 950)
        mock_db[ticker] = {
            "name": f"{ticker} Corp.", "sector": "Technology", "price": float(base_price),
            "market_cap": float(base_price * 1e9 * random.uniform(0.5, 5)),
            "rev_growth": random.uniform(-0.1, 0.5), "pe_forward": random.uniform(15, 50),
            "eps": float(base_price) / random.uniform(15, 40), "dividend_yield": random.choice([0.0, 0.0, 0.0, 0.02, 0.04]),
            "roe": random.uniform(0.05, 0.40), "beta": random.uniform(0.8, 2.0)
        }
    
    mock = mock_db[ticker]
    price = float(mock["price"])
    
    data = {
        "ticker": ticker, "name": mock["name"], "short_name": ticker,
        "sector": mock["sector"], "industry": "Technology", "country": "United States",
        "employees": int(random.uniform(10000, 200000)), "website": "#",
        "summary": f"{mock['name']} - Datos de demostración.",
        "price": price, "prev_close": price * random.uniform(0.98, 1.02),
        "open": price * random.uniform(0.99, 1.01), "day_high": price * 1.02,
        "day_low": price * 0.98, "fifty_two_high": price * 1.3,
        "fifty_two_low": price * 0.7, "volume": int(random.uniform(10e6, 100e6)),
        "avg_volume": int(random.uniform(15e6, 80e6)), "market_cap": mock["market_cap"],
        "enterprise_value": mock["market_cap"] * 1.1, "rev_growth": mock["rev_growth"],
        "ebitda_margin": random.uniform(0.20, 0.45), "profit_margin": random.uniform(0.10, 0.35),
        "operating_margin": random.uniform(0.15, 0.40), "gross_margin": random.uniform(0.40, 0.80),
        "pe_trailing": mock["pe_forward"] * random.uniform(0.9, 1.1), "pe_forward": mock["pe_forward"],
        "peg_ratio": 2.0, "price_to_sales": random.uniform(3, 15), "price_to_book": random.uniform(2, 10),
        "eps": mock["eps"], "eps_forward": mock["eps"] * 1.15, "eps_growth": mock["rev_growth"] * 1.2,
        "roe": mock["roe"], "roa": mock["roe"] * 0.6, "cash": mock["market_cap"] * 0.05,
        "free_cashflow": mock["market_cap"] * 0.03, "operating_cashflow": mock["market_cap"] * 0.04,
        "debt": mock["market_cap"] * 0.15, "debt_to_equity": random.uniform(20, 80),
        "current_ratio": random.uniform(1.0, 3.0), "dividend_rate": price * mock["dividend_yield"],
        "dividend_yield": mock["dividend_yield"], "ex_div_date": None,
        "payout_ratio": random.uniform(0.1, 0.6) if mock["dividend_yield"] > 0 else 0,
        "target_high": price * 1.3, "target_low": price * 0.8, "target_mean": price * 1.1,
        "target_median": price * 1.1, "recommendation": random.choice(['buy', 'strong_buy', 'hold']),
        "num_analysts": int(random.uniform(20, 50)), "hist": pd.DataFrame(), "beta": mock["beta"],
        "is_real_data": False, "data_source": "mock", "change_pct": random.uniform(-3, 3),
        "change_abs": 0, "pct_from_high": random.uniform(-20, -5)
    }
    data["change_abs"] = data["price"] * (data["change_pct"] / 100)
    return data

# ────────────────────────────────────────────────
# FUNCIONES DE RENDER (simplificadas)
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
        return f"{prefix}{value:.{decimals}f}{suffix}"
    return str(value)

def format_percentage(value, decimals=2):
    if value is None:
        return "N/A", "#888"
    if isinstance(value, float):
        color = "#00ffad" if value >= 0 else "#f23645"
        return f"{value:.{decimals}f}%", color
    return str(value), "#888"

def render_header(data):
    change_color = "#00ffad" if data['change_pct'] >= 0 else "#f23645"
    arrow = "▲" if data['change_pct'] >= 0 else "▼"
    source_colors = {"Yahoo Finance": "#00ffad", "Finnhub": "#4caf50", "mock": "#f23645"}
    source_labels = {"Yahoo Finance": "🟢 YAHOO", "Finnhub": "🟢 FINNHUB", "mock": "🔴 DEMO"}
    source = data.get('data_source', 'mock')
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 5px;">
            <span style="background: #1a1e26; color: {source_colors.get(source, '#888')}; padding: 4px 10px; border-radius: 4px; font-size: 10px; font-weight: bold; border: 1px solid {source_colors.get(source, '#888')}44;">
                {source_labels.get(source, source.upper())}
            </span>
            <span style="color: #666; font-size: 11px; margin-left: 10px;">{data['sector']}</span>
        </div>
        <h1 style="color: white; margin: 0; font-size: 2rem;">{data['name']} <span style="color: #00ffad; font-size: 1rem;">({data['ticker']})</span></h1>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: right;">
            <div style="color: white; font-size: 2.2rem; font-weight: bold;">${data['price']:,.2f}</div>
            <div style="color: {change_color}; font-size: 1rem; font-weight: bold;">{arrow} {data['change_pct']:+.2f}%</div>
            <div style="color: #666; font-size: 10px;">Cap: {format_value(data['market_cap'], '$')}</div>
        </div>
        """, unsafe_allow_html=True)

def render_metrics(data):
    st.markdown("### 📊 Métricas Clave")
    cols = st.columns(4)
    metrics = [
        ("Crec. Ingresos", data.get('rev_growth'), "%"),
        ("Margen EBITDA", data.get('ebitda_margin'), "%"),
        ("ROE", data.get('roe'), "%"),
        ("P/E Forward", data.get('pe_forward'), "x"),
    ]
    for col, (label, value, suffix) in zip(cols, metrics):
        with col:
            if suffix == "%":
                formatted, color = format_percentage(value)
            else:
                formatted = format_value(value, '', suffix, 1)
                color = "#00ffad"
            st.markdown(f"""
            <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 12px; text-align: center;">
                <div style="color: #666; font-size: 9px; text-transform: uppercase;">{label}</div>
                <div style="color: {color}; font-size: 1.2rem; font-weight: bold;">{formatted}</div>
            </div>
            """, unsafe_allow_html=True)

def render_chart(data):
    if data['hist'].empty:
        st.info("📊 Gráfico histórico no disponible")
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
        height=280, margin=dict(l=30, r=30, t=30, b=30)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_outlook(data):
    st.markdown("### 🔮 Perspectivas")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background: rgba(0,255,173,0.1); border: 1px solid #00ffad44; border-radius: 10px; padding: 15px;">
            <h4 style="color: #00ffad; margin-bottom: 10px;">📈 Positivo</h4>
            <ul style="color: #ccc; font-size: 13px; padding-left: 18px;">
                <li>Crecimiento sostenido de ingresos</li>
                <li>Márgenes operativos estables</li>
                <li>Posición de liderazgo en sector</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background: rgba(242,54,69,0.1); border: 1px solid #f2364544; border-radius: 10px; padding: 15px;">
            <h4 style="color: #f23645; margin-bottom: 10px;">⚠️ Desafíos</h4>
            <ul style="color: #ccc; font-size: 13px; padding-left: 18px;">
                <li>Presión competitiva creciente</li>
                <li>Volatilidad macroeconómica</li>
                <li>Costos operativos variables</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def render_ai_analysis(data):
    st.markdown("### 🤖 Análisis IA")
    model, name, err = get_ia_model()
    if not model:
        st.info("IA no disponible")
        return
    prompt = f"Análisis de {data['name']} ({data['ticker']}): Precio ${data['price']:.2f}, Cap {format_value(data['market_cap'], '$')}, Crecimiento {format_value(data.get('rev_growth'), '', '%', 1)}. Resumen, 3 fortalezas, 3 riesgos, veredicto Compra/Mantener/Vender. En español."
    try:
        with st.spinner("Analizando..."):
            response = model.generate_content(prompt)
            st.markdown(f"<div style='background: #1a1e26; border: 1px solid #2a3f5f; border-radius: 10px; padding: 20px;'>{response.text}</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error IA: {e}")

# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; }
        .stTextInput > div > div > input { background-color: #1a1e26; color: white; border: 1px solid #2a3f5f; border-radius: 8px; }
        .stButton > button { background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); color: #0c0e12; border: none; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Análisis de Earnings")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    with col2:
        st.write("")
        st.write("")
        if st.button("🔍 Analizar", use_container_width=True):
            pass
    
    if ticker:
        with st.spinner("Cargando datos..."):
            data, source = get_comprehensive_earnings_data_robust(ticker)
        
        if data:
            render_header(data)
            render_metrics(data)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                render_chart(data)
            with col2:
                st.markdown("#### 📋 Sobre")
                st.markdown(f"<div style='color: #aaa; font-size: 12px;'>{data['summary'][:200]}...</div>", unsafe_allow_html=True)
                st.markdown("#### 💰 Datos")
                st.markdown(f"""
                - Cash: {format_value(data['cash'], '$')}
                - Deuda: {format_value(data['debt'], '$')}
                - Beta: {data['beta']:.2f}
                """)
            
            st.markdown("---")
            render_outlook(data)
            st.markdown("---")
            render_ai_analysis(data)

if __name__ == "__main__":
    render()
