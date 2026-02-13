# -*- coding: utf-8 -*-
"""
CAN SLIM Scanner Pro - Módulo para RSU Terminal
Ubicación: modules/canslim.py
Versión: 2.2.1
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import warnings
import os
import re as re_module
import traceback
import time
import random
warnings.filterwarnings('ignore')

# ============================================================
# CONSTANTES Y CONFIGURACIÓN GLOBAL
# ============================================================

def get_timestamp():
    return datetime.now().strftime('%H:%M:%S')

def hex_to_rgba(hex_color, alpha=1.0):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

# Paleta de colores CAN SLIM
COLORS = {
    'primary': '#00ffad',
    'warning': '#ff9800',
    'danger': '#f23645',
    'neutral': '#888888',
    'bg_dark': '#0c0e12',
    'bg_card': '#1a1e26',
    'border': '#2a2e36',
    'text': '#ffffff',
    'text_secondary': '#aaaaaa'
}

# Ruta al archivo de tickers (desde directorio raíz)
TICKERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tickers.txt")

# ============================================================
# CONFIGURACIÓN PARA EVITAR RATE LIMITING
# ============================================================

class YFSession:
    """Maneja sesiones de yfinance con rate limiting integrado"""
    _last_request_time = 0
    _min_delay = 0.5
    _cache = {}
    
    @classmethod
    def get_ticker(cls, symbol, max_retries=3):
        """Obtiene ticker con retry logic y delays"""
        symbol = symbol.upper().strip()
        
        cache_key = f"{symbol}_{datetime.now().strftime('%Y-%m-%d_%H')}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        elapsed = time.time() - cls._last_request_time
        if elapsed < cls._min_delay:
            time.sleep(cls._min_delay - elapsed)
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    sleep_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(sleep_time)
                
                ticker = yf.Ticker(symbol)
                cls._last_request_time = time.time()
                cls._cache[cache_key] = ticker
                return ticker
                
            except Exception as e:
                if "rate limit" in str(e).lower() or "too many" in str(e).lower():
                    continue
                raise
        
        raise Exception("Max retries exceeded for rate limiting")

# ============================================================
# IMPORTS OPCIONALES
# ============================================================

try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# ============================================================
# GESTIÓN DE TICKERS S&P 500 DESDE ARCHIVO .TXT
# ============================================================

def load_sp500_tickers():
    """
    Carga los tickers del S&P 500 desde tickers.txt en directorio raíz
    """
    try:
        if not os.path.exists(TICKERS_FILE):
            # Si no existe, crear con lista por defecto
            default_tickers = get_default_sp500_tickers()
            save_sp500_tickers(default_tickers)
            return default_tickers
        
        with open(TICKERS_FILE, 'r') as f:
            content = f.read()
        
        # Parsear: por líneas o por comas
        if '\n' in content:
            tickers = [line.strip() for line in content.split('\n') if line.strip()]
        else:
            tickers = [t.strip() for t in content.split(',') if t.strip()]
        
        # Limpiar y validar
        valid_tickers = []
        for t in tickers:
            t_clean = str(t).strip().upper()
            t_clean = re_module.sub(r'[^\w\.\-]', '', t_clean)
            if t_clean and len(t_clean) <= 5:
                valid_tickers.append(t_clean)
        
        # Eliminar duplicados
        seen = set()
        unique_tickers = [t for t in valid_tickers if not (t in seen or seen.add(t))]
        
        return unique_tickers if unique_tickers else get_default_sp500_tickers()

    except Exception as e:
        return get_default_sp500_tickers()

def get_default_sp500_tickers():
    """Lista por defecto de principales tickers del S&P 500"""
    return [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'TSLA', 'BRK-B', 'UNH',
        'JPM', 'XOM', 'JNJ', 'V', 'PG', 'HD', 'MA', 'CVX', 'LLY', 'MRK',
        'PEP', 'KO', 'ABBV', 'AVGO', 'COST', 'TMO', 'DIS', 'ABT', 'WMT', 'ACN',
        'MCD', 'VZ', 'DHR', 'NKE', 'TXN', 'CRM', 'ADBE', 'PM', 'NEE', 'BMY',
        'RTX', 'HON', 'UNP', 'QCOM', 'UPS', 'LOW', 'LIN', 'AMGN', 'SPGI', 'MDT'
    ]

def save_sp500_tickers(tickers_list):
    """Guarda lista de tickers al archivo"""
    try:
        with open(TICKERS_FILE, 'w') as f:
            for ticker in tickers_list:
                f.write(f"{ticker}\n")
        return True
    except Exception as e:
        return False

# Cargar tickers al iniciar módulo
SP500_TICKERS = load_sp500_tickers()

# ============================================================
# SCRAPER ALTERNATIVO PARA DATOS FUNDAMENTALES
# ============================================================

def get_fundamental_data_alternative(ticker):
    """Obtiene datos fundamentales de fuentes alternativas"""
    data = {
        'marketCap': None,
        'earningsGrowth': None,
        'revenueGrowth': None,
        'heldPercentInstitutions': None,
        'shortName': ticker,
        'sector': 'N/A',
        'industry': 'N/A'
    }
    
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'root.App.main' in script.string:
                text = script.string
                if '"marketCap":' in text:
                    try:
                        start = text.find('"marketCap":') + len('"marketCap":')
                        end = text.find(',', start)
                        data['marketCap'] = int(text[start:end])
                    except:
                        pass
                
                if '"earningsGrowth":' in text:
                    try:
                        start = text.find('"earningsGrowth":') + len('"earningsGrowth":')
                        end = text.find(',', start)
                        val = text[start:end].strip()
                        if val != 'null':
                            data['earningsGrowth'] = float(val)
                    except:
                        pass
                break
        
        # Stats page
        stats_url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
        response = requests.get(stats_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].text.strip()
                    value = cells[1].text.strip()
                    
                    if 'Market cap' in label:
                        try:
                            value = value.replace(',', '')
                            if 'T' in value:
                                data['marketCap'] = float(value.replace('T', '')) * 1e12
                            elif 'B' in value:
                                data['marketCap'] = float(value.replace('B', '')) * 1e9
                            elif 'M' in value:
                                data['marketCap'] = float(value.replace('M', '')) * 1e6
                        except:
                            pass
                    
                    elif 'Held by institutions' in label:
                        try:
                            data['heldPercentInstitutions'] = float(value.replace('%', '')) / 100
                        except:
                            pass
        
    except:
        pass
    
    return data

# ============================================================
# FUNCIÓN MEJORADA PARA OBTENER DATOS
# ============================================================

def get_enhanced_stock_data(ticker):
    """Obtiene datos del stock combinando múltiples fuentes"""
    ticker = ticker.upper().strip()
    result = {'info': {}, 'history': None, 'calculated': {}}
    
    try:
        stock = YFSession.get_ticker(ticker)
    except Exception as e:
        return None
    
    try:
        hist = stock.history(period="1y")
        if hist is not None and not hist.empty and len(hist) >= 50:
            result['history'] = hist
        else:
            return None
    except:
        return None
    
    # Múltiples fuentes de datos
    info_sources = []
    
    try:
        yf_info = stock.info
        if yf_info and len(yf_info) > 10:
            info_sources.append(('yfinance.info', yf_info))
    except:
        pass
    
    try:
        fast = stock.fast_info
        fast_dict = {
            'marketCap': getattr(fast, 'market_cap', None),
            'fifty_two_week_high': getattr(fast, 'fifty_two_week_high', None),
        }
        info_sources.append(('fast_info', fast_dict))
    except:
        pass
    
    try:
        web_data = get_fundamental_data_alternative(ticker)
        info_sources.append(('web_scraping', web_data))
    except:
        pass
    
    # Calcular métricas desde historial
    hist_metrics = {}
    try:
        closes = result['history']['Close']
        hist_metrics['volatility'] = closes.pct_change().std() * np.sqrt(252)
        hist_metrics['ytd_return'] = (closes.iloc[-1] / closes.iloc[0] - 1) * 100
        hist_metrics['fifty_two_week_high'] = closes.max()
        hist_metrics['fifty_two_week_low'] = closes.min()
    except:
        pass
    
    # Combinar fuentes
    combined_info = {}
    field_priority = {
        'marketCap': ['web_scraping', 'yfinance.info', 'fast_info'],
        'earningsGrowth': ['web_scraping', 'yfinance.info'],
        'revenueGrowth': ['web_scraping', 'yfinance.info'],
        'heldPercentInstitutions': ['web_scraping', 'yfinance.info'],
        'shortName': ['yfinance.info', 'web_scraping', 'fast_info'],
        'sector': ['yfinance.info', 'web_scraping'],
        'industry': ['yfinance.info', 'web_scraping']
    }
    
    for field, sources in field_priority.items():
        for source_name in sources:
            for src_name, src_data in info_sources:
                if src_name == source_name and field in src_data:
                    val = src_data[field]
                    if val is not None and val != 0 and val != 'N/A':
                        combined_info[field] = val
                        break
            if field in combined_info:
                break
    
    if 'shortName' not in combined_info:
        combined_info['shortName'] = ticker
    
    result['info'] = combined_info
    result['calculated'] = hist_metrics
    
    return result

# ============================================================
# ANÁLISIS DE MERCADO
# ============================================================

class MarketAnalyzer:
    def __init__(self):
        self.indices = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ 100',
            'IWM': 'Russell 2000',
            'VIX': 'Volatilidad (Miedo)'
        }
    
    def get_market_data(self):
        market_data = {}
        for ticker, name in self.indices.items():
            try:
                if ticker == 'VIX':
                    data = yf.Ticker('^VIX').history(period="6mo")
                else:
                    data = yf.Ticker(ticker).history(period="6mo")
                
                if len(data) > 0:
                    market_data[ticker] = {
                        'name': name,
                        'data': data,
                        'current': data['Close'].iloc[-1],
                        'sma_50': data['Close'].rolling(50).mean().iloc[-1],
                        'sma_200': data['Close'].rolling(200).mean().iloc[-1],
                        'trend_20d': (data['Close'].iloc[-1] / data['Close'].iloc[-20] - 1) * 100,
                        'trend_60d': (data['Close'].iloc[-1] / data['Close'].iloc[-60] - 1) * 100
                    }
            except:
                continue
        return market_data
    
    def calculate_market_score(self):
        data = self.get_market_data()
        score = 50
        signals = []
        
        if 'SPY' in data:
            spy = data['SPY']
            if spy['current'] > spy['sma_50'] > spy['sma_200']:
                score += 20
                signals.append("SPY: Golden Cross (Alcista)")
            elif spy['current'] > spy['sma_50']:
                score += 10
                signals.append("SPY: Sobre SMA50")
            elif spy['current'] < spy['sma_50'] < spy['sma_200']:
                score -= 20
                signals.append("SPY: Death Cross (Bajista)")
            elif spy['current'] < spy['sma_50']:
                score -= 10
                signals.append("SPY: Bajo SMA50")
            
            if spy['trend_20d'] > 5:
                score += 10
            elif spy['trend_20d'] < -5:
                score -= 10
        
        if 'QQQ' in data:
            qqq = data['QQQ']
            if qqq['current'] > qqq['sma_50']:
                score += 10
                signals.append("QQQ: Tendencia positiva")
            else:
                score -= 5
        
        if 'IWM' in data:
            iwm = data['IWM']
            if iwm['current'] > iwm['sma_50']:
                score += 10
                signals.append("Small Caps: Participación amplia")
            else:
                score -= 5
        
        if 'VIX' in data:
            vix = data['VIX']
            if vix['current'] < 20:
                score += 10
                signals.append("VIX: Bajo (Complacencia)")
            elif vix['current'] > 30:
                score -= 15
                signals.append("VIX: Alto (Miedo extremo)")
        
        score = max(0, min(100, score))
        
        if score >= 80:
            phase = "CONFIRMED UPTREND"
            color = COLORS['primary']
        elif score >= 60:
            phase = "UPTREND UNDER PRESSURE"
            color = COLORS['warning']
        elif score >= 40:
            phase = "MARKET IN TRANSITION"
            color = COLORS['neutral']
        elif score >= 20:
            phase = "DOWNTREND UNDER PRESSURE"
            color = COLORS['warning']
        else:
            phase = "CONFIRMED DOWNTREND"
            color = COLORS['danger']
        
        return {
            'score': score,
            'phase': phase,
            'color': color,
            'signals': signals,
            'data': data
        }

# ============================================================
# MACHINE LEARNING
# ============================================================

class CANSlimMLPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.model_path = "canslim_ml_model.pkl"
        self.features = [
            'earnings_growth', 'revenue_growth', 'eps_growth',
            'rs_rating', 'volume_ratio', 'inst_ownership',
            'pct_from_high', 'volatility', 'price_momentum'
        ]
        
        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
    
    def prepare_features(self, metrics):
        if not SKLEARN_AVAILABLE:
            return None
            
        features = np.array([
            metrics.get('earnings_growth', 0),
            metrics.get('revenue_growth', 0),
            metrics.get('eps_growth', 0),
            metrics.get('rs_rating', 50),
            metrics.get('volume_ratio', 1),
            metrics.get('inst_ownership', 0),
            abs(metrics.get('pct_from_high', 0)),
            metrics.get('volatility', 0.2),
            metrics.get('price_momentum', 0)
        ]).reshape(1, -1)
        return self.scaler.fit_transform(features)
    
    def predict(self, metrics):
        if not SKLEARN_AVAILABLE:
            return 0.5
            
        if self.model is None:
            if os.path.exists(self.model_path):
                self.model, self.scaler = joblib.load(self.model_path)
            else:
                return 0.5
        
        features = self.prepare_features(metrics)
        if features is None:
            return 0.5
            
        prob = self.model.predict_proba(features)[0][1]
        return prob
    
    def get_feature_importance(self):
        if not SKLEARN_AVAILABLE or self.model is None:
            return {f: 0.11 for f in self.features}
        return dict(zip(self.features, self.model.feature_importances_))

# ============================================================
# CÁLCULOS CAN SLIM
# ============================================================

def calculate_can_slim_metrics(ticker, market_analyzer=None):
    """Calcula métricas CAN SLIM con datos mejorados"""
    try:
        ticker = str(ticker).strip().upper()
        
        if not ticker:
            return None
        
        data = get_enhanced_stock_data(ticker)
        if data is None:
            return None
        
        hist = data['history']
        info = data['info']
        calc = data.get('calculated', {})
        
        current_price = float(hist['Close'].iloc[-1])
        
        market_cap = info.get('marketCap', 0) / 1e9 if info.get('marketCap') else 0
        
        if market_cap == 0:
            try:
                avg_volume = hist['Volume'].mean()
                estimated_shares = avg_volume * 20
                market_cap = (current_price * estimated_shares) / 1e9
            except:
                market_cap = 0
        
        earnings_growth = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
        revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
        eps_growth = info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0
        
        if earnings_growth == 0 and 'ytd_return' in calc:
            earnings_growth = calc['ytd_return'] * 0.5
        
        high_52w = info.get('fifty_two_week_high') or calc.get('fifty_two_week_high') or hist['High'].max()
        pct_from_high = ((current_price - high_52w) / high_52w) * 100 if high_52w > 0 else -100
        
        try:
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        except:
            volume_ratio = 1.0
        
        rs_rating = 50
        try:
            spy_data = get_enhanced_stock_data("SPY")
            if spy_data and spy_data['history'] is not None:
                spy_hist = spy_data['history']
                if len(hist) > 0 and len(spy_hist) > 0:
                    stock_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                    spy_return = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0] - 1) * 100
                    rs_rating = 50 + (stock_return - spy_return) * 2
                    rs_rating = max(0, min(100, rs_rating))
        except:
            pass
        
        inst_ownership = info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0
        
        if market_analyzer is None:
            market_analyzer = MarketAnalyzer()
        try:
            market_data = market_analyzer.calculate_market_score()
            m_score = market_data['score']
            m_phase = market_data.get('phase', 'N/A')
        except:
            m_score = 50
            m_phase = 'N/A'
        
        volatility = calc.get('volatility', 0.2) * 100
        if volatility == 0:
            volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
        if np.isnan(volatility):
            volatility = 20.0
            
        try:
            price_momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100 if len(hist) >= 20 else 0
        except:
            price_momentum = 0
        
        # Calcular Score CAN SLIM
        score = 0
        grades = {}
        scores = {}
        
        if earnings_growth > 50: 
            score += 20; grades['C'] = 'A'; scores['C'] = 20
        elif earnings_growth > 25: 
            score += 15; grades['C'] = 'A'; scores['C'] = 15
        elif earnings_growth > 15: 
            score += 10; grades['C'] = 'B'; scores['C'] = 10
        elif earnings_growth > 0: 
            score += 5; grades['C'] = 'C'; scores['C'] = 5
        else: 
            grades['C'] = 'D'; scores['C'] = 0
        
        if eps_growth > 50: 
            score += 15; grades['A'] = 'A'; scores['A'] = 15
        elif eps_growth > 25: 
            score += 12; grades['A'] = 'A'; scores['A'] = 12
        elif eps_growth > 15: 
            score += 8; grades['A'] = 'B'; scores['A'] = 8
        elif eps_growth > 0: 
            score += 4; grades['A'] = 'C'; scores['A'] = 4
        else: 
            grades['A'] = 'D'; scores['A'] = 0
        
        if pct_from_high > -3: 
            score += 15; grades['N'] = 'A'; scores['N'] = 15
        elif pct_from_high > -10: 
            score += 12; grades['N'] = 'A'; scores['N'] = 12
        elif pct_from_high > -20: 
            score += 8; grades['N'] = 'B'; scores['N'] = 8
        elif pct_from_high > -30: 
            score += 4; grades['N'] = 'C'; scores['N'] = 4
        else: 
            grades['N'] = 'D'; scores['N'] = 0
        
        if volume_ratio > 2.0: 
            score += 10; grades['S'] = 'A'; scores['S'] = 10
        elif volume_ratio > 1.5: 
            score += 8; grades['S'] = 'A'; scores['S'] = 8
        elif volume_ratio > 1.0: 
            score += 5; grades['S'] = 'B'; scores['S'] = 5
        else: 
            score += 2; grades['S'] = 'C'; scores['S'] = 2
        
        if rs_rating > 90: 
            score += 15; grades['L'] = 'A'; scores['L'] = 15
        elif rs_rating > 80: 
            score += 12; grades['L'] = 'A'; scores['L'] = 12
        elif rs_rating > 70: 
            score += 8; grades['L'] = 'B'; scores['L'] = 8
        elif rs_rating > 60: 
            score += 4; grades['L'] = 'C'; scores['L'] = 4
        else: 
            grades['L'] = 'D'; scores['L'] = 0
        
        if inst_ownership > 80: 
            score += 10; grades['I'] = 'A'; scores['I'] = 10
        elif inst_ownership > 60: 
            score += 8; grades['I'] = 'A'; scores['I'] = 8
        elif inst_ownership > 40: 
            score += 5; grades['I'] = 'B'; scores['I'] = 5
        elif inst_ownership > 20: 
            score += 3; grades['I'] = 'C'; scores['I'] = 3
        else: 
            grades['I'] = 'D'; scores['I'] = 0
        
        if m_score >= 80: 
            score += 15; grades['M'] = 'A'; scores['M'] = 15
        elif m_score >= 60: 
            score += 10; grades['M'] = 'B'; scores['M'] = 10
        elif m_score >= 40: 
            score += 5; grades['M'] = 'C'; scores['M'] = 5
        else: 
            grades['M'] = 'D'; scores['M'] = 0
        
        ml_prob = 0.5
        try:
            ml_predictor = CANSlimMLPredictor()
            ml_prob = ml_predictor.predict({
                'earnings_growth': earnings_growth,
                'revenue_growth': revenue_growth,
                'eps_growth': eps_growth,
                'rs_rating': rs_rating,
                'volume_ratio': volume_ratio,
                'inst_ownership': inst_ownership,
                'pct_from_high': pct_from_high,
                'volatility': volatility / 100 if volatility else 0.2,
                'price_momentum': price_momentum
            })
        except:
            pass
        
        return {
            'ticker': ticker,
            'name': info.get('shortName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': market_cap,
            'price': current_price,
            'score': score,
            'ml_probability': ml_prob,
            'grades': grades,
            'scores': scores,
            'metrics': {
                'earnings_growth': earnings_growth,
                'revenue_growth': revenue_growth,
                'eps_growth': eps_growth,
                'pct_from_high': pct_from_high,
                'volume_ratio': volume_ratio,
                'rs_rating': rs_rating,
                'inst_ownership': inst_ownership,
                'market_score': m_score,
                'market_phase': m_phase,
                'volatility': volatility if not np.isnan(volatility) else 0,
                'price_momentum': price_momentum
            }
        }
        
    except Exception as e:
        return None

def scan_sp500(min_score=40, max_tickers=None):
    """Escanea los tickers del S&P 500"""
    candidates = []
    
    tickers_to_scan = SP500_TICKERS[:max_tickers] if max_tickers else SP500_TICKERS
    
    for i, ticker in enumerate(tickers_to_scan):
        result = calculate_can_slim_metrics(ticker, None)
        if result and result['score'] >= min_score:
            candidates.append(result)
    
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates

# ============================================================
# VISUALIZACIONES
# ============================================================

def create_score_gauge(score, title="CAN SLIM Score"):
    color = COLORS['primary'] if score >= 80 else COLORS['warning'] if score >= 60 else COLORS['danger']
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 14, 'color': 'white'}},
        number={'font': {'size': 36, 'color': color, 'family': 'Arial Black'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color, 'thickness': 0.75},
            'bgcolor': COLORS['bg_dark'],
            'borderwidth': 2,
            'bordercolor': COLORS['bg_card'],
            'steps': [
                {'range': [0, 60], 'color': hex_to_rgba(COLORS['danger'], 0.2)},
                {'range': [60, 80], 'color': hex_to_rgba(COLORS['warning'], 0.2)},
                {'range': [80, 100], 'color': hex_to_rgba(COLORS['primary'], 0.2)}
            ],
            'threshold': {'line': {'color': "white", 'width': 3}, 'thickness': 0.8, 'value': score}
        }
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        font={'color': "white"},
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_grades_radar(grades_dict):
    categories = ['C', 'A', 'N', 'S', 'L', 'I', 'M']
    values = []
    
    grade_map = {'A': 100, 'B': 75, 'C': 50, 'D': 25, 'F': 0}
    for cat in categories:
        values.append(grade_map.get(grades_dict.get(cat, 'F'), 0))
    
    values.append(values[0])
    categories.append(categories[0])
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 255, 173, 0.3)',
        line=dict(color=COLORS['primary'], width=2),
        marker=dict(size=8, color=COLORS['primary'])
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='white', gridcolor=COLORS['bg_card']),
            angularaxis=dict(color='white', gridcolor=COLORS['bg_card']),
            bgcolor=COLORS['bg_dark']
        ),
        paper_bgcolor=COLORS['bg_dark'],
        font=dict(color='white'),
        title=dict(text="Calificaciones CAN SLIM", font=dict(color='white', size=14)),
        height=350,
        margin=dict(l=60, r=60, t=50, b=40)
    )
    return fig

# ============================================================
# FUNCIÓN PRINCIPAL PARA STREAMLIT
# ============================================================

def render_canslim_tab():
    """
    Función principal que renderiza la pestaña CAN SLIM.
    Llámala desde app.py
    """
    
    # CSS
    st.markdown(f"""
    <style>
    .main {{ background: {COLORS['bg_dark']}; color: white; }}
    .stApp {{ background: {COLORS['bg_dark']}; }}
    h1, h2, h3 {{ color: white !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background: {COLORS['bg_dark']};
        color: #888;
        border: 1px solid {COLORS['bg_card']};
        border-radius: 8px 8px 0 0;
    }}
    .stTabs [aria-selected="true"] {{
        background: {COLORS['bg_card']};
        color: {COLORS['primary']};
        border-bottom: 2px solid {COLORS['primary']};
    }}
    .metric-card {{
        background: {COLORS['bg_dark']};
        border: 1px solid {COLORS['bg_card']};
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }}
    .grade-badge {{
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 6px;
        text-align: center;
        line-height: 30px;
        font-weight: bold;
        font-size: 14px;
        margin: 2px;
    }}
    .grade-A {{ background: rgba(0, 255, 173, 0.2); color: {COLORS['primary']}; border: 1px solid {COLORS['primary']}; }}
    .grade-B {{ background: rgba(255, 152, 0, 0.2); color: {COLORS['warning']}; border: 1px solid {COLORS['warning']}; }}
    .grade-C {{ background: rgba(242, 54, 69, 0.2); color: {COLORS['danger']}; border: 1px solid {COLORS['danger']}; }}
    .grade-D {{ background: rgba(136, 136, 136, 0.2); color: #888; border: 1px solid #888; }}
    .market-badge {{
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }}
    .sp500-badge {{
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        background: rgba(0, 255, 173, 0.2);
        color: {COLORS['primary']};
        border: 1px solid {COLORS['primary']};
    }}
    </style>
    """, unsafe_allow_html=True)

    # Header
    market_analyzer = MarketAnalyzer()
    market_status = market_analyzer.calculate_market_score()
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="font-size: 2.5rem; margin-bottom: 10px; color: {COLORS['primary']};">
            🎯 CAN SLIM Scanner Pro
        </h1>
        <p style="color: #888; font-size: 1.1rem;">S&P 500 Edition - v2.2.1</p>
        <div style="margin-top: 15px;">
            <span class="market-badge" style="background: {hex_to_rgba(market_status['color'], 0.2)}; color: {market_status['color']}; border: 1px solid {market_status['color']};">
                M-MARKET: {market_status['phase']} ({market_status['score']}/100)
            </span>
            <span class="sp500-badge" style="margin-left: 10px;">
                S&P 500: {len(SP500_TICKERS)} stocks
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs del módulo CAN SLIM
    tab1, tab2, tab3 = st.tabs([
        "🚀 Scanner S&P 500", 
        "📊 Análisis Detallado", 
        "⚙️ Configuración"
    ])

    # TAB 1: SCANNER
    with tab1:
        st.subheader(f"🔍 Scanner del S&P 500 ({len(SP500_TICKERS)} stocks)")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            min_score = st.slider("Score Mínimo CAN SLIM", 0, 100, 60, key="canslim_min_score")
        with col2:
            max_results = st.number_input("Máx Resultados", 5, 100, 20, key="canslim_max_results")
        with col3:
            limit_scan = st.checkbox("Limitar a 50", value=True, key="canslim_limit")
        
        scan_button = st.button("🚀 ESCANEAR S&P 500", type="primary", use_container_width=True, key="canslim_scan_btn")
        
        if scan_button:
            max_to_scan = 50 if limit_scan else None
            
            with st.spinner(f"Escaneando {max_to_scan if max_to_scan else len(SP500_TICKERS)} stocks..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                candidates = []
                tickers_to_scan = SP500_TICKERS[:max_to_scan] if max_to_scan else SP500_TICKERS
                
                for i, ticker in enumerate(tickers_to_scan):
                    progress = (i + 1) / len(tickers_to_scan)
                    progress_bar.progress(progress)
                    status_text.text(f"Analizando {ticker}... ({i+1}/{len(tickers_to_scan)})")
                    
                    result = calculate_can_slim_metrics(ticker, market_analyzer)
                    if result and result['score'] >= min_score:
                        candidates.append(result)
                
                progress_bar.empty()
                status_text.empty()
                
                candidates.sort(key=lambda x: x['score'], reverse=True)
            
            if candidates:
                st.success(f"✅ {len(candidates)} candidatos CAN SLIM encontrados")
                
                # Top 3
                cols = st.columns(min(3, len(candidates)))
                for i, col in enumerate(cols):
                    if i < len(candidates):
                        c = candidates[i]
                        with col:
                            st.plotly_chart(create_score_gauge(c['score']), use_container_width=True, key=f"canslim_gauge_{i}")
                            st.markdown(f"""
                            <div style="text-align: center;">
                                <h3 style="color: {COLORS['primary']}; margin: 0;">{c['ticker']}</h3>
                                <p style="color: #888; font-size: 12px;">{c['name'][:30]}</p>
                                <div>
                                    <span class="grade-badge grade-{c['grades']['C']}">C</span>
                                    <span class="grade-badge grade-{c['grades']['A']}">A</span>
                                    <span class="grade-badge grade-{c['grades']['N']}">N</span>
                                    <span class="grade-badge grade-{c['grades']['S']}">S</span>
                                    <span class="grade-badge grade-{c['grades']['L']}">L</span>
                                    <span class="grade-badge grade-{c['grades']['I']}">I</span>
                                    <span class="grade-badge grade-{c['grades']['M']}">M</span>
                                </div>
                                <p style="color: {COLORS['primary']}; font-size: 0.9rem;">ML: {c['ml_probability']:.0%}</p>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Tabla
                table_data = []
                for c in candidates[:max_results]:
                    table_data.append({
                        'Ticker': c['ticker'],
                        'Nombre': c['name'][:25],
                        'Score': c['score'],
                        'ML': f"{c['ml_probability']:.0%}",
                        'C': c['grades']['C'],
                        'A': c['grades']['A'],
                        'N': c['grades']['N'],
                        'S': c['grades']['S'],
                        'L': c['grades']['L'],
                        'I': c['grades']['I'],
                        'M': c['grades']['M'],
                        'EPS': f"{c['metrics']['earnings_growth']:.1f}%",
                        'RS': f"{c['metrics']['rs_rating']:.0f}",
                        'Sector': c['sector']
                    })
                
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, height=600)
                
                # Exportar
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Descargar CSV",
                    csv,
                    f"sp500_canslim_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key="canslim_download"
                )
            else:
                st.warning("⚠️ No se encontraron candidatos")

    # TAB 2: ANÁLISIS DETALLADO
    with tab2:
        st.subheader("📊 Análisis Individual - S&P 500")
        
        ticker_input = st.selectbox(
            "Seleccionar ticker del S&P 500",
            options=SP500_TICKERS,
            key="canslim_ticker_select"
        )
        
        ticker_manual = st.text_input("O ingresar manualmente", "", key="canslim_ticker_manual").strip().upper()
        ticker_to_analyze = ticker_manual if ticker_manual else ticker_input
        
        if st.button("🔍 Analizar", type="primary", key="canslim_analyze_btn"):
            if not ticker_to_analyze:
                st.error("❌ Selecciona o ingresa un ticker")
            else:
                with st.spinner(f"Analizando {ticker_to_analyze}..."):
                    result = calculate_can_slim_metrics(ticker_to_analyze, market_analyzer)
                    
                    if result:
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.plotly_chart(create_score_gauge(result['score']), use_container_width=True, key="canslim_detail_gauge")
                            st.plotly_chart(create_grades_radar(result['grades']), use_container_width=True, key="canslim_detail_radar")
                            
                            st.metric("RS Rating", f"{result['metrics']['rs_rating']:.0f}")
                            st.metric("ML Probability", f"{result['ml_probability']:.1%}")
                        
                        with col2:
                            # Gráfico de precios
                            try:
                                data = get_enhanced_stock_data(ticker_to_analyze)
                                if data and data['history'] is not None:
                                    hist = data['history']
                                    
                                    fig = go.Figure()
                                    fig.add_trace(go.Candlestick(
                                        x=hist.index,
                                        open=hist['Open'],
                                        high=hist['High'],
                                        low=hist['Low'],
                                        close=hist['Close'],
                                        name='Price'
                                    ))
                                    
                                    sma50 = hist['Close'].rolling(50).mean()
                                    sma200 = hist['Close'].rolling(200).mean()
                                    
                                    fig.add_trace(go.Scatter(x=hist.index, y=sma50, name='SMA 50',
                                                           line=dict(color=COLORS['warning'], width=1)))
                                    fig.add_trace(go.Scatter(x=hist.index, y=sma200, name='SMA 200',
                                                           line=dict(color=COLORS['primary'], width=1)))
                                    
                                    fig.update_layout(
                                        title=f"{result['name']} - ${result['price']:.2f}",
                                        paper_bgcolor=COLORS['bg_dark'],
                                        plot_bgcolor=COLORS['bg_dark'],
                                        font=dict(color='white'),
                                        height=500
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True, key="canslim_chart")
                            except:
                                pass
                            
                            # Métricas
                            metrics_df = pd.DataFrame({
                                'Métrica': ['Market Cap', 'EPS Growth', 'Revenue Growth', 'Inst. Ownership', 
                                          'Volume Ratio', 'From 52W High', 'Volatility', 'Price Momentum'],
                                'Valor': [
                                    f"${result['market_cap']:.2f}B" if result['market_cap'] > 0 else "N/A",
                                    f"{result['metrics']['earnings_growth']:.1f}%" if result['metrics']['earnings_growth'] != 0 else "N/A",
                                    f"{result['metrics']['revenue_growth']:.1f}%" if result['metrics']['revenue_growth'] != 0 else "N/A",
                                    f"{result['metrics']['inst_ownership']:.1f}%" if result['metrics']['inst_ownership'] != 0 else "N/A",
                                    f"{result['metrics']['volume_ratio']:.2f}x",
                                    f"{result['metrics']['pct_from_high']:.1f}%",
                                    f"{result['metrics']['volatility']:.1f}%",
                                    f"{result['metrics']['price_momentum']:.1f}%"
                                ]
                            })
                            st.table(metrics_df)
                    else:
                        st.error(f"❌ No se pudo analizar {ticker_to_analyze}")

    # TAB 3: CONFIGURACIÓN
    with tab3:
        st.subheader("⚙️ Configuración del Scanner S&P 500")
        
        st.markdown(f"""
        **Estado actual:**
        - Archivo de tickers: `{TICKERS_FILE}`
        - Tickers cargados: {len(SP500_TICKERS)}
        - Rate limiting: {YFSession._min_delay}s entre requests
        
        **Tickers cargados:**
        """)
        
        with st.expander(f"Ver {len(SP500_TICKERS)} tickers"):
            st.write(SP500_TICKERS)
        
        new_delay = st.slider("Delay entre requests (s)", 0.1, 5.0, float(YFSession._min_delay), 0.1, key="canslim_delay")
        YFSession._min_delay = new_delay

# ============================================================
# PARA EJECUCIÓN DIRECTA (TESTING)
# ============================================================

if __name__ == "__main__":
    # Si se ejecuta directamente, mostrar el módulo
    render_canslim_tab()
