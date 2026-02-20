
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
# API KEYS DESDE SECRETS
# ────────────────────────────────────────────────

def get_api_keys():
    """Obtiene las API keys desde secrets."""
    return {
        'alpha_vantage': st.secrets.get("ALPHA_VANTAGE_API_KEY", ""),
        'finnhub': st.secrets.get("FINNHUB_API_KEY", ""),
    }

# ────────────────────────────────────────────────
# CACHE DE DATOS PARA OPTIMIZAR LLAMADAS API
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_alpha_vantage_data_cached(ticker, api_key):
    """Versión cacheada de get_alpha_vantage_data - SIN elementos de UI."""
    return _fetch_alpha_vantage_data(ticker, api_key)

@st.cache_data(ttl=1800)  # Cache por 30 minutos para precios
def get_yfinance_data_cached(ticker_symbol):
    """Versión cacheada de get_yfinance_data - SIN elementos de UI."""
    return _fetch_yfinance_data(ticker_symbol)

@st.cache_data(ttl=900)  # Cache por 15 minutos para noticias (más frecuente)
def get_finnhub_data_cached(ticker, api_key):
    """Versión cacheada de get_finnhub_data - SIN elementos de UI."""
    return _fetch_finnhub_data(ticker, api_key)

# ────────────────────────────────────────────────
# FINNHUB API - DATOS DE SEGMENTOS Y NOTICIAS
# ────────────────────────────────────────────────

