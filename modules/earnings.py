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
import html

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
                
            if name != 'earnings':
                time.sleep(12)
                
        except Exception as e:
            debug_log(f"{name} EXCEPTION", str(e))
            result[name] = {}
    
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
        
        # Institutional data
        f['institutional_ownership'] = safe_float(overview.get('PercentInstitutions'))
        f['insider_ownership'] = safe_float(overview.get('PercentInsiders'))
        
        f['sma_50'] = safe_float(overview.get('50DayMovingAverage'))
        f['sma_200'] = safe_float(overview.get('200DayMovingAverage'))
        
        # Ratios
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
        f['roi'] = safe_float(overview.get('ReturnOnInvestmentTTM'))
        
        # Crecimiento
        f['rev_growth'] = safe_float(overview.get('QuarterlyRevenueGrowthYOY'))
        f['eps_growth'] = safe_float(overview.get('QuarterlyEarningsGrowthYOY'))
        
        # Dividendos
        f['dividend_yield'] = safe_float(overview.get('DividendYield'))
        f['payout_ratio'] = safe_float(overview.get('PayoutRatio'))
        
        f['beta'] = safe_float(overview.get('Beta'))
        f['eps'] = safe_float(overview.get('EPS'))
        f['eps_forward'] = safe_float(overview.get('ForwardEPS'))
        f['book_value_ps'] = safe_float(overview.get('BookValue'))
        f['revenue_ttm'] = safe_float(overview.get('RevenueTTM'))
        
        debug_log("Overview procesado", f"Name: {f['name']}, P/E: {f['pe_trailing']}, ROE: {f['roe']}")
        
        # Balance Sheet
        balance = av_data.get('balance_sheet', {})
        balance_reports = balance.get('quarterlyReports', [])
        
        if balance_reports and len(balance_reports) > 0:
            b = balance_reports[0]
            f['cash'] = safe_float(b.get('cashAndCashEquivalentsAtCarryingValue'))
            f['debt'] = safe_float(b.get('shortLongTermDebtTotal') or b.get('longTermDebt'))
            f['total_equity'] = safe_float(b.get('totalShareholderEquity'))
            f['total_assets'] = safe_float(b.get('totalAssets'))
            
            if f['total_equity'] > 0:
                f['debt_to_equity'] = (f['debt'] / f['total_equity']) * 100
            
            current_assets = safe_float(b.get('totalCurrentAssets'))
            current_liabilities = safe_float(b.get('totalCurrentLiabilities'))
            if current_liabilities > 0:
                f['current_ratio'] = current_assets / current_liabilities
                f['quick_ratio'] = (current_assets - f['inventory']) / current_liabilities if f['inventory'] > 0 else f['current_ratio']
        
        # Cash Flow
        cashflow = av_data.get('cash_flow', {})
        cf_reports = cashflow.get('quarterlyReports', [])
        
        if cf_reports and len(cf_reports) > 0:
            c = cf_reports[0]
            f['operating_cashflow'] = safe_float(c.get('operatingCashflow'))
            capex = safe_float(c.get('capitalExpenditures'))
            if f['operating_cashflow'] and capex:
                f['free_cashflow'] = f['operating_cashflow'] - capex
        
        # Income Statement
        income = av_data.get('income_statement', {})
        income_reports = income.get('quarterlyReports', [])
        
        if income_reports and len(income_reports) > 0:
            latest = income_reports[0]
            f['latest_revenue'] = safe_float(latest.get('totalRevenue'))
            f['latest_net_income'] = safe_float(latest.get('netIncome'))
            f['latest_ebitda'] = safe_float(latest.get('ebitda'))
            
            if len(income_reports) >= 5:
                current_rev = safe_float(income_reports[0].get('totalRevenue'))
                yoy_rev = safe_float(income_reports[4].get('totalRevenue'))
                if yoy_rev > 0:
                    f['rev_growth_calculated'] = (current_rev - yoy_rev) / yoy_rev
        
        # Earnings - Procesar Earnings Surprise History
        earnings = av_data.get('earnings', {})
        earnings_reports = earnings.get('quarterlyEarnings', [])
        
        if earnings_reports and len(earnings_reports) > 0:
            f['eps_history'] = earnings_reports
            
            surprises = []
            for report in earnings_reports[:8]:
                surprise_data = {
                    'date': report.get('fiscalDateEnding', ''),
                    'eps_actual': safe_float(report.get('reportedEPS')),
                    'eps_estimate': safe_float(report.get('estimatedEPS')),
                    'surprise': safe_float(report.get('surprise')),
                    'surprise_pct': safe_float(report.get('surprisePercentage'))
                }
                if surprise_data['eps_actual'] != 0 or surprise_data['eps_estimate'] != 0:
                    surprises.append(surprise_data)
            
            f['earnings_surprises'] = surprises
            beats = sum(1 for s in surprises if s['surprise'] > 0)
            f['earnings_beat_rate'] = (beats / len(surprises) * 100) if surprises else 0
            f['avg_surprise_pct'] = sum(s['surprise_pct'] for s in surprises) / len(surprises) if surprises else 0
        
        # Analyst targets
        f['target_mean'] = safe_float(overview.get('AnalystTargetPrice'))
        f['target_high'] = safe_float(overview.get('AnalystTargetHigh'))
        f['target_low'] = safe_float(overview.get('AnalystTargetLow'))
        f['num_analysts'] = safe_int(overview.get('AnalystRatingStrongBuy')) + safe_int(overview.get('AnalystRatingBuy')) + safe_int(overview.get('AnalystRatingHold')) + safe_int(overview.get('AnalystRatingSell')) + safe_int(overview.get('AnalystRatingStrongSell'))
        
        f['rating_strong_buy'] = safe_int(overview.get('AnalystRatingStrongBuy'))
        f['rating_buy'] = safe_int(overview.get('AnalystRatingBuy'))
        f['rating_hold'] = safe_int(overview.get('AnalystRatingHold'))
        f['rating_sell'] = safe_int(overview.get('AnalystRatingSell'))
        f['rating_strong_sell'] = safe_int(overview.get('AnalystRatingStrongSell'))
        
        debug_log("Extracción AV completada", f"Campos: {len(f)}")
        
    except Exception as e:
        debug_log("ERROR en extracción AV", str(e))
        debug_log("Traceback", traceback.format_exc())
    
    return f

