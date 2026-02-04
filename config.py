# app.py
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math
from datetime import datetime
import pytz
import yfinance as yf

# --- IMPORTACION DE CONFIGURACION Y MODULOS ---
from config import set_style, get_cnn_fear_greed, actualizar_contador_usuarios
import modules.auth as auth
import modules.market as market
import modules.manifest as manifest          
import modules.rsu_club as rsu_club          
import modules.rsrw as rsrw
import modules.rsu_algoritmo as rsu_algoritmo 
import modules.ema_edge as ema_edge          
import modules.earnings as earnings
import modules.cartera as cartera
import modules.tesis as tesis
import modules.ia_report as ia_report
import modules.academy as academy
import modules.trade_grader as trade_grader
import modules.spxl_strategy as spxl_strategy
import modules.roadmap_2026 as roadmap_2026
import modules.trump_playbook as trump_playbook
import modules.comunidad as comunidad          
import modules.disclaimer as disclaimer      

# Aplicar estilos definidos en config.py
set_style()

# CSS Profesional mejorado
st.markdown("""
<style>
    /* Sidebar base */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0c10 0%, #11141a 50%, #0c0e12 100%);
        border-right: 1px solid #1a1e26;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    
    /* Logo container con efecto glow */
    .logo-container {
        background: linear-gradient(135deg, #0c0e1226;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    
    /* Logo container con efecto glow */
    .logo-container {
        background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%);
        padding: 25px 20px;
        border-bottom: 1px solid #2a3f5f;
        margin: -1rem -1rem 0 -1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .logo-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0,255,173,0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        50% { left: 100%; }
        100% { left: 100%; }
    }
    
    /* Live badge premium */
    .live-badge {
        display: inline-flex26;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    
    /* Logo container con efecto glow */
    .logo-container {
        background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%);
        padding: 25px 20px;
        border-bottom: 1px solid #2a3f5f;
        margin: -1rem -1rem 0 -1rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .logo-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0,255,173,0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        50% { left: 100%; }
        100% { left: 100%; }
    }
    
    /* Live badge premium */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, rgba(0,255,173,0.15) 0%, rgba(41,98,255,0.1) 100%);
        border: 1px solid rgba(0, 255, 173, 0.4);
        padding: 8px 16px;
        border-radius: 25px;
        margin-top: 15px;
        box-shadow: 0 0 15px rgba(0,255,173,0.1);
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: #00ffad;
        border-radius: 50%;
        animation: pulse 2s infinite;
        box-shadow: 0 0 10px #00ffad;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }
    
    /* Mini ticker en sidebar */
    .mini-ticker {
        background: #0c0e12;
        border: 1px solid #1a1e26;
        border-radius: 8px;
        padding: 10px;
        margin: 15px 0;
        overflow: hidden;
        position: relative;
    }
    
    .mini-ticker-content {
        display: flex;
        animation: ticker-slide 20s linear infinite;
        white-space: nowrap;
    }
    
    @keyframes ticker-slide {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    
    .ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 20px;
        font-size: 0.75rem;
    }
    
    /* Market clock */
    .market-clock {
        background: linear-gradient(135deg, rgba(41,98,255,0.1) 0%, rgba(0,255,173,0.05) 100%);
        border: 1px solid #2a3f5f;
        border-radius: 12px;
        padding: 15px;
        margin: 15px 0;
    }
    
    .clock-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .clock-title {
        color: #888;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .market-status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.7rem;
    }
    
    .status-open { color: #00ffad; }
    .status-closed { color: #f23645; }
    
    .clock-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }
    
    .clock-item {
        background: rgba(0,0,0,0.3);
        padding: 8px;
        border-radius: 6px;
        text-align: center;
    }
    
    .clock-city {
        color: #666;
        font-size: 0.65rem;
        text-transform: uppercase;
    }
    
    .clock-time {
        color: white;
        font-size: 0.9rem;
        font-weight: bold;
        font-family: 'Courier New', monospace;
    }
    
    /* Menu styling premium */
    .stRadio > div[role="radiogroup"] > label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 12px 15px;
        margin: 3px 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .stRadio > div[role="radiogroup"] > label::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        height: 100%;
        width: 0;
        background: linear-gradient(90deg, #2962ff 0%, #00ffad 100%);
        opacity: 0.1;
        transition: width 0.3s ease;
    }
    
    .stRadio > div[role="radiogroup"] > label:hover::before {
        width: 100%;
    }
    
    .stRadio > div[role="radiogroup"] > label:hover {
        border-color: rgba(41, 98, 255, 0.5);
        transform: translateX(5px);
    }
    
    .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(41, 98, 255, 0.15) 0%, rgba(0, 255, 173, 0.08) 100%);
        border-left: 3px solid #00ffad;
        border-top: 1px solid rgba(0, 255, 173, 0.3);
        border-bottom: 1px solid rgba(0, 255, 173, 0.3);
        border-right: 1px solid rgba(0, 255, 173, 0.3);
        box-shadow: 0 0 20px rgba(0,255,173,0.1);
    }
    
    /* FNG Container */
    .fng-container {
        background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
        border: 1px solid #1a1e26;
        border-radius: 16px;
        padding: 20px;
        margin-top: 15px;
        position: relative;
    }
    
    .fng-container::after {
        content: '';
        position: absolute;
        top: -1px;
        left: 20%;
        right: 20%;
        height: 1px;
        background: linear-gradient(90deg, transparent, #2962ff, transparent);
    }
    
    .fng-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 15px;
    }
    
    .fng-title {
        color: white;
        font-size: 0.8rem;
        font-weight: bold;
        letter-spacing: 1px;
    }
    
    .fng-value {
        background: linear-gradient(135deg, #2962ff 0%, #00ffad 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(41,98,255,0.3);
    }
    
    /* Quick stats */
    .quick-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin: 15px 0;
    }
    
    .stat-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid #1a1e26;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        transition: all 0.2s;
    }
    
    .stat-box:hover {
        background: rgba(41,98,255,0.05);
        border-color: #2a3f5f;
    }
    
    .stat-label {
        color: #666;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    
    .stat-value {
        color: white;
        font-size: 1rem;
        font-weight: bold;
    }
    
    .stat-change {
        font-size: 0.7rem;
        margin-top: 2px;
    }
    
    /* Section headers */
    .section-header {
        color: #2962ff;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin: 20px 0 12px 0;
        padding-left: 5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #2962ff, transparent);
    }
    
    /* Separator */
    .sidebar-separator {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #2a3f5f 50%, transparent 100%);
        margin: 20px 0;
        border: none;
        position: relative;
    }
    
    .sidebar-separator::after {
        content: '◆';
        position-separator-separator::-se-separator::after {
        content: '◆';
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        color: #2962ff;
        font-size: 0.5rem;
        background: #11141a;
        padding: 0 10px;
    }
    
    /* Legend grid */
    .legend-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-top: 12px;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 8px;
        background: rgba(255,255,255,0.02);
        border-radius: 6px;
        border: 1px solid transparent;
        transition: all 0.2s;
    }
    
    .legend-item:hover {
        background: rgba(255,255,255,0.05);
        border-color: #1a1e26;
    }
    
    .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        box-shadow: 0 0 8px currentColor;
    }
    
    .legend-text {
        color: #999;
        font-size: 0.7rem;
    }
    
    /* Footer */
    .sidebar-footer {
        text-align: center;
        padding: 20px 0 10px;
        margin-top: 10px;
        border-top: 1px solid #1a1e26;
    }
    
    .footer-version {
        color: #2962ff;
        font-size: 0.75rem;
        font-weight: bold;
        letter-spacing: 2px;
    }
    
    .footer-copy {
        color: #444;
        font-size: 0.65rem;
        margin-top: 6px;
    }
    
    /* Scrollbar personalizada */
    [data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 6px;
    }
    
    [data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: #0c0e12;
    }
    
    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: #2a3f5f;
        border-radius: 3px;
    }
    
    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: #2962ff;
    }
</style>
""", unsafe_allow_html=True)

