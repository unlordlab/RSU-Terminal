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
import json

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────

def rate_limit_delay():
    time.sleep(random.uniform(0.3, 0.8))

# ────────────────────────────────────────────────
# OBTENCIÓN DE DATOS CON DEBUG
# ────────────────────────────────────────────────

def debug_info(info):
    """Muestra campos disponibles para depuración."""
    if not info:
        return "No info disponible"
    
    # Campos que nos interesan
    key_fields = [
        'longName', 'shortName', 'sector', 'industry',
        'currentPrice', 'regularMarketPrice', 'previousClose',
        'marketCap', 'revenueGrowth', 'ebitdaMargins',
        'profitMargins', 'trailingPE', 'forwardPE',
        'returnOnEquity', 'trailingEps', 'beta',
        'totalCash', 'totalDebt', 'dividendYield'
    ]
    
    available = {}
    for key in key_fields:
        if key in info:
            available[key] = info[key]
    
    return available

def get_yfinance_data_debug(ticker_symbol):
    """
    Obtiene datos con logging detallado.
    """
    try:
        rate_limit_delay()
        
        st.write(f"🔍 Intentando obtener datos para {ticker_symbol}...")
        
        ticker = yf.Ticker(ticker_symbol)
        
        # Intentar obtener info
        try:
            info = ticker.info
            st.write(f"✅ Info obtenida: {len(info)} campos")
            
            # Debug: mostrar campos clave
            debug_data = debug_info(info)
            with st.expander("Ver campos disponibles"):
                st.json(debug_data)
                
        except Exception as e:
            st.error(f"❌ Error obteniendo info: {e}")
            info = {}
        
        # Si no hay precio, intentar fast_info
        if not info.get('currentPrice') and not info.get('regularMarketPrice'):
            try:
                st.write("🔄 Intentando fast_info...")
                fast = ticker.fast_info
                # Convertir fast_info a dict
                fast_dict = dict(fast) if hasattr(fast, 'items') else {}
                if fast_dict:
                    st.write(f"✅ Fast info obtenido: {list(fast_dict.keys())}")
                    # Merge con info
                    info.update(fast_dict)
            except Exception as e:
                st.warning(f"⚠️ Fast info no disponible: {e}")
        
        # Histórico
        try:
            hist = ticker.history(period="6mo", auto_adjust=True)
            st.write(f"✅ Histórico: {len(hist)} días")
            hist_dict = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            } if not hist.empty else None
        except Exception as e:
            st.warning(f"⚠️ Histórico no disponible: {e}")
            hist_dict = None
        
        return {'info': info, 'history': hist_dict, 'source': 'yfinance'}
        
    except Exception as e:
        st.error(f"❌ Error general: {e}")
        return None

def get_finnhub_data(ticker, api_key):
    """Obtiene datos de Finnhub."""
    if not api_key:
        return None
    
    try:
        base_url = "https://finnhub.io/api/v1"
        headers = {"X-Finnhub-Token": api_key}
        
        st.write(f"🔄 Intentando Finnhub para {ticker}...")
        
        # Quote
        quote_resp = requests.get(
            f"{base_url}/quote", 
            params={"symbol": ticker}, 
            headers=headers,
            timeout=10
        )
        quote = quote_resp.json() if quote_resp.status_code == 200 else {}
        
        # Profile
        profile_resp = requests.get(
            f"{base_url}/stock/profile2",
            params={"symbol": ticker},
            headers=headers,
            timeout=10
        )
        profile = profile_resp.json() if profile_resp.status_code == 200 else {}
        
        # Metrics
        metrics_resp = requests.get(
            f"{base_url}/stock/metric",
            params={"symbol": ticker, "metric": "all"},
            headers=headers,
            timeout=10
        )
        metrics = metrics_resp.json().get('metric', {}) if metrics_resp.status_code == 200 else {}
        
        st.write(f"✅ Finnhub: Quote={bool(quote)}, Profile={bool(profile)}")
        
        # Mapear a formato unificado
        info = {
            'longName': profile.get('name'),
            'sector': profile.get('finnhubIndustry'),
            'industry': profile.get('industry'),
            'country': profile.get('country'),
            'website': profile.get('weburl'),
            'longBusinessSummary': profile.get('description'),
            'currentPrice': quote.get('c'),
            'previousClose': quote.get('pc'),
            'open': quote.get('o'),
            'dayHigh': quote.get('h'),
            'dayLow': quote.get('l'),
            'marketCap': (profile.get('marketCapitalization') or 0) * 1e6,
            'volume': quote.get('v'),
            'beta': metrics.get('beta'),
            'revenueGrowth': metrics.get('revenueGrowth5Y'),
            'ebitdaMargins': metrics.get('ebitdaMarginAnnual'),
            'profitMargins': metrics.get('netProfitMarginAnnual'),
            'trailingPE': metrics.get('peTTM'),
            'forwardPE': metrics.get('peNormalizedAnnual'),
            'returnOnEquity': metrics.get('roeTTM'),
            'trailingEps': metrics.get('epsTTM'),
            'totalCash': metrics.get('cashPerShareAnnual', 0) * (profile.get('shareOutstanding') or 0) * 1e6 if profile.get('shareOutstanding') else 0,
            'totalDebt': metrics.get('totalDebtAnnual'),
            'dividendYield': metrics.get('dividendYieldIndicatedAnnual'),
            'debtToEquity': metrics.get('totalDebtToTotalEquityAnnual'),
        }
        
        return {'info': info, 'history': None, 'source': 'finnhub'}
        
    except Exception as e:
        st.error(f"❌ Error Finnhub: {e}")
        return None