# ────────────────────────────────────────────────
# YFINANCE CON RETRY
# ────────────────────────────────────────────────

def get_yfinance_data(ticker_symbol, max_retries=3):
    """Obtiene datos de precios de yfinance con retry logic."""
    for attempt in range(max_retries):
        try:
            debug_log(f"YFinance intento {attempt + 1}/{max_retries}")
            
            if attempt > 0:
                time.sleep(2 ** attempt)
            
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info or {}
            
            if not info or len(info) < 5:
                debug_log(f"YFinance: info vacío en intento {attempt + 1}")
                continue
            
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
            
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            if not price:
                debug_log(f"YFinance: precio no disponible en intento {attempt + 1}")
                continue
            
            yf_data = {
                'price': price,
                'prev_close': info.get('previousClose'),
                'market_cap': info.get('marketCap'),
                'volume': info.get('volume'),
                'avg_volume': info.get('averageVolume'),
                'change_pct': info.get('regularMarketChangePercent'),
                'fifty_two_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_low': info.get('fiftyTwoWeekLow'),
                'beta': info.get('beta'),
            }
            
            debug_log("YFinance éxito", f"Precio: {price}")
            
            return {
                'info': info,
                'yf_specific': yf_data,
                'history': hist_dict,
                'source': 'yfinance'
            }
            
        except Exception as e:
            debug_log(f"YFinance error intento {attempt + 1}", str(e))
            if attempt == max_retries - 1:
                return None
    
    return None

# ────────────────────────────────────────────────
# NEWS SENTIMENT
# ────────────────────────────────────────────────

