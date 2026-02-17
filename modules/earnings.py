import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from config import get_ia_model
import time
import random
from functools import wraps
import hashlib
import requests
import os
import json
import sys
import traceback

# ────────────────────────────────────────────────
# CONFIGURACIÓN Y DEBUGGING
# ────────────────────────────────────────────────

def debug_log(msg, data=None):
    """Log detallado para debugging."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    if data is not None:
        full_msg += f": {data}"
    print(full_msg)
    return full_msg

# ────────────────────────────────────────────────
# FMP API - VERSIÓN CORREGIDA
# ────────────────────────────────────────────────

def get_fmp_data(ticker, api_key):
    """Obtiene datos de FMP con manejo de errores detallado."""
    if not api_key:
        debug_log("ERROR: FMP_API_KEY no proporcionada")
        return None
    
    base_url = "https://financialmodelingprep.com/api/v3"
    result = {}
    
    endpoints = {
        'quote': f"/quote/{ticker}?apikey={api_key}",
        'profile': f"/profile/{ticker}?apikey={api_key}",
        'income': f"/income-statement/{ticker}?period=quarter&limit=8&apikey={api_key}",
        'balance': f"/balance-sheet-statement/{ticker}?period=quarter&limit=1&apikey={api_key}",
        'cashflow': f"/cash-flow-statement/{ticker}?period=quarter&limit=1&apikey={api_key}",
        'metrics': f"/key-metrics/{ticker}?period=quarter&limit=1&apikey={api_key}",
        'ratios': f"/ratios/{ticker}?period=quarter&limit=1&apikey={api_key}",
        'surprises': f"/earnings-surprises/{ticker}?apikey={api_key}",
        'calendar': f"/earning_calendar/{ticker}?apikey={api_key}",
        'estimates': f"/analyst-estimates/{ticker}?period=quarter&limit=4&apikey={api_key}",
    }
    
    debug_log(f"Iniciando solicitudes FMP para {ticker}")
    
    for name, endpoint in endpoints.items():
        try:
            url = f"{base_url}{endpoint}"
            debug_log(f"Solicitando {name}")
            
            response = requests.get(url, timeout=15)
            debug_log(f"{name} status", response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                
                # FMP devuelve array para la mayoría de endpoints
                if isinstance(data, list) and len(data) > 0:
                    result[name] = data
                    debug_log(f"{name} OK", f"{len(data)} registros")
                elif isinstance(data, dict):
                    result[name] = [data] if name not in ['quote', 'profile'] else data
                    debug_log(f"{name} OK", "dict")
                else:
                    result[name] = []
                    debug_log(f"{name} vacío")
            else:
                debug_log(f"{name} ERROR", f"Status {response.status_code}: {response.text[:100]}")
                result[name] = [] if name not in ['quote', 'profile'] else {}
                
        except Exception as e:
            debug_log(f"{name} EXCEPTION", str(e))
            result[name] = [] if name not in ['quote', 'profile'] else {}
    
    # Verificar si tenemos datos mínimos
    quote_data = result.get('quote', [])
    if not quote_data or len(quote_data) == 0:
        debug_log("ERROR CRÍTICO: No se obtuvo quote")
        return None
    
    # Asegurar que quote y profile son diccionarios, no listas
    quote = quote_data[0] if isinstance(quote_data, list) else quote_data
    profile_data = result.get('profile', {})
    profile = profile_data[0] if isinstance(profile_data, list) and len(profile_data) > 0 else profile_data
    
    debug_log("FMP datos obtenidos exitosamente")
    
    return {
        'quote': quote,
        'profile': profile,
        'income_statement': result.get('income', []),
        'balance_sheet': result.get('balance', []),
        'cash_flow': result.get('cashflow', []),
        'key_metrics': result.get('metrics', []),
        'ratios': result.get('ratios', []),
        'earnings_surprises': result.get('surprises', []),
        'earnings_calendar': result.get('calendar', []),
        'analyst_estimates': result.get('estimates', []),
        'source': 'fmp',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# ────────────────────────────────────────────────
# EXTRACCIÓN DE DATOS CON VALIDACIÓN
# ────────────────────────────────────────────────

def safe_float(value):
    """Convierte a float de manera segura."""
    if value is None or value == '' or value == 'N/A':
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_int(value):
    """Convierte a int de manera segura."""
    if value is None or value == '' or value == 'N/A':
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0

def extract_fundamentals_from_fmp(fmp_data):
    """Extrae métricas con validación exhaustiva."""
    if not fmp_data:
        debug_log("extract_fundamentals: fmp_data es None")
        return {}
    
    debug_log("Iniciando extracción de fundamentos")
    f = {}
    
    try:
        # Quote - precios y métricas básicas
        quote = fmp_data.get('quote', {})
        debug_log("Quote data", quote)
        
        f['price'] = safe_float(quote.get('price'))
        f['market_cap'] = safe_float(quote.get('marketCap'))
        f['volume'] = safe_int(quote.get('volume'))
        f['avg_volume'] = safe_int(quote.get('avgVolume'))
        f['change_pct'] = safe_float(quote.get('changesPercentage'))
        f['prev_close'] = safe_float(quote.get('previousClose'))
        f['open'] = safe_float(quote.get('open'))
        f['day_high'] = safe_float(quote.get('dayHigh'))
        f['day_low'] = safe_float(quote.get('dayLow'))
        f['fifty_two_high'] = safe_float(quote.get('yearHigh'))
        f['fifty_two_low'] = safe_float(quote.get('yearLow'))
        f['beta'] = safe_float(quote.get('beta'))
        f['eps'] = safe_float(quote.get('eps'))
        f['pe_trailing'] = safe_float(quote.get('pe'))
        f['exchange'] = quote.get('exchange', 'N/A')
        
        debug_log("Quote procesado", f"Price: {f['price']}, MarketCap: {f['market_cap']}")
        
        # Profile
        profile = fmp_data.get('profile', {})
        debug_log("Profile data", profile)
        
        f['name'] = profile.get('companyName') or quote.get('name', 'Unknown')
        f['sector'] = profile.get('sector', 'N/A')
        f['industry'] = profile.get('industry', 'N/A')
        f['country'] = profile.get('country', 'N/A')
        f['employees'] = safe_int(profile.get('fullTimeEmployees'))
        f['website'] = profile.get('website', '#')
        f['summary'] = profile.get('description', f"Empresa {f.get('name', '')}")
        
        # Key Metrics
        metrics = fmp_data.get('key_metrics', [])
        if metrics and len(metrics) > 0:
            m = metrics[0]
            debug_log("Key metrics", m)
            f['pe_forward'] = safe_float(m.get('peRatio'))
            f['price_to_book'] = safe_float(m.get('pbRatio'))
            f['price_to_sales'] = safe_float(m.get('priceToSalesRatio'))
            f['peg_ratio'] = safe_float(m.get('pegRatio'))
            f['roe'] = safe_float(m.get('roe'))
            f['roa'] = safe_float(m.get('roa'))
            f['debt_to_equity'] = safe_float(m.get('debtToEquity'))
            f['current_ratio'] = safe_float(m.get('currentRatio'))
            f['dividend_yield'] = safe_float(m.get('dividendYield'))
            f['payout_ratio'] = safe_float(m.get('payoutRatio'))
            debug_log("Métricas asignadas", f"ROE: {f['roe']}, P/E Forward: {f['pe_forward']}")
        
        # Ratios (márgenes)
        ratios = fmp_data.get('ratios', [])
        if ratios and len(ratios) > 0:
            r = ratios[0]
            debug_log("Ratios", r)
            f['gross_margin'] = safe_float(r.get('grossProfitMargin'))
            f['operating_margin'] = safe_float(r.get('operatingProfitMargin'))
            f['profit_margin'] = safe_float(r.get('netProfitMargin'))
            f['ebitda_margin'] = safe_float(r.get('ebitdaMargin'))
            f['rev_growth'] = safe_float(r.get('revenueGrowth'))
            f['eps_growth'] = safe_float(r.get('epsgrowth'))
        
        # Balance Sheet
        balance = fmp_data.get('balance_sheet', [])
        if balance and len(balance) > 0:
            b = balance[0]
            debug_log("Balance", b)
            f['cash'] = safe_float(b.get('cashAndCashEquivalents'))
            f['debt'] = safe_float(b.get('totalDebt'))
            f['total_equity'] = safe_float(b.get('totalStockholdersEquity'))
        
        # Cash Flow
        cashflow = fmp_data.get('cash_flow', [])
        if cashflow and len(cashflow) > 0:
            c = cashflow[0]
            debug_log("Cashflow", c)
            f['operating_cashflow'] = safe_float(c.get('operatingCashFlow'))
            capex = safe_float(c.get('capitalExpenditure'))
            if f['operating_cashflow'] and capex:
                f['free_cashflow'] = f['operating_cashflow'] - capex
        
        # Analyst estimates
        estimates = fmp_data.get('analyst_estimates', [])
        if estimates and len(estimates) > 0:
            e = estimates[0]
            f['eps_forward'] = safe_float(e.get('estimatedEps'))
            f['target_mean'] = safe_float(e.get('targetPrice'))
            f['target_high'] = safe_float(e.get('targetHighPrice'))
            f['target_low'] = safe_float(e.get('targetLowPrice'))
            f['num_analysts'] = safe_int(e.get('numberOfAnalysts'))
            f['recommendation'] = e.get('recommendation', 'none')
        
        # Calcular pct_from_high
        if f.get('price') and f.get('fifty_two_high'):
            f['pct_from_high'] = ((f['price'] - f['fifty_two_high']) / f['fifty_two_high']) * 100
        
        debug_log("Extracción completada", f"Campos: {len(f)}")
        
    except Exception as e:
        debug_log("ERROR en extracción", str(e))
        debug_log("Traceback", traceback.format_exc())
    
    return f

# ────────────────────────────────────────────────
# PROCESAMIENTO DE DATOS
# ────────────────────────────────────────────────

def process_combined_data(ticker, fmp_data, yf_data):
    """Combina datos con validación extensiva."""
    debug_log("Iniciando process_combined_data")
    
    # Datos base
    data = {
        'ticker': ticker,
        'name': ticker,
        'sector': 'N/A',
        'industry': 'N/A',
        'country': 'N/A',
        'employees': 0,
        'website': '#',
        'summary': f"Empresa {ticker}",
        'price': 0,
        'prev_close': 0,
        'market_cap': 0,
        'change_pct': 0,
        'volume': 0,
        'avg_volume': 0,
        'beta': 0,
        'eps': 0,
        'pe_trailing': 0,
        'pe_forward': 0,
        'peg_ratio': 0,
        'price_to_book': 0,
        'price_to_sales': 0,
        'roe': 0,
        'roa': 0,
        'gross_margin': 0,
        'operating_margin': 0,
        'profit_margin': 0,
        'ebitda_margin': 0,
        'rev_growth': 0,
        'eps_growth': 0,
        'cash': 0,
        'debt': 0,
        'free_cashflow': 0,
        'operating_cashflow': 0,
        'debt_to_equity': 0,
        'current_ratio': 0,
        'dividend_yield': 0,
        'payout_ratio': 0,
        'eps_forward': 0,
        'target_mean': 0,
        'target_high': 0,
        'target_low': 0,
        'num_analysts': 0,
        'recommendation': 'none',
        'hist': pd.DataFrame(),
        'earnings_calendar': [],
        'data_source': 'none',
        'is_real_data': False
    }
    
    has_fmp = False
    has_yf = False
    
    # 1. Procesar FMP
    if fmp_data:
        debug_log("Procesando datos FMP")
        fmp_fund = extract_fundamentals_from_fmp(fmp_data)
        
        if fmp_fund and fmp_fund.get('price', 0) > 0:
            debug_log("FMP tiene datos válidos")
            has_fmp = True
            
            # Copiar todos los valores no nulos
            for key, value in fmp_fund.items():
                if value is not None and value != 0 and value != '':
                    data[key] = value
            
            data['data_source'] = 'fmp'
            data['is_real_data'] = True
            debug_log("Datos FMP aplicados", f"Precio: {data['price']}")
        else:
            debug_log("FMP no tiene precio válido", fmp_fund.get('price') if fmp_fund else "No fmp_fund")
    
    # 2. Procesar YFinance (backup para precios e histórico)
    if yf_data:
        debug_log("Procesando datos YFinance")
        info = yf_data.get('info', {})
        
        # Solo usar si FMP no dio precio
        if data['price'] == 0:
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            if price:
                data['price'] = float(price)
                data['prev_close'] = float(info.get('previousClose', price))
                data['market_cap'] = float(info.get('marketCap', 0))
                data['volume'] = int(info.get('volume', 0))
                data['beta'] = float(info.get('beta', 0))
                data['name'] = info.get('longName', ticker)
                data['sector'] = info.get('sector', 'N/A')
                data['industry'] = info.get('industry', 'N/A')
                data['country'] = info.get('country', 'N/A')
                data['summary'] = info.get('longBusinessSummary', f"Empresa {ticker}")
                data['data_source'] = 'yfinance'
                has_yf = True
                debug_log("Precio de YFinance usado", price)
        
        # Siempre usar histórico de YFinance
        if yf_data.get('history'):
            try:
                hist = yf_data['history']
                data['hist'] = pd.DataFrame({
                    'Open': hist['open'],
                    'High': hist['high'],
                    'Low': hist['low'],
                    'Close': hist['close'],
                    'Volume': hist['volume']
                }, index=pd.to_datetime(hist['dates']))
                debug_log("Histórico cargado", len(data['hist']))
            except Exception as e:
                debug_log("Error cargando histórico", str(e))
        
        data['earnings_calendar'] = yf_data.get('calendar', [])
    
    # 3. Calcular campos derivados
    if data['price'] > 0 and data['prev_close'] > 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
    
    if data['price'] > 0 and data.get('fifty_two_high', 0) > 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    
    # 4. Validación final
    if data['price'] == 0:
        debug_log("ERROR: Precio sigue siendo 0 después de todas las fuentes")
        return None
    
    debug_log("Datos procesados exitosamente", f"Fuente: {data['data_source']}, Precio: {data['price']}")
    return data

# ────────────────────────────────────────────────
# YFINANCE
# ────────────────────────────────────────────────

def get_yfinance_data(ticker_symbol):
    """Obtiene datos de yfinance."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info or {}
        
        hist = ticker.history(period="1y", auto_adjust=True)
        hist_dict = None
        if not hist.empty:
            hist_dict = {
                'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                'open': hist['Open'].tolist(),
                'high': hist['High'].tolist(),
                'low': hist['Low'].tolist(),
                'close': hist['Close'].tolist(),
                'volume': hist['Volume'].tolist()
            }
        
        calendar_list = []
        try:
            calendar = ticker.calendar
            if calendar is not None and not calendar.empty:
                for idx, row in calendar.iterrows():
                    calendar_list.append({
                        'date': str(idx),
                        'eps_est': row.get('Earnings Estimate', 'N/A'),
                        'revenue_est': row.get('Revenue Estimate', 'N/A')
                    })
        except:
            pass
        
        return {
            'info': info,
            'history': hist_dict,
            'calendar': calendar_list,
            'source': 'yfinance'
        }
    except Exception as e:
        debug_log("YFinance error", str(e))
        return None

