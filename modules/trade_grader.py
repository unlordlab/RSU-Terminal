# -*- coding: utf-8 -*-
"""
RSU MARKET THEMES - DATOS REALES VIA YAHOO FINANCE
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import time

# Cache para no saturar la API de Yahoo
@st.cache_data(ttl=300)  # Cache 5 minutos
def download_data_cached(symbol, period, interval):
    """Descarga datos con cache y manejo de errores"""
    try:
        data = yf.download(
            symbol, 
            period=period, 
            interval=interval, 
            progress=False, 
            auto_adjust=True,
            timeout=10
        )
        return data
    except Exception as e:
        st.error(f"Error descargando {symbol}: {e}")
        return pd.DataFrame()

def flatten_columns(df):
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df

def ensure_1d_series(data):
    if isinstance(data, pd.DataFrame):
        if data.shape[1] == 1:
            return data.iloc[:, 0]
        if 'Close' in data.columns:
            return data['Close']
        return data.iloc[:, 0]
    return data

def calculate_ema(prices, period):
    prices = ensure_1d_series(prices)
    return prices.ewm(span=period, adjust=False).mean()

def calculate_rsi(prices, period=14):
    prices = ensure_1d_series(prices)
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_theme_symbol_real(symbol, tf_config):
    """
    ANÁLISIS REAL CON DATOS DE YAHOO FINANCE
    Retorna diccionario con métricas calculadas sobre datos reales
    """
    try:
        # 1. DESCARGA REAL DE DATOS
        data = download_data_cached(symbol, tf_config["period"], tf_config["interval"])
        
        if data.empty or len(data) < 30:
            return None
            
        data = flatten_columns(data)
        
        # 2. CÁLCULOS REALES SOBRE PRECIOS REALES
        close = ensure_1d_series(data['Close'])
        
        # EMAs reales
        ema_fast = calculate_ema(close, tf_config["ema_fast"])
        ema_slow = calculate_ema(close, tf_config["ema_slow"])
        
        # Tendencia real basada en cruce EMA
        last_fast = float(ema_fast.iloc[-1])
        last_slow = float(ema_slow.iloc[-1])
        last_price = float(close.iloc[-1])
        
        trend = "BULLISH" if last_fast > last_slow else "BEARISH"
        
        # Fuerza de tendencia real (distancia entre EMAs como % del precio)
        spread_pct = abs(last_fast - last_slow) / last_price * 100
        trend_strength = min(spread_pct * 10, 100)  # Normalizar a 0-100
        
        # 3. MOMENTUM REAL (RSI)
        rsi_series = calculate_rsi(close)
        momentum = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
        
        # 4. PERFORMANCE REAL DEL PERÍODO
        first_price = float(close.iloc[0])
        last_price = float(close.iloc[-1])
        performance = ((last_price - first_price) / first_price) * 100
        
        # 5. VOLATILIDAD REAL (desviación estándar anualizada)
        returns = close.pct_change().dropna()
        if len(returns) >= 20:
            current_vol = float(returns.tail(20).std() * np.sqrt(252) * 100)
        else:
            current_vol = 0
            
        if current_vol < 15:
            vol_regime, vol_color = "BAJA", "#00ffad"
        elif current_vol < 30:
            vol_regime, vol_color = "MODERADA", "#ff9800"
        else:
            vol_regime, vol_color = "ALTA", "#f23645"
        
        # 6. VOLUMEN REAL (si está disponible)
        vol_ratio = 1.0
        if 'Volume' in data.columns:
            volume = ensure_1d_series(data['Volume'])
            if len(volume) >= 20:
                avg_vol = float(volume.tail(20).mean())
                current_vol_val = float(volume.iloc[-1])
                vol_ratio = current_vol_val / avg_vol if avg_vol > 0 else 1.0
        
        return {
            "symbol": symbol,
            "trend": trend,
            "trend_strength": trend_strength,
            "spread": spread_pct,
            "momentum": momentum,
            "performance": performance,
            "volatility_regime": vol_regime,
            "volatility_value": current_vol,
            "volatility_color": vol_color,
            "volume_ratio": vol_ratio,
            "price": last_price,
            "ema_fast": last_fast,
            "ema_slow": last_slow,
            "data": data,  # DataFrame completo para gráficos
            "last_updated": datetime.now().strftime("%H:%M:%S")
        }
        
    except Exception as e:
        st.warning(f"Error analizando {symbol}: {str(e)}")
        return None

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE TEMAS (120+ ACTIVOS REALES)
# ────────────────────────────────────────────────

THEMES_CONFIG = {
    "AI_REVOLUTION": {
        "name": "🤖 Revolución IA",
        "description": "NVIDIA, AMD, TSMC, Broadcom - Chips para IA generativa",
        "symbols": ["NVDA", "AMD", "TSM", "AVGO", "ARM", "SMCI", "PLTR", "MSFT", "GOOGL", "AMZN"],
        "color": "#00ffad",
        "icon": "🧠"
    },
    "SEMICONDUCTOR_CYCLE": {
        "name": "⚡ Ciclo Semiconductores",
        "description": "Ciclos de inventario: Micron, Intel, Lam Research",
        "symbols": ["NVDA", "AMD", "INTC", "MU", "LRCX", "AMAT", "KLAC", "ASML", "QCOM", "TXN"],
        "color": "#00d9ff",
        "icon": "🔌"
    },
    "CLEAN_ENERGY": {
        "name": "🌱 Energía Limpia",
        "description": "Solar, EVs, Nuclear: Tesla, Enphase, Constellation",
        "symbols": ["TSLA", "ENPH", "SEDG", "FSLR", "NXT", "NEE", "CEG", "SMR", "OKLO", "PLUG"],
        "color": "#4caf50",
        "icon": "⚡"
    },
    "DEFENSE_SPACE": {
        "name": "🚀 Defensa & Aeroespacial",
        "description": "Lockheed, Northrop, Raytheon, SpaceX-adjacent",
        "symbols": ["LMT", "NOC", "RTX", "GD", "BA", "SPCE", "RKLB", "ASTS"],
        "color": "#ff6d00",
        "icon": "🛰️"
    },
    "BIOTECH_INNOVATION": {
        "name": "🧬 Biotech & Pharma",
        "description": "GLP-1, Gene editing: Eli Lilly, Novo Nordisk, Vertex",
        "symbols": ["LLY", "NVO", "MRK", "JNJ", "PFE", "AMGN", "GILD", "REGN", "VRTX", "CRSP"],
        "color": "#9c27b0",
        "icon": "💊"
    },
    "CRYPTO_INFRASTRUCTURE": {
        "name": "₿ Infraestructura Crypto",
        "description": "Coinbase, MicroStrategy, Mineros Bitcoin",
        "symbols": ["COIN", "MSTR", "RIOT", "MARA", "CLSK", "BITF", "HOOD"],
        "color": "#ff9800",
        "icon": "⛏️"
    },
    "CYBERSECURITY": {
        "name": "🔒 Ciberseguridad",
        "description": "CrowdStrike, Palo Alto, Zscaler - Seguridad endpoint",
        "symbols": ["CRWD", "PANW", "FTNT", "ZS", "OKTA", "CYBR", "S", "NET"],
        "color": "#f23645",
        "icon": "🛡️"
    },
    "GOLD_PRECIOUS": {
        "name": " Oro & Metales",
        "description": "Oro físico (ETFs) y mineras: Newmont, Barrick",
        "symbols": ["GLD", "IAU", "NEM", "GOLD", "FNV", "WPM", "RGLD", "AU"],
        "color": "#ffc107",
        "icon": "⛏️"
    }
}

TIMEFRAMES = {
    "INTRADAY": {
        "label": "⚡ INTRADÍA",
        "period": "5d",
        "interval": "15m",
        "ema_fast": 9,
        "ema_slow": 21,
        "color": "#f23645"
    },
    "SWING": {
        "label": "📊 SWING",
        "period": "1mo",
        "interval": "1h",
        "ema_fast": 20,
        "ema_slow": 50,
        "color": "#ff9800"
    },
    "POSITIONAL": {
        "label": "📈 POSITIONAL",
        "period": "3mo",
        "interval": "1d",
        "ema_fast": 20,
        "ema_slow": 50,
        "color": "#00ffad"
    }
}

# ────────────────────────────────────────────────
# UI COMPONENTS
# ────────────────────────────────────────────────

def render_real_metric_card(title, value, subtitle, color, icon=""):
    st.markdown(f"""
    <div style="background:#0c0e12; padding:15px; border-radius:10px; border:1px solid #1a1e26; text-align:center;">
        <div style="color:#888; font-size:11px; text-transform:uppercase; margin-bottom:5px;">{title}</div>
        <div style="color:{color}; font-size:28px; font-weight:bold;">{icon} {value}</div>
        <div style="color:#666; font-size:10px; margin-top:5px;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_market_themes_real_data():
    """Versión con datos reales de Yahoo Finance"""
    
    st.markdown("""
    <style>
        .stApp { background: #0c0e12; }
        h1, h2, h3 { color: white !important; }
        div[data-testid="stButton"] > button[kind="primary"] {
            background: #00ffad;
            color: #0c0e12;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="font-size: 2.5rem; color: #00ffad; text-shadow: 0 0 20px #00ffad44;">
            🎯 RSU MARKET THEMES
        </h1>
        <p style="color: #888;">Datos reales vía Yahoo Finance • Actualización en tiempo real</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Selector temporalidad
    tf_cols = st.columns(3)
    selected_tf = "SWING"
    
    for i, (tf_key, tf_data) in enumerate(TIMEFRAMES.items()):
        with tf_cols[i]:
            if st.button(
                f"{tf_data['label']}",
                key=f"tf_{tf_key}",
                use_container_width=True,
                type="primary" if tf_key == selected_tf else "secondary"
            ):
                selected_tf = tf_key
                st.session_state.selected_tf = tf_key
    
    if "selected_tf" in st.session_state:
        selected_tf = st.session_state.selected_tf
    
    tf_config = TIMEFRAMES[selected_tf]
    
    # Info de datos reales
    st.info(f"""
    📡 **Datos Reales Activos**: Periodo `{tf_config['period']}` | Intervalo `{tf_config['interval']}` | 
    EMAs {tf_config['ema_fast']}/{tf_config['ema_slow']} | 
    Fuente: Yahoo Finance (15min delay)
    """)
    
    if st.button("🚀 ESCANEAR MERCADO REAL", type="primary", use_container_width=True):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = {}
        total_symbols = sum(len(t["symbols"]) for t in THEMES_CONFIG.values())
        processed = 0
        
        # Analizar todos los temas con datos reales
        for theme_key, theme in THEMES_CONFIG.items():
            status_text.text(f"Analizando {theme['name']}...")
            
            theme_results = []
            for symbol in theme["symbols"]:
                result = analyze_theme_symbol_real(symbol, tf_config)
                if result:
                    theme_results.append(result)
                processed += 1
                progress_bar.progress(min(processed / total_symbols, 1.0))
                time.sleep(0.1)  # Rate limiting amable
            
            all_results[theme_key] = theme_results
        
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados reales
        st.success(f"✅ Análisis completado a las {datetime.now().strftime('%H:%M:%S')}")
        
        # Grid de tarjetas con datos reales
        cols = st.columns(2)
        col_idx = 0
        
        for theme_key, theme in THEMES_CONFIG.items():
            results = all_results[theme_key]
            valid = [r for r in results if r is not None]
            
            if not valid:
                continue
            
            with cols[col_idx % 2]:
                # Métricas reales calculadas
                bullish = len([r for r in valid if r["trend"] == "BULLISH"])
                total = len(valid)
                bullish_pct = (bullish / total * 100) if total > 0 else 0
                avg_momentum = np.mean([r["momentum"] for r in valid])
                avg_perf = np.mean([r["performance"] for r in valid])
                
                # Determinar color de sentimiento
                if bullish_pct >= 70:
                    sent_color = "#00ffad"
                    sentiment = "ALCISTA FUERTE"
                elif bullish_pct >= 50:
                    sent_color = "#4caf50"
                    sentiment = "ALCISTA"
                elif bullish_pct >= 30:
                    sent_color = "#ff9800"
                    sentiment = "MIXTO"
                else:
                    sent_color = "#f23645"
                    sentiment = "BAJISTA"
                
                # Tarjeta con datos reales
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
                            border: 1px solid {theme['color']};
                            border-radius: 12px;
                            padding: 20px;
                            margin-bottom: 20px;">
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 28px;">{theme['icon']}</span>
                            <div>
                                <div style="color: white; font-size: 18px; font-weight: bold;">{theme['name']}</div>
                                <div style="color: #888; font-size: 12px;">{theme['description']}</div>
                            </div>
                        </div>
                        <div style="background: {sent_color}22; 
                                    color: {sent_color}; 
                                    padding: 6px 12px; 
                                    border-radius: 20px; 
                                    font-size: 11px; 
                                    font-weight: bold;
                                    border: 1px solid {sent_color}44;">
                            {sentiment}
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 15px;">
                        <div style="background: #0c0e12; padding: 10px; border-radius: 8px; text-align: center;">
                            <div style="color: #888; font-size: 10px;">Alcistas</div>
                            <div style="color: {sent_color}; font-size: 22px; font-weight: bold;">{bullish_pct:.0f}%</div>
                            <div style="color: #666; font-size: 9px;">{bullish}/{total}</div>
                        </div>
                        <div style="background: #0c0e12; padding: 10px; border-radius: 8px; text-align: center;">
                            <div style="color: #888; font-size: 10px;">Momentum</div>
                            <div style="color: {'#00ffad' if avg_momentum > 60 else '#ff9800' if avg_momentum > 40 else '#f23645'}; 
                                        font-size: 22px; font-weight: bold;">{avg_momentum:.0f}</div>
                            <div style="color: #666; font-size: 9px;">RSI Avg</div>
                        </div>
                        <div style="background: #0c0e12; padding: 10px; border-radius: 8px; text-align: center;">
                            <div style="color: #888; font-size: 10px;">Performance</div>
                            <div style="color: {'#00ffad' if avg_perf > 0 else '#f23645'}; 
                                        font-size: 22px; font-weight: bold;">{avg_perf:+.1f}%</div>
                            <div style="color: #666; font-size: 9px;">Período</div>
                        </div>
                    </div>
                    
                    <div style="color: #888; font-size: 11px; margin-bottom: 8px;">🏆 Top Performers (Reales):</div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                """, unsafe_allow_html=True)
                
                # Top 3 reales ordenados por performance real
                top_3 = sorted(valid, key=lambda x: x["performance"], reverse=True)[:3]
                for perf in top_3:
                    trend_icon = "📈" if perf["trend"] == "BULLISH" else "📉"
                    st.markdown(f"""
                        <div style="background: {'#00ffad15' if perf['trend'] == 'BULLISH' else '#f2364515'}; 
                                    border: 1px solid {'#00ffad33' if perf['trend'] == 'BULLISH' else '#f2364533'};
                                    border-radius: 6px; 
                                    padding: 6px 10px;
                                    font-size: 12px;">
                            {trend_icon} <b>{perf['symbol']}</b> 
                            <span style="color: {'#00ffad' if perf['performance'] > 0 else '#f23645'}">
                                {perf['performance']:+.1f}%
                            </span>
                            <span style="color: #666; font-size: 9px;">@ ${perf['price']:.2f}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Expander con tabla de datos reales
                with st.expander(f"Ver datos reales de {theme['name']}"):
                    df_real = pd.DataFrame([
                        {
                            "Símbolo": r["symbol"],
                            "Precio Real": f"${r['price']:.2f}",
                            "Tendencia": r["trend"],
                            "Fuerza": f"{r['trend_strength']:.1f}",
                            "RSI": f"{r['momentum']:.1f}",
                            "Performance": f"{r['performance']:+.2f}%",
                            "Volatilidad": f"{r['volatility_value']:.1f}%",
                            "Volumen vs Prom": f"{r['volume_ratio']:.2f}x",
                            "Actualizado": r["last_updated"]
                        }
                        for r in valid
                    ])
                    
                    # Colores según valores reales
                    def color_performance(val):
                        num = float(val.replace('%', '').replace('+', ''))
                        return f'color: {"#00ffad" if num > 0 else "#f23645"}; font-weight: bold'
                    
                    def color_trend(val):
                        return f'color: {"#00ffad" if val == "BULLISH" else "#f23645"}; font-weight: bold'
                    
                    styled = df_real.style\
                        .applymap(color_performance, subset=['Performance'])\
                        .applymap(color_trend, subset=['Tendencia'])
                    
                    st.dataframe(styled, use_container_width=True, height=300)
            
            col_idx += 1
        
        # Métricas de mercado agregadas (reales)
        st.markdown("---")
        st.subheader("📊 Métricas de Mercado Agregadas (Datos Reales)")
        
        all_valid = [r for results in all_results.values() for r in results if r is not None]
        if all_valid:
            total_bullish = len([r for r in all_valid if r["trend"] == "BULLISH"])
            total_symbols = len(all_valid)
            market_breadth = (total_bullish / total_symbols * 100) if total_symbols > 0 else 0
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                render_real_metric_card("MARKET BREADTH", f"{market_breadth:.0f}%", 
                                     f"{total_bullish}/{total_symbols} alcistas", 
                                     "#00ffad" if market_breadth > 60 else "#ff9800" if market_breadth > 40 else "#f23645", 
                                     "📊")
            with m2:
                avg_mom = np.mean([r["momentum"] for r in all_valid])
                render_real_metric_card("MOMENTUM PROMEDIO", f"{avg_mom:.0f}", 
                                     "RSI medio del mercado", 
                                     "#00ffad" if avg_mom > 60 else "#ff9800" if avg_mom > 40 else "#f23645", 
                                     "💪")
            with m3:
                avg_perf = np.mean([r["performance"] for r in all_valid])
                render_real_metric_card("PERFORMANCE PROMEDIO", f"{avg_perf:+.1f}%", 
                                     "Retorno medio del período", 
                                     "#00ffad" if avg_perf > 0 else "#f23645", 
                                     "📈")
            with m4:
                high_vol = len([r for r in all_valid if r["volatility_regime"] == "ALTA"])
                render_real_metric_card("ALTA VOLATILIDAD", f"{high_vol}", 
                                     f"activos de {total_symbols}", 
                                     "#f23645" if high_vol > total_symbols/3 else "#ff9800", 
                                     "⚠️")

if __name__ == "__main__":
    render_market_themes_real_data()