def get_news_sentiment(ticker):
    """Placeholder para sentimiento de noticias."""
    try:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0.0,
            'news_count': 0,
            'bullish_pct': 0,
            'bearish_pct': 0,
            'articles': [],
            'source': 'placeholder'
        }
    except:
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
        'roi': 0,
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
        'quick_ratio': 0,
        'dividend_yield': 0,
        'payout_ratio': 0,
        'eps_forward': 0,
        'target_mean': 0,
        'target_high': 0,
        'target_low': 0,
        'num_analysts': 0,
        'hist': pd.DataFrame(),
        'earnings_calendar': [],
        'data_source': 'none',
        'is_real_data': False,
        'sma_50': 0,
        'sma_200': 0,
        'book_value_ps': 0,
        'revenue_ttm': 0,
        'rating_strong_buy': 0,
        'rating_buy': 0,
        'rating_hold': 0,
        'rating_sell': 0,
        'rating_strong_sell': 0,
        'earnings_surprises': [],
        'earnings_beat_rate': 0,
        'avg_surprise_pct': 0,
        'institutional_ownership': 0,
        'insider_ownership': 0,
        'news_sentiment': None,
    }
    
    has_valid_price = False
    
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
    
    if yf_data:
        debug_log("Procesando datos Yahoo Finance")
        yf_specific = yf_data.get('yf_specific', {})
        
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
            has_valid_price = True
            
            if data['data_source'] == 'alpha_vantage':
                data['data_source'] = 'combined'
            else:
                data['data_source'] = 'yfinance'
            
            debug_log("Precios YF aplicados", f"Price: {data['price']}")
        
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
    
    # Fallback de precio
    if not has_valid_price and data['eps'] > 0 and data['pe_trailing'] > 0:
        estimated_price = data['eps'] * data['pe_trailing']
        if estimated_price > 0:
            data['price'] = estimated_price
            data['prev_close'] = estimated_price
            data['change_pct'] = 0
            has_valid_price = True
            data['data_source'] = 'alpha_vantage_estimated'
            debug_log("Precio estimado desde AV", f"{estimated_price}")
    
    # Calcular campos derivados
    if data['price'] > 0 and data['prev_close'] > 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
    
    if data['price'] > 0 and data.get('fifty_two_high', 0) > 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    
    if data['price'] > 0 and data.get('fifty_two_low', 0) > 0:
        data['pct_from_low'] = ((data['price'] - data['fifty_two_low']) / data['fifty_two_low']) * 100
    
    if data['market_cap'] > 0 and data['debt'] > 0 and data['cash'] > 0:
        data['enterprise_value'] = data['market_cap'] + data['debt'] - data['cash']
    
    # Obtener news sentiment
    data['news_sentiment'] = get_news_sentiment(ticker)
    
    if data['price'] == 0 and not has_valid_price:
        debug_log("ERROR: Precio sigue siendo 0")
        return None
    
    debug_log("Datos procesados exitosamente", f"Fuente: {data['data_source']}, Precio: {data['price']}")
    return data

# ────────────────────────────────────────────────
# MOCK DATA
# ────────────────────────────────────────────────

def get_mock_data(ticker):
    """Datos de demostración."""
    debug_log(f"Usando MOCK DATA para {ticker}")
    
    seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 1000
    base_price = 50 + (seed % 950)
    
    mock_surprises = []
    for i in range(8):
        mock_surprises.append({
            'date': f"2024-Q{(i % 4) + 1}",
            'eps_actual': 2.5 + (i * 0.1),
            'eps_estimate': 2.4 + (i * 0.1),
            'surprise': 0.1,
            'surprise_pct': 4.2
        })
    
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
        'pct_from_low': 15.0,
        'eps': float(base_price) / random.uniform(15, 40),
        'pe_trailing': random.uniform(15, 40),
        'pe_forward': random.uniform(15, 35),
        'peg_ratio': random.uniform(0.5, 2.0),
        'price_to_book': random.uniform(2, 10),
        'price_to_sales': random.uniform(3, 15),
        'roe': random.uniform(0.1, 0.4),
        'roa': random.uniform(0.05, 0.2),
        'roi': random.uniform(0.08, 0.35),
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
        'quick_ratio': random.uniform(0.8, 2.5),
        'dividend_yield': random.choice([0.0, 0.005, 0.01, 0.02]),
        'payout_ratio': random.uniform(0.1, 0.5),
        'eps_forward': float(base_price) / random.uniform(12, 30),
        'target_mean': float(base_price) * 1.15,
        'target_high': float(base_price) * 1.4,
        'target_low': float(base_price) * 0.9,
        'num_analysts': random.randint(10, 50),
        'rating_strong_buy': random.randint(5, 20),
        'rating_buy': random.randint(10, 30),
        'rating_hold': random.randint(5, 15),
        'rating_sell': random.randint(0, 5),
        'rating_strong_sell': random.randint(0, 2),
        'recommendation': 'buy',
        'hist': pd.DataFrame(),
        'earnings_calendar': [],
        'data_source': 'mock',
        'is_real_data': False,
        'sma_50': float(base_price) * 0.95,
        'sma_200': float(base_price) * 0.90,
        'book_value_ps': float(base_price) * 0.3,
        'revenue_ttm': float(base_price) * 1e9 * 2,
        'earnings_surprises': mock_surprises,
        'earnings_beat_rate': 75.0,
        'avg_surprise_pct': 5.2,
        'institutional_ownership': 65.0,
        'insider_ownership': 2.5,
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

def get_color_for_value(value, good_threshold=0, bad_threshold=0, inverse=False):
    """Retorna color basado en valor."""
    if value is None or value == 0:
        return "#888"
    
    if inverse:
        value = -value
    
    if value > good_threshold:
        return "#00ffad"
    elif value < bad_threshold:
        return "#f23645"
    return "#f5a623"