# ────────────────────────────────────────────────
# MOCK DATA
# ────────────────────────────────────────────────

def get_mock_data(ticker):
    """Datos de demostración."""
    debug_log(f"Usando MOCK DATA para {ticker}")
    
    seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
    base_price = 50 + (seed % 950)
    
    return {
        'ticker': ticker,
        'name': f"{ticker} Corporation",
        'sector': "Technology",
        'industry': "Software",
        'country': "United States",
        'employees': 50000,
        'website': "#",
        'summary': f"{ticker} es una empresa líder en su sector con operaciones globales.",
        'price': float(base_price),
        'prev_close': float(base_price) * 0.98,
        'market_cap': float(base_price) * 1e9 * random.uniform(0.5, 5),
        'volume': 10000000,
        'avg_volume': 12000000,
        'beta': random.uniform(0.8, 2.0),
        'change_pct': 2.0,
        'fifty_two_high': float(base_price) * 1.3,
        'fifty_two_low': float(base_price) * 0.7,
        'pct_from_high': -5.0,
        'eps': float(base_price) / random.uniform(15, 40),
        'pe_trailing': random.uniform(15, 40),
        'pe_forward': random.uniform(15, 35),
        'peg_ratio': random.uniform(0.5, 2.0),
        'price_to_book': random.uniform(2, 10),
        'price_to_sales': random.uniform(3, 15),
        'roe': random.uniform(0.1, 0.4),
        'roa': random.uniform(0.05, 0.2),
        'gross_margin': random.uniform(0.4, 0.8),
        'operating_margin': random.uniform(0.15, 0.35),
        'profit_margin': random.uniform(0.1, 0.25),
        'ebitda_margin': random.uniform(0.2, 0.4),
        'rev_growth': random.uniform(-0.05, 0.3),
        'eps_growth': random.uniform(-0.05, 0.3),
        'cash': float(base_price) * 1e9 * 0.1,
        'debt': float(base_price) * 1e9 * 0.05,
        'free_cashflow': float(base_price) * 1e9 * 0.05,
        'operating_cashflow': float(base_price) * 1e9 * 0.08,
        'debt_to_equity': random.uniform(20, 80),
        'current_ratio': random.uniform(1.0, 3.0),
        'dividend_yield': random.choice([0.0, 0.005, 0.01, 0.02]),
        'payout_ratio': random.uniform(0.1, 0.5),
        'eps_forward': float(base_price) / random.uniform(12, 30),
        'target_mean': float(base_price) * 1.15,
        'target_high': float(base_price) * 1.4,
        'target_low': float(base_price) * 0.9,
        'num_analysts': random.randint(10, 50),
        'recommendation': random.choice(['buy', 'hold', 'buy']),
        'hist': pd.DataFrame(),
        'earnings_calendar': [],
        'data_source': 'mock',
        'is_real_data': False
    }

