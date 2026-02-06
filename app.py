# app.py
import os
import sys
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math
from datetime import datetime
import pytz

# --- CONFIGURACION Y MODULOS ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import set_style, get_cnn_fear_greed, actualizar_contador_usuarios, get_market_index

# Importar TODOS los módulos desde modules/
from modules import market as market_module
from modules import manifest as manifest_module
from modules import rsu_club as rsu_club_module
from modules import rsrw as rsrw_module
from modules import rsu_algoritmo as rsu_algoritmo_module
from modules import ema_edge as ema_edge_module
from modules import earnings as earnings_module
from modules import cartera as cartera_module
from modules import tesis as tesis_module
from modules import ia_report as ia_report_module
from modules import academy as academy_module
from modules import trade_grader as trade_grader_module
from modules import spxl_strategy as spxl_strategy_module
from modules import roadmap_2026 as roadmap_2026_module
from modules import trump_playbook as trump_playbook_module
from modules import comunidad as comunidad_module
from modules import disclaimer as disclaimer_module
from modules import auth as auth_module  # Sistema de auth mejorado

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
    
    /* Logo container */
    [data-testid="stSidebar"] .logo-container {
        background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 50%, #0c0e12 100%);
        padding: 25px 20px;
        border-bottom: 1px solid #2a3f5f;
        margin: -1rem -1rem 0 -1rem;
        text-align: center;
        position: relative;
    }
    
    /* Live badge */
    [data-testid="stSidebar"] .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, rgba(0,255,173,0.15) 0%, rgba(41,98,255,0.1) 100%);
        border: 1px solid rgba(0, 255, 173, 0.4);
        padding: 8px 16px;
        border-radius: 25px;
        margin-top: 15px;
    }
    
    [data-testid="stSidebar"] .live-dot {
        width: 8px;
        height: 8px;
        background: #00ffad;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Mini ticker */
    [data-testid="stSidebar"] .mini-ticker {
        background: #0c0e12;
        border: 1px solid #1a1e26;
        border-radius: 8px;
        padding: 10px;
        margin: 15px 0;
        overflow: hidden;
    }
    
    [data-testid="stSidebar"] .mini-ticker-content {
        display: flex;
        animation: ticker-slide 20s linear infinite;
        white-space: nowrap;
    }
    
    @keyframes ticker-slide {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    
    /* Market clock */
    [data-testid="stSidebar"] .market-clock {
        background: linear-gradient(135deg, rgba(41,98,255,0.1) 0%, rgba(0,255,173,0.05) 100%);
        border: 1px solid #2a3f5f;
        border-radius: 12px;
        padding: 15px;
        margin: 15px 0;
    }
    
    /* Menu styling */
    [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 12px 15px;
        margin: 3px 0;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
        border-color: rgba(41, 98, 255, 0.5);
        background: rgba(41, 98, 255, 0.05);
    }
    
    [data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(41, 98, 255, 0.15) 0%, rgba(0, 255, 173, 0.08) 100%);
        border-left: 3px solid #00ffad;
        border-top: 1px solid rgba(0, 255, 173, 0.3);
        border-bottom: 1px solid rgba(0, 255, 173, 0.3);
        border-right: 1px solid rgba(0, 255, 173, 0.3);
    }
    
    /* Section headers */
    [data-testid="stSidebar"] .section-header {
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
    
    /* User info en sidebar */
    .user-info {
        background: rgba(0, 255, 173, 0.05);
        border: 1px solid rgba(0, 255, 173, 0.2);
        border-radius: 8px;
        padding: 12px;
        margin: 15px 0;
    }
    
    .user-status {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #00ffad;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .session-timer {
        color: #888;
        font-size: 0.7rem;
        margin-top: 4px;
        font-family: monospace;
    }
    
    /* Logout button */
    .logout-btn {
        background: rgba(242, 54, 69, 0.1) !important;
        border: 1px solid rgba(242, 54, 69, 0.3) !important;
        color: #f23645 !important;
    }
    
    .logout-btn:hover {
        background: rgba(242, 54, 69, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# Funciones auxiliares
def get_market_status():
    """Determina si el mercado esta abierto"""
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    hour = ny_time.hour
    minute = ny_time.minute
    weekday = ny_time.weekday()
    
    if weekday < 5:
        if (hour == 9 and minute >= 30) or (10 <= hour < 16):
            return True, "OPEN"
    return False, "CLOSED"

def get_clock_times():
    """Obtiene horas de diferentes mercados"""
    times = {}
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
    
    return times

def format_session_time():
    """Formatea tiempo restante de sesión"""
    if "last_activity" in st.session_state and st.session_state["last_activity"]:
        elapsed = datetime.now() - st.session_state["last_activity"]
        remaining = timedelta(minutes=30) - elapsed
        if remaining.total_seconds() > 0:
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            return f"{minutes:02d}:{seconds:02d}"
    return "00:00"

# Control de acceso REAL usando auth.py mejorado
if not auth_module.login():
    st.stop()

# Inicializar motores
if 'rsrw_engine' not in st.session_state:
    try:
        from modules.rsrw import RSRWEngine
        st.session_state.rsrw_engine = RSRWEngine()
    except Exception as e:
        st.session_state.rsrw_engine = None

# --- SIDEBAR PROFESIONAL ---
with st.sidebar:
    
    # 1. LOGO Y HEADER
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
    
    # Badge de usuarios online
    try:
        usuarios_activos = actualizar_contador_usuarios()
    except:
        usuarios_activos = 1
    
    st.markdown(f"""
        <div style="text-align: center;">
            <div class="live-badge">
                <div class="live-dot"></div>
                <span style="color: #00ffad; font-size: 0.8rem; font-weight: 600;">{usuarios_activos} ONLINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. INFO DE USUARIO Y SESIÓN
    st.markdown("""
        <div class="user-info">
            <div class="user-status">
                <span>🟢</span>
                <span>SESIÓN ACTIVA</span>
            </div>
            <div class="session-timer">⏱️ Expira en: {}</div>
        </div>
    """.format(format_session_time()), unsafe_allow_html=True)
    
    # 3. MINI TICKER
    st.markdown('<div class="section-header">Live Markets</div>', unsafe_allow_html=True)
    
    try:
        spx = get_market_index("^GSPC")
        ndx = get_market_index("^IXIC")
        vix = get_market_index("^VIX")
        
        spx_color = "#00ffad" if spx[1] >= 0 else "#f23645"
        ndx_color = "#00ffad" if ndx[1] >= 0 else "#f23645"
        
        ticker_content = f"""
            <div class="mini-ticker">
                <div class="mini-ticker-content">
                    <span style="margin-right: 20px;">
                        <span style="color: #888;">S&P 500</span>
                        <span style="color: white; font-weight: bold;">{spx[0]:,.0f}</span>
                        <span style="color: {spx_color};">{spx[1]:+.2f}%</span>
                    </span>
                    <span style="margin-right: 20px;">
                        <span style="color: #888;">NASDAQ</span>
                        <span style="color: white; font-weight: bold;">{ndx[0]:,.0f}</span>
                        <span style="color: {ndx_color};">{ndx[1]:+.2f}%</span>
                    </span>
                    <span style="margin-right: 20px;">
                        <span style="color: #888;">VIX</span>
                        <span style="color: white; font-weight: bold;">{vix[0]:.2f}</span>
                    </span>
                </div>
            </div>
        """
        st.markdown(ticker_content, unsafe_allow_html=True)
    except:
        pass
    
    # 4. RELOJ DE MERCADOS
    is_open, status_text = get_market_status()
    status_dot = "🟢" if is_open else "🔴"
    times = get_clock_times()
    
    st.markdown(f"""
        <div class="market-clock">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: #888; font-size: 0.7rem; text-transform: uppercase;">Market Hours</span>
                <span style="color: {'#00ffad' if is_open else '#f23645'}; font-size: 0.7rem;">
                    {status_dot} {status_text}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px; text-align: center;">
                    <div style="color: #666; font-size: 0.65rem;">NY</div>
                    <div style="color: white; font-weight: bold;">{times['NY']}</div>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px; text-align: center;">
                    <div style="color: #666; font-size: 0.65rem;">LON</div>
                    <div style="color: white; font-weight: bold;">{times['LON']}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
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
    
    # 6. LOGOUT BUTTON
    st.markdown("---")
    if st.button("🔒 Cerrar Sesión", use_container_width=True, type="secondary"):
        auth_module.logout()

# --- LOGICA DE NAVEGACION ---
if menu == "📊 DASHBOARD":
    market_module.render()
elif menu == "📜 MANIFEST":
    manifest_module.render()
elif menu == "♣️ RSU CLUB":
    rsu_club_module.render()
elif menu == "📈 SCANNER RS/RW":
    rsrw_module.render()
elif menu == "🤖 ALGORITMO RSU":
    rsu_algoritmo_module.render()
elif menu == "⚡ EMA EDGE":
    ema_edge_module.render()
elif menu == "📅 EARNINGS":
    earnings_module.render()
elif menu == "💼 CARTERA":
    cartera_module.render()
elif menu == "📝 TESIS":
    tesis_module.render()
elif menu == "🤖 AI REPORT":
    ia_report_module.render()
elif menu == "🎓 ACADEMY":
    academy_module.render()
elif menu == "🏆 TRADE GRADER":
    trade_grader_module.render()
elif menu == "🚀 SPXL STRATEGY":
    spxl_strategy_module.render()
elif menu == "🗺️ ROADMAP 2026":
    roadmap_2026_module.render()
elif menu == "🇺🇸 TRUMP PLAYBOOK":
    trump_playbook_module.render()
elif menu == "👥 COMUNIDAD":
    comunidad_module.render()
elif menu == "⚠️ DISCLAIMER":
    disclaimer_module.render()