# Funciones auxiliares
def get_market_index_local(ticker):
    """Funcion local para obtener datos de mercado sin circular import"""
    try:
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) >= 2:
            current = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
            change = ((current - prev) / prev) * 100
            return current, change
    except:
        pass
    return 0, 0

def get_market_status():
    """Determina si el mercado esta abierto"""
    try:
        ny_time = datetime.now(pytz.timezone('America/New_York'))
        hour = ny_time.hour
        minute = ny_time.minute
        weekday = ny_time.weekday()
        
        if weekday < 5:
            if (hour == 9 and minute >= 30) or (10 <= hour < 16):
                return True, "OPEN"
    except:
        pass
    return False, "CLOSED"

def get_clock_times():
    """Obtiene horas de diferentes mercados"""
    times = {}
    try:
        now = datetime.now(pytz.UTC)
        
        markets = {
            'NY': 'America/New_York',
            'LON': 'Europe/London',
            'TKY': 'Asia/Tokyo',
            'SYD': 'Australia/Sydney'
        }
        
        for city, tz in markets.items():
            local_time = now.astimezone(pytz.timezone(tz))
            times[city] = local_time.strftime('%H:%M')
    except:
        times = {'NY': '--:--', 'LON': '--:--', 'TKY': '--:--', 'SYD': '--:--'}
    
    return times