# ────────────────────────────────────────────────
# FORMATO Y UTILIDADES
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

def format_pct(value, decimals=2):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A", "#888"
    try:
        val = float(value) * 100 if abs(float(value)) < 1 else float(value)
        color = "#00ffad" if val >= 0 else "#f23645"
        return f"{val:.{decimals}f}%", color
    except:
        return "N/A", "#888"

# ────────────────────────────────────────────────
# VISUALIZACIÓN DE EARNINGS
# ────────────────────────────────────────────────

def get_latest_earnings_summary(fmp_data):
    """Extrae el resumen del último earnings report."""
    if not fmp_data:
        return None
    
    income = fmp_data.get('income_statement', [])
    surprises = fmp_data.get('earnings_surprises', [])
    
    if not income or len(income) == 0:
        return None
    
    latest = income[0]
    latest_surprise = surprises[0] if surprises and len(surprises) > 0 else {}
    
    revenue_growth = None
    eps_growth = None
    
    if len(income) >= 5:
        try:
            current_rev = latest.get('revenue', 0)
            current_eps = latest.get('eps', 0)
            yoy = income[4]
            if yoy:
                yoy_rev = yoy.get('revenue', 0)
                yoy_eps = yoy.get('eps', 0)
                if yoy_rev > 0:
                    revenue_growth = ((current_rev - yoy_rev) / yoy_rev) * 100
                if yoy_eps != 0:
                    eps_growth = ((current_eps - yoy_eps) / abs(yoy_eps)) * 100
        except:
            pass
    
    return {
        'date': latest.get('date', 'N/D'),
        'period': latest.get('period', 'N/D'),
        'revenue': latest.get('revenue', 0),
        'net_income': latest.get('netIncome', 0),
        'eps': latest.get('eps', 0),
        'ebitda': latest.get('ebitda', 0),
        'gross_profit': latest.get('grossProfit', 0),
        'operating_income': latest.get('operatingIncome', 0),
        'revenue_growth_yoy': revenue_growth,
        'eps_growth_yoy': eps_growth,
        'eps_surprise_pct': latest_surprise.get('surprisePercentage', 0) if isinstance(latest_surprise, dict) else 0,
        'eps_beat': False
    }

