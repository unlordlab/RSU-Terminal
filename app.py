# app.py
import os
import sys
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import pytz

# ============================================================
# CONFIGURACIÓN DE PÁGINA - DEBE SER LA PRIMERA LLAMADA STREAMLIT
# ============================================================
st.set_page_config(
    page_title="RSU Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# NO importar set_style todavía
from config import get_cnn_fear_greed, actualizar_contador_usuarios, get_market_index

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
from modules import auth as auth_module

# Control de acceso PRIMERO, sin estilos globales
if not auth_module.login():
    st.stop()

# AHORA sí aplicar estilos globales (después del login)
from config import set_style
set_style()

# CSS Sidebar con estética de market.py
st.markdown("""
<style>
    /* FONDO DEL SIDEBAR - Estética market.py */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0c10 0%, #11141a 50%, #0c0e12 100%);
        border-right: 1px solid #1a1e26;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding: 1rem 0.8rem;
    }
    
    /* CONTADOR DE USUARIOS - Sutil y pequeño */
    .visitor-counter {
        background: rgba(0, 255, 173, 0.03);
        border: 1px solid rgba(0, 255, 173, 0.15);
        border-radius: 20px;
        padding: 3px 10px;
        margin: 8px 0 15px 0;
        text-align: center;
        font-size: 0.6rem;
        color: #00ffad;
        font-family: 'Courier New', monospace;
        letter-spacing: 0.5px;
        opacity: 0.8;
    }
    
    .visitor-counter:hover {
        opacity: 1;
        border-color: rgba(0, 255, 173, 0.3);
    }
    
    /* INFO DE USUARIO */
    .user-info {
        background: rgba(0, 255, 173, 0.05);
        border: 1px solid rgba(0, 255, 173, 0.2);
        border-radius: 8px;
        padding: 10px 12px;
        margin: 10px 0;
        position: relative;
    }
    
    .user-status {
        color: #00ffad;
        font-size: 0.75rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .session-timer {
        color: #666;
        font-size: 0.65rem;
        margin-top: 4px;
        font-family: 'Courier New', monospace;
    }
    
    /* RELOJES GLOBALES - Grid 2x2 compacto */
    .clocks-container {
        background: #0c0e12;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        border: 1px solid #1a1e26;
    }
    
    .clocks-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
    }
    
    .clock-item {
        text-align: center;
        padding: 6px 2px;
        background: rgba(26, 30, 38, 0.5);
        border-radius: 4px;
        border: 1px solid transparent;
        transition: all 0.2s;
    }
    
    .clock-item:hover {
        border-color: #2a3f5f;
        background: rgba(26, 30, 38, 0.8);
    }
    
    .clock-label {
        color: #555;
        font-size: 0.55rem;
        font-weight: bold;
        letter-spacing: 1px;
        margin-bottom: 1px;
    }
    
    .clock-time {
        color: #00ffad;
        font-size: 0.8rem;
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }
    
    .market-status {
        text-align: center;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #1a1e26;
    }
    
    .market-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 0.6rem;
        font-weight: bold;
    }
    
    .market-open {
        background: rgba(0, 255, 173, 0.1);
        color: #00ffad;
        border: 1px solid rgba(0, 255, 173, 0.3);
    }
    
    .market-closed {
        background: rgba(242, 54, 69, 0.1);
        color: #f23645;
        border: 1px solid rgba(242, 54, 69, 0.3);
    }
    
    /* MENÚ ESTÉTICO - Botones MÁS PEQUEÑOS */
    .stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    
    .stRadio > div > label {
        background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%);
        border: 1px solid #1a1e26;
        border-radius: 6px;
        padding: 8px 12px !important;
        margin: 0 !important;
        transition: all 0.2s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        min-height: auto !important;
    }
    
    .stRadio > div > label:hover {
        border-color: #2a3f5f;
        background: linear-gradient(135deg, #1a1e26 0%, #11141a 100%);
        transform: translateX(2px);
    }
    
    .stRadio > div > label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
    
    .stRadio > div > label > div {
        color: #888;
        font-size: 0.75rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
        line-height: 1.2;
    }
    
    /* Estado seleccionado */
    .stRadio > div > label[aria-checked="true"] {
        background: linear-gradient(135deg, #1a3a2f 0%, #0f2a1f 100%);
        border-color: #00ffad;
        box-shadow: 0 0 10px rgba(0, 255, 173, 0.1);
    }
    
    .stRadio > div > label[aria-checked="true"] > div {
        color: #00ffad;
        font-weight: 600;
    }
    
    .stRadio > div > label[aria-checked="true"]::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 2px;
        background: #00ffad;
    }
    
    /* Separador elegante */
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #1a1e26 50%, transparent 100%);
        margin: 15px 0;
    }
    
    /* Botón logout estilizado y pequeño */
    .stButton > button {
        background: linear-gradient(135deg, #1a1e26 0%, #11141a 100%) !important;
        border: 1px solid #f23645 !important;
        color: #f23645 !important;
        border-radius: 6px !important;
        padding: 8px !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background: rgba(242, 54, 69, 0.1) !important;
        box-shadow: 0 0 8px rgba(242, 54, 69, 0.2) !important;
    }
    
    /* Ocultar radio circle nativo */
    .stRadio > div > div > div > div {
        display: none;
    }
    
    /* Reducir espacio entre elementos del sidebar */
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def get_market_status():
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    hour, minute, weekday = ny_time.hour, ny_time.minute, ny_time.weekday()
    
    if weekday < 5:
        if (hour == 9 and minute >= 30) or (10 <= hour < 16):
            return True, "OPEN"
    return False, "CLOSED"

def get_clock_times():
    times = {}
    now = datetime.now(pytz.UTC)
    markets = {
        'NY': 'America/New_York', 
        'LON': 'Europe/London', 
        'TKY': 'Asia/Tokyo',
        'MAD': 'Europe/Madrid',
        'SYD': 'Australia/Sydney'
    }
    
    for city, tz in markets.items():
        local_time = now.astimezone(pytz.timezone(tz))
        times[city] = local_time.strftime('%H:%M')
    return times

def format_session_time():
    if "last_activity" not in st.session_state or st.session_state["last_activity"] is None:
        return "30:00"
    
    try:
        elapsed = datetime.now() - st.session_state["last_activity"]
        remaining = timedelta(minutes=30) - elapsed
        
        if remaining.total_seconds() <= 0:
            return "00:00"
        
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        return f"{minutes:02d}:{seconds:02d}"
    except Exception:
        return "30:00"

def get_active_visitors():
    """Simula contador de visitantes activos - reemplazar con lógica real"""
    return 42

# Inicializar motores
if 'rsrw_engine' not in st.session_state:
    try:
        from modules.rsrw import RSRWEngine
        st.session_state.rsrw_engine = RSRWEngine()
    except:
        st.session_state.rsrw_engine = None

# Sidebar
with st.sidebar:
    # Logo más pequeño
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #00ffad; font-size: 1.5rem; margin-bottom: 3px;'>RSU</h2>", unsafe_allow_html=True)
    
    # CONTADOR DE VISITANTES
    active_visitors = get_active_visitors()
    st.markdown(f"""
        <div class="visitor-counter">
            ● {active_visitors} USUARIOS ACTIVOS
        </div>
    """, unsafe_allow_html=True)
    
    # Usuario y sesión compacto
    st.markdown(f"""
        <div class="user-info">
            <div class="user-status">🟢 SESIÓN ACTIVA</div>
            <div class="session-timer">⏱️ {format_session_time()}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # RELOJES GLOBALES compactos
    is_open, status = get_market_status()
    times = get_clock_times()
    
    status_class = "market-open" if is_open else "market-closed"
    status_icon = "🟢" if is_open else "🔴"
    
    st.markdown(f"""
        <div class="clocks-container">
            <div class="clocks-grid">
                <div class="clock-item">
                    <div class="clock-label">NY</div>
                    <div class="clock-time">{times['NY']}</div>
                </div>
                <div class="clock-item">
                    <div class="clock-label">LON</div>
                    <div class="clock-time">{times['LON']}</div>
                </div>
                <div class="clock-item">
                    <div class="clock-label">MAD</div>
                    <div class="clock-time">{times['MAD']}</div>
                </div>
                <div class="clock-item">
                    <div class="clock-label">SYD</div>
                    <div class="clock-time">{times['SYD']}</div>
                </div>
            </div>
            <div class="market-status">
                <span class="market-badge {status_class}">
                    {status_icon} MARKET {status}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # MENÚ ESTÉTICO COMPACTO
    menu = st.radio("", [
        "📊 DASHBOARD", "📜 MANIFEST", "♣️ RSU CLUB", "📈 SCANNER RS/RW", 
        "🤖 ALGORITMO RSU", "⚡ EMA EDGE", "📅 EARNINGS", "💼 CARTERA", 
        "📝 TESIS", "🤖 AI REPORT", "🎓 ACADEMY", "🏆 TRADE GRADER",
        "🚀 SPXL STRATEGY", "🗺️ ROADMAP 2026", "🇺🇸 TRUMP PLAYBOOK",
        "👥 COMUNIDAD", "⚠️ DISCLAIMER"
    ], label_visibility="collapsed")
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # Logout compacto
    if st.button("🔒 Cerrar Sesión", use_container_width=True, type="secondary"):
        auth_module.logout()

# Navegación
modules = {
    "📊 DASHBOARD": market_module,
    "📜 MANIFEST": manifest_module,
    "♣️ RSU CLUB": rsu_club_module,
    "📈 SCANNER RS/RW": rsrw_module,
    "🤖 ALGORITMO RSU": rsu_algoritmo_module,
    "⚡ EMA EDGE": ema_edge_module,
    "📅 EARNINGS": earnings_module,
    "💼 CARTERA": cartera_module,
    "📝 TESIS": tesis_module,
    "🤖 AI REPORT": ia_report_module,
    "🎓 ACADEMY": academy_module,
    "🏆 TRADE GRADER": trade_grader_module,
    "🚀 SPXL STRATEGY": spxl_strategy_module,
    "🗺️ ROADMAP 2026": roadmap_2026_module,
    "🇺🇸 TRUMP PLAYBOOK": trump_playbook_module,
    "👥 COMUNIDAD": comunidad_module,
    "⚠️ DISCLAIMER": disclaimer_module
}

if menu in modules:
    try:
        modules[menu].render()
    except Exception as e:
        st.error(f"Error cargando módulo: {e}")
