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
        
        rsi_prev = float(df['rsi'].iloc[-2]) if len(df) > 1 else rsi_val
        rsi_trend = rsi_val - rsi_prev
        
        return rsi_val, precio_val, rsi_trend
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None, None

def calcular_estado(rsi):
    if rsi < 30:
        return "VERDE", "COMPRA", "#00ffad", "RSI < 30: Zona de sobreventa"
    elif rsi > 70:
        return "ROJO", "VENTA", "#f23645", "RSI > 70: Zona de sobrecompra"
    else:
        return "AMBAR", "NEUTRAL", "#ff9800", "RSI 30-70: Zona neutral"

def render():
    set_style()
    
    # CSS Global
    st.markdown("""
    <style>
    .rsu-main { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .rsu-card { 
        background: #11141a; 
        border: 1px solid #1a1e26; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        overflow: visible;
    }
    .rsu-header { 
        background: #0c0e12; 
        padding: 15px 20px; 
        border-bottom: 1px solid #1a1e26; 
        border-radius: 10px 10px 0 0;
        display: flex; justify-content: space-between; align-items: center;
    }
    .rsu-title { color: white; font-size: 16px; font-weight: bold; margin: 0; }
    .rsu-content { padding: 20px; }
    .rsu-semaforo { 
        display: flex; flex-direction: column; align-items: center; 
        gap: 15px; padding: 30px; 
    }
    .rsu-luz {
        width: 80px; height: 80px; border-radius: 50%; border: 4px solid #1a1e26;
        background: #0c0e12; box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }
    .rsu-luz.active { transform: scale(1.1); box-shadow: 0 0 30px currentColor; }
    .rsu-luz-roja.active { background: radial-gradient(circle at 30% 30%, #ff6b6b, #f23645); border-color: #f23645; }
    .rsu-luz-ambar.active { background: radial-gradient(circle at 30% 30%, #ffb74d, #ff9800); border-color: #ff9800; }
    .rsu-luz-verde.active { background: radial-gradient(circle at 30% 30%, #69f0ae, #00ffad); border-color: #00ffad; }
    .rsu-metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
    .rsu-metric-box { 
        background: #0c0e12; border: 1px solid #1a1e26; 
        border-radius: 10px; padding: 20px; text-align: center; 
    }
    .rsu-metric-value { font-size: 2.2rem; font-weight: bold; color: white; margin: 10px 0; }
    .rsu-metric-label { color: #888; font-size: 0.85rem; text-transform: uppercase; }
    .rsu-bar-container { background: #0c0e12; border-radius: 10px; padding: 15px; margin-top: 15px; border: 1px solid #1a1e26; }
    .rsu-bar-bg { height: 10px; background: #1a1e26; border-radius: 5px; overflow: hidden; }
    .rsu-bar-fill { height: 100%; border-radius: 5px; }
    .rsu-signal-badge { 
        display: inline-flex; align-items: center; gap: 8px;
        padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 1.1rem;
    }
    .rsu-pulse { width: 10px; height: 10px; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 
        0% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0.4); }
        70% { opacity: 0.8; box-shadow: 0 0 0 10px rgba(255,255,255,0); }
        100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0); }
    }
    .rsu-tooltip-wrap { position: relative; display: inline-block; }
    .rsu-tooltip-icon {
        width: 26px; height: 26px; border-radius: 50%; background: #1a1e26;
        border: 2px solid #555; display: flex; align-items: center; justify-content: center;
        color: #aaa; font-size: 14px; font-weight: bold; cursor: help;
    }
    .rsu-tooltip-icon:hover { border-color: #2962ff; color: #2962ff; }
    .rsu-tooltip-text {
        visibility: hidden; width: 260px; background-color: #1e222d; color: #eee;
        text-align: left; padding: 12px; border-radius: 8px; position: absolute;
        z-index: 9999; top: 35px; right: 0; opacity: 0; transition: opacity 0.3s;
        font-size: 12px; border: 1px solid #444; box-shadow: 0 4px 20px rgba(0,0,0,0.8);
        line-height: 1.4;
    }
    .rsu-tooltip-wrap:hover .rsu-tooltip-text { visibility: visible; opacity: 1; }
    .rsu-zone-card { text-align: center; padding: 20px; }
    .rsu-zone-icon { 
        width: 50px; height: 50px; border-radius: 50%; margin: 0 auto 15px;
        display: flex; align-items: center; justify-content: center; font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="rsu-main">', unsafe_allow_html=True)
    
    header_col1, header_col2 = st.columns([6, 1])
    with header_col1:
        st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888;font-size:14px;margin-top:0;'>Estrategia RSI Semanal del S&P 500 (SPY)</p>", unsafe_allow_html=True)
    
    with header_col2:
        st.markdown("""
        <div style="position:relative;height:50px;">
            <div class="rsu-tooltip-wrap" style="position:absolute;top:10px;right:0;">
                <div class="rsu-tooltip-icon">?</div>
                <div class="rsu-tooltip-text">
                    <strong>RSU Algoritmo</strong><br><br>
                    🟢 RSI < 30: Compra<br>
                    🟡 RSI 30-70: Neutral<br>
                    🔴 RSI > 70: Venta
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Datos
    with st.spinner('Calculando...'):
        rsi_val, precio_val, rsi_trend = obtener_datos_spy()
    
    if rsi_val is None:
        st.error("Error al obtener datos")
        if st.button("🔄 Recargar"):
            st.rerun()
        return
    
    estado, senal, color, desc = calcular_estado(rsi_val)
    trend_color = "#00ffad" if rsi_trend >= 0 else "#f23645"
    trend_arrow = "↑" if rsi_trend >= 0 else "↓"
    hora = pd.Timestamp.now().strftime('%H:%M')
    
    # Columnas principales
    col1, col2 = st.columns(2)
    
    # Columna Izquierda - Semáforo
    with col1:
        luz_r = "active" if estado == "ROJO" else ""
        luz_a = "active" if estado == "AMBAR" else ""
        luz_v = "active" if estado == "VERDE" else ""
        
        semaforo_html = f"""
        <div class="rsu-card">
            <div class="rsu-header">
                <span class="rsu-title">Señal del Mercado</span>
                <span style="color:{color};font-size:12px;font-weight:bold;">● TIEMPO REAL</span>
            </div>
            <div class="rsu-semaforo">
                <div class="rsu-luz rsu-luz-roja {luz_r}"></div>
                <div class="rsu-luz rsu-luz-ambar {luz_a}"></div>
                <div class="rsu-luz rsu-luz-verde {luz_v}"></div>
                <div style="margin-top:10px;text-align:center;">
                    <div class="rsu-signal-badge" style="background:{color}22;border:2px solid {color};color:{color};">
                        <span class="rsu-pulse" style="background:{color};"></span>
                        {senal}
                    </div>
                    <p style="color:#888;font-size:13px;margin-top:15px;">{desc}</p>
                </div>
            </div>
        </div>
        """
        st.markdown(semaforo_html, unsafe_allow_html=True)
    
    # Columna Derecha - Métricas
    with col2:
        metricas_html = f"""
        <div class="rsu-card">
            <div class="rsu-header">
                <span class="rsu-title">Métricas Clave</span>
            </div>
            <div class="rsu-content">
                <div class="rsu-metric-grid">
                    <div class="rsu-metric-box">
                        <div class="rsu-metric-label">RSI Semanal</div>
                        <div class="rsu-metric-value" style="color:{color};">{rsi_val:.2f}</div>
                        <div style="color:{trend_color};font-size:0.9rem;">{trend_arrow} {abs(rsi_trend):.2f}</div>
                    </div>
                    <div class="rsu-metric-box">
                        <div class="rsu-metric-label">Precio SPY</div>
                        <div class="rsu-metric-value">${precio_val:.2f}</div>
                        <div style="color:#888;font-size:0.8rem;">{hora}</div>
                    </div>
                </div>
                
                <div class="rsu-bar-container">
                    <div style="color:#888;font-size:11px;margin-bottom:8px;text-transform:uppercase;">Posición RSI</div>
                    <div class="rsu-bar-bg">
                        <div class="rsu-bar-fill" style="width:{rsi_val}%;background:linear-gradient(90deg,#00ffad,#ff9800,#f23645);"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#555;margin-top:5px;">
                        <span>0</span>
                        <span style="color:#00ffad;font-weight:bold;">30</span>
                        <span style="color:#ff9800;font-weight:bold;">70</span>
                        <span>100</span>
                    </div>
                    <div style="text-align:center;margin-top:8px;color:{color};font-weight:bold;font-size:13px;">
                        {rsi_val:.1f} → {estado}
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(metricas_html, unsafe_allow_html=True)
    
    # Zonas de interpretación
    st.markdown("<h3 style='color:white;margin-top:30px;'>📊 Interpretación</h3>", unsafe_allow_html=True)
    
    z1, z2, z3 = st.columns(3)
    
    with z1:
        st.markdown("""
        <div class="rsu-card" style="border-color:#f2364544;">
            <div class="rsu-zone-card">
                <div class="rsu-zone-icon" style="background:#f2364522;border:2px solid #f23645;color:#f23645;">🔴</div>
                <h4 style="color:#f23645;margin:0 0 10px 0;">VENTA</h4>
                <div style="color:white;font-size:1.5rem;font-weight:bold;">> 70</div>
                <p style="color:#888;font-size:12px;margin:10px 0 0 0;">Sobrecompra</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with z2:
        st.markdown("""
        <div class="rsu-card" style="border-color:#ff980044;">
            <div class="rsu-zone-card">
                <div class="rsu-zone-icon" style="background:#ff980022;border:2px solid #ff9800;color:#ff9800;">🟡</div>
                <h4 style="color:#ff9800;margin:0 0 10px 0;">NEUTRAL</h4>
                <div style="color:white;font-size:1.5rem;font-weight:bold;">30-70</div>
                <p style="color:#888;font-size:12px;margin:10px 0 0 0;">Esperar</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with z3:
        st.markdown("""
        <div class="rsu-card" style="border-color:#00ffad44;">
            <div class="rsu-zone-card">
                <div class="rsu-zone-icon" style="background:#00ffad22;border:2px solid #00ffad;color:#00ffad;">🟢</div>
                <h4 style="color:#00ffad;margin:0 0 10px 0;">COMPRA</h4>
                <div style="color:white;font-size:1.5rem;font-weight:bold;">< 30</div>
                <p style="color:#888;font-size:12px;margin:10px 0 0 0;">Sobreventa</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🔄 Recalcular", use_container_width=True):
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
