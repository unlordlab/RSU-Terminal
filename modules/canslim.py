# -*- coding: utf-8 -*-
"""
CAN SLIM Scanner Pro - Versión 2.2.0
S&P 500 Scanner - Lee tickers desde tickers.txt
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
from functools import lru_cache
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

TICKERS_FILE = "tickers.txt"  # Archivo de tickers del S&P 500

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
                    st.warning(f"⏳ Rate limit detectado. Esperando {sleep_time:.1f}s... (intento {attempt + 1}/{max_retries})")
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
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    from threading import Thread
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from zipline.api import order_target_percent, record, symbol, set_benchmark
    from zipline import run_algorithm
    from zipline.data import bundles
    ZIPPILINE_AVAILABLE = True
except ImportError:
    ZIPPILINE_AVAILABLE = False

# ============================================================
# GESTIÓN DE TICKERS S&P 500 DESDE ARCHIVO .TXT
# ============================================================

def load_sp500_tickers():
    """
    Carga los tickers del S&P 500 desde tickers.txt
    Formato esperado: un ticker por línea, o separados por comas
    """
    try:
        if not os.path.exists(TICKERS_FILE):
            st.error(f"❌ No se encontró el archivo {TICKERS_FILE} en el directorio raíz")
            st.info("💡 Crea un archivo tickers.txt con los tickers del S&P 500, uno por línea")
            return get_default_sp500_tickers()  # Fallback a lista por defecto
        
        with open(TICKERS_FILE, 'r') as f:
            content = f.read()
        
        # Intentar parsear: primero por líneas, luego por comas
        tickers = []
        
        # Si hay saltos de línea, usar eso
        if '\n' in content:
            tickers = [line.strip() for line in content.split('\n') if line.strip()]
        else:
            # Si no, intentar separar por comas
            tickers = [t.strip() for t in content.split(',') if t.strip()]
        
        # Limpiar y validar tickers
        valid_tickers = []
        for t in tickers:
            t_clean = str(t).strip().upper()
            # Remover símbolos comunes de formato
            t_clean = re_module.sub(r'[^\w\.\-]', '', t_clean)
            if t_clean and len(t_clean) <= 5:
                valid_tickers.append(t_clean)
        
        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_tickers = [t for t in valid_tickers if not (t in seen or seen.add(t))]
        
        if len(unique_tickers) == 0:
            st.warning("⚠️ No se encontraron tickers válidos en el archivo")
            return get_default_sp500_tickers()
        
        return unique_tickers

    except Exception as e:
        st.error(f"❌ Error al cargar {TICKERS_FILE}: {str(e)}")
        return get_default_sp500_tickers()

def get_default_sp500_tickers():
    """Lista por defecto de principales tickers del S&P 500 si no hay archivo"""
    default_tickers = [
        'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'META', 'GOOG', 'TSLA', 'BRK-B', 'UNH',
        'JPM', 'XOM', 'JNJ', 'V', 'PG', 'HD', 'MA', 'CVX', 'LLY', 'MRK',
        'PEP', 'KO', 'ABBV', 'AVGO', 'COST', 'TMO', 'DIS', 'ABT', 'WMT', 'ACN',
        'MCD', 'VZ', 'DHR', 'NKE', 'TXN', 'CRM', 'ADBE', 'PM', 'NEE', 'BMY',
        'RTX', 'HON', 'UNP', 'QCOM', 'UPS', 'LOW', 'LIN', 'AMGN', 'SPGI', 'MDT'
    ]
    st.warning(f"⚠️ Usando lista por defecto de {len(default_tickers)} tickers")
    return default_tickers

def save_sp500_tickers(tickers_list):
    """Guarda lista de tickers al archivo (útil para actualizar)"""
    try:
        with open(TICKERS_FILE, 'w') as f:
            for ticker in tickers_list:
                f.write(f"{ticker}\n")
        return True
    except Exception as e:
        st.error(f"❌ Error guardando tickers: {e}")
        return False

# Variable global de tickers
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
        
        # Scraping de tabla de estadísticas
        stats_url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
        response = requests.get(stats_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
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
        st.error(f"❌ No se pudo conectar con Yahoo Finance para {ticker}: {e}")
        return None
    
    try:
        hist = stock.history(period="1y")
        if hist is not None and not hist.empty and len(hist) >= 50:
            result['history'] = hist
        else:
            st.error(f"❌ Datos históricos insuficientes para {ticker}")
            return None
    except Exception as e:
        st.error(f"❌ Error obteniendo historial: {e}")
        return None
    
    # Obtener datos fundamentales de múltiples fuentes
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
            'last_price': getattr(fast, 'last_price', None),
            'fifty_two_week_high': getattr(fast, 'fifty_two_week_high', None),
            'fifty_two_week_low': getattr(fast, 'fifty_two_week_low', None)
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
    
    def train(self, historical_data):
        if not SKLEARN_AVAILABLE:
            return 0.0
            
        X = []
        y = []
        
        for stock_data in historical_data:
            features = self.prepare_features(stock_data['metrics'])
            if features is not None:
                X.append(features[0])
                y.append(1 if stock_data['future_return'] > stock_data['market_return'] else 0)
        
        if len(X) < 10:
            return 0.0
            
        X = np.array(X)
        y = np.array(y)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        self.model.fit(X_train, y_train)
        
        joblib.dump((self.model, self.scaler), self.model_path)
        return self.model.score(X_test, y_test)
    
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
            st.error("❌ Ticker vacío")
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
        
        # Calcular Score
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
        st.error(f"❌ Error analizando {ticker}: {str(e)}")
        return None

@st.cache_data(ttl=600)
def scan_sp500(min_score=40, _market_analyzer=None, max_tickers=None):
    """Escanea solo los tickers del S&P 500 desde el archivo"""
    candidates = []
    
    tickers_to_scan = SP500_TICKERS[:max_tickers] if max_tickers else SP500_TICKERS
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers_to_scan):
        progress = (i + 1) / len(tickers_to_scan)
        progress_bar.progress(progress)
        status_text.text(f"Analizando {ticker}... ({i+1}/{len(tickers_to_scan)}) [S&P 500]")
        
        result = calculate_can_slim_metrics(ticker, None)
        if result and result['score'] >= min_score:
            candidates.append(result)
    
    progress_bar.empty()
    status_text.empty()
    
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

def create_market_dashboard(market_data):
    if not market_data or 'data' not in market_data:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('S&P 500 Trend', 'NASDAQ 100', 'Russell 2000', 'VIX Volatility'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    indices = ['SPY', 'QQQ', 'IWM', 'VIX']
    colors = [COLORS['primary'], '#2962FF', '#00BCD4', COLORS['danger']]
    
    for idx, (ticker, color) in enumerate(zip(indices, colors)):
        row = idx // 2 + 1
        col = idx % 2 + 1
        
        if ticker in market_data['data']:
            data = market_data['data'][ticker]['data']
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    name=ticker,
                    line=dict(color=color, width=2),
                    fill='tozeroy',
                    fillcolor=hex_to_rgba(color, 0.1)
                ),
                row=row, col=col
            )
            
            if len(data) >= 50:
                sma50 = data['Close'].rolling(50).mean()
                fig.add_trace(
                    go.Scatter(
                        x=data.index,
                        y=sma50,
                        name=f'{ticker} SMA50',
                        line=dict(color=color, width=1, dash='dash')
                    ),
                    row=row, col=col
                )
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_dark'],
        font=dict(color='white'),
        showlegend=False,
        height=600,
        title=dict(
            text=f"Market Direction Score: {market_data['score']}/100 - {market_data['phase']}",
            font=dict(size=16, color=market_data['color'])
        )
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['bg_card'], color='white')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLORS['bg_card'], color='white')
    
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
        title=dict(text="Calificaciones CAN SLIM Completas", font=dict(color='white', size=14)),
        height=350,
        margin=dict(l=60, r=60, t=50, b=40)
    )
    return fig

def create_ml_feature_importance(predictor):
    importance = predictor.get_feature_importance()
    if not importance:
        return go.Figure()
    
    features = list(importance.keys())
    values = list(importance.values())
    
    fig = go.Figure(go.Bar(
        x=features,
        y=values,
        marker_color=COLORS['primary'],
        text=[f'{v:.2%}' for v in values],
        textposition='auto'
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['bg_dark'],
        plot_bgcolor=COLORS['bg_dark'],
        font=dict(color='white'),
        title=dict(text="Importancia de Factores ML", font=dict(color='white')),
        xaxis=dict(color='white', gridcolor=COLORS['bg_card']),
        yaxis=dict(color='white', gridcolor=COLORS['bg_card']),
        height=300
    )
    return fig

# ============================================================
# FASTAPI
# ============================================================

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="CAN SLIM Pro API - S&P 500",
        description="API para análisis CAN SLIM del S&P 500",
        version="2.2.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class TickerRequest(BaseModel):
        ticker: str
        include_ml: bool = True

    @app.get("/")
    async def root():
        return {
            "message": "CAN SLIM Pro API - S&P 500 Scanner",
            "version": "2.2.0",
            "universe": f"S&P 500 ({len(SP500_TICKERS)} tickers)"
        }

    @app.get("/market/status")
    async def get_market_status():
        analyzer = MarketAnalyzer()
        return analyzer.calculate_market_score()

    @app.post("/analyze")
    async def analyze_ticker(request: TickerRequest):
        analyzer = MarketAnalyzer()
        result = calculate_can_slim_metrics(request.ticker, analyzer)
        if result is None:
            raise HTTPException(status_code=404, detail=f"No se pudo analizar {request.ticker}")
        return result

    @app.get("/sp500/list")
    async def get_sp500_list():
        return {"count": len(SP500_TICKERS), "tickers": SP500_TICKERS}

    def run_api_server():
        uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    app = None

# ============================================================
# CONTENIDO EDUCATIVO
# ============================================================

EDUCATIONAL_CONTENT = {
    "guia_completa": """
    ### 📚 Guía Completa CAN SLIM
    
    **C - Current Quarterly Earnings**
    - Buscar crecimiento >25% vs mismo trimestre año anterior
    - Idealmente >50% o aceleración quarter-over-quarter
    
    **A - Annual Earnings Growth**
    - Crecimiento EPS últimos 3-5 años >25% anual
    - ROE >17%
    
    **N - New Products, New Management, New Highs**
    - Lanzamientos innovadores, cambios de CEO, máximos históricos
    
    **S - Supply and Demand**
    - Volumen superior al promedio (1.5x - 3x)
    - Float bajo
    
    **L - Leader or Laggard**
    - RS Rating >80
    - Top 10% de rendimiento en su sector
    
    **I - Institutional Sponsorship**
    - Fondos institucionales >40% del float
    
    **M - Market Direction**
    - No operar contra la tendencia
    - Confirmar uptrend con índices sobre SMA 50/200
    """,
    
    "reglas_operacion": """
    ### 📋 Reglas de Operación
    
    **Entradas:**
    - Breakout desde base de consolidación + volumen
    - Máximo 10-12% por posición inicial
    - 5-10 stocks diversificados
    
    **Gestión de Riesgo:**
    - Stop Loss: 7-8% máximo
    - Profit Taking: 20-25%
    - Trailing Stop: Breakeven cuando suba 8-10%
    """,
    
    "senales_venta": """
    ### 🚨 Señales de Venta
    
    1. Climax Top (subida parabólica + volumen extremo)
    2. Pérdida de SMA 50 con volumen
    3. Desaceleración de earnings (2 trimestres)
    4. Cambio en dirección del mercado (M)
    5. Stop loss de 7-8% alcanzado
    """,
    
    "errores_comunes": """
    ### ⚠️ Errores a Evitar
    
    1. Promediar a la baja
    2. Ignorar el factor M (Market)
    3. Operar sin stop loss
    4. Posiciones muy grandes (>20%)
    5. Comprar antes de earnings
    """,
    
    "recursos_adicionales": """
    ### 📖 Recursos
    
    **Libros:**
    - How to Make Money in Stocks (William O'Neil)
    - The Successful Investor
    
    **Herramientas:**
    - Investor's Business Daily
    - MarketSmith
    - TradingView
    """
}

# ============================================================
# RENDER PRINCIPAL - S&P 500 FOCUSED
# ============================================================

def render():
    # CSS Global
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
        <p style="color: #888; font-size: 1.1rem;">S&P 500 Edition - v2.2.0</p>
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

    # Info del sistema
    with st.expander("ℹ️ Información del Sistema"):
        st.markdown(f"""
        **S&P 500 Scanner v2.2.0**
        
        - **Universo:** {len(SP500_TICKERS)} tickers del S&P 500
        - **Archivo fuente:** `{TICKERS_FILE}`
        - **Rate limiting:** {YFSession._min_delay}s entre requests
        - **Cache:** {len(YFSession._cache)} tickers en memoria
        
        **Módulos opcionales:**
        - scikit-learn: {'✅' if SKLEARN_AVAILABLE else '❌'}
        - FastAPI: {'✅' if FASTAPI_AVAILABLE else '❌'}
        - Zipline: {'✅' if ZIPPILINE_AVAILABLE else '❌'}
        """)
        
        # Gestión de archivo de tickers
        st.subheader("📁 Gestión de Tickers S&P 500")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Recargar tickers.txt"):
                global SP500_TICKERS
                SP500_TICKERS = load_sp500_tickers()
                st.success(f"✅ Recargados {len(SP500_TICKERS)} tickers")
        
        with col2:
            with st.expander("👁️ Ver tickers cargados"):
                st.write(SP500_TICKERS)
        
        # Editor de tickers
        st.subheader("✏️ Editor de Tickers")
        new_tickers = st.text_area(
            "Editar lista de tickers (uno por línea)",
            value="\n".join(SP500_TICKERS),
            height=200
        )
        if st.button("💾 Guardar cambios a tickers.txt"):
            tickers_list = [t.strip().upper() for t in new_tickers.split('\n') if t.strip()]
            if save_sp500_tickers(tickers_list):
                SP500_TICKERS = tickers_list
                st.success(f"✅ Guardados {len(tickers_list)} tickers")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🚀 Scanner S&P 500", 
        "📊 Análisis Detallado", 
        "📚 Metodología",
        "🤖 ML Predictivo",
        "📈 Backtesting",
        "⚙️ Configuración"
    ])

    # TAB 1: SCANNER S&P 500
    with tab1:
        st.subheader(f"🔍 Scanner del S&P 500 ({len(SP500_TICKERS)} stocks)")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            min_score = st.slider("Score Mínimo CAN SLIM", 0, 100, 60)
        with col2:
            max_results = st.number_input("Máx Resultados", 5, 100, 20)
        with col3:
            limit_scan = st.checkbox("Limitar a 50", value=True,
                                   help="Escanea solo los primeros 50 para pruebas rápidas")
        
        scan_button = st.button("🚀 ESCANEAR S&P 500", type="primary", use_container_width=True)
        
        with st.expander("📊 Condiciones de Mercado"):
            market_fig = create_market_dashboard(market_status)
            st.plotly_chart(market_fig, use_container_width=True)
            for signal in market_status['signals']:
                st.markdown(f"- {signal}")
        
        if scan_button:
            max_to_scan = 50 if limit_scan else None
            
            st.info(f"⏳ Escaneando {max_to_scan if max_to_scan else len(SP500_TICKERS)} stocks del S&P 500...")
            st.warning("⚠️ Esto puede tomar varios minutos debido al rate limiting")
            
            candidates = scan_sp500(min_score, None, max_to_scan)
            
            if candidates:
                st.success(f"✅ {len(candidates)} candidatos CAN SLIM encontrados en S&P 500")
                
                # Top 3 destacados
                cols = st.columns(min(3, len(candidates)))
                for i, col in enumerate(cols):
                    if i < len(candidates):
                        c = candidates[i]
                        with col:
                            st.plotly_chart(create_score_gauge(c['score']), use_container_width=True, key=f"gauge_{i}")
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
                
                # Tabla completa
                st.subheader("📋 Resultados Detallados - S&P 500")
                
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
                        'EPS Growth': f"{c['metrics']['earnings_growth']:.1f}%",
                        'RS Rating': f"{c['metrics']['rs_rating']:.0f}",
                        'Sector': c['sector']
                    })
                
                df = pd.DataFrame(table_data)
                
                def color_score(val):
                    try:
                        score = int(val)
                        color = COLORS['primary'] if score >= 80 else COLORS['warning'] if score >= 60 else COLORS['danger']
                        return f'color: {color}; font-weight: bold'
                    except:
                        return ''
                
                def color_grade(val):
                    color_map = {'A': COLORS['primary'], 'B': COLORS['warning'], 'C': COLORS['danger'], 'D': '#888888'}
                    return f'color: {color_map.get(val, "white")}; font-weight: bold'
                
                styled_df = df.style\
                    .applymap(color_score, subset=['Score'])\
                    .applymap(color_grade, subset=['C', 'A', 'N', 'S', 'L', 'I', 'M'])
                
                st.dataframe(styled_df, use_container_width=True, height=600)
                
                # Exportar
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Descargar CSV (S&P 500)",
                    csv,
                    f"sp500_canslim_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            else:
                st.warning("⚠️ No se encontraron candidatos con los criterios seleccionados")

    # TAB 2: ANÁLISIS DETALLADO
    with tab2:
        st.subheader("📊 Análisis Individual - S&P 500")
        
        # Dropdown con tickers del S&P 500
        ticker_input = st.selectbox(
            "Seleccionar ticker del S&P 500",
            options=SP500_TICKERS,
            index=0 if SP500_TICKERS else None
        )
        
        # O input manual como alternativa
        ticker_manual = st.text_input("O ingresar manualmente", "").strip().upper()
        
        ticker_to_analyze = ticker_manual if ticker_manual else ticker_input
        
        if st.button("🔍 Analizar", type="primary"):
            if not ticker_to_analyze:
                st.error("❌ Selecciona o ingresa un ticker")
            else:
                with st.spinner(f"Analizando {ticker_to_analyze}..."):
                    result = calculate_can_slim_metrics(ticker_to_analyze, market_analyzer)
                    
                    if result:
                        st.success(f"✅ {ticker_to_analyze} analizado")
                        
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.plotly_chart(create_score_gauge(result['score']), use_container_width=True)
                            st.plotly_chart(create_grades_radar(result['grades']), use_container_width=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <h4>RS Rating</h4>
                                <h2 style="color: {COLORS['primary'] if result['metrics']['rs_rating'] > 80 else COLORS['warning'] if result['metrics']['rs_rating'] > 60 else COLORS['danger']};">
                                    {result['metrics']['rs_rating']:.0f}
                                </h2>
                            </div>
                            <div class="metric-card" style="margin-top: 10px;">
                                <h4>ML Probability</h4>
                                <h2 style="color: {COLORS['primary'] if result['ml_probability'] > 0.7 else COLORS['warning'] if result['ml_probability'] > 0.5 else COLORS['danger']};">
                                    {result['ml_probability']:.1%}
                                </h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
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
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error en gráfico: {e}")
                            
                            # Métricas
                            metrics_df = pd.DataFrame({
                                'Métrica': [
                                    'Market Cap', 'EPS Growth', 'Revenue Growth',
                                    'Inst. Ownership', 'Volume Ratio', 'From 52W High',
                                    'Volatility', 'Price Momentum', 'Market Score'
                                ],
                                'Valor': [
                                    f"${result['market_cap']:.2f}B" if result['market_cap'] > 0 else "N/A",
                                    f"{result['metrics']['earnings_growth']:.1f}%" if result['metrics']['earnings_growth'] != 0 else "N/A",
                                    f"{result['metrics']['revenue_growth']:.1f}%" if result['metrics']['revenue_growth'] != 0 else "N/A",
                                    f"{result['metrics']['inst_ownership']:.1f}%" if result['metrics']['inst_ownership'] != 0 else "N/A",
                                    f"{result['metrics']['volume_ratio']:.2f}x",
                                    f"{result['metrics']['pct_from_high']:.1f}%",
                                    f"{result['metrics']['volatility']:.1f}%",
                                    f"{result['metrics']['price_momentum']:.1f}%",
                                    f"{result['metrics']['market_score']:.0f}/100"
                                ]
                            })
                            st.table(metrics_df)
                            
                            if result['market_cap'] == 0 or result['metrics']['earnings_growth'] == 0:
                                st.info("ℹ️ Algunos datos fundamentales no están disponibles vía Yahoo Finance")
                    else:
                        st.error(f"❌ No se pudo analizar {ticker_to_analyze}")

    # TAB 3: METODOLOGÍA
    with tab3:
        st.markdown(EDUCATIONAL_CONTENT["guia_completa"])
        st.markdown(EDUCATIONAL_CONTENT["reglas_operacion"])
        st.markdown(EDUCATIONAL_CONTENT["senales_venta"])
        st.markdown(EDUCATIONAL_CONTENT["errores_comunes"])
        st.markdown(EDUCATIONAL_CONTENT["recursos_adicionales"])

    # TAB 4: ML
    with tab4:
        st.header("🤖 ML Predictivo")
        if not SKLEARN_AVAILABLE:
            st.warning("Instala: `pip install scikit-learn joblib`")
        else:
            ml = CANSlimMLPredictor()
            st.plotly_chart(create_ml_feature_importance(ml), use_container_width=True)
            
            pred_ticker = st.selectbox("Ticker del S&P 500 para predicción", SP500_TICKERS)
            if st.button("Predecir"):
                result = calculate_can_slim_metrics(pred_ticker, market_analyzer)
                if result:
                    prob = result['ml_probability']
                    color = COLORS['primary'] if prob > 0.7 else COLORS['warning'] if prob > 0.5 else COLORS['danger']
                    st.markdown(f"""
                    <div style="background: {COLORS['bg_card']}; padding: 20px; border-radius: 10px; text-align: center;">
                        <h3>Probabilidad de Outperformance</h3>
                        <h1 style="color: {color}; font-size: 4rem;">{prob:.1%}</h1>
                    </div>
                    """, unsafe_allow_html=True)

    # TAB 5: BACKTESTING
    with tab5:
        st.header("📈 Backtesting")
        if not ZIPPILINE_AVAILABLE:
            st.warning("Instala: `pip install zipline-reloaded`")
        else:
            st.info("Backtesting disponible con datos del S&P 500")

    # TAB 6: CONFIGURACIÓN
    with tab6:
        st.header("⚙️ Configuración del Scanner S&P 500")
        
        st.subheader("Rate Limiting")
        new_delay = st.slider("Delay entre requests (s)", 0.1, 5.0, float(YFSession._min_delay), 0.1)
        YFSession._min_delay = new_delay
        
        st.markdown(f"""
        **Configuración actual:**
        - Archivo de tickers: `{TICKERS_FILE}`
        - Tickers cargados: {len(SP500_TICKERS)}
        - Delay: {YFSession._min_delay}s
        - Cache: {len(YFSession._cache)} items
        
        **Para actualizar el S&P 500:**
        1. Edita el archivo `tickers.txt` en el directorio raíz
        2. Agrega un ticker por línea
        3. Usa el botón "Recargar tickers.txt" en el panel de información
        """)

if __name__ == "__main__":
    render()