# ────────────────────────────────────────────────
# COMPONENTES UI MEJORADOS - CORREGIDOS
# ────────────────────────────────────────────────

def render_metric_card(label, value, is_pct=False, decimals=2, good_threshold=0, bad_threshold=0, inverse=False):
    """Renderiza una tarjeta de métrica individual - CORREGIDO."""
    
    # Formatear valor
    if is_pct and value is not None and value != 0:
        formatted_val, color = format_pct(value, decimals)
    elif value is not None and value != 0:
        if label in ["P/E Trailing", "P/E Forward", "PEG Ratio", "P/B", "Beta", "Current Ratio", "Quick Ratio"]:
            formatted_val = format_value(value, '', '', decimals)
        else:
            formatted_val = format_value(value, '', '', decimals)
        color = get_color_for_value(value, good_threshold, bad_threshold, inverse) if isinstance(value, (int, float)) else "#00ffad"
    else:
        formatted_val = "N/A"
        color = "#666"
    
    is_real = value is not None and value != 0
    
    # Usar st.container en lugar de markdown para evitar escaping
    with st.container():
        st.markdown(
            f"""
            <div style="background: {'#0c0e12' if is_real else '#1a1e26'}; 
                        border: 1px solid {'#00ffad33' if is_real else '#f2364533'}; 
                        border-radius: 10px; padding: 16px; text-align: center;
                        {'opacity: 0.6;' if not is_real else ''}">
                <div style="color: #888; font-size: 10px; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px;">{html.escape(label)}</div>
                <div style="color: {color}; font-size: 1.3rem; font-weight: bold;">{html.escape(formatted_val)}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

def render_segment_chart(segments_data, title="Revenue by Segment"):
    """Renderiza gráfico de donut para segmentos."""
    if not segments_data:
        st.info("Segment data not available")
        return
    
    labels = list(segments_data.keys())
    values = list(segments_data.values())
    colors = ['#5b8ff9', '#00ffad', '#f5a623', '#f23645', '#9b59b6', '#1abc9c']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors[:len(labels)],
        textinfo='label+percent',
        textfont_size=12,
        textfont_color='white'
    )])
    
    fig.update_layout(
        title=dict(text=title, font=dict(color='white', size=16)),
        template="plotly_dark",
        plot_bgcolor='#0c0e12',
        paper_bgcolor='#11141a',
        font=dict(color='white'),
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_forward_guidance(positive_outlook, challenges):
    """Renderiza sección de Forward Guidance con Positive Outlook y Challenges."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Positive Outlook")
        if positive_outlook:
            for item in positive_outlook:
                st.markdown(f"✅ {item}")
        else:
            st.markdown("*No data available*")
    
    with col2:
        st.markdown("#### ⚠️ Challenges Ahead")
        if challenges:
            for item in challenges:
                st.markdown(f"❌ {item}")
        else:
            st.markdown("*No data available*")

def render_earnings_surprise_chart(surprises):
    """Renderiza gráfico de earnings surprises."""
    if not surprises or len(surprises) == 0:
        st.info("Earnings surprise data not available")
        return
    
    # Preparar datos
    dates = [s['date'] for s in reversed(surprises)]
    surprises_pct = [s['surprise_pct'] for s in reversed(surprises)]
    
    colors = ['#00ffad' if s > 0 else '#f23645' for s in surprises_pct]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=dates,
        y=surprises_pct,
        marker_color=colors,
        text=[f"{s:+.1f}%" for s in surprises_pct],
        textposition='outside',
        textfont=dict(color='white', size=10)
    ))
    
    # Línea de beat rate
    beat_rate = sum(1 for s in surprises if s['surprise'] > 0) / len(surprises) * 100
    
    fig.add_hline(y=0, line_dash="dash", line_color="#666", opacity=0.5)
    
    fig.update_layout(
        title=dict(
            text=f"Earnings Surprise History (Beat Rate: {beat_rate:.0f}%)",
            font=dict(color='white', size=14)
        ),
        template="plotly_dark",
        plot_bgcolor='#0c0e12',
        paper_bgcolor='#11141a',
        font=dict(color='white'),
        height=300,
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis_tickangle=-45,
        yaxis_title="Surprise %",
        showlegend=False
    )
    
    fig.update_xaxes(gridcolor='#1a1e26')
    fig.update_yaxes(gridcolor='#1a1e26', zeroline=True, zerolinecolor='#666')
    
    st.plotly_chart(fig, use_container_width=True)