def _fetch_finnhub_data(ticker, api_key):
    """Función interna que obtiene datos de Finnhub (sin UI)."""
    if not api_key:
        debug_log("ERROR: FINNHUB_API_KEY no proporcionada")
        return None
    
    base_url = "https://finnhub.io/api/v1"
    headers = {"X-Finnhub-Token": api_key}
    result = {}
    
    try:
        # 1. Revenue Breakdown by Segment
        debug_log("Solicitando revenue breakdown de Finnhub")
        rev_response = requests.get(
            f"{base_url}/stock/revenue-breakdown",
            params={"symbol": ticker},
            headers=headers,
            timeout=10
        )
        
        if rev_response.status_code == 200:
            rev_data = rev_response.json()
            debug_log("Revenue breakdown OK", list(rev_data.keys())[:5])
            result['revenue_breakdown'] = rev_data
        else:
            debug_log(f"Revenue breakdown error: {rev_response.status_code}")
            result['revenue_breakdown'] = {}
        
        time.sleep(0.5)  # Rate limiting
        
        # 2. Revenue Breakdown by Geographic
        debug_log("Solicitando geographic revenue de Finnhub")
        geo_response = requests.get(
            f"{base_url}/stock/revenue-breakdown",
            params={"symbol": ticker, "breakdown": "geographic"},
            headers=headers,
            timeout=10
        )
        
        if geo_response.status_code == 200:
            geo_data = geo_response.json()
            debug_log("Geographic revenue OK")
            result['geographic_revenue'] = geo_data
        else:
            debug_log(f"Geographic revenue error: {geo_response.status_code}")
            result['geographic_revenue'] = {}
        
        time.sleep(0.5)
        
        # 3. Company News con Sentiment
        debug_log("Solicitando noticias de Finnhub")
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        news_response = requests.get(
            f"{base_url}/company-news",
            params={
                "symbol": ticker,
                "from": from_date,
                "to": to_date
            },
            headers=headers,
            timeout=10
        )
        
        if news_response.status_code == 200:
            news_data = news_response.json()
            debug_log(f"Noticias OK: {len(news_data)} artículos")
            result['news'] = news_response.json()
        else:
            debug_log(f"Noticias error: {news_response.status_code}")
            result['news'] = []
        
        time.sleep(0.5)
        
        # 4. Social Sentiment
        debug_log("Solicitando social sentiment de Finnhub")
        sentiment_response = requests.get(
            f"{base_url}/stock/social-sentiment",
            params={"symbol": ticker},
            headers=headers,
            timeout=10
        )
        
        if sentiment_response.status_code == 200:
            sentiment_data = sentiment_response.json()
            debug_log("Social sentiment OK")
            result['social_sentiment'] = sentiment_data
        else:
            debug_log(f"Social sentiment error: {sentiment_response.status_code}")
            result['social_sentiment'] = {}
        
        result['source'] = 'finnhub'
        result['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return result
        
    except Exception as e:
        debug_log("ERROR en Finnhub", str(e))
        return None

def get_finnhub_data(ticker, api_key):
    """Versión pública con spinner (no cacheada)."""
    if not api_key:
        return None
    with st.spinner("📰 Cargando datos de Finnhub..."):
        return _fetch_finnhub_data(ticker, api_key)

def process_finnhub_segments(finnhub_data):
    """Procesa los datos de segmentos de Finnhub."""
    if not finnhub_data:
        return None
    
    segments = {}
    
    # Procesar revenue breakdown por segmento de negocio
    rev_breakdown = finnhub_data.get('revenue_breakdown', {})
    if rev_breakdown and 'data' in rev_breakdown:
        for item in rev_breakdown['data']:
            segment_name = item.get('segment', 'Unknown')
            revenue = item.get('revenue', 0)
            if revenue > 0:
                segments[segment_name] = revenue
    
    # Si no hay segmentos de negocio, usar geográficos
    if not segments:
        geo_breakdown = finnhub_data.get('geographic_revenue', {})
        if geo_breakdown and 'data' in geo_breakdown:
            for item in geo_breakdown['data']:
                region = item.get('region', 'Unknown')
                revenue = item.get('revenue', 0)
                if revenue > 0:
                    segments[region] = revenue
    
    return segments if segments else None

def calculate_news_sentiment(finnhub_data):
    """Calcula sentimiento basado en noticias de Finnhub."""
    if not finnhub_data or 'news' not in finnhub_data:
        return None
    
    news = finnhub_data['news']
    if not news:
        return None
    
    # Análisis basado en palabras clave en títulos
    bullish_words = [
        'beat', 'strong', 'growth', 'profit', 'gain', 'rise', 'surge', 'bull', 
        'upgrade', 'buy', 'outperform', 'exceeds', 'beats', 'record', 'soar',
        'rally', 'boom', 'breakthrough', 'partnership', 'deal', 'expansion',
        'innovation', 'launch', 'success', 'positive', 'optimistic', 'surge',
        'moon', 'rocket', ' ATH', 'all time high', 'dividend increase'
    ]
    bearish_words = [
        'miss', 'weak', 'loss', 'decline', 'fall', 'drop', 'bear', 'downgrade', 
        'sell', 'cut', 'underperform', 'misses', 'plunge', 'crash', 'concern',
        'risk', 'investigation', 'lawsuit', 'layoff', 'recession', 'inflation',
        'bankruptcy', 'debt crisis', 'fraud', 'scandal', 'delay', 'postpone',
        'warning', 'cut forecast', 'bearish', 'dump', 'correction', 'dip'
    ]
    
    bullish_count = 0
    bearish_count = 0
    total_analyzed = 0
    
    for article in news[:30]:  # Últimas 30 noticias para más precisión
        title = article.get('headline', '').lower()
        if not title:
            continue
            
        total_analyzed += 1
        
        # Buscar palabras alcistas
        for word in bullish_words:
            if word in title:
                bullish_count += 1
                break
        
        # Buscar palabras bajistas
        for word in bearish_words:
            if word in title:
                bearish_count += 1
                break
    
    total_sentiment = bullish_count + bearish_count
    if total_sentiment == 0:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0,
            'news_count': len(news),
            'bullish_pct': 0,
            'bearish_pct': 0,
            'analyzed_count': total_analyzed,
            'source': 'finnhub'
        }
    
    bullish_pct = (bullish_count / total_sentiment) * 100
    bearish_pct = (bearish_count / total_sentiment) * 100
    
    # Calcular score entre -1 y 1
    if bullish_pct > 60:
        sentiment = 'bullish'
        score = 0.5 + (bullish_pct - 60) / 80  # 0.5 a 1.0
    elif bearish_pct > 60:
        sentiment = 'bearish'
        score = -0.5 - (bearish_pct - 60) / 80  # -0.5 a -1.0
    else:
        sentiment = 'neutral'
        score = (bullish_pct - bearish_pct) / 100  # -0.5 a 0.5
    
    return {
        'overall_sentiment': sentiment,
        'sentiment_score': max(-1, min(1, score)),
        'news_count': len(news),
        'bullish_pct': round(bullish_pct, 1),
        'bearish_pct': round(bearish_pct, 1),
        'analyzed_count': total_analyzed,
        'source': 'finnhub'
    }

# ────────────────────────────────────────────────
# ALPHA VANTAGE API - DATOS FUNDAMENTALES
# ────────────────────────────────────────────────

def _fetch_alpha_vantage_data(ticker, api_key):
    """Función interna que obtiene datos de Alpha Vantage (sin UI)."""
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