def process_data(raw_data, ticker):
    """Procesa datos crudos en formato estándar."""
    if not raw_data:
        return None
    
    info = raw_data.get('info', {})
    source = raw_data.get('source', 'unknown')
    
    # Función de extracción segura
    def get(keys, default=None):
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            if key in info and info[key] is not None:
                val = info[key]
                # Convertir tipos problemáticos
                if isinstance(val, pd.Series):
                    return val.iloc[0] if len(val) > 0 else default
                if isinstance(val, (int, float, str, bool)):
                    return val
                try:
                    return float(val)
                except:
                    return val
        return default
    
    # Extraer precio
    price = get(['currentPrice', 'regularMarketPrice', 'previousClose', 'c'], 0)
    prev_close = get(['previousClose', 'regularMarketPreviousClose', 'pc'], price)
    
    if price == 0:
        st.error("❌ No se pudo obtener precio")
        return None
    
    # Reconstruir DataFrame histórico
    hist_df = pd.DataFrame()
    hist_data = raw_data.get('history')
    if hist_data:
        try:
            hist_df = pd.DataFrame({
                'Open': hist_data['open'],
                'High': hist_data['high'],
                'Low': hist_data['low'],
                'Close': hist_data['close'],
                'Volume': hist_data['volume']
            }, index=pd.to_datetime(hist_data['dates']))
        except Exception as e:
            st.warning(f"⚠️ Error reconstruyendo histórico: {e}")
    
    # Procesar métricas
    rev_growth = get(['revenueGrowth', 'revenueGrowth5Y'])
    ebitda_margin = get(['ebitdaMargins', 'ebitdaMarginAnnual', 'ebitdaMargin'])
    profit_margin = get(['profitMargins', 'netProfitMarginAnnual', 'profitMargin'])
    pe_trailing = get(['trailingPE', 'peTrailing', 'peTTM', 'trailingPegRatio'])
    pe_forward = get(['forwardPE', 'peForward', 'peNormalizedAnnual'])
    roe = get(['returnOnEquity', 'roeTTM', 'roe'])
    eps = get(['trailingEps', 'epsTTM', 'eps'])
    
    # Dividend yield puede venir como decimal o porcentaje
    div_yield = get(['dividendYield', 'dividendYieldIndicatedAnnual'], 0)
    if div_yield and div_yield > 1:  # Si es > 1, probablemente es porcentaje, convertir a decimal
        div_yield = div_yield / 100
    
    data = {
        "ticker": ticker,
        "name": get(['longName', 'shortName', 'name'], ticker),
        "sector": get(['sector', 'finnhubIndustry'], 'N/A'),
        "industry": get(['industry'], 'N/A'),
        "country": get(['country'], 'N/A'),
        "employees": int(get(['fullTimeEmployees'], 0) or 0),
        "website": get(['website', 'weburl'], '#'),
        "summary": get(['longBusinessSummary', 'description'], f"Empresa {ticker}"),
        
        "price": float(price),
        "prev_close": float(prev_close),
        "open": float(get(['open', 'regularMarketOpen', 'o'], price)),
        "day_high": float(get(['dayHigh', 'regularMarketDayHigh', 'h'], price * 1.01)),
        "day_low": float(get(['dayLow', 'regularMarketDayLow', 'l'], price * 0.99)),
        "fifty_two_high": float(get(['fiftyTwoWeekHigh', '52WeekHigh'], price * 1.2)),
        "fifty_two_low": float(get(['fiftyTwoWeekLow', '52WeekLow'], price * 0.8)),
        "volume": int(get(['volume', 'regularMarketVolume', 'v'], 0) or 0),
        "avg_volume": int(get(['averageVolume', 'avgVolume'], 0) or 0),
        
        "market_cap": float(get(['marketCap', 'marketCapitalization'], 0) or 0),
        "enterprise_value": float(get(['enterpriseValue'], 0) or 0),
        
        # Métricas fundamentales (pueden ser None)
        "rev_growth": float(rev_growth) if rev_growth is not None else None,
        "ebitda_margin": float(ebitda_margin) if ebitda_margin is not None else None,
        "profit_margin": float(profit_margin) if profit_margin is not None else None,
        "operating_margin": float(get(['operatingMargins'], 0) or 0) if get(['operatingMargins']) else None,
        "gross_margin": float(get(['grossMargins'], 0) or 0) if get(['grossMargins']) else None,
        
        "pe_trailing": float(pe_trailing) if pe_trailing is not None else None,
        "pe_forward": float(pe_forward) if pe_forward is not None else None,
        "peg_ratio": float(get(['pegRatio'], 0) or 0) if get(['pegRatio']) else None,
        "price_to_sales": float(get(['priceToSalesTrailing12Months'], 0) or 0) if get(['priceToSalesTrailing12Months']) else None,
        "price_to_book": float(get(['priceToBook'], 0) or 0) if get(['priceToBook']) else None,
        
        "eps": float(eps) if eps is not None else None,
        "eps_forward": float(get(['forwardEps'], 0) or 0) if get(['forwardEps']) else None,
        "eps_growth": float(get(['earningsGrowth'], 0) or 0) if get(['earningsGrowth']) else None,
        
        "roe": float(roe) if roe is not None else None,
        "roa": float(get(['returnOnAssets', 'roa'], 0) or 0) if get(['returnOnAssets']) else None,
        
        "cash": float(get(['totalCash', 'freeCashflow'], 0) or 0),
        "free_cashflow": float(get(['freeCashflow'], 0) or 0),
        "operating_cashflow": float(get(['operatingCashflow'], 0) or 0),
        "debt": float(get(['totalDebt', 'totalDebtAnnual'], 0) or 0),
        "debt_to_equity": float(get(['debtToEquity', 'totalDebtToTotalEquityAnnual'], 0) or 0) if get(['debtToEquity']) else None,
        "current_ratio": float(get(['currentRatio'], 0) or 0) if get(['currentRatio']) else None,
        
        "dividend_rate": float(get(['dividendRate'], 0) or 0),
        "dividend_yield": float(div_yield),
        "ex_div_date": get(['exDividendDate']),
        "payout_ratio": float(get(['payoutRatio'], 0) or 0),
        
        "target_high": float(get(['targetHighPrice'], price * 1.2)),
        "target_low": float(get(['targetLowPrice'], price * 0.8)),
        "target_mean": float(get(['targetMeanPrice', 'targetMedianPrice'], price)),
        "target_median": float(get(['targetMedianPrice', 'targetMeanPrice'], price)),
        "recommendation": get(['recommendationKey'], 'none'),
        "num_analysts": int(get(['numberOfAnalystOpinions'], 0) or 0),
        
        "hist": hist_df,
        "beta": float(get(['beta'], 0) or 0),
        
        "is_real_data": source != 'mock',
        "data_source": source
    }
    
    # Calcular cambios
    if data['prev_close'] and data['prev_close'] != 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
        data['change_abs'] = data['price'] - data['prev_close']
    else:
        data['change_pct'] = 0
        data['change_abs'] = 0
        
    if data['fifty_two_high'] and data['fifty_two_high'] != 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    else:
        data['pct_from_high'] = 0
    
    return data

