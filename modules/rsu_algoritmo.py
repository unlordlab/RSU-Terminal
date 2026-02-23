# modules/rsu_algoritmo.py
import streamlit as st
import pandas as pd
import yfinance as yf
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import set_style

def calcular_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def obtener_datos_spy():
    """
    Obtiene datos de SPY. Intenta usar backend primero, fallback a yfinance.
    """
    # === NUEVO: Intentar backend primero ===
    try:
        from modules.api_client import get_api_client
        client = get_api_client()
        
        # Obtener históricos de 6 meses (aprox 26 semanas)
        data_json = client.get_history("SPY", "6mo")
        
        if data_json and "data" in data_json:
            df = pd.DataFrame(data_json["data"])
            
            # Convertir fecha a índice
            date_col = 'Date' if 'Date' in df.columns else 'Datetime' if 'Datetime' in df.columns else None
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col])
                df.set_index(date_col, inplace=True)
            
            # Resamplear a semanal (igual que yfinance interval="1wk")
            df = df.resample('W').last().dropna()
            
            if len(df) < 14:
                raise ValueError("Datos insuficientes del backend")
            
            df['rsi'] = calcular_rsi(df['Close'])
            rsi_val = float(df['rsi'].iloc[-1])
            precio_val = float(df['Close'].iloc[-1])
            rsi_prev = float(df['rsi'].iloc[-2]) if len(df) > 1 else rsi_val
            rsi_trend = rsi_val - rsi_prev
            
            # Indicador silencioso de que usó backend (solo en desarrollo)
            # st.caption("🟢 Backend")  # Descomenta para debug
            return rsi_val, precio_val, rsi_trend
            
    except Exception as e:
        # Silencioso: no mostrar error, solo fallback
        pass
    
    # === ORIGINAL: Fallback a yfinance ===
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
    
    # CSS (sin cambios)
    css = """
    <style>
    .rsu-box { background: #11141a; border: 1px solid #1a1e26; border-radius: 10px; margin-bottom: 20px; }
    .rsu-head { background: #0c0e12; padding: 15px 20px; border-bottom: 1px solid #1a1e26; border-radius: 10px 10px 0 0; display: flex; justify-content: space-between; align-items: center; }
    .rsu-title { color: white; font-size: 16px; font-weight: bold; margin: 0; }
    .rsu-body { padding: 20px; }
    .rsu-luz { width: 80px; height: 80px; border-radius: 50%; border: 4px solid #1a1e26; background: #0c0e12; margin: 10px auto; }
    .rsu-luz.on { box-shadow: 0 0 30px currentColor; transform: scale(1.1); }
    .rsu-luz.red { color: #f23645; }
    .rsu-luz.red.on { background: radial-gradient(circle at 30% 30%, #ff6b6b, #f23645); border-color: #f23645; }
    .rsu-luz.yel { color: #ff9800; }
    .rsu-luz.yel.on { background: radial-gradient(circle at 30% 30%, #ffb74d, #ff9800); border-color: #ff9800; }
    .rsu-luz.grn { color: #00ffad; }
    .rsu-luz.grn.on { background: radial-gradient(circle at 30% 30%, #69f0ae, #00ffad); border-color: #00ffad; }
    .rsu-center { text-align: center; }
    .rsu-metric { background: #0c0e12; border: 1px solid #1a1e26; border-radius: 10px; padding: 20px; text-align: center; }
    .rsu-big { font-size: 2.2rem; font-weight: bold; color: white; margin: 10px 0; }
    .rsu-small { color: #888; font-size: 0.85rem; text-transform: uppercase; }
    .rsu-badge { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 1.1rem; margin-top: 10px; }
    .rsu-dot { width: 10px; height: 10px; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0.4); } 70% { opacity: 0.8; box-shadow: 0 0 0 10px rgba(255,255,255,0); } 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(255,255,255,0); } }
    .rsu-bar-box { background: #0c0e12; border-radius: 10px; padding: 15px; margin-top: 15px; border: 1px solid #1a1e26; }
    .rsu-bar-line { height: 10px; background: #1a1e26; border-radius: 5px; overflow: hidden; }
    .rsu-bar-fill { height: 100%; border-radius: 5px; }
    .rsu-flex { display: flex; justify-content: space-between; font-size: 11px; color: #555; margin-top: 5px; }
    .rsu-tip { position: relative; display: inline-block; }
    .rsu-tip-icon { width: 26px; height: 26px; border-radius: 50%; background: #1a1e26; border: 2px solid #555; display: flex; align-items: center; justify-content: center; color: #aaa; font-size: 14px; font-weight: bold; cursor: help; }
    .rsu-tip-icon:hover { border-color: #2962ff; color: #2962ff; }
    .rsu-tip-text { visibility: hidden; width: 260px; background-color: #1e222d; color: #eee; text-align: left; padding: 12px; border-radius: 8px; position: absolute; z-index: 9999; top: 35px; right: 0; opacity: 0; transition: opacity 0.3s; font-size: 12px; border: 1px solid #444; box-shadow: 0 4px 20px rgba(0,0,0,0.8); line-height: 1.4; }
    .rsu-tip:hover .rsu-tip-text { visibility: visible; opacity: 1; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    st.markdown('<div style="max-width:1200px;margin:0 auto;padding:20px;">', unsafe_allow_html=True)
    
    # Header
    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown("<h1 style='color:white;margin-bottom:5px;'>🚦 RSU ALGORITMO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#888;font-size:14px;margin-top:0;'>RSI Semanal del S&P 500 (SPY)</p>", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="position:relative;height:50px;">
            <div class="rsu-tip" style="position:absolute;top:10px;right:0;">
                <div class="rsu-tip-icon">?</div>
                <div class="rsu-tip-text">
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
    
    # Columnas
    left, right = st.columns(2)
    
    # Semáforo - usando .format() en lugar de f-string
    with left:
        luz_r = "on" if estado == "ROJO" else ""
        luz_a = "on" if estado == "AMBAR" else ""
        luz_v = "on" if estado == "VERDE" else ""
        
        html_semaforo = """
        <div class="rsu-box">
            <div class="rsu-head">
                <span class="rsu-title">Señal del Mercado</span>
                <span style="color:{color};font-size:12px;font-weight:bold;">● TIEMPO REAL</span>
            </div>
            <div class="rsu-body rsu-center">
                <div class="rsu-luz red {luz_r}"></div>
                <div class="rsu-luz yel {luz_a}"></div>
                <div class="rsu-luz grn {luz_v}"></div>
                <div class="rsu-badge" style="background:{color}22;border:2px solid {color};color:{color};">
                    <span class="rsu-dot" style="background:{color};"></span>
                    {senal}
                </div>
                <p style="color:#888;font-size:13px;margin-top:15px;">{desc}</p>
            </div>
        </div>
        """.format(
            color=color,
            luz_r=luz_r,
            luz_a=luz_a,
            luz_v=luz_v,
            senal=senal,
            desc=desc
        )
        st.markdown(html_semaforo, unsafe_allow_html=True)
    
    # Métricas
    with right:
        # Primero las métricas simples
        m1, m2 = st.columns(2)
        with m1:
            st.markdown("""
            <div class="rsu-metric">
                <div class="rsu-small">RSI Semanal</div>
                <div class="rsu-big" style="color:{color};">{rsi:.2f}</div>
                <div style="color:{trend_color};font-size:0.9rem;">{arrow} {trend:.2f}</div>
            </div>
            """.format(
                color=color,
                rsi=rsi_val,
                trend_color=trend_color,
                arrow=trend_arrow,
                trend=abs(rsi_trend)
            ), unsafe_allow_html=True)
        
        with m2:
            st.markdown("""
            <div class="rsu-metric">
                <div class="rsu-small">Precio SPY</div>
                <div class="rsu-big">${price:.2f}</div>
                <div style="color:#888;font-size:0.8rem;">{hora}</div>
            </div>
            """.format(
                price=precio_val,
                hora=hora
            ), unsafe_allow_html=True)
        
        # Barra de progreso - HTML separado y simple
        bar_html = """
        <div class="rsu-bar-box">
            <div style="color:#888;font-size:11px;margin-bottom:8px;text-transform:uppercase;">Posición RSI</div>
            <div class="rsu-bar-line">
                <div class="rsu-bar-fill" style="width:{width}%;background:linear-gradient(90deg,#00ffad,#ff9800,#f23645);"></div>
            </div>
            <div class="rsu-flex">
                <span>0</span>
                <span style="color:#00ffad;font-weight:bold;">30</span>
                <span style="color:#ff9800;font-weight:bold;">70</span>
                <span>100</span>
            </div>
            <div style="text-align:center;margin-top:8px;color:{color};font-weight:bold;font-size:13px;">
                {rsi:.1f} → {estado}
            </div>
        </div>
        """.format(
            width=rsi_val,
            color=color,
            rsi=rsi_val,
            estado=estado
        )
        st.markdown(bar_html, unsafe_allow_html=True)
    
    # Zonas
    st.markdown("<h3 style='color:white;margin-top:30px;'>📊 Zonas</h3>", unsafe_allow_html=True)
    z1, z2, z3 = st.columns(3)
    
    zonas = [
        ("#f23645", "red", "VENTA", "> 70", "🔴", "Sobrecompra"),
        ("#ff9800", "yel", "NEUTRAL", "30-70", "🟡", "Esperar"),
        ("#00ffad", "grn", "COMPRA", "< 30", "🟢", "Sobreventa")
    ]
    
    cols = [z1, z2, z3]
    for i, (col, (col_hex, col_name, title, range_txt, emoji, sub)) in enumerate(zip(cols, zonas)):
        with col:
            zona_html = """
            <div class="rsu-box" style="border-color:{col_hex}44;">
                <div style="text-align:center;padding:20px;">
                    <div style="width:50px;height:50px;background:{col_hex}22;border:2px solid {col_hex};border-radius:50%;margin:0 auto 15px;display:flex;align-items:center;justify-content:center;font-size:20px;color:{col_hex};">{emoji}</div>
                    <h4 style="color:{col_hex};margin:0 0 10px 0;">{title}</h4>
                    <div style="color:white;font-size:1.5rem;font-weight:bold;">{range_txt}</div>
                    <p style="color:#888;font-size:12px;margin:10px 0 0 0;">{sub}</p>
                </div>
            </div>
            """.format(
                col_hex=col_hex,
                emoji=emoji,
                title=title,
                range_txt=range_txt,
                sub=sub
            )
            st.markdown(zona_html, unsafe_allow_html=True)
    
    if st.button("🔄 Recalcular", use_container_width=True):
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