def render_earnings_report_section(data, fmp_data):
    """Renderiza una sección de earnings report estilo profesional."""
    
    if not fmp_data:
        st.info("📊 Datos de FMP no disponibles. Configura FMP_API_KEY en secrets para ver el reporte completo.")
        return
    
    latest = get_latest_earnings_summary(fmp_data)
    
    if not latest:
        st.warning("⚠️ No se pudieron obtener datos recientes de earnings")
        return
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <div style="color: #00ffad; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">
            📅 {latest['date']} • {data['ticker']} Earnings Report
        </div>
        <h2 style="color: white; margin: 0; font-size: 2rem;">
            {data['name']} {latest['period']} Earnings
        </h2>
        <p style="color: #888; margin-top: 10px;">
            {data['sector']} • {data.get('industry', 'N/A')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = latest['revenue']
        rev_growth = latest['revenue_growth_yoy']
        rev_color = "#00ffad" if rev_growth and rev_growth > 0 else "#f23645" if rev_growth and rev_growth < 0 else "#888"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Total Revenue</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${revenue/1e9:.2f}B</div>
            {f'<div style="color: {rev_color}; font-size: 12px; margin-top: 5px;">{"▲" if rev_growth > 0 else "▼"} {abs(rev_growth):.1f}% YoY</div>' if rev_growth else '<div style="color: #666; font-size: 12px;">N/D</div>'}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        eps = latest['eps']
        eps_growth = latest['eps_growth_yoy']
        eps_color = "#00ffad" if eps_growth and eps_growth > 0 else "#f23645"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">EPS</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${eps:.2f}</div>
            {f'<div style="color: {eps_color}; font-size: 12px; margin-top: 5px;">{"▲" if eps_growth > 0 else "▼"} {abs(eps_growth):.1f}% YoY</div>' if eps_growth else ''}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        net_income = latest['net_income']
        margin = (net_income / latest['revenue'] * 100) if latest['revenue'] > 0 else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Net Income</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${net_income/1e6:.0f}M</div>
            <div style="color: #888; font-size: 12px; margin-top: 5px;">{margin:.1f}% Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        ebitda = latest['ebitda']
        ebitda_margin = (ebitda / latest['revenue'] * 100) if latest['revenue'] > 0 else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">EBITDA</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${ebitda/1e6:.0f}M</div>
            <div style="color: #888; font-size: 12px; margin-top: 5px;">{ebitda_margin:.1f}% Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráfico histórico
    st.markdown("---")
    render_earnings_history_chart(fmp_data)
    
    # Forward guidance
    st.markdown("---")
    render_forward_guidance(fmp_data, data)

def render_earnings_history_chart(fmp_data):
    """Renderiza gráfico histórico de revenue y EPS."""
    income = fmp_data.get('income_statement', [])
    
    if not income or len(income) < 2:
        st.info("📊 Datos históricos insuficientes")
        return
    
    dates = []
    revenues = []
    eps_values = []
    
    for i in reversed(income[:8]):
        dates.append(i.get('date', ''))
        revenues.append(i.get('revenue', 0) / 1e9)
        eps_values.append(i.get('eps', 0))
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=dates,
            y=revenues,
            name='Revenue (B$)',
            marker_color='#2a3f5f',
            opacity=0.8
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=eps_values,
            name='EPS ($)',
            mode='lines+markers',
            line=dict(color='#00ffad', width=3),
            marker=dict(size=8, color='#00ffad', symbol='diamond')
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title="📈 Revenue & EPS History (Quarterly)",
        template="plotly_dark",
        plot_bgcolor='#0c0e12',
        paper_bgcolor='#11141a',
        font=dict(color='white', size=11),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='x unified'
    )
    
    fig.update_xaxes(gridcolor='#1a1e26', showgrid=True, tickangle=-45)
    fig.update_yaxes(title_text="Revenue (Billions $)", secondary_y=False, gridcolor='#1a1e26')
    fig.update_yaxes(title_text="EPS ($)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

def render_forward_guidance(fmp_data, data):
    """Renderiza sección de forward guidance."""
    
    estimates = fmp_data.get('analyst_estimates', [])
    calendar = fmp_data.get('earnings_calendar', [])
    
    st.markdown("### 🎯 Forward Guidance & Expectativas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(0,255,173,0.1) 0%, rgba(0,255,173,0.02) 100%); border: 1px solid #00ffad33; border-radius: 12px; padding: 20px;">
            <div style="color: #00ffad; font-size: 14px; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center;">
                <span style="margin-right: 8px;">📈</span> Expectativas Positivas
            </div>
            <ul style="color: #ccc; line-height: 1.8; margin: 0; padding-left: 20px;">
        """, unsafe_allow_html=True)
        
        positive_points = []
        
        if estimates and len(estimates) > 1:
            next_eps = estimates[0].get('estimatedEps', 0)
            curr_eps = estimates[1].get('estimatedEps', next_eps)
            if next_eps > curr_eps:
                positive_points.append(f"Crecimiento EPS esperado: ${curr_eps:.2f} → ${next_eps:.2f}")
        
        income = fmp_data.get('income_statement', [])
        if income and len(income) >= 2:
            latest_rev = income[0].get('revenue', 0)
            prev_rev = income[1].get('revenue', 0)
            if latest_rev > prev_rev:
                growth = ((latest_rev - prev_rev) / prev_rev) * 100
                positive_points.append(f"Momentum revenue: +{growth:.1f}% vs trimestre anterior")
        
        if data.get('rev_growth') and data['rev_growth'] > 0.1:
            positive_points.append(f"Fuerte crecimiento anual de ingresos ({data['rev_growth']:.1%})")
        
        if not positive_points:
            positive_points = [
                "Tendencia de crecimiento en segmentos clave",
                "Mejoras operativas esperadas",
                "Demanda sostenida en mercados principales"
            ]
        
        for point in positive_points[:4]:
            st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(242,54,69,0.1) 0%, rgba(242,54,69,0.02) 100%); border: 1px solid #f2364533; border-radius: 12px; padding: 20px;">
            <div style="color: #f23645; font-size: 14px; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center;">
                <span style="margin-right: 8px;">⚠️</span> Riesgos a Monitorear
            </div>
            <ul style="color: #ccc; line-height: 1.8; margin: 0; padding-left: 20px;">
        """, unsafe_allow_html=True)
        
        risk_points = []
        
        if data.get('beta') and data['beta'] > 1.5:
            risk_points.append(f"Alta volatilidad (Beta: {data['beta']:.2f})")
        
        if data.get('pe_forward') and data['pe_forward'] > 30:
            risk_points.append(f"Valoración exigente (P/E Forward: {data['pe_forward']:.1f}x)")
        
        if not risk_points:
            risk_points = [
                "Incertidumbre macroeconómica global",
                "Presión competitiva en el sector",
                "Volatilidad en costos de materiales"
            ]
        
        for point in risk_points[:4]:
            st.markdown(f"<li>{point}</li>", unsafe_allow_html=True)
        
        st.markdown("</ul></div>", unsafe_allow_html=True)
    
    if calendar:
        st.markdown("---")
        st.markdown("#### 📅 Próximos Earnings")
        
        cols = st.columns(min(len(calendar), 3))
        for i, (col, event) in enumerate(zip(cols, calendar[:3])):
            with col:
                eps_est = event.get('epsEstimated', 'TBA')
                rev_est = event.get('revenueEstimated', 0)
                date = event.get('date', 'TBA')
                
                st.markdown(f"""
                <div style="background: #0c0e12; border: 1px solid #2a3f5f; border-radius: 8px; padding: 15px; text-align: center;">
                    <div style="color: #00ffad; font-size: 11px; font-weight: bold; margin-bottom: 5px;">{date}</div>
                    <div style="color: white; font-size: 16px; font-weight: bold; margin: 5px 0;">EPS Est: ${eps_est}</div>
                    {f'<div style="color: #888; font-size: 11px;">Rev Est: ${rev_est/1e9:.2f}B</div>' if isinstance(rev_est, (int, float)) and rev_est > 0 else ''}
                </div>
                """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ANÁLISIS RSU CON IA
# ────────────────────────────────────────────────

def load_rsu_prompt():
    """Carga el prompt de análisis."""
    try:
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'earnings.txt'),
            os.path.join(os.path.dirname(__file__), 'earnings.txt'),
            os.path.join(os.getcwd(), 'earnings.txt'),
            'earnings.txt',
        ]
        
        for prompt_path in possible_paths:
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        return content
        
        return get_embedded_prompt()
    except Exception as e:
        return get_embedded_prompt()