def get_mock_data(ticker):
    """Datos de demostración."""
    mock_db = {
        "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 185.50, "market_cap": 2.8e12, "rev_growth": 0.02, "pe_forward": 28.5, "eps": 6.15, "dividend_yield": 0.005, "roe": 0.30, "beta": 1.2, "ebitda_margin": 0.32},
        "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "price": 420.30, "market_cap": 3.1e12, "rev_growth": 0.15, "pe_forward": 32.0, "eps": 11.80, "dividend_yield": 0.007, "roe": 0.38, "beta": 0.9, "ebitda_margin": 0.45},
        "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "price": 875.50, "market_cap": 2.15e12, "rev_growth": 2.10, "pe_forward": 35.0, "eps": 12.90, "dividend_yield": 0.0003, "roe": 0.55, "beta": 1.75, "ebitda_margin": 0.58},
    }
    
    if ticker not in mock_db:
        seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
        base_price = 50 + (seed % 950)
        mock_db[ticker] = {
            "name": f"{ticker} Corp.", "sector": "Technology", "price": float(base_price),
            "market_cap": float(base_price * 1e9 * random.uniform(0.5, 5)),
            "rev_growth": random.uniform(-0.1, 0.5), "pe_forward": random.uniform(15, 50),
            "eps": float(base_price) / random.uniform(15, 40), "dividend_yield": random.choice([0.0, 0.0, 0.0, 0.02, 0.04]),
            "roe": random.uniform(0.05, 0.40), "beta": random.uniform(0.8, 2.0),
            "ebitda_margin": random.uniform(0.15, 0.40)
        }
    
    mock = mock_db[ticker]
    price = float(mock["price"])
    
    return {
        "ticker": ticker, "name": mock["name"], "sector": mock["sector"],
        "price": price, "prev_close": price * 0.98, "market_cap": mock["market_cap"],
        "rev_growth": mock["rev_growth"], "pe_forward": mock["pe_forward"],
        "eps": mock["eps"], "dividend_yield": mock["dividend_yield"],
        "roe": mock["roe"], "ebitda_margin": mock["ebitda_margin"],
        "beta": mock["beta"], "is_real_data": False, "data_source": "mock",
        "change_pct": 2.04, "change_abs": price * 0.02,
        "hist": pd.DataFrame(), "summary": "Datos de demostración"
    }