# Control de acceso
if not auth.login():
    st.stop()

# Inicializamos el motor del algoritmo RS/RW en la sesion
if 'rsrw_engine' not in st.session_state:
    st.session_state.rsrw_engine = rsrw.RSRWEngine()
    st.session_state.algoritmo_engine = rsu_algoritmo.RSUAlgoritmo()

# --- SIDEBAR PROFESIONAL MEJORADO ---
with st.sidebar:
    
    # 1. LOGO Y HEADER CON EFECTO
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 2.5rem; font-weight: bold; background: linear-gradient(135deg, #00ffad 0%, #2962ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">RSU</div>
                <div style="font-size: 0.75rem; color: #666; letter-spacing: 4px; margin-top: 5px;">TERMINAL</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Live users badge premium
    try:
        usuarios_activos = actualizar_contador_usuarios()
    except:
        usuarios_activos = 1
    
    st.markdown(f"""
        <div style="text-align: center;">
            <div class="live-badge">
                <div class="live-dot"></div>
                <span style="color: #00ffad; font-size: 0.8rem; font-weight: 600; letter-spacing: 1px;">{usuarios_activos} ONLINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. MINI TICKER DE PRECIOS (Scrolleable)
    st.markdown('<div class="section-header">Live Markets</div>', unsafe_allow_html=True)
    
    # Obtener datos rapidos para el mini ticker
    try:
        spx_val, spx_chg = get_market_index_local("^GSPC")
        ndx_val, ndx_chg = get_market_index_local("^IXIC")
        vix_val, vix_chg = get_market_index_local("^VIX")
        
        spx_color = "#00ffad" if spx_chg >= 0 else "#f23645"
        ndx_color = "#00ffad" if ndx_chg >= 0 else "#f23645"
        
        ticker_content = f"""
            <div class="mini-ticker">
                <div class="mini-ticker-content">
                    <span class="ticker-item">
                        <span style="color: #888;">S&P 500</span>
                        <span style="color: white; font-weight: bold;">{spx_val:,.0f}</span>
                        <span style="color: {spx_color};">{spx_chg:+.2f}%</span>
                    </span>
                    <span class="ticker-item">
                        <span style="color: #888;">NASDAQ</span>
                        <span style="color: white; font-weight: bold;">{ndx_val:,.0f}</span>
                        <span style="color: {ndx_color};">{ndx_chg:+.2f}%</span>
                    </span>
                    <span class="ticker-item">
                        <span style="color: #888;">VIX</span>
                        <span style="color: white; font-weight: bold;">{vix_val:.2f}</span>
                        <span style="color: #f23645;">{vix_chg:+.2f}%</span>
                    </span>
                    <span class="ticker-item">
                        <span style="color: #888;">BTC</span>
                        <span style="color: white; font-weight: bold;">$104K</span>
                        <span style="color: #00ffad;">+2.4%</span>
                    </span>
                    <span class="ticker-item">
                        <span style="color: #888;">S&P 500</span>
                        <span style="color: white; font-weight: bold;">{spx_val:,.0f}</span>
                        <span style="color: {spx_color};">{spx_chg:+.2f}%</span>
                    </span>
                    <span class="ticker-item">
                        <span style="color: #888;">NASDAQ</span>
                        <span style="color: white; font-weight: bold;">{ndx_val:,.0f}</span>
                        <span style="color: {ndx_color};">{ndx_chg:+.2f}%</span>
                    </span>
                    <span class="ticker-item">
                        <span style="color: #888;">VIX</span>
                        <span style="color: white; font-weight: bold;">{vix_val:.2f}</span>
                        <span style="color: #f23645;">{vix_chg:+.2f}%</span>
                    </span>
                    <span class="ticker-item">
                        <span style="color: #888;">BTC</span>
                        <span style="color: white; font-weight: bold;">$104K</span>
                        <span style="color: #00ffad;">+2.4%</span>
                    </span>
                </div>
            </div>
        """
        st.markdown(ticker_content, unsafe_allow_html=True)
    except:
        st.markdown("""
            <div class="mini-ticker" style="text-align: center; color: #666; font-size: 0.75rem;">
                Market data loading...
            </div>
        """, unsafe_allow_html=True)
    
    # 3. RELOJ DE MERCADOS GLOBALES
    is_open, status_text = get_market_status()
    status_class = "status-open" if is_open else "status-closed"
    status_dot = "🟢" if is_open else "🔴"
    times = get_clock_times()
    
    st.markdown(f"""
        <div class="market-clock">
            <div class="clock-header">
                <span class="clock-title">🌍 Market Hours</span>
                <span class="market-status {status_class}">
                    {status_dot} {status_text}
                </span>
            </div>
            <div class="clock-grid">
                <div class="clock-item">
                    <div class="clock-city">New York</div>
                    <div class="clock-time" style="color: {'#00ffad' if is_open else '#f23645'};">{times['NY']}</div>
                </div>
                <div class="clock-item">
                    <div class="clock-city">London</div>
                    <div class="clock-time">{times['LON']}</div>
                </div>
                <div class="clock-item">
                    <div class="clock-city">Tokyo</div>
                    <div class="clock-time">{times['TKY']}</div>
                </div>
                <div class="clock-item">
                    <div class="clock-city">Sydney</div>
                    <div class="clock-time">{times['SYD']}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Separador decorativo
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    
    # 4. QUICK STATS (Stats rapidas)
    st.markdown('<div class="section-header">Quick Stats</div>', unsafe_allow_html=True)
    
    # Obtener datos para stats
    try:
        fng = get_cnn_fear_greed()
        
        col1_stat, col2_stat = st.columns(2)
        with col1_stat:
            spx_color = "#00ffad" if spx_chg >= 0 else "#f23645"
            st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">S&P 500</div>
                    <div class="stat-value">{spx_val:,.0f}</div>
                    <div class="stat-change" style="color: {spx_color};">
                        {'▲' if spx_chg >= 0 else '▼'} {abs(spx_chg):.2f}%
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2_stat:
            fng_val = fng if fng else 50
            fng_color = "#00ffad" if fng_val > 50 else "#f23645"
            st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-label">Fear & Greed</div>
                    <div class="stat-value">{fng_val}</div>
                    <div class="stat-change" style="color: {fng_color};">
                        {'Greed' if fng_val > 50 else 'Fear'}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    except:
        st.markdown("""
            <div style="text-align: center; color: #444; font-size: 0.75rem; padding: 20px;">
                Stats loading...
            </div>
        """, unsafe_allow_html=True)
    
    # Separador
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    
    # 5. MENU DE NAVEGACION
    st.markdown('<div class="section-header">Navigation</div>', unsafe_allow_html=True)
    
    menu = st.radio(
        "",
        [
            "📊 DASHBOARD", 
            "📜 MANIFEST",
            "♣️ RSU CLUB",
            "📈 SCANNER RS/RW", 
            "🤖 ALGORITMO RSU",
            "⚡ EMA EDGE",
            "📅 EARNINGS", 
            "💼 CARTERA", 
            "📝 TESIS",
            "🤖 AI REPORT",
            "🎓 ACADEMY",
            "🏆 TRADE GRADER",
            "🚀 SPXL STRATEGY",
            "🗺️ ROADMAP 2026",
            "🇺🇸 TRUMP PLAYBOOK",
            "👥 COMUNIDAD",
            "⚠️ DISCLAIMER"
        ],
        label_visibility="collapsed"
    )
    
    # Separador final
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    
    # 6. FEAR & GREED DETALLADO (Al final, mas compacto)
    try:
        fng = get_cnn_fear_greed()
    except:
        fng = None
    
    if fng is not None:
        # Determinar color y estado
        if fng < 25: 
            estado, color, bg_color = "EXTREME FEAR", "#d32f2f", "rgba(211, 47, 47, 0.1)"
        elif fng < 45: 
            estado, color, bg_color = "FEAR", "#f57c00", "rgba(245, 124, 0, 0.1)"
        elif fng < 55: 
            estado, color, bg_color = "NEUTRAL", "#ff9800", "rgba(255, 152, 0, 0.1)"
        elif fng < 75: 
            estado, color, bg_color = "GREED", "#4caf50", "rgba(76, 175, 80, 0.1)"
        else: 
            estado, color, bg_color = "EXTREME GREED", "#00ffad", "rgba(0, 255, 173, 0.1)"
        
        st.markdown(f"""
            <div class="fng-container">
                <div class="fng-header">
                    <span class="fng-title">📊 SENTIMENT</span>
                    <span class="fng-value">{fng}</span>
                </div>
        """, unsafe_allow_html=True)
        
        # Gauge minimalista
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fng,
            number = {'font': {'size': 0}},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 0, 'tickcolor': "transparent"},
                'bar': {'color': "rgba(0,0,0,0)"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 0,
                'steps': [
                    {'range':  {'range': [0, 25], 'color': "#d32f2f"},
                    {' {'range': [0, 25], 'color': "#d32f2f"},
                    {'range': [25, 45], 'color': "#f57c00"},
                    {'range': [45, 55], 'color': "#ff9800"},
                    {'range': [55, 75], 'color': "#4caf50"},
                    {'range': [75, 100], 'color': "#00ffad"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 3},
                    'thickness': 0.85,
                    'value': fng
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=90,
            margin=dict(l=10, r=10, t=5, b=5)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Estado
        st.markdown(f"""
                <div style="text-align: center; margin-top: 8px;">
                    <div style="display: inline-block; background: {bg_color}; border: 1px solid {color}; padding: 8px 18px; border-radius: 25px;">
                        <span style="color: {color}; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px;">{estado}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Leyenda compacta
        st.markdown("""
            <div class="legend-grid">
                <div class="legend-item">
                    <div class="legend-color" style="background: #d32f2f; color: #d32f2f;"></div>
                    <span class="legend-text">Extreme Fear</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f57c00; color: #f57c00;"></div>
                    <span class="legend-text">Fear</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff9800; color: #ff9800;"></div>
                    <span class="legend-text">Neutral</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4caf50; color: #4caf50;"></div>
                    <span class="legend-text">Greed</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # 7. FOOTER PREMIUM
    st.markdown("""
        <div class="sidebar-footer">
            <div class="footer-version">RSU TERMINAL v2.0</div>
            <div class="footer-copy">© 2026 Professional Trading Suite</div>
        </div>
    """, unsafe_allow_html=True)

# --- LOGICA DE NAVEGACION ---
if menu == "📊 DASHBOARD":
    market.render()
elif menu == "📜 MANIFEST":
    manifest.render()
elif menu == "♣️ RSU CLUB":
    rsu_club.render()
elif menu == "📈 SCANNER RS/RW":
    rsrw.render()
elif menu == "🤖 ALGORITMO RSU":
    rsu_algoritmo.render()
elif menu == "⚡ EMA EDGE":
    ema_edge.render()
elif menu == "📅 EARNINGS":
    earnings.render()
elif menu == "💼 CARTERA":
    cartera.render()
elif menu == "📝 TESIS":
    tesis.render()
elif menu == "🤖 AI REPORT":
    ia_report.render()
elif menu == "🎓 ACADEMY":
    academy.render()
elif menu == "🏆 TRADE GRADER":
    trade_grader.render()
elif menu == "🚀 SPXL STRATEGY":
    spxl_strategy.render()
elif menu == "🗺️ ROADMAP 2026":
    roadmap_2026.render()
elif menu == "🇺🇸 TRUMP PLAYBOOK":
    trump_playbook.render()
elif menu == "👥 COMUNIDAD":
    comunidad.render()
elif menu == "⚠️ DISCLAIMER":
    disclaimer.render()