def get_embedded_prompt():
    return """Eres un analista de hedge fund senior. Analiza la empresa usando estos datos:

{datos_ticker}

Genera un análisis fundamental completo en español con todas las secciones requeridas.
Fecha actual: {current_date}"""

def render_rsu_earnings_analysis(data, fmp_data=None):
    """Renderiza el análisis con IA."""
    
    base_prompt = load_rsu_prompt()
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    datos_ticker = f"""=== DATOS DEL TICKER ===
TICKER: {data['ticker']}
COMPANY: {data['name']}
SECTOR: {data.get('sector', 'N/A')}
INDUSTRY: {data.get('industry', 'N/A')}

=== DATOS DE MERCADO ===
PRICE: ${data['price']:.2f} | CHANGE: {data.get('change_pct', 0):+.2f}% | MARKET_CAP: {format_value(data['market_cap'], '$')}
VOLUME: {format_value(data['volume'], '', '', 0)} | BETA: {data.get('beta', 'N/A')}
52W_RANGE: ${data.get('fifty_two_low', 0):.2f}-${data.get('fifty_two_high', 0):.2f}

=== VALORACIÓN ===
P/E_TRAILING: {format_value(data.get('pe_trailing'), '', 'x', 2)} | P/E_FORWARD: {format_value(data.get('pe_forward'), '', 'x', 2)}
PEG_RATIO: {format_value(data.get('peg_ratio'), '', '', 2)} | ROE: {format_value(data.get('roe'), '', '%', 2)}

=== MÁRGENES ===
GROSS_MARGIN: {format_value(data.get('gross_margin'), '', '%', 2)} | OPERATING_MARGIN: {format_value(data.get('operating_margin'), '', '%', 2)}
EBITDA_MARGIN: {format_value(data.get('ebitda_margin'), '', '%', 2)} | PROFIT_MARGIN: {format_value(data.get('profit_margin'), '', '%', 2)}

=== BALANCE ===
CASH: {format_value(data.get('cash'), '$')} | DEBT: {format_value(data.get('debt'), '$')}
FREE_CASH_FLOW: {format_value(data.get('free_cashflow'), '$')} | DEBT_TO_EQUITY: {format_value(data.get('debt_to_equity'), '', '%', 2)}

=== FECHA ===
{current_date}
"""
    
    prompt_completo = base_prompt.replace("{datos_ticker}", datos_ticker).replace("{current_date}", current_date)
    
    model, name, err = get_ia_model()
    
    if not model:
        st.info("🤖 IA no configurada.")
        return
    
    try:
        with st.spinner("🧠 Generando análisis..."):
            response = model.generate_content(
                prompt_completo,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 8192,
                }
            )
            
            st.markdown("""
            <style>
            .terminal-box {
                background-color: #0c0e12;
                border: 1px solid #00ffad;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                margin: 20px 0;
            }
            .terminal-header {
                background: linear-gradient(90deg, #00ffad22 0%, #00ffad11 100%);
                border-bottom: 1px solid #00ffad;
                padding: 12px 16px;
            }
            .terminal-title {
                color: #00ffad;
                font-size: 13px;
                font-weight: bold;
                text-transform: uppercase;
            }
            .terminal-body {
                padding: 20px;
                color: #e0e0e0;
                line-height: 1.6;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="terminal-box">
                <div class="terminal-header">
                    <span class="terminal-title">RSU Hedge Fund Analysis Terminal</span>
                </div>
                <div class="terminal-body">
            """, unsafe_allow_html=True)
            
            st.markdown(response.text)
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"❌ Error en generación: {e}")

# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────

def render():
    st.set_page_config(page_title="RSU Earnings", layout="wide")
    
    st.markdown("""
    <style>
        .stApp { background-color: #0c0e12; color: white; }
        .stTextInput > div > div > input { background-color: #1a1e26; color: white; border: 1px solid #2a3f5f; }
        .stButton > button { background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); color: #0c0e12; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Análisis de Earnings")
    st.markdown('<div style="color: #888; margin-bottom: 20px;">Análisis fundamental con IA y datos en tiempo real</div>', unsafe_allow_html=True)
    
    # Verificar FMP_API_KEY
    fmp_key = st.secrets.get("FMP_API_KEY", "")
    if not fmp_key:
        st.warning("⚠️ **FMP_API_KEY no configurado**. Agrega tu API key en Settings > Secrets.")
    
    # Input
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 Analizar", use_container_width=True)
    
    if analyze and ticker:
        # Debug expander
        debug_expander = st.expander("🔧 Ver log de debugging", expanded=False)
        log_container = debug_expander.empty()
        logs = []
        
        class LogCapture:
            def write(self, msg):
                if msg.strip():
                    logs.append(msg.strip())
                    log_container.code('\n'.join(logs[-50:]), language='text')
        
        import sys
        old_stdout = sys.stdout
        sys.stdout = LogCapture()
        
        try:
            with st.spinner("Cargando datos..."):
                # Obtener datos
                fmp_data = get_fmp_data(ticker, fmp_key) if fmp_key else None
                yf_data = get_yfinance_data(ticker)
                
                # Procesar
                data = process_combined_data(ticker, fmp_data, yf_data)
                
                if not data:
                    st.error("❌ No se pudieron obtener datos válidos de ninguna fuente.")
                    data = get_mock_data(ticker)
                    st.warning("⚠️ Usando datos de demostración.")
        finally:
            sys.stdout = old_stdout
        
        # Mostrar datos
        st.divider()
        
        # Indicador de fuente
        source_colors = {'fmp': '🟢', 'yfinance': '🟡', 'mock': '🔴'}
        source_names = {'fmp': 'FMP API (Datos Completos)', 'yfinance': 'Yahoo Finance (Precios)', 'mock': 'Demo'}
        
        col_info, col_price = st.columns([2, 1])
        
        with col_info:
            st.markdown(f"""
            **{source_colors.get(data['data_source'], '⚪')} Fuente:** {source_names.get(data['data_source'], 'Desconocida')}
            
            ### {data['name']} ({data['ticker']})
            {data.get('sector', 'N/A')} • {data.get('industry', 'N/A')} • {data.get('country', 'N/A')}
            """)
        
        with col_price:
            change_color = "#00ffad" if data.get('change_pct', 0) >= 0 else "#f23645"
            st.markdown(f"""
            <div style="text-align: right;">
                <div style="font-size: 2.5rem; font-weight: bold; color: white;">${data['price']:.2f}</div>
                <div style="color: {change_color}; font-size: 1.2rem; font-weight: 600;">{data.get('change_pct', 0):+.2f}%</div>
                <div style="color: #666; font-size: 11px; margin-top: 5px;">
                    Cap: {format_value(data['market_cap'], '$')} | Vol: {format_value(data['volume'], '', '', 0)}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Sección Earnings Report
        st.markdown("---")
        render_earnings_report_section(data, fmp_data)
        
        # Métricas Fundamentales
        st.markdown("---")
        st.markdown("### 📊 Métricas Fundamentales")
        
        if data['data_source'] == 'mock':
            st.error("⚠️ **Datos de demostración.** Configura FMP_API_KEY para datos reales.")
        
        cols = st.columns(4)
        metrics_display = [
            ("Crec. Ingresos", data.get('rev_growth'), True),
            ("Margen EBITDA", data.get('ebitda_margin'), True),
            ("ROE", data.get('roe'), True),
            ("P/E Forward", data.get('pe_forward'), False),
        ]
        
        for col, (label, value, is_pct) in zip(cols, metrics_display):
            with col:
                if is_pct and value is not None and value != 0:
                    formatted, color = format_pct(value)
                elif value is not None and value != 0:
                    formatted = format_value(value, '', 'x' if 'P/E' in label else '', 1)
                    color = "#00ffad"
                else:
                    formatted = "N/A"
                    color = "#666"
                
                is_real = value is not None and value != 0
                
                st.markdown(f"""
                <div style="background: {'#0c0e12' if is_real else '#1a1e26'}; 
                            border: 1px solid {'#00ffad33' if is_real else '#f2364533'}; 
                            border-radius: 10px; padding: 20px; text-align: center;
                            {'opacity: 0.6;' if not is_real else ''}">
                    <div style="color: #666; font-size: 10px; text-transform: uppercase; margin-bottom: 8px;">{label}</div>
                    <div style="color: {color}; font-size: 1.5rem; font-weight: bold;">{formatted}</div>
                    {f'<div style="color: #00ffad; font-size: 9px; margin-top: 5px;">● Real</div>' if is_real else f'<div style="color: #f23645; font-size: 9px; margin-top: 5px;">○ No disponible</div>'}
                </div>
                """, unsafe_allow_html=True)
        
        # Gráfico y métricas clave
        st.markdown("---")
        col_chart, col_info = st.columns([3, 2])
        
        with col_chart:
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
                    height=400, margin=dict(l=30, r=30, t=30, b=30),
                    title="Precio (1 año)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Gráfico no disponible")
        
        with col_info:
            st.markdown("#### 📋 Sobre la Empresa")
            st.markdown(f"<div style='color: #aaa; font-size: 13px; line-height: 1.6;'>{data.get('summary', 'N/A')[:300]}...</div>", unsafe_allow_html=True)
            
            st.markdown("#### 💰 Métricas Clave")
            
            metrics = [
                ("Cash", data.get('cash'), "#00ffad"),
                ("Deuda", data.get('debt'), "#f23645"),
                ("FCF", data.get('free_cashflow'), "#00ffad" if data.get('free_cashflow', 0) > 0 else "#f23645"),
                ("Beta", data.get('beta'), "white"),
            ]
            
            for label, value, color in metrics:
                val_str = format_value(value, '$') if label != "Beta" else f"{value:.2f}"
                is_na = val_str == "N/A" or val_str == "0.00"
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1a1e26;">
                    <span style="color: #666;">{label}:</span>
                    <span style="color: {'#666' if is_na else color}; font-weight: bold;">{val_str}</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Análisis RSU
        st.markdown("---")
        render_rsu_earnings_analysis(data, fmp_data)
        
        # Footer
        st.markdown(f"""
        <div style="text-align: center; color: #444; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a1e26;">
            RSU Dashboard Pro • Datos: FMP + Yahoo Finance • {datetime.now().year}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