# ────────────────────────────────────────────────
# RENDER (con verificación de datos)
# ────────────────────────────────────────────────

def format_value(value, prefix="", suffix="", decimals=2):
    if value is None or value == 0 or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    try:
        val = float(value)
        if abs(val) >= 1e12:
            return f"{prefix}{val/1e12:.{decimals}f}T{suffix}"
        elif abs(val) >= 1e9:
            return f"{prefix}{val/1e9:.{decimals}f}B{suffix}"
        elif abs(val) >= 1e6:
            return f"{prefix}{val/1e6:.{decimals}f}M{suffix}"
        elif abs(val) >= 1e3:
            return f"{prefix}{val/1e3:.{decimals}f}K{suffix}"
        return f"{prefix}{val:.{decimals}f}{suffix}"
    except:
        return str(value)

def format_pct(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A", "#888"
    try:
        val = float(value) * 100 if abs(float(value)) < 1 else float(value)
        color = "#00ffad" if val >= 0 else "#f23645"
        return f"{val:.2f}%", color
    except:
        return "N/A", "#888"

def render():
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; }
        .stTextInput > div > div > input { background-color: #1a1e26; color: white; border: 1px solid #2a3f5f; border-radius: 8px; }
        .stButton > button { background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); color: #0c0e12; border: none; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Análisis de Earnings (Debug Mode)")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 Analizar", use_container_width=True)
    with col3:
        st.write("")
        st.write("")
        if st.button("🎲 Demo", use_container_width=True):
            ticker = random.choice(["AAPL", "MSFT", "NVDA", "TSLA"])
            analyze = True
    
    if analyze and ticker:
        st.markdown("---")
        st.subheader("🔧 Proceso de obtención de datos")
        
        # Paso 1: Intentar Yahoo
        raw_data = get_yfinance_data_debug(ticker)
        
        if not raw_data or not raw_data.get('info'):
            st.warning("⚠️ Yahoo Finance falló, intentando alternativas...")
            
            # Paso 2: Intentar Finnhub
            api_key = st.secrets.get("FINNHUB_API_KEY", None)
            if api_key:
                raw_data = get_finnhub_data(ticker, api_key)
            
            if not raw_data:
                st.error("❌ Todas las fuentes fallaron. Usando datos de demostración.")
                data = get_mock_data(ticker)
            else:
                data = process_data(raw_data, ticker)
        else:
            data = process_data(raw_data, ticker)
        
        if not data:
            st.error("❌ No se pudieron procesar los datos")
            return
        
        # Mostrar datos procesados
        with st.expander("Ver datos procesados", expanded=True):
            st.json({
                k: v for k, v in data.items() 
                if k not in ['hist', 'summary'] and v is not None
            })
        
        # Renderizar UI
        st.markdown("---")
        
        # Header
        change_color = "#00ffad" if data.get('change_pct', 0) >= 0 else "#f23645"
        source_color = {"yfinance": "#00ffad", "finnhub": "#4caf50", "mock": "#f23645"}.get(data.get('data_source'), "#888")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div>
                <span style="background: {source_color}22; color: {source_color}; padding: 4px 10px; border-radius: 4px; font-size: 10px; border: 1px solid {source_color};">
                    {data.get('data_source', 'unknown').upper()}
                </span>
                <span style="color: #666; font-size: 12px; margin-left: 10px;">{data.get('sector', 'N/A')}</span>
                <h1 style="color: white; margin: 5px 0; font-size: 1.8rem;">{data.get('name', ticker)} <span style="color: #00ffad;">({ticker})</span></h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: right;">
                <div style="color: white; font-size: 2rem; font-weight: bold;">${data.get('price', 0):,.2f}</div>
                <div style="color: {change_color}; font-size: 1rem; font-weight: bold;">{data.get('change_pct', 0):+.2f}%</div>
                <div style="color: #666; font-size: 11px;">Cap: {format_value(data.get('market_cap'), '$')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Métricas
        st.markdown("### 📊 Métricas Fundamentales")
        
        # Verificar qué métricas tenemos
        metrics_available = {
            'rev_growth': data.get('rev_growth'),
            'ebitda_margin': data.get('ebitda_margin'),
            'roe': data.get('roe'),
            'pe_forward': data.get('pe_forward')
        }
        
        cols = st.columns(4)
        metrics_display = [
            ("Crec. Ingresos", data.get('rev_growth'), True),
            ("Margen EBITDA", data.get('ebitda_margin'), True),
            ("ROE", data.get('roe'), True),
            ("P/E Forward", data.get('pe_forward'), False),
        ]
        
        for col, (label, value, is_pct) in zip(cols, metrics_display):
            with col:
                if is_pct and value is not None:
                    formatted, color = format_pct(value)
                else:
                    formatted = format_value(value, '', 'x' if 'P/E' in label else '', 1)
                    color = "#00ffad" if value else "#888"
                
                st.markdown(f"""
                <div style="background: #0c0e12; border: 1px solid #1a1e26; border-radius: 8px; padding: 15px; text-align: center;">
                    <div style="color: #666; font-size: 9px; text-transform: uppercase;">{label}</div>
                    <div style="color: {color}; font-size: 1.3rem; font-weight: bold;">{formatted}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Gráfico y descripción
        col1, col2 = st.columns([2, 1])
        with col1:
            if not data.get('hist', pd.DataFrame()).empty:
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
            else:
                st.info("📊 Sin datos históricos")
        
        with col2:
            st.markdown("#### 📋 Sobre la empresa")
            st.markdown(f"<div style='color: #aaa; font-size: 12px;'>{data.get('summary', 'N/A')[:200]}...</div>", unsafe_allow_html=True)
            
            st.markdown("#### 💰 Finanzas")
            st.markdown(f"""
            - **Cash:** {format_value(data.get('cash'), '$')}
            - **Deuda:** {format_value(data.get('debt'), '$')}
            - **Beta:** {data.get('beta', 0):.2f}
            - **Empleados:** {format_value(data.get('employees'), '', '', 0)}
            """)

if __name__ == "__main__":
    render()
