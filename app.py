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
    layout="wide",  # ← MODO WIDE ACTIVADO
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

# CSS Sidebar (solo para usuarios logueados)
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0c10 0%, #11141a 50%, #0c0e12 100%);
        border-right: 1px solid #1a1e26;
    }
    
    .user-info {
        background: rgba(0, 255, 173, 0.05);
        border: 1px solid rgba(0, 255, 173, 0.2);
        border-radius: 8px;
        padding: 12px;
        margin: 15px 0;
    }
    
    .user-status {
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
    markets = {'NY': 'America/New_York', 'LON': 'Europe/London', 'TKY': 'Asia/Tokyo'}
    
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

# Inicializar motores
if 'rsrw_engine' not in st.session_state:
    try:
        from modules.rsrw import RSRWEngine
        st.session_state.rsrw_engine = RSRWEngine()
    except:
        st.session_state.rsrw_engine = None

# Sidebar
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #00ffad;'>RSU</h2>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="user-info">
            <div class="user-status">🟢 SESIÓN ACTIVA</div>
            <div class="session-timer">⏱️ {format_session_time()}</div>
        </div>
    """, unsafe_allow_html=True)
    
    is_open, status = get_market_status()
    times = get_clock_times()
    
    st.markdown(f"""
        <div style="background: #0c0e12; border-radius: 8px; padding: 12px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #888; font-size: 0.7rem;">Market</span>
                <span style="color: {'#00ffad' if is_open else '#f23645'}; font-size: 0.7rem;">
                    {'🟢' if is_open else '🔴'} {status}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px;">
                <div style="text-align: center;">
                    <div style="color: #666; font-size: 0.6rem;">NY</div>
                    <div style="color: white; font-size: 0.8rem;">{times['NY']}</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #666; font-size: 0.6rem;">LON</div>
                    <div style="color: white; font-size: 0.8rem;">{times['LON']}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio("", [
        "📊 DASHBOARD", "📜 MANIFEST", "♣️ RSU CLUB", "📈 SCANNER RS/RW", 
        "🤖 ALGORITMO RSU", "⚡ EMA EDGE", "📅 EARNINGS", "💼 CARTERA", 
        "📝 TESIS", "🤖 AI REPORT", "🎓 ACADEMY", "🏆 TRADE GRADER",
        "🚀 SPXL STRATEGY", "🗺️ ROADMAP 2026", "🇺🇸 TRUMP PLAYBOOK",
        "👥 COMUNIDAD", "⚠️ DISCLAIMER"
    ], label_visibility="collapsed")
    
    st.markdown("---")
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
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