def get_alpha_vantage_data(ticker, api_key):
    """Versión pública con spinner (no cacheada)."""
    if not api_key:
        return None
    with st.spinner("📊 Cargando datos fundamentales de Alpha Vantage..."):
        return _fetch_alpha_vantage_data(ticker, api_key)

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
        
        # Ratios de valoración
        f['pe_trailing'] = safe_float(overview.get('TrailingPE'))
        f['pe_forward'] = safe_float(overview.get('ForwardPE'))
        f['peg_ratio'] = safe_float(overview.get('PEGRatio'))
        f['price_to_book'] = safe_float(overview.get('PriceToBookRatio'))
        f['price_to_sales'] = safe_float(overview.get('PriceToSalesRatioTTM'))
        
        # Márgenes - Normalización
        gross_margin_raw = safe_float(overview.get('GrossProfitTTM'))
        revenue_ttm_raw = safe_float(overview.get('RevenueTTM'))
        
        if revenue_ttm_raw > 0 and gross_margin_raw > 0:
            if gross_margin_raw > 1:
                f['gross_margin'] = gross_margin_raw / 100
            else:
                f['gross_margin'] = gross_margin_raw / revenue_ttm_raw
        
        f['operating_margin'] = safe_float(overview.get('OperatingMarginTTM'))
        f['profit_margin'] = safe_float(overview.get('ProfitMargin'))
        f['ebitda_margin'] = safe_float(overview.get('EBITDA')) / safe_float(overview.get('RevenueTTM')) if overview.get('RevenueTTM') else 0
        
        # Normalizar márgenes
        for margin_key in ['operating_margin', 'profit_margin', 'ebitda_margin']:
            if f.get(margin_key, 0) > 1:
                f[margin_key] = f[margin_key] / 100
        
        # Rentabilidad
        f['roe'] = safe_float(overview.get('ReturnOnEquityTTM'))
        f['roa'] = safe_float(overview.get('ReturnOnAssetsTTM'))
        f['roi'] = safe_float(overview.get('ReturnOnInvestmentTTM'))
        
        # Normalizar ratios
        for ratio_key in ['roe', 'roa', 'roi']:
            if f.get(ratio_key, 0) > 1:
                f[ratio_key] = f[ratio_key] / 100
        
        # Crecimiento
        f['rev_growth'] = safe_float(overview.get('QuarterlyRevenueGrowthYOY'))
        f['eps_growth'] = safe_float(overview.get('QuarterlyEarningsGrowthYOY'))
        
        # Normalizar crecimiento
        for growth_key in ['rev_growth', 'eps_growth']:
            if abs(f.get(growth_key, 0)) > 1:
                f[growth_key] = f[growth_key] / 100
        
        # Dividendos
        f['dividend_yield'] = safe_float(overview.get('DividendYield'))
        f['payout_ratio'] = safe_float(overview.get('PayoutRatio'))
        
        if f.get('dividend_yield', 0) > 0.5:
            f['dividend_yield'] = f['dividend_yield'] / 100
        
        f['beta'] = safe_float(overview.get('Beta'))
        f['eps'] = safe_float(overview.get('EPS'))
        f['eps_forward'] = safe_float(overview.get('ForwardEPS'))
        f['book_value_ps'] = safe_float(overview.get('BookValue'))
        f['revenue_ttm'] = safe_float(overview.get('RevenueTTM'))
        
        debug_log("Overview procesado", f"Name: {f['name']}, P/E: {f['pe_trailing']}, ROE: {f['roe']}, Profit Margin: {f['profit_margin']}")
        
        # Balance Sheet
        balance = av_data.get('balance_sheet', {})
        balance_reports = balance.get('quarterlyReports', [])
        
        if balance_reports and len(balance_reports) > 0:
            b = balance_reports[0]
            debug_log("Balance sheet", f"Fecha: {b.get('fiscalDateEnding')}")
            f['cash'] = safe_float(b.get('cashAndCashEquivalentsAtCarryingValue'))
            f['debt'] = safe_float(b.get('shortLongTermDebtTotal') or b.get('longTermDebt'))
            f['total_equity'] = safe_float(b.get('totalShareholderEquity'))
            f['total_assets'] = safe_float(b.get('totalAssets'))
            f['total_liabilities'] = safe_float(b.get('totalLiabilities'))
            f['inventory'] = safe_float(b.get('inventory'))
            f['goodwill'] = safe_float(b.get('goodwill'))
            
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
            debug_log("Cash flow", f"Fecha: {c.get('fiscalDateEnding')}")
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
            f['latest_operating_income'] = safe_float(latest.get('operatingIncome'))
            f['research_dev'] = safe_float(latest.get('researchAndDevelopment'))
            f['interest_expense'] = safe_float(latest.get('interestExpense'))
            f['income_tax'] = safe_float(latest.get('incomeTaxExpense'))
            
            debug_log("Income Statement Latest", f"Revenue: {f['latest_revenue']}, Net Income: {f['latest_net_income']}, EBITDA: {f['latest_ebitda']}")
            
            # Calcular crecimiento YoY
            if len(income_reports) >= 5:
                current_rev = safe_float(income_reports[0].get('totalRevenue'))
                yoy_rev = safe_float(income_reports[4].get('totalRevenue'))
                if yoy_rev > 0:
                    f['rev_growth_calculated'] = (current_rev - yoy_rev) / yoy_rev
        
        # Earnings
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

