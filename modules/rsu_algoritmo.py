# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import yfinance as yf
import sys
import os

# Agregar el directorio padre al path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import set_style

def calcular_rsi(prices, period=14):
    """Calcula RSI manualmente"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def obtener_datos_spy():
    """Obtiene RSI y precio de SPY"""
    try:
        ticker = yf.Ticker("SPY")
        df = ticker.history(interval="1wk", period="6mo")
        
        if df.empty or len(df) < 14:
            return None, None, None
        
        df['rsi'] = calcular_rsi(df['Close'])
        rsi_val = float(df['rsi'].iloc[-1])
        precio_val = float(df['Close'].iloc[-1])
        
        # Calcular tendencia del RSI (comparar con valor de hace 1 semana)
        rsi_prev = float(df['rsi'].iloc[-2]) if len(df) > 1 else rsi_val
        rsi_trend = rsi_val - rsi_prev
        
        return rsi_val, precio_val, rsi_trend
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None, None

def calcular_estado(rsi):
    if rsi < 30:
        return "VERDE", "COMPRA", "#00ffad", "RSI < 30: Zona de sobreventa. Oportunidad de entrada."
    elif rsi > 70:
        return "ROJO", "VENTA", "#f23645", "RSI > 70: Zona de sobrecompra. Considerar toma de beneficios."
    else:
        return "AMBAR", "NEUTRAL", "#ff9800", "RSI 30-70: Zona neutral. Esperar confirmación."

def render():
    set_style()
    
    # CSS consistente con market.py - CORREGIDO
    st.markdown("""
    <style>
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: visible;
            background: #11141a;
            margin-bottom: 20px;
            position: relative;
        }
        .group-header {
            background: #0c0e12;
            padding: 15px 20px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 10px 10px 0 0;
        }
        .group-title {
            margin: 0;
            color: white;
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 0.5px;
        }
        .tooltip-container {
            position: relative;
            cursor: help;
            z-index: 1000;
        }
        .tooltip-icon {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #1a1e26;
            border: 2px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .tooltip-icon:hover {
            border-color: #2962ff;
            color: #2962ff;
        }
        .tooltip-text {
            visibility: hidden;
            width: 280px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 12px;
            border-radius: 8px;
            position: absolute;
            z-index: 9999;
            top: 35px;
            right: 0;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 4px 20px rgba(0,0,0,0.8);
            line-height: 1.4;
            pointer-events: none;
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .metric-card {
            background: #0c0e12;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: #2962ff;
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: white;
            margin: 10px 0;
        }
        .metric-label {
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0.4); }
            70% { opacity: 0.8; box-shadow: 0 0 0 10px rgba(255,255,255,0); }
            100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0); }
        }
        .semaforo-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
            padding: 30px;
        }
        .luz {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            border: 4px solid #1a1e26;
            background: #0c0e12;
            transition: all 0.5s ease;
            position: relative;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        }
        .luz.active {
            box-shadow: 0 0 30px currentColor, inset 0 0 20px rgba(255,255,255,0.2);
            border-color: currentColor;
            transform: scale(1.05);
        }
        .luz-roja { color: #f23645; }
        .luz-ambar { color: #ff9800; }
        .luz-verde { color: #00ffad; }
        
        .luz-roja.active { background: radial-gradient(circle at 30% 30%, #ff6b6b, #f23645); }
        .luz-ambar.active { background: radial-gradient(circle at 30% 30%, #ffb74d, #ff9800); }
        .luz-verde.active { background: radial-gradient(circle at 30% 30%, #69f0ae, #00ffad); }
        
        /* CORRECCIÓN: Estilos para el contexto histórico */
        .historical-context {
            background: #0c0e12;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            border: 1px solid #1a1e26;
        }
        .context-bar {
            height: 8px;
            background: #1a1e26;
            border-radius: 4px;
            margin: 10px 0;
            position: relative;
            overflow: hidden;
        }
        .context-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.8s ease;
        }
        .refresh-btn {
            background: linear-gradient(135deg, #2962ff 0%, #1e88e5 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 20px;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(41, 98, 255, 0.4);
        }
        .signal-badge {
            display: inline-flex;
            align-items: center;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Título con tooltip explicativo - CORREGIDO POSICIONAMIENTO
    col_title, col_info = st.columns([6, 1])
    with col_title:
        st.markdown("<h1 style='color: white; margin-bottom: 5px;'>🚦 RSU ALGORITMO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #888; font-size: 14px; margin-top: 0;'>Estrategia basada en RSI Semanal del S&P 500 (SPY)</p>", unsafe_allow_html=True)
    
    with col_info:
        st.markdown("""
        <div style="position: relative; height: 60px;">
            <div class="tooltip-container" style="position: absolute; top: 10px; right: 0;">
                <div class="tooltip-icon">?</div>
                <div class="tooltip-text">
                    <strong>RSU Algoritmo:</strong><br>
                    Sistema de trading basado en el índice de fuerza relativa (RSI) 
                    del ETF SPY en timeframe semanal.<br><br>
                    <strong>Señales:</strong><br>
                    🟢 RSI < 30: Compra (Sobreventa)<br>
                    🟡 RSI 30-70: Neutral<br>
                    🔴 RSI > 70: Venta (Sobrecompra)
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Obtener datos
    with st.spinner('Calculando RSI...'):
        rsi_val, precio_val, rsi_trend = obtener_datos_spy()
    
    if rsi_val is None:
        st.error("Error al obtener datos de Yahoo Finance. Intenta recargar.")
        if st.button("🔄 Recargar", key="reload_error"):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Determinar estado
    estado, senal, color_hex, descripcion = calcular_estado(rsi_val)
    
    # Layout de dos columnas: Semáforo + Métricas
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Contenedor del semáforo
        luz_r = "active" if estado == "ROJO" else ""
        luz_a = "active" if estado == "AMBAR" else ""
        luz_v = "active" if estado == "VERDE" else ""
        
        st.markdown(f"""
        <div class="group-container">
            <div class="group-header">
                <span class="group-title">Señal del Mercado</span>
                <span style="color: {color_hex}; font-size: 12px; font-weight: bold;">
                    ● EN TIEMPO REAL
                </span>
            </div>
            <div class="semaforo-container">
                <div class="luz luz-roja {luz_r}"></div>
                <div class="luz luz-ambar {luz_a}"></div>
                <div class="luz luz-verde {luz_v}"></div>
                <div style="margin-top: 20px; text-align: center;">
                    <div class="signal-badge" style="background: {color_hex}22; border: 2px solid {color_hex}; color: {color_hex};">
                        <span class="status-indicator" style="background: {color_hex};"></span>
                        {senal}
                    </div>
                    <p style="color: #888; font-size: 13px; margin-top: 15px; line-height: 1.4; padding: 0 20px;">
                        {descripcion}
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_right:
        # Métricas principales
        trend_color = "#00ffad" if rsi_trend >= 0 else "#f23645"
        trend_icon = "↑" if rsi_trend >= 0 else "↓"
        
        st.markdown(f"""
        <div class="group-container">
            <div class="group-header">
                <span class="group-title">Métricas Clave</span>
            </div>
            <div style="padding: 20px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="metric-card">
                        <div class="metric-label">RSI Semanal</div>
                        <div class="metric-value" style="color: {color_hex};">{rsi_val:.2f}</div>
                        <div style="color: {trend_color}; font-size: 0.9rem; margin-top: 5px;">
                            {trend_icon} {abs(rsi_trend):.2f} vs semana ant.
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Precio SPY</div>
                        <div class="metric-value">${precio_val:.2f}</div>
                        <div style="color: #888; font-size: 0.8rem; margin-top: 5px;">
                            Actualizado {pd.Timestamp.now().strftime('%H:%M')}
                        </div>
                    </div>
                </div>
                
                <div class="historical-context">
                    <div style="color: #888; font-size: 12px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px;">
                        Posición en Rango RSI
                    </div>
                    <div class="context-bar">
                        <div class="context-fill" style="width: {rsi_val}%; background: linear-gradient(to right, #00ffad, #ff9800, #f23645);"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #555; margin-top: 5px;">
                        <span>0</span>
                        <span style="color: #00ffad; font-weight: bold;">30</span>
                        <span style="color: #ff9800; font-weight: bold;">70</span>
                        <span>100</span>
                    </div>
                    <div style="text-align: center; margin-top: 10px; color: {color_hex}; font-weight: bold; font-size: 14px;">
                        {rsi_val:.1f} → {estado}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Grid de interpretación
    st.markdown("<h3 style='color: white; margin-top: 30px; margin-bottom: 15px;'>📊 Interpretación de Señales</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="group-container" style="border: 1px solid #f2364544;">
            <div style="padding: 20px; text-align: center;">
                <div style="width: 60px; height: 60px; background: #f2364522; border: 2px solid #f23645; 
                            border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; 
                            justify-content: center; color: #f23645; font-size: 24px;">🔴</div>
                <h4 style="color: #f23645; margin: 0 0 10px 0;">ZONA DE VENTA</h4>
                <div style="color: white; font-size: 1.8rem; font-weight: bold; margin: 10px 0;">RSI > 70</div>
                <p style="color: #888; font-size: 13px; line-height: 1.4; margin: 0;">
                    Sobrecompra extrema. Considerar reducir exposición o tomar beneficios.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="group-container" style="border: 1px solid #ff980044;">
            <div style="padding: 20px; text-align: center;">
                <div style="width: 60px; height: 60px; background: #ff980022; border: 2px solid #ff9800; 
                            border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; 
                            justify-content: center; color: #ff9800; font-size: 24px;">🟡</div>
                <h4 style="color: #ff9800; margin: 0 0 10px 0;">ZONA NEUTRAL</h4>
                <div style="color: white; font-size: 1.8rem; font-weight: bold; margin: 10px 0;">30-70</div>
                <p style="color: #888; font-size: 13px; line-height: 1.4; margin: 0;">
                    Momentum equilibrado. Mantener posiciones actuales y esperar ruptura.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="group-container" style="border: 1px solid #00ffad44;">
            <div style="padding: 20px; text-align: center;">
                <div style="width: 60px; height: 60px; background: #00ffad22; border: 2px solid #00ffad; 
                            border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; 
                            justify-content: center; color: #00ffad; font-size: 24px;">🟢</div>
                <h4 style="color: #00ffad; margin: 0 0 10px 0;">ZONA DE COMPRA</h4>
                <div style="color: white; font-size: 1.8rem; font-weight: bold; margin: 10px 0;">RSI < 30</div>
                <p style="color: #888; font-size: 13px; line-height: 1.4; margin: 0;">
                    Sobreventa extrema. Oportunidad potencial de entrada acumulativa.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Botón de recálculo
    if st.button("🔄 Forzar Recálculo", key="refresh_main"):
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
