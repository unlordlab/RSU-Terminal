

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
# ALPHA VANTAGE API - DATOS FUNDAMENTALES
# ────────────────────────────────────────────────

def get_alpha_vantage_data(ticker, api_key):
    """Obtiene datos fundamentales de Alpha Vantage."""
    if not api_key:
        debug_log("ERROR: ALPHA_VANTAGE_API_KEY no proporcionada")
        return None
    
    base_url = "https://www.alphavantage.co/query"
    result = {}
    
    endpoints = {
        'overview': {'function': 'OVERVIEW', 'symbol': ticker},
        'income': {'function': 'INCOME_STATEMENT', 'symbol': ticker},
        'balance': {'function': 'BALANCE_SHEET', 'symbol': ticker},
        'cashflow': {'function': 'CASH_FLOW', 'symbol': ticker},
        'earnings': {'function': 'EARNINGS', 'symbol': ticker},
    }
    
    debug_log(f"Iniciando solicitudes Alpha Vantage para {ticker}")
    
    for name, params in endpoints.items():
        try:
            params['apikey'] = api_key
            debug_log(f"Solicitando {name}")
            
            response = requests.get(base_url, params=params, timeout=20)
            debug_log(f"{name} status", response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar si hay error de límite de requests
                if 'Note' in data:
                    debug_log(f"{name} LÍMITE ALCANZADO", data['Note'])
                    result[name] = {}
                elif 'Information' in data:
                    debug_log(f"{name} INFO", data['Information'])
                    result[name] = {}
                else:
                    result[name] = data
                    debug_log(f"{name} OK", f"Keys: {list(data.keys())[:5]}")
            else:
                debug_log(f"{name} ERROR", f"Status {response.status_code}")
                result[name] = {}
                
            # Alpha Vantage tiene límite de 5 requests por minuto en plan gratuito
            if name != 'earnings':  # No esperar después del último
                time.sleep(12)  # 12 segundos entre requests = 5 por minuto
                
        except Exception as e:
            debug_log(f"{name} EXCEPTION", str(e))
            result[name] = {}
    
    # Verificar si tenemos datos mínimos
    if not result.get('overview') or len(result.get('overview', {})) == 0:
        debug_log("ERROR CRÍTICO: No se obtuvo overview")
        return None
    
    return {
        'overview': result.get('overview', {}),
        'income_statement': result.get('income', {}),
        'balance_sheet': result.get('balance', {}),
        'cash_flow': result.get('cashflow', {}),
        'earnings': result.get('earnings', {}),
        'source': 'alpha_vantage',
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# ────────────────────────────────────────────────
# EXTRACCIÓN DE DATOS ALPHA VANTAGE
# ────────────────────────────────────────────────

def safe_float(value):
    """Convierte a float de manera segura."""
    if value is None or value == '' or value == 'None' or value == 'N/A':
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_int(value):
    """Convierte a int de manera segura."""
    if value is None or value == '' or value == 'None' or value == 'N/A':
        return 0
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0

def extract_fundamentals_from_av(av_data):
    """Extrae métricas de Alpha Vantage."""
    if not av_data:
        debug_log("extract_fundamentals: av_data es None")
        return {}
    
    debug_log("Iniciando extracción de fundamentos Alpha Vantage")
    f = {}
    
    try:
        # Overview - datos generales y ratios
        overview = av_data.get('overview', {})
        debug_log("Overview keys", list(overview.keys())[:10])
        
        f['name'] = overview.get('Name', 'Unknown')
        f['sector'] = overview.get('Sector', 'N/A')
        f['industry'] = overview.get('Industry', 'N/A')
        f['country'] = overview.get('Country', 'N/A')
        f['employees'] = safe_int(overview.get('FullTimeEmployees'))
        f['website'] = overview.get('OfficialSite', '#')
        f['summary'] = overview.get('Description', f"Empresa {f.get('name', '')}")
        f['exchange'] = overview.get('Exchange', 'N/A')
        
        # Ratios de valoración
        f['pe_trailing'] = safe_float(overview.get('TrailingPE'))
        f['pe_forward'] = safe_float(overview.get('ForwardPE'))
        f['peg_ratio'] = safe_float(overview.get('PEGRatio'))
        f['price_to_book'] = safe_float(overview.get('PriceToBookRatio'))
        f['price_to_sales'] = safe_float(overview.get('PriceToSalesRatioTTM'))
        
        # Márgenes
        f['gross_margin'] = safe_float(overview.get('GrossProfitTTM')) / safe_float(overview.get('RevenueTTM')) if overview.get('RevenueTTM') else 0
        f['operating_margin'] = safe_float(overview.get('OperatingMarginTTM'))
        f['profit_margin'] = safe_float(overview.get('ProfitMargin'))
        f['ebitda_margin'] = safe_float(overview.get('EBITDA')) / safe_float(overview.get('RevenueTTM')) if overview.get('RevenueTTM') else 0
        
        # Rentabilidad
        f['roe'] = safe_float(overview.get('ReturnOnEquityTTM'))
        f['roa'] = safe_float(overview.get('ReturnOnAssetsTTM'))
        
        # Crecimiento
        f['rev_growth'] = safe_float(overview.get('QuarterlyRevenueGrowthYOY'))
        f['eps_growth'] = safe_float(overview.get('QuarterlyEarningsGrowthYOY'))
        
        # Dividendos
        f['dividend_yield'] = safe_float(overview.get('DividendYield'))
        f['payout_ratio'] = safe_float(overview.get('PayoutRatio'))
        
        # Beta
        f['beta'] = safe_float(overview.get('Beta'))
        
        # EPS
        f['eps'] = safe_float(overview.get('EPS'))
        f['eps_forward'] = safe_float(overview.get('ForwardEPS'))
        
        debug_log("Overview procesado", f"Name: {f['name']}, P/E: {f['pe_trailing']}, ROE: {f['roe']}")
        
        # Balance Sheet (último trimestre)
        balance = av_data.get('balance_sheet', {})
        balance_reports = balance.get('quarterlyReports', [])
        
        if balance_reports and len(balance_reports) > 0:
            b = balance_reports[0]
            debug_log("Balance sheet", f"Fecha: {b.get('fiscalDateEnding')}")
            f['cash'] = safe_float(b.get('cashAndCashEquivalentsAtCarryingValue'))
            f['debt'] = safe_float(b.get('shortLongTermDebtTotal') or b.get('longTermDebt'))
            f['total_equity'] = safe_float(b.get('totalShareholderEquity'))
            f['total_assets'] = safe_float(b.get('totalAssets'))
            
            # Calcular debt_to_equity
            if f['total_equity'] > 0:
                f['debt_to_equity'] = (f['debt'] / f['total_equity']) * 100
            
            # Current ratio
            current_assets = safe_float(b.get('totalCurrentAssets'))
            current_liabilities = safe_float(b.get('totalCurrentLiabilities'))
            if current_liabilities > 0:
                f['current_ratio'] = current_assets / current_liabilities
        
        # Cash Flow
        cashflow = av_data.get('cash_flow', {})
        cf_reports = cashflow.get('quarterlyReports', [])
        
        if cf_reports and len(cf_reports) > 0:
            c = cf_reports[0]
            debug_log("Cash flow", f"Fecha: {c.get('fiscalDateEnding')}")
            f['operating_cashflow'] = safe_float(c.get('operatingCashflow'))
            capex = safe_float(c.get('capitalExpenditures'))
            if f['operating_cashflow'] and capex:
                f['free_cashflow'] = f['operating_cashflow'] - capex
        
        # Income Statement para revenue histórico
        income = av_data.get('income_statement', {})
        income_reports = income.get('quarterlyReports', [])
        
        if income_reports and len(income_reports) > 0:
            latest = income_reports[0]
            f['latest_revenue'] = safe_float(latest.get('totalRevenue'))
            f['latest_net_income'] = safe_float(latest.get('netIncome'))
            f['latest_ebitda'] = safe_float(latest.get('ebitda'))
            
            # Calcular crecimiento YoY si hay datos
            if len(income_reports) >= 5:
                current_rev = safe_float(income_reports[0].get('totalRevenue'))
                yoy_rev = safe_float(income_reports[4].get('totalRevenue'))
                if yoy_rev > 0:
                    f['rev_growth_calculated'] = (current_rev - yoy_rev) / yoy_rev
        
        # Earnings (EPS histórico)
        earnings = av_data.get('earnings', {})
        earnings_reports = earnings.get('quarterlyEarnings', [])
        
        if earnings_reports and len(earnings_reports) > 0:
            f['eps_history'] = earnings_reports
        
        # Analyst targets (de overview)
        f['target_mean'] = safe_float(overview.get('AnalystTargetPrice'))
        f['num_analysts'] = safe_int(overview.get('AnalystRatingStrongBuy')) + safe_int(overview.get('AnalystRatingBuy')) + safe_int(overview.get('AnalystRatingHold')) + safe_int(overview.get('AnalystRatingSell')) + safe_int(overview.get('AnalystRatingStrongSell'))
        
        debug_log("Extracción AV completada", f"Campos: {len(f)}")
        
    except Exception as e:
        debug_log("ERROR en extracción AV", str(e))
        debug_log("Traceback", traceback.format_exc())
    
    return f

# ────────────────────────────────────────────────
# YFINANCE (precios en tiempo real)
# ────────────────────────────────────────────────

def get_yfinance_data(ticker_symbol):
    """Obtiene datos de precios de yfinance."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info or {}
        
        # Datos de precios
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
        
        # Datos adicionales que YF proporciona bien
        yf_data = {
            'price': info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose'),
            'prev_close': info.get('previousClose'),
            'market_cap': info.get('marketCap'),
            'volume': info.get('volume'),
            'avg_volume': info.get('averageVolume'),
            'change_pct': info.get('regularMarketChangePercent'),
            'fifty_two_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_low': info.get('fiftyTwoWeekLow'),
            'beta': info.get('beta'),
        }
        
        return {
            'info': info,
            'yf_specific': yf_data,
            'history': hist_dict,
            'source': 'yfinance'
        }
    except Exception as e:
        debug_log("YFinance error", str(e))
        return None

# ────────────────────────────────────────────────
# PROCESAMIENTO DE DATOS COMBINADO
# ────────────────────────────────────────────────

def process_combined_data(ticker, av_data, yf_data):
    """Combina datos de Alpha Vantage y Yahoo Finance."""
    debug_log("Iniciando process_combined_data")
    
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
        'num_analysts': 0,
        'hist': pd.DataFrame(),
        'earnings_calendar': [],
        'data_source': 'none',
        'is_real_data': False
    }
    
    # 1. Procesar Alpha Vantage (fundamentales)
    if av_data:
        debug_log("Procesando datos Alpha Vantage")
        av_fund = extract_fundamentals_from_av(av_data)
        
        if av_fund and av_fund.get('name') != 'Unknown':
            debug_log("Alpha Vantage tiene datos válidos")
            
            for key, value in av_fund.items():
                if value is not None and value != 0 and value != '':
                    if key in data:
                        data[key] = value
            
            data['data_source'] = 'alpha_vantage'
            data['is_real_data'] = True
            debug_log("Datos AV aplicados", f"Name: {data['name']}, ROE: {data['roe']}, P/E: {data['pe_trailing']}")
        else:
            debug_log("Alpha Vantage no tiene datos válidos")
    
    # 2. Procesar Yahoo Finance (precios en tiempo real + histórico)
    if yf_data:
        debug_log("Procesando datos Yahoo Finance")
        
        # Usar precios de YF (más actualizados)
        yf_specific = yf_data.get('yf_specific', {})
        
        # Priorizar precios de YF sobre AV
        if yf_specific.get('price'):
            data['price'] = float(yf_specific['price'])
            data['prev_close'] = float(yf_specific.get('prev_close') or yf_specific['price'])
            data['market_cap'] = float(yf_specific.get('market_cap') or 0)
            data['volume'] = int(yf_specific.get('volume') or 0)
            data['avg_volume'] = int(yf_specific.get('avg_volume') or 0)
            data['change_pct'] = float(yf_specific.get('change_pct') or 0)
            data['fifty_two_high'] = float(yf_specific.get('fifty_two_high') or 0)
            data['fifty_two_low'] = float(yf_specific.get('fifty_two_low') or 0)
            data['beta'] = float(yf_specific.get('beta') or 0)
            
            if data['data_source'] == 'none':
                data['data_source'] = 'yfinance'
            
            debug_log("Precios YF aplicados", f"Price: {data['price']}")
        
        # Histórico de precios
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
    
    # 3. Calcular campos derivados
    if data['price'] > 0 and data['prev_close'] > 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
    
    if data['price'] > 0 and data.get('fifty_two_high', 0) > 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    
    # 4. Validación final
    if data['price'] == 0:
        debug_log("ERROR: Precio sigue siendo 0")
        return None
    
    debug_log("Datos procesados exitosamente", f"Fuente: {data['data_source']}")
    return data

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
        'summary': f"{ticker} es una empresa líder en su sector.",
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
        'recommendation': 'buy',
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

def render_earnings_section(data, av_data):
    """Renderiza sección de earnings con datos de Alpha Vantage."""
    
    if not av_data:
        st.info("📊 Datos fundamentales no disponibles.")
        return
    
    # Extraer reports de income statement
    income = av_data.get('income_statement', {})
    income_reports = income.get('quarterlyReports', [])
    
    if not income_reports or len(income_reports) == 0:
        st.warning("⚠️ No hay datos de income statement")
        return
    
    latest = income_reports[0]
    
    # Calcular crecimiento YoY
    revenue_growth = None
    if len(income_reports) >= 5:
        try:
            current = safe_float(income_reports[0].get('totalRevenue'))
            yoy = safe_float(income_reports[4].get('totalRevenue'))
            if yoy > 0:
                revenue_growth = ((current - yoy) / yoy) * 100
        except:
            pass
    
    revenue = safe_float(latest.get('totalRevenue'))
    net_income = safe_float(latest.get('netIncome'))
    ebitda = safe_float(latest.get('ebitda'))
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <div style="color: #00ffad; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px;">
            📅 {latest.get('fiscalDateEnding', 'N/D')} • {data['ticker']} Financials
        </div>
        <h2 style="color: white; margin: 0; font-size: 2rem;">
            {data['name']}
        </h2>
        <p style="color: #888; margin-top: 10px;">
            {data['sector']} • {data.get('industry', 'N/A')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        rev_color = "#00ffad" if revenue_growth and revenue_growth > 0 else "#f23645" if revenue_growth and revenue_growth < 0 else "#888"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Total Revenue (TTM)</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${revenue/1e9:.2f}B</div>
            {f'<div style="color: {rev_color}; font-size: 12px; margin-top: 5px;">{"▲" if revenue_growth > 0 else "▼"} {abs(revenue_growth):.1f}% YoY</div>' if revenue_growth else ''}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">Net Income</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${net_income/1e6:.0f}M</div>
            <div style="color: #888; font-size: 12px; margin-top: 5px;">{(net_income/revenue*100):.1f}% Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">EBITDA</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${ebitda/1e6:.0f}M</div>
            <div style="color: #888; font-size: 12px; margin-top: 5px;">{(ebitda/revenue*100):.1f}% Margin</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        eps = data.get('eps', 0)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%); border: 1px solid #2a3f5f; border-radius: 12px; padding: 20px; text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; margin-bottom: 8px;">EPS (TTM)</div>
            <div style="color: white; font-size: 1.8rem; font-weight: bold;">${eps:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráfico histórico
    st.markdown("---")
    
    if len(income_reports) >= 2:
        dates = []
        revenues = []
        
        for i in reversed(income_reports[:8]):
            dates.append(i.get('fiscalDateEnding', ''))
            revenues.append(safe_float(i.get('totalRevenue')) / 1e9)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates,
            y=revenues,
            name='Revenue',
            marker_color='#00ffad',
            opacity=0.8
        ))
        
        fig.update_layout(
            title="📈 Revenue History (Quarterly)",
            template="plotly_dark",
            plot_bgcolor='#0c0e12',
            paper_bgcolor='#11141a',
            font=dict(color='white'),
            height=400,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        fig.update_xaxes(gridcolor='#1a1e26', tickangle=-45)
        fig.update_yaxes(gridcolor='#1a1e26', title_text="Revenue (Billions $)")
        
        st.plotly_chart(fig, use_container_width=True)

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
    except:
        return get_embedded_prompt()

def get_embedded_prompt():
    return """Eres un analista de hedge fund senior. Analiza la empresa usando estos datos:

{datos_ticker}

Genera un análisis fundamental completo en español con:
1. Snapshot ejecutivo
2. Valoración relativa (P/E, PEG, etc.)
3. Calidad del negocio (márgenes, ROE)
4. Salud financiera (cash, deuda)
5. Catalysts y riesgos
6. Bull/Bear case
7. Score /10 y recomendación

Fecha actual: {current_date}"""

def render_rsu_analysis(data):
    """Renderiza el análisis con IA."""
    
    base_prompt = load_rsu_prompt()
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    datos_ticker = f"""TICKER: {data['ticker']}
COMPANY: {data['name']}
SECTOR: {data.get('sector', 'N/A')} | INDUSTRY: {data.get('industry', 'N/A')}

MERCADO:
Precio: ${data['price']:.2f} | Cambio: {data.get('change_pct', 0):+.2f}%
Market Cap: {format_value(data['market_cap'], '$')} | Beta: {data.get('beta', 'N/A')}

VALORACIÓN:
P/E Trailing: {format_value(data.get('pe_trailing'), '', 'x', 2)}
P/E Forward: {format_value(data.get('pe_forward'), '', 'x', 2)}
PEG: {format_value(data.get('peg_ratio'), '', '', 2)}
P/B: {format_value(data.get('price_to_book'), '', 'x', 2)}

RENTABILIDAD:
ROE: {format_value(data.get('roe'), '', '%', 2)}
ROA: {format_value(data.get('roa'), '', '%', 2)}
Margen Neto: {format_value(data.get('profit_margin'), '', '%', 2)}
Margen EBITDA: {format_value(data.get('ebitda_margin'), '', '%', 2)}

CRECIMIENTO:
Crec. Ingresos: {format_value(data.get('rev_growth'), '', '%', 2)}
Crec. EPS: {format_value(data.get('eps_growth'), '', '%', 2)}

BALANCE:
Cash: {format_value(data.get('cash'), '$')}
Deuda: {format_value(data.get('debt'), '$')}
FCF: {format_value(data.get('free_cashflow'), '$')}
Deuda/Patrimonio: {format_value(data.get('debt_to_equity'), '', '%', 2)}

FECHA: {current_date}
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
                generation_config={"temperature": 0.2, "max_output_tokens": 8192}
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
    st.markdown('<div style="color: #888; margin-bottom: 20px;">Datos fundamentales por Alpha Vantage + Precios por Yahoo Finance</div>', unsafe_allow_html=True)
    
    # Verificar API keys
    av_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")
    if not av_key:
        st.warning("⚠️ **ALPHA_VANTAGE_API_KEY no configurada**")
        st.info("💡 Obtén tu API key gratuita en: https://www.alphavantage.co/support/#api-key")
        st.info("⏱️ Plan gratuito: 5 requests por minuto, 500 por día")
    
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
                    log_container.code('\n'.join(logs[-100:]), language='text')
        
        old_stdout = sys.stdout
        sys.stdout = LogCapture()
        
        try:
            with st.spinner("Cargando datos (esto puede tomar 1 minuto por el límite de Alpha Vantage)..."):
                # Alpha Vantage (fundamentales)
                av_data = get_alpha_vantage_data(ticker, av_key) if av_key else None
                
                # Yahoo Finance (precios en tiempo real)
                yf_data = get_yfinance_data(ticker)
                
                # Procesar
                data = process_combined_data(ticker, av_data, yf_data)
                
                if not data:
                    st.error("❌ No se pudieron obtener datos válidos.")
                    data = get_mock_data(ticker)
                    st.warning("⚠️ Usando datos de demostración.")
        finally:
            sys.stdout = old_stdout
        
        # Mostrar resultados
        st.divider()
        
        source_colors = {'alpha_vantage': '🟢', 'yfinance': '🟡', 'mock': '🔴'}
        source_names = {'alpha_vantage': 'Alpha Vantage + YF', 'yfinance': 'Yahoo Finance', 'mock': 'Demo'}
        
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
                <div style="color: {change_color}; font-size: 1.2rem;">{data.get('change_pct', 0):+.2f}%</div>
                <div style="color: #666; font-size: 11px;">Cap: {format_value(data['market_cap'], '$')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Sección Earnings
        st.markdown("---")
        render_earnings_section(data, av_data)
        
        # Métricas Fundamentales
        st.markdown("---")
        st.markdown("### 📊 Métricas Fundamentales")
        
        if data['data_source'] == 'mock':
            st.error("⚠️ Datos de demostración. Configura ALPHA_VANTAGE_API_KEY.")
        
        cols = st.columns(4)
        metrics_display = [
            ("Crec. Ingresos", data.get('rev_growth'), True),
            ("Margen Neto", data.get('profit_margin'), True),
            ("ROE", data.get('roe'), True),
            ("P/E Trailing", data.get('pe_trailing'), False),
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
        
        with col_info:
            st.markdown("#### 📋 Sobre la Empresa")
            st.markdown(f"<div style='color: #aaa; font-size: 13px;'>{data.get('summary', 'N/A')[:300]}...</div>", unsafe_allow_html=True)
            
            st.markdown("#### 💰 Métricas Clave")
            
            metrics = [
                ("Cash", data.get('cash'), "#00ffad"),
                ("Deuda", data.get('debt'), "#f23645"),
                ("FCF", data.get('free_cashflow'), "#00ffad"),
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
        render_rsu_analysis(data)
        
        # Footer
        st.markdown(f"""
        <div style="text-align: center; color: #444; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a1e26;">
            RSU Dashboard Pro • Alpha Vantage + Yahoo Finance • {datetime.now().year}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    render()