def _fetch_yfinance_data(ticker_symbol, max_retries=3):
    """Función interna que obtiene datos de yfinance (sin UI)."""
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

def get_yfinance_data(ticker_symbol):
    """Versión pública con spinner (no cacheada)."""
    with st.spinner("📈 Cargando precios de Yahoo Finance..."):
        return _fetch_yfinance_data(ticker_symbol)

# ────────────────────────────────────────────────
# PROCESAMIENTO DE DATOS COMBINADO
# ────────────────────────────────────────────────

def process_combined_data(ticker, av_data, yf_data, finnhub_data=None):
    """Combina datos de Alpha Vantage, Yahoo Finance y Finnhub."""
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
        'segments': None,
        'latest_revenue': 0,
        'latest_net_income': 0,
        'latest_ebitda': 0,
    }
    
    has_valid_price = False
    
    # Procesar Alpha Vantage
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
    
    # Procesar Yahoo Finance
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
    
    # Procesar Finnhub
    if finnhub_data:
        debug_log("Procesando datos Finnhub")
        
        # Segmentos
        segments = process_finnhub_segments(finnhub_data)
        if segments:
            data['segments'] = segments
            debug_log("Segmentos procesados", list(segments.keys()))
        
        # Sentimiento
        sentiment = calculate_news_sentiment(finnhub_data)
        if sentiment:
            data['news_sentiment'] = sentiment
            debug_log("Sentimiento calculado", f"{sentiment['overall_sentiment']} ({sentiment['sentiment_score']:.2f})")
    
    # Fallback de precio
    if not has_valid_price and data['eps'] > 0 and data['pe_trailing'] > 0:
        estimated_price = data['eps'] * data['pe_trailing']
        if estimated_price > 0:
            data['price'] = estimated_price
            data['prev_close'] = estimated_price
            data['change_pct'] = 0
            has_valid_price = True
            data['data_source'] = 'alpha_vantage_estimated'
    
    # Calcular campos derivados
    if data['price'] > 0 and data['prev_close'] > 0:
        data['change_pct'] = ((data['price'] - data['prev_close']) / data['prev_close']) * 100
    
    if data['price'] > 0 and data.get('fifty_two_high', 0) > 0:
        data['pct_from_high'] = ((data['price'] - data['fifty_two_high']) / data['fifty_two_high']) * 100
    
    if data['price'] > 0 and data.get('fifty_two_low', 0) > 0:
        data['pct_from_low'] = ((data['price'] - data['fifty_two_low']) / data['fifty_two_low']) * 100
    
    if data['market_cap'] > 0 and data['debt'] > 0 and data['cash'] > 0:
        data['enterprise_value'] = data['market_cap'] + data['debt'] - data['cash']
    
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
        'latest_revenue': float(base_price) * 1e9 * 2,
        'latest_net_income': float(base_price) * 1e9 * 0.1,
        'latest_ebitda': float(base_price) * 1e9 * 0.3,
        'segments': {
            'Producto A': 65,
            'Producto B': 25,
            'Servicios': 10
        },
        'news_sentiment': {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0.1,
            'news_count': 15,
            'bullish_pct': 55,
            'bearish_pct': 45,
            'analyzed_count': 12,
            'source': 'mock'
        }
    }

# ────────────────────────────────────────────────
# FORMATO Y UTILIDADES
# ────────────────────────────────────────────────

def format_value(value, prefix="", suffix="", decimals=2):
    if value is None or value == 0 or (isinstance(value, float) and pd.isna(value)):
        return "N/D"
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
        return "N/D", "#888"
    try:
        val = float(value) * 100 if abs(float(value)) < 1 else float(value)
        color = "#00ffad" if val >= 0 else "#f23645"
        return f"{val:.{decimals}f}%", color
    except:
        return "N/D", "#888"

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
# COMPONENTES UI
# ────────────────────────────────────────────────