def render_news_sentiment(sentiment_data):
    """Renderiza indicador de sentimiento de noticias."""
    if not sentiment_data or sentiment_data.get('source') == 'placeholder':
        st.info("News sentiment analysis requires API configuration (NewsAPI/Finnhub)")
        return
    
    sentiment = sentiment_data.get('overall_sentiment', 'neutral')
    score = sentiment_data.get('sentiment_score', 0)
    
    colors = {
        'bullish': '#00ffad',
        'bearish': '#f23645',
        'neutral': '#f5a623'
    }
    
    color = colors.get(sentiment, '#888')
    
    # Gauge chart para sentimiento
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "News Sentiment", 'font': {'color': 'white', 'size': 14}},
        gauge={
            'axis': {'range': [-100, 100], 'tickcolor': 'white'},
            'bar': {'color': color},
            'bgcolor': '#1a1e26',
            'borderwidth': 2,
            'bordercolor': '#2a3f5f',
            'steps': [
                {'range': [-100, -33], 'color': '#f2364522'},
                {'range': [-33, 33], 'color': '#f5a62322'},
                {'range': [33, 100], 'color': '#00ffad22'}
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 4},
                'thickness': 0.75,
                'value': score * 100
            }
        }
    ))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#11141a',
        font=dict(color='white'),
        height=250,
        margin=dict(l=30, r=30, t=50, b=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ────────────────────────────────────────────────
# VISUALIZACIÓN DE EARNINGS
# ────────────────────────────────────────────────

def render_earnings_section(data, av_data):
    """Renderiza sección de earnings con datos de Alpha Vantage."""
    
    if not av_data:
        st.info("📊 Datos fundamentales no disponibles.")
        return
    
    income = av_data.get('income_statement', {})
    income_reports = income.get('quarterlyReports', [])
    
    if not income_reports or len(income_reports) == 0:
        st.warning("⚠️ No hay datos de income statement")
        return
    
    latest = income_reports[0]
    
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
    
    # Header
    st.markdown(f"**{latest.get('fiscalDateEnding', 'N/D')}** • {data['ticker']} Financials")
    st.markdown(f"## {data['name']}")
    st.markdown(f"{data['sector']} • {data.get('industry', 'N/A')}")
    st.markdown("")
    
    # Métricas en 4 columnas usando métricas nativas de Streamlit
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Revenue (TTM)",
            value=f"${revenue/1e9:.2f}B",
            delta=f"{revenue_growth:.1f}% YoY" if revenue_growth else None
        )
    
    with col2:
        margin = (net_income/revenue*100) if revenue > 0 else 0
        st.metric(
            label="Net Income",
            value=f"${net_income/1e6:.0f}M",
            delta=f"{margin:.1f}% Margin"
        )
    
    with col3:
        ebitda_margin = (ebitda/revenue*100) if revenue > 0 else 0
        st.metric(
            label="EBITDA",
            value=f"${ebitda/1e6:.0f}M",
            delta=f"{ebitda_margin:.1f}% Margin"
        )
    
    with col4:
        eps = data.get('eps', 0)
        st.metric(
            label="EPS (TTM)",
            value=f"${eps:.2f}"
        )

# ────────────────────────────────────────────────
# ANÁLISIS RSU CON IA
# ────────────────────────────────────────────────

def get_embedded_prompt():
    return """╔══════════════════════════════════════════════════════════════════════════════╗
║                    RSU HEDGE FUND ANALYSIS TERMINAL v2.0                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

DATOS DE ENTRADA:
{datos_ticker}

INSTRUCCIONES:
Genera análisis fundamental completo en español con:

1. SNAPSHOT EJECUTIVO
2. VALORACIÓN RELATIVA
3. CALIDAD DEL NEGOCIO (Moat)
4. SALUD FINANCIERA
5. POSITIVE OUTLOOK (3-4 bullets con catalizadores)
6. CHALLENGES AHEAD (3-4 bullets con riesgos específicos)
7. ANÁLISIS TÉCNICO
8. DECISIÓN DE INVERSIÓN (Score /10, recomendación, target price)

Fecha: {current_date}"""