def render_metric_card(label, value, is_pct=False, decimals=2, good_threshold=0, bad_threshold=0, inverse=False):
    """Renderiza una tarjeta de métrica individual."""
    
    if is_pct and value is not None and value != 0:
        formatted_val, color = format_pct(value, decimals)
    elif value is not None and value != 0:
        if label in ["P/E Trailing", "P/E Forward", "PEG Ratio", "P/B", "Beta", "Current Ratio", "Quick Ratio"]:
            formatted_val = format_value(value, '', '', decimals)
        else:
            formatted_val = format_value(value, '', '', decimals)
        color = get_color_for_value(value, good_threshold, bad_threshold, inverse) if isinstance(value, (int, float)) else "#00ffad"
    else:
        formatted_val = "N/D"
        color = "#666"
    
    is_real = value is not None and value != 0
    
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

def render_segment_chart(segments_data, title="Ingresos por Segmento"):
    """Renderiza gráfico de donut para segmentos."""
    if not segments_data:
        st.info("Datos de segmentos no disponibles")
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

def render_forward_guidance(data, av_data):
    """Renderiza sección de Forward Guidance basado en datos reales."""
    
    income = av_data.get('income_statement', {}) if av_data else {}
    income_reports = income.get('quarterlyReports', [])
    
    # Calcular tendencias
    if len(income_reports) >= 2:
        latest = income_reports[0]
        previous = income_reports[1]
        
        rev_growth = ((safe_float(latest.get('totalRevenue')) - safe_float(previous.get('totalRevenue'))) / 
                     safe_float(previous.get('totalRevenue')) * 100) if safe_float(previous.get('totalRevenue')) > 0 else 0
    else:
        rev_growth = 0
    
    positive_outlook = []
    challenges = []
    
    # Análisis de tendencias reales
    if data.get('rev_growth', 0) > 0:
        positive_outlook.append(f"Crecimiento de ingresos positivo ({data['rev_growth']*100:.1f}%) impulsado por demanda sostenida")
    elif data.get('rev_growth', 0) < -0.1:
        challenges.append(f"Contracción de ingresos ({data['rev_growth']*100:.1f}%) requiere atención en próximos trimestres")
    
    if data.get('profit_margin', 0) > 0.15:
        positive_outlook.append(f"Márgenes de beneficio sólidos ({data['profit_margin']*100:.1f}%) respaldan rentabilidad")
    elif data.get('profit_margin', 0) < 0:
        challenges.append(f"Pérdidas operativas ({data['profit_margin']*100:.1f}%) requieren optimización de costes")
    
    if data.get('free_cashflow', 0) > 0:
        positive_outlook.append(f"Generación positiva de FCF ({format_value(data['free_cashflow'], '$')}) permite flexibilidad financiera")
    else:
        challenges.append(f"Quema de caja ({format_value(data['free_cashflow'], '$')}) requiere monitoreo de liquidez")
    
    if data.get('debt_to_equity', 0) < 50:
        positive_outlook.append(f"Balance sheet conservador con bajo apalancamiento ({data['debt_to_equity']:.1f}%)")
    elif data.get('debt_to_equity', 0) > 100:
        challenges.append(f"Alto nivel de apalancamiento ({data['debt_to_equity']:.1f}%) expone a riesgos de tipos de interés")
    
    if len(positive_outlook) < 2:
        positive_outlook.append("Posición de mercado estable en segmentos core")
    if len(challenges) < 2:
        challenges.append("Entorno competitivo y presión regulatoria en sectores clave")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Perspectivas Positivas")
        for item in positive_outlook[:4]:
            st.markdown(f"✅ {item}")
    
    with col2:
        st.markdown("#### ⚠️ Desafíos por Delante")
        for item in challenges[:4]:
            st.markdown(f"❌ {item}")

def render_earnings_surprise_chart(surprises):
    """Renderiza gráfico de earnings surprises."""
    if not surprises or len(surprises) == 0:
        st.info("Datos de earnings surprises no disponibles")
        return
    
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
    
    beat_rate = sum(1 for s in surprises if s['surprise'] > 0) / len(surprises) * 100
    
    fig.add_hline(y=0, line_dash="dash", line_color="#666", opacity=0.5)
    
    fig.update_layout(
        title=dict(
            text=f"Historial de Earnings Surprises (Beat Rate: {beat_rate:.0f}%)",
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
    if not sentiment_data:
        st.info("📰 Análisis de sentimiento no disponibles - Configura FINNHUB_API_KEY")
        return
    
    sentiment = sentiment_data.get('overall_sentiment', 'neutral')
    score = sentiment_data.get('sentiment_score', 0)
    source = sentiment_data.get('source', 'unknown')
    
    colors = {
        'bullish': '#00ffad',
        'bearish': '#f23645',
        'neutral': '#f5a623'
    }
    
    color = colors.get(sentiment, '#888')
    
    # Mostrar badge de fuente
    if source == 'finnhub':
        st.success("✅ Sentimiento basado en noticias reales de Finnhub")
    else:
        st.info("ℹ️ Datos de sentimiento de ejemplo")
    
    # Métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sentimiento", sentiment.upper())
    
    with col2:
        bullish_pct = sentiment_data.get('bullish_pct', 0)
        st.metric("Noticias Alcistas", f"{bullish_pct:.0f}%")
    
    with col3:
        bearish_pct = sentiment_data.get('bearish_pct', 0)
        st.metric("Noticias Bajistas", f"{bearish_pct:.0f}%")
    
    with col4:
        score_pct = score * 100
        delta_color = "normal" if score_pct >= 0 else "inverse"
        st.metric("Score", f"{score_pct:+.0f}", delta_color=delta_color)
    
    # Gauge chart - CORREGIDO: sin transparencia en steps
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score * 100,
        delta={'reference': 0, 'increasing': {'color': "#00ffad"}, 'decreasing': {'color': "#f23645"}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Sentimiento de Noticias", 'font': {'color': 'white', 'size': 14}},
        gauge={
            'axis': {'range': [-100, 100], 'tickcolor': 'white', 'tickwidth': 1},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': '#1a1e26',
            'borderwidth': 2,
            'bordercolor': '#2a3f5f',
            'steps': [
                {'range': [-100, -33], 'color': '#3d1f1f'},  # Rojo oscuro sin transparencia
                {'range': [-33, 33], 'color': '#3d3520'},     # Amarillo oscuro sin transparencia
                {'range': [33, 100], 'color': '#1f3d2e'}      # Verde oscuro sin transparencia
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 3},
                'thickness': 0.8,
                'value': score * 100
            }
        }
    ))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='#11141a',
        font=dict(color='white'),
        height=280,
        margin=dict(l=30, r=30, t=50, b=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Información adicional
    news_count = sentiment_data.get('news_count', 0)
    analyzed = sentiment_data.get('analyzed_count', 0)
    
    st.caption(f"📊 Análisis basado en {analyzed} noticias relevantes de las últimas {news_count} disponibles")

# ────────────────────────────────────────────────
# VISUALIZACIÓN DE EARNINGS
# ────────────────────────────────────────────────

def render_earnings_section(data, av_data):
    """Renderiza sección de earnings con datos reales."""
    
    if not av_data:
        st.info("📊 Datos fundamentales no disponibles.")
        return
    
    income = av_data.get('income_statement', {})
    income_reports = income.get('quarterlyReports', [])
    
    if not income_reports or len(income_reports) == 0:
        st.warning("⚠️ No hay datos de income statement")
        return
    
    latest = income_reports[0]
    
    # Calcular crecimiento YoY real
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
    
    st.markdown(f"**{latest.get('fiscalDateEnding', 'N/D')}** • Resultados {data['ticker']}")
    st.markdown(f"## {data['name']}")
    st.markdown(f"{data['sector']} • {data.get('industry', 'N/A')}")
    st.markdown("")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Ingresos Totales (TTM)",
            value=f"${revenue/1e9:.2f}B" if revenue >= 1e9 else f"${revenue/1e6:.1f}M",
            delta=f"{revenue_growth:.1f}% YoY" if revenue_growth else None
        )
    
    with col2:
        margin = (net_income/revenue*100) if revenue > 0 else 0
        st.metric(
            label="Beneficio Neto",
            value=f"${net_income/1e6:.0f}M" if abs(net_income) >= 1e6 else f"${net_income/1e3:.0f}K",
            delta=f"{margin:.1f}% Margen"
        )
    
    with col3:
        ebitda_margin = (ebitda/revenue*100) if revenue > 0 else 0
        st.metric(
            label="EBITDA",
            value=f"${ebitda/1e6:.0f}M" if abs(ebitda) >= 1e6 else f"${ebitda/1e3:.0f}K",
            delta=f"{ebitda_margin:.1f}% Margen"
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
    return """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           ██╗░░░██╗███████╗██╗░░██╗         ██████╗ ███████╗██╗   ██╗        ║
║           ██║░░░██║██╔════╝╚██╗██╔╝         ██╔══██╗██╔════╝██║   ██║        ║
║           ╚██╗░██╔╝█████╗░░░╚███╔╝░         ██████╔╝█████╗░░██║   ██║        ║
║           ░╚████╔╝░██╔══╝░░░██╔██╗░         ██╔══██╗██╔══╝░░╚██╗ ██╔╝        ║
║           ░░╚██╔╝░░███████╗██╔╝╚██╗         ██║░░██║███████╗░╚████╔╝░        ║
║           ░░░╚═╝░░░╚══════╝╚═╝░░╚═╝         ╚═╝░░╚═╝╚══════╝░░╚═══╝░░        ║
║                                                                              ║
║     ██████╗  █████╗ ███╗   ██╗ █████╗ ██╗     ██╗███████╗██╗███████╗         ║
║     ██╔══██╗██╔══██╗████╗  ██║██╔══██╗██║     ██║██╔════╝██║██╔════╝         ║
║     ██████╔╝███████║██╔██╗ ██║███████║██║     ██║█████╗  ██║███████╗         ║
║     ██╔══██╗██╔══██║██║╚██╗██║██╔══██║██║     ██║██╔══╝  ██║╚════██║         ║
║     ██║  ██║██║  ██║██║ ╚████║██║  ██║███████╗██║██║     ██║███████║         ║
║     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝     ╚═╝╚══════╝         ║
║                                                                              ║
║                    TERMINAL DE ANÁLISIS DE RENTA VARIABLE                    ║
║                              v2.0 - RSU Edition                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

DATOS DE ENTRADA:
{datos_ticker}

INSTRUCCIONES:
Genera análisis fundamental completo en español con:

1. SNAPSHOT EJECUTIVO
2. VALORACIÓN RELATIVA  
3. CALIDAD DEL NEGOCIO (Moat)
4. SALUD FINANCIERA
5. PERSPECTIVAS POSITIVAS (3-4 bullets con catalizadores)
6. DESAFÍOS POR DELANTE (3-4 bullets con riesgos específicos)
7. ANÁLISIS TÉCNICO
8. DECISIÓN DE INVERSIÓN (Score /10, recomendación, target price)

Fecha: {current_date}"""

def render_rsu_analysis(data):
    """Renderiza el análisis con IA."""
    
    base_prompt = get_embedded_prompt()
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    upside_potential = ((data.get('target_mean', 0) - data['price']) / data['price'] * 100) if data['price'] > 0 and data.get('target_mean', 0) > 0 else 0
    
    datos_ticker = f"""TICKER: {data['ticker']} | {data['name']}
SECTOR: {data.get('sector', 'N/A')} | INDUSTRIA: {data.get('industry', 'N/A')}

MERCADO: ${data['price']:.2f} ({data.get('change_pct', 0):+.2f}%) | Cap: {format_value(data['market_cap'], '$')}
VALORACIÓN: P/E {data.get('pe_trailing', 0):.1f}x | PEG {data.get('peg_ratio', 0):.2f} | P/B {data.get('price_to_book', 0):.1f}x
RENTABILIDAD: ROE {data.get('roe', 0)*100:.1f}% | Margen Neto {data.get('profit_margin', 0)*100:.1f}%
CRECIMIENTO: Rev {data.get('rev_growth', 0)*100:.1f}% | EPS {data.get('eps_growth', 0)*100:.1f}%
BALANCE: Cash {format_value(data.get('cash'), '$')} | Deuda {format_value(data.get('debt'), '$')} | FCF {format_value(data.get('free_cashflow'), '$')}
ANALISTAS: Target ${data.get('target_mean', 0):.2f} ({upside_potential:+.1f}% upside) | {data.get('num_analysts', 0)} analistas
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
            st.markdown("### 🤖 Análisis RSU AI")
            
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
                    white-space: pre-wrap;
                    overflow-x: auto;
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
        '<div style="color: #888; margin-bottom: 20px;">Datos fundamentales por Alpha Vantage + Precios por Yahoo Finance + Segmentos por Finnhub</div>',
        unsafe_allow_html=True
    )
    
    # Obtener API keys
    api_keys = get_api_keys()
    
    # Verificar API keys
    if not api_keys['alpha_vantage']:
        st.warning("⚠️ **ALPHA_VANTAGE_API_KEY no configurada**")
        st.info("💡 Obtén tu API key gratuita en: https://www.alphavantage.co/support/#api-key")
    
    if not api_keys['finnhub']:
        st.info("ℹ️ **FINNHUB_API_KEY no configurada** - Los datos de segmentos y sentimiento usarán datos de ejemplo")
        st.markdown("""
        💡 **Para obtener API key de Finnhub (GRATIS):**
        1. Ve a https://finnhub.io/
        2. Clic en "Get free api key"
        3. Regístrate con email
        4. Copia tu API key del dashboard
        """)
    
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
            with st.spinner("Cargando datos (esto puede tomar 1-2 minutos)..."):
                # USAR FUNCIONES CACHEADAS (sin spinner interno)
                av_data = get_alpha_vantage_data_cached(ticker, api_keys['alpha_vantage']) if api_keys['alpha_vantage'] else None
                yf_data = get_yfinance_data_cached(ticker)
                finnhub_data = get_finnhub_data_cached(ticker, api_keys['finnhub']) if api_keys['finnhub'] else None
                
                data = process_combined_data(ticker, av_data, yf_data, finnhub_data)
                
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
        st.markdown("### 1️⃣ Resumen Financiero")
        render_earnings_section(data, av_data)
        
        # 2. REVENUE BY SEGMENT
        st.markdown("---")
        st.markdown("### 2️⃣ Ingresos por Segmento")
        
        if data.get('segments') and data['data_source'] != 'mock':
            st.success("✅ Datos de segmentos reales de Finnhub")
            render_segment_chart(data['segments'], f"{data['ticker']} - Ingresos por Segmento")
        else:
            st.info("ℹ️ Datos de segmentos no disponibles. Configura FINNHUB_API_KEY para datos reales.")
            # Datos de ejemplo
            segment_data = {
                'Producto A': 65,
                'Producto B': 25,
                'Servicios': 10
            }
            render_segment_chart(segment_data, f"{data['ticker']} - Ingresos por Segmento (Ejemplo)")
        
        # 3. FORWARD GUIDANCE
        st.markdown("---")
        st.markdown("### 3️⃣ Perspectivas Futuras")
        st.info("ℹ️ Este análisis se genera automáticamente basado en tendencias reales de los últimos trimestres.")
        
        render_forward_guidance(data, av_data)
        
        # 4. METRICS GRID
        st.markdown("---")
        st.markdown("### 4️⃣ Métricas Fundamentales")
        
        if data['data_source'] == 'mock':
            st.error("⚠️ Datos de demostración. Configura ALPHA_VANTAGE_API_KEY.")
        
        # Grid 4x3
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
        st.markdown("### 5️⃣ Acción del Precio y Métricas Clave")
        
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
                    name='Precio'
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
                    name='Volumen', 
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
                fig.update_yaxes(gridcolor='#1a1e26', title_text="Precio", row=1, col=1)
                fig.update_yaxes(gridcolor='#1a1e26', title_text="Volumen", row=2, col=1)
                
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
            st.markdown("#### 📋 Información de la Empresa")
            summary = data.get('summary', 'N/A')
            if len(summary) > 300:
                st.markdown(summary[:300] + "...")
            else:
                st.markdown(summary)
            
            st.markdown("#### 💰 Métricas Clave")
            
            metrics_list = [
                ("Cash", data.get('cash'), True),
                ("Deuda", data.get('debt'), True),
                ("FCF", data.get('free_cashflow'), True),
                ("Op. Cash Flow", data.get('operating_cashflow'), True),
                ("Empleados", data.get('employees'), False),
                ("Book Value/Acción", data.get('book_value_ps'), False),
            ]
            
            for label, value, is_currency in metrics_list:
                if is_currency:
                    val_str = format_value(value, '$')
                elif label == "Empleados":
                    val_str = format_value(value, '', '', 0)
                else:
                    val_str = f"${value:.2f}" if value else "N/D"
                
                st.markdown(f"**{label}:** {val_str}")
            
            if data.get('institutional_ownership', 0) > 0:
                st.markdown("#### 🏛️ Propiedad")
                st.markdown(f"Institucional: **{data.get('institutional_ownership', 0):.1f}%**")
                st.markdown(f"Insider: **{data.get('insider_ownership', 0):.1f}%**")
            
            if data.get('num_analysts', 0) > 0:
                st.markdown("#### 👥 Consenso de Analistas")
                
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
        st.markdown("### 6️⃣ Historial de Earnings Surprises")
        render_earnings_surprise_chart(data.get('earnings_surprises', []))
        
        # 7. NEWS SENTIMENT
        st.markdown("---")
        st.markdown("### 7️⃣ Sentimiento de Noticias")
        
        render_news_sentiment(data.get('news_sentiment'))
        
        # 8. RSU ANALYSIS TERMINAL
        st.markdown("---")
        st.markdown("### 8️⃣ Análisis RSU AI")
        render_rsu_analysis(data)
        
        # Footer
        st.markdown(
            f"""
            <div style="text-align: center; color: #444; font-size: 11px; margin-top: 40px; padding-top: 20px; border-top: 1px solid #1a1e26;">
                RSU Dashboard Pro • Alpha Vantage + Yahoo Finance + Finnhub • {datetime.now().year}
            </div>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    render()