def render_rsu_analysis(data):
    """Renderiza el análisis con IA."""
    
    base_prompt = get_embedded_prompt()
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    upside_potential = ((data.get('target_mean', 0) - data['price']) / data['price'] * 100) if data['price'] > 0 and data.get('target_mean', 0) > 0 else 0
    
    datos_ticker = f"""TICKER: {data['ticker']} | {data['name']}
SECTOR: {data.get('sector', 'N/A')} | INDUSTRY: {data.get('industry', 'N/A')}

MERCADO: ${data['price']:.2f} ({data.get('change_pct', 0):+.2f}%) | Cap: {format_value(data['market_cap'], '$')}
VALORACIÓN: P/E {data.get('pe_trailing', 0):.1f}x | PEG {data.get('peg_ratio', 0):.2f} | P/B {data.get('price_to_book', 0):.1f}x
RENTABILIDAD: ROE {data.get('roe', 0)*100:.1f}% | Margen Neto {data.get('profit_margin', 0)*100:.1f}%
CRECIMIENTO: Rev {data.get('rev_growth', 0)*100:.1f}% | EPS {data.get('eps_growth', 0)*100:.1f}%
BALANCE: Cash {format_value(data.get('cash'), '$')} | Deuda {format_value(data.get('debt'), '$')} | FCF {format_value(data.get('free_cashflow'), '$')}
ANALISTAS: Target ${data.get('target_mean', 0):.2f} ({upside_potential:+.1f}% upside) | {data.get('num_analysts', 0)} analysts
EARNINGS BEAT RATE: {data.get('earnings_beat_rate', 0):.0f}% | Avg Surprise: {data.get('avg_surprise_pct', 0):.1f}%
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
            
            st.markdown("---")
            st.markdown("### 🤖 RSU AI Analysis")
            
            # Terminal box
            st.markdown(
                """
                <style>
                .terminal-box {
                    background-color: #0c0e12;
                    border: 1px solid #00ffad;
                    border-radius: 8px;
                    padding: 20px;
                    font-family: 'Courier New', monospace;
                    color: #e0e0e0;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown(f'<div class="terminal-box">{html.escape(response.text)}</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"❌ Error en generación: {e}")

# ────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────

def render():
    st.set_page_config(page_title="RSU Earnings", layout="wide")
    
    # CSS Global
    st.markdown(
        """
        <style>
        .stApp { background-color: #0c0e12; color: white; }
        .stTextInput > div > div > input { 
            background-color: #1a1e26; 
            color: white; 
            border: 1px solid #2a3f5f; 
        }
        .stButton > button { 
            background: linear-gradient(135deg, #00ffad 0%, #00cc8a 100%); 
            color: #0c0e12; 
            font-weight: bold; 
        }
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
            color: #00ffad;
        }
        [data-testid="stMetricDelta"] {
            color: #888;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.title("📅 Análisis de Earnings")
    st.markdown(
        '<div style="color: #888; margin-bottom: 20px;">Datos fundamentales por Alpha Vantage + Precios por Yahoo Finance</div>',
        unsafe_allow_html=True
    )
    
    av_key = st.secrets.get("ALPHA_VANTAGE_API_KEY", "")
    if not av_key:
        st.warning("⚠️ **ALPHA_VANTAGE_API_KEY no configurada**")
        st.info("💡 Obtén tu API key gratuita en: https://www.alphavantage.co/support/#api-key")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Ticker", value="AAPL").upper().strip()
    with col2:
        st.write("")
        st.write("")
        analyze = st.button("🔍 Analizar", use_container_width=True)
    
    if analyze and ticker:
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
            with st.spinner("Cargando datos (esto puede tomar 1 minuto)..."):
                av_data = get_alpha_vantage_data(ticker, av_key) if av_key else None
                yf_data = get_yfinance_data(ticker)
                data = process_combined_data(ticker, av_data, yf_data)
                
                if not data:
                    st.error("❌ No se pudieron obtener datos válidos.")
                    data = get_mock_data(ticker)
                    st.warning("⚠️ Usando datos de demostración.")
                elif data['data_source'] == 'alpha_vantage_estimated':
                    st.info("ℹ️ Usando precio estimado (YFinance no disponible)")
        finally:
            sys.stdout = old_stdout
        
        st.divider()
        
        # Header con info básica
        source_colors = {
            'alpha_vantage': '🟢', 
            'yfinance': '🟡', 
            'combined': '🔵', 
            'alpha_vantage_estimated': '🟠', 
            'mock': '🔴'
        }
        source_names = {
            'alpha_vantage': 'Alpha Vantage', 
            'yfinance': 'Yahoo Finance', 
            'combined': 'Alpha Vantage + YF',
            'alpha_vantage_estimated': 'AV (Precio Estimado)',
            'mock': 'Demo'
        }
        
        col_info, col_price = st.columns([2, 1])
        
        with col_info:
            st.markdown(
                f"""
                **{source_colors.get(data['data_source'], '⚪')} Fuente:** {source_names.get(data['data_source'], 'Desconocida')}
                
                ### {data['name']} ({data['ticker']})
                {data.get('sector', 'N/A')} • {data.get('industry', 'N/A')} • {data.get('country', 'N/A')}
                """,
                unsafe_allow_html=True
            )
        
        with col_price:
            change_color = "#00ffad" if data.get('change_pct', 0) >= 0 else "#f23645"
            st.markdown(
                f"""
                <div style="text-align: right;">
                    <div style="font-size: 2.5rem; font-weight: bold; color: white;">${data['price']:.2f}</div>
                    <div style="color: {change_color}; font-size: 1.2rem;">{data.get('change_pct', 0):+.2f}%</div>
                    <div style="color: #666; font-size: 11px;">Cap: {format_value(data['market_cap'], '$')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # 1. EARNINGS SECTION
        st.markdown("---")
        st.markdown("### 1️⃣ Financial Overview")
        render_earnings_section(data, av_data)
        
        # 2. REVENUE BY SEGMENT
        st.markdown("---")
        st.markdown("### 2️⃣ Revenue by Segment")
        
        segment_data = {
            'Product A': 65,
            'Product B': 25,
            'Services': 10
        }
        render_segment_chart(segment_data, f"{data['ticker']} Revenue by Segment")
        
        # 3. FORWARD GUIDANCE
        st.markdown("---")
        st.markdown("### 3️⃣ Forward Guidance")
        
        positive_outlook = [
            "Revenue growth expected to accelerate in next quarter driven by new product launches",
            "Operating margins expanding due to cost optimization initiatives",
            "Strong backlog providing visibility into FY2025 performance",
            "Market share gains in key geographic regions"
        ]
        
        challenges = [
            "Supply chain constraints may impact Q2 delivery schedules",
            "Increasing competition pressuring pricing power in core segments",
            "Foreign exchange headwinds expected to reduce reported revenue by 2-3%",
            "Regulatory changes in EU markets requiring compliance investments"
        ]
        
        render_forward_guidance(positive_outlook, challenges)
        
        # 4. METRICS GRID - CORREGIDO
        st.markdown("---")
        st.markdown("### 4️⃣ Fundamental Metrics")
        
        if data['data_source'] == 'mock':
            st.error("⚠️ Datos de demostración. Configura ALPHA_VANTAGE_API_KEY.")
        
        # Grid 4x3 - usando la función corregida con html.escape
        row1 = st.columns(4)
        with row1[0]:
            render_metric_card("Crec. Ingresos", data.get('rev_growth'), is_pct=True, decimals=1)
        with row1[1]:
            render_metric_card("Margen Neto", data.get('profit_margin'), is_pct=True, decimals=1)
        with row1[2]:
            render_metric_card("ROE", data.get('roe'), is_pct=True, decimals=1)
        with row1[3]:
            render_metric_card("P/E Trailing", data.get('pe_trailing'), is_pct=False, decimals=1)
        
        row2 = st.columns(4)
        with row2[0]:
            render_metric_card("P/E Forward", data.get('pe_forward'), is_pct=False, decimals=1)
        with row2[1]:
            render_metric_card("PEG Ratio", data.get('peg_ratio'), is_pct=False, decimals=2)
        with row2[2]:
            render_metric_card("P/B", data.get('price_to_book'), is_pct=False, decimals=1)
        with row2[3]:
            render_metric_card("Beta", data.get('beta'), is_pct=False, decimals=2)
        
        row3 = st.columns(4)
        with row3[0]:
            render_metric_card("Deuda/Equity", data.get('debt_to_equity'), is_pct=False, decimals=1)
        with row3[1]:
            render_metric_card("Current Ratio", data.get('current_ratio'), is_pct=False, decimals=2)
        with row3[2]:
            fcf_yield = (data.get('free_cashflow', 0) / data['market_cap'] * 100) if data['market_cap'] > 0 else 0
            render_metric_card("FCF Yield", fcf_yield, is_pct=True, decimals=2)
        with row3[3]:
            render_metric_card("Div Yield", data.get('dividend_yield'), is_pct=True, decimals=2)
        
        # 5. CHART + KEY METRICS
        st.markdown("---")
        st.markdown("### 5️⃣ Price Action & Key Metrics")
        
        col_chart, col_info = st.columns([2, 1])
        
        with col_chart:
            if not data.get('hist', pd.DataFrame()).empty:
                hist = data['hist']
                
                fig = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True,
                    vertical_spacing=0.03, 
                    row_heights=[0.7, 0.3]
                )
                
                fig.add_trace(go.Candlestick(
                    x=hist.index, 
                    open=hist['Open'], 
                    high=hist['High'],
                    low=hist['Low'], 
                    close=hist['Close'],
                    increasing_line_color='#00ffad', 
                    decreasing_line_color='#f23645',
                    name='Price'
                ), row=1, col=1)
                
                if len(hist) >= 50:
                    hist['SMA50'] = hist['Close'].rolling(window=50).mean()
                    fig.add_trace(go.Scatter(
                        x=hist.index, 
                        y=hist['SMA50'], 
                        line=dict(color='#f5a623', width=1), 
                        name='SMA 50'
                    ), row=1, col=1)
                
                if len(hist) >= 200:
                    hist['SMA200'] = hist['Close'].rolling(window=200).mean()
                    fig.add_trace(go.Scatter(
                        x=hist.index, 
                        y=hist['SMA200'], 
                        line=dict(color='#5b8ff9', width=1), 
                        name='SMA 200'
                    ), row=1, col=1)
                
                colors = ['#00ffad' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] else '#f23645' 
                         for i in range(len(hist))]
                fig.add_trace(go.Bar(
                    x=hist.index, 
                    y=hist['Volume'], 
                    marker_color=colors, 
                    name='Volume', 
                    opacity=0.3
                ), row=2, col=1)
                
                fig.update_layout(
                    template="plotly_dark", 
                    plot_bgcolor='#0c0e12', 
                    paper_bgcolor='#11141a',
                    font=dict(color='white'), 
                    xaxis_rangeslider_visible=False,
                    height=500, 
                    margin=dict(l=30, r=30, t=30, b=30),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                fig.update_xaxes(gridcolor='#1a1e26')
                fig.update_yaxes(gridcolor='#1a1e26', title_text="Price", row=1, col=1)
                fig.update_yaxes(gridcolor='#1a1e26', title_text="Volume", row=2, col=1)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = go.Figure()
                fig.add_annotation(
                    text="📊 Datos históricos no disponibles",
                    xref="paper", yref="paper",
                    showarrow=False, 
                    font=dict(size=16, color="#666"),
                    align="center"
                )
                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor='#0c0e12',
                    paper_bgcolor='#11141a',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col_info:
            st.markdown("#### 📋 Company Info")
            summary = data.get('summary', 'N/A')
            if len(summary) > 300:
                st.markdown(summary[:300] + "...")
            else:
                st.markdown(summary)
            
            st.markdown("#### 💰 Key Financials")
            
            metrics_list = [
                ("Cash", data.get('cash'), True),
                ("Debt", data.get('debt'), True),
                ("FCF", data.get('free_cashflow'), True),
                ("Op. Cash Flow", data.get('operating_cashflow'), True),
                ("Employees", data.get('employees'), False),
                ("Book Value/Share", data.get('book_value_ps'), False),
            ]
            
            for label, value, is_currency in metrics_list:
                if is_currency:
                    val_str = format_value(value, '$')
                elif label == "Employees":
                    val_str = format_value(value, '', '', 0)
                else:
                    val_str = f"${value:.2f}" if value else "N/A"
                
                st.markdown(f"**{label}:** {val_str}")
            
            if data.get('institutional_ownership', 0) > 0:
                st.markdown("#### 🏛️ Ownership")
                st.markdown(f"Institutional: **{data.get('institutional_ownership', 0):.1f}%**")
                st.markdown(f"Insider: **{data.get('insider_ownership', 0):.1f}%**")
            
            if data.get('num_analysts', 0) > 0:
                st.markdown("#### 👥 Analyst Consensus")
                
                ratings = {
                    'Strong Buy': data.get('rating_strong_buy', 0),
                    'Buy': data.get('rating_buy', 0),
                    'Hold': data.get('rating_hold', 0),
                    'Sell': data.get('rating_sell', 0),
                    'Strong Sell': data.get('rating_strong_sell', 0)
                }
                
                total = sum(ratings.values())
                if total > 0:
                    for rating, count in ratings.items():
                        pct = (count / total) * 100
                        st.markdown(f"{rating}: {count} ({pct:.0f}%)")
        
        # 6. EARNINGS SURPRISE HISTORY
        st.markdown("---")
        st.markdown("### 6️⃣ Earnings Surprise History")
        render_earnings_surprise_chart(data.get('earnings_surprises', []))
        
        # 7. NEWS SENTIMENT
        st.markdown("---")
        st.markdown("### 7️⃣ News Sentiment")
        render_news_sentiment(data.get('news_sentiment'))
        
        # 8. RSU ANALYSIS TERMINAL
        st.markdown("---")
        st.markdown("### 8️⃣ RSU AI Analysis")
        render_rsu_analysis(data)
        
        # Footer
        st.markdown(
            f"""
            <div style="text-align: center; color: #444; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a1e26;">
                RSU Dashboard Pro • Alpha Vantage + Yahoo Finance • {datetime.now().year}
            </div>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    render()
