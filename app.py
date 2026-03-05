# app.py
import os
import sys
import base64
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

from config import get_cnn_fear_greed, actualizar_contador_usuarios, get_market_index

from modules import market as market_module
from modules import manifest as manifest_module
from modules import rsu_club as rsu_club_module
from modules import rsrw as rsrw_module
from modules import rsu_algoritmo as rsu_algoritmo_module
from modules import ema_edge as ema_edge_module
from modules import canslim as canslim_module
from modules import rsudb as rsudb_module
from modules import earnings as earnings_module
from modules import cartera as cartera_module
from modules import tesis as tesis_module
from modules import ia_report as ia_report_module
from modules import academy as academy_module
from modules import trade_grader as trade_grader_module
from modules import spxl_strategy as spxl_strategy_module
from modules import btc_stratum as btc_stratum_module
from modules import roadmap_2026 as roadmap_2026_module
from modules import trump_playbook as trump_playbook_module
from modules import comunidad as comunidad_module
from modules import disclaimer as disclaimer_module
from modules import auth as auth_module

# Control de acceso PRIMERO
if not auth_module.login():
    st.stop()

# Aplicar estilos globales tras login
from config import set_style
set_style()

# ============================================================
# HELPER: Logo con glow effect en base64
# ============================================================
def get_logo_html(logo_path: str) -> str:
    """Renderiza el logo con efecto glow neon animado. Si no existe el archivo,
    usa el fallback de texto."""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = logo_path.split(".")[-1].lower()
        mime = "image/png" if ext == "png" else f"image/{ext}"
        return f"""
        <div class="logo-glow-wrapper">
            <img src="data:{mime};base64,{b64}" class="logo-glow-img" alt="RSU Logo"/>
            <div class="logo-glow-ring"></div>
        </div>
        """
    else:
        return """
        <div class="logo-glow-wrapper">
            <div class="logo-text-fallback">RSU</div>
            <div class="logo-glow-ring"></div>
        </div>
        """

# ============================================================
# CSS GLOBAL — Estética terminal hacker (roadmap_2026 + sidebar)
# ============================================================
st.markdown("""
<style>
    /* ── FUENTES ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    /* ── APP BACKGROUND ──────────────────────────────────── */
    .stApp {
        background: #0c0e12;
    }

    /* ── HEADINGS GLOBALES (estética roadmap) ────────────── */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'VT323', monospace !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    h1 { font-size: 3.5rem !important; color: #00ffad !important; text-shadow: 0 0 20px #00ffad66; border-bottom: 2px solid #00ffad; padding-bottom: 15px; margin-bottom: 30px !important; }
    h2 { font-size: 2.2rem !important; color: #00d9ff !important; border-left: 4px solid #00ffad; padding-left: 15px; margin-top: 40px !important; }
    h3 { font-size: 1.8rem !important; color: #ff9800 !important; margin-top: 30px !important; }
    h4 { font-size: 1.5rem !important; color: #9c27b0 !important; }

    p, li { font-family: 'Courier New', monospace; color: #ccc !important; line-height: 1.8; font-size: 0.95rem; }
    strong { color: #00ffad; font-weight: bold; }
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00ffad, transparent); margin: 40px 0; }

    /* ── SIDEBAR BASE ────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0c10 0%, #11141a 50%, #0c0e12 100%);
        border-right: 1px solid #1a1e26;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 1rem 0.8rem;
    }

    /* ── LOGO GLOW ───────────────────────────────────────── */
    .logo-glow-wrapper {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px auto;
        width: 110px;
        height: 110px;
    }
    .logo-glow-img {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        object-fit: cover;
        position: relative;
        z-index: 2;
        filter:
            drop-shadow(0 0 8px #00ffad)
            drop-shadow(0 0 20px #00ffad99)
            drop-shadow(0 0 40px #00ffad44);
        animation: logoPulse 3s ease-in-out infinite;
    }
    .logo-text-fallback {
        font-family: 'VT323', monospace;
        font-size: 2.8rem;
        color: #00ffad;
        position: relative;
        z-index: 2;
        text-shadow: 0 0 15px #00ffad, 0 0 30px #00ffad88;
        animation: logoPulse 3s ease-in-out infinite;
    }
    .logo-glow-ring {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        width: 104px; height: 104px;
        border-radius: 50%;
        border: 1.5px solid #00ffad66;
        box-shadow:
            0 0 12px #00ffad44,
            inset 0 0 12px #00ffad22;
        animation: ringPulse 3s ease-in-out infinite;
        z-index: 1;
    }
    @keyframes logoPulse {
        0%, 100% { filter: drop-shadow(0 0 8px #00ffad) drop-shadow(0 0 20px #00ffad99) drop-shadow(0 0 40px #00ffad44); }
        50%       { filter: drop-shadow(0 0 14px #00ffad) drop-shadow(0 0 35px #00ffadcc) drop-shadow(0 0 60px #00ffad66); }
    }
    @keyframes ringPulse {
        0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
        50%       { opacity: 1;   transform: translate(-50%, -50%) scale(1.06); }
    }

    /* ── BRAND NAME ──────────────────────────────────────── */
    .brand-name {
        text-align: center;
        font-family: 'VT323', monospace;
        font-size: 1.3rem;
        color: #00ffad;
        letter-spacing: 4px;
        text-shadow: 0 0 10px #00ffad66;
        margin-bottom: 4px;
    }
    .brand-tagline {
        text-align: center;
        font-family: 'Courier New', monospace;
        font-size: 0.5rem;
        color: #334;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }

    /* ── VISITOR COUNTER ─────────────────────────────────── */
    .visitor-counter {
        background: rgba(0, 255, 173, 0.03);
        border: 1px solid rgba(0, 255, 173, 0.15);
        border-radius: 20px;
        padding: 3px 10px;
        margin: 8px 0 12px 0;
        text-align: center;
        font-size: 0.6rem;
        color: #00ffad;
        font-family: 'Courier New', monospace;
        letter-spacing: 0.5px;
        opacity: 0.8;
        transition: opacity 0.2s;
    }
    .visitor-counter:hover { opacity: 1; border-color: rgba(0, 255, 173, 0.3); }

    /* ── USER INFO ───────────────────────────────────────── */
    .user-info {
        background: rgba(0, 255, 173, 0.05);
        border: 1px solid rgba(0, 255, 173, 0.2);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 8px 0;
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
        color: #555;
        font-size: 0.62rem;
        margin-top: 3px;
        font-family: 'Courier New', monospace;
    }

    /* ── WORLD CLOCKS ────────────────────────────────────── */
    .clocks-container {
        background: #0c0e12;
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
        border: 1px solid #1a1e26;
    }
    .clocks-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 5px;
    }
    .clock-item {
        text-align: center;
        padding: 5px 2px;
        background: rgba(26, 30, 38, 0.5);
        border-radius: 4px;
        border: 1px solid transparent;
        transition: all 0.2s;
    }
    .clock-item:hover { border-color: #2a3f5f; background: rgba(26, 30, 38, 0.8); }
    .clock-label { color: #444; font-size: 0.52rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 1px; font-family: 'VT323', monospace; }
    .clock-time  { color: #00ffad; font-size: 0.85rem; font-family: 'Courier New', monospace; font-weight: bold; }
    .market-status { text-align: center; margin-top: 8px; padding-top: 6px; border-top: 1px solid #1a1e26; }
    .market-badge  { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 10px; font-size: 0.6rem; font-weight: bold; font-family: 'VT323', monospace; letter-spacing: 1px; }
    .market-open   { background: rgba(0, 255, 173, 0.1); color: #00ffad; border: 1px solid rgba(0, 255, 173, 0.3); }
    .market-closed { background: rgba(242, 54, 69, 0.1);  color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3); }

    /* ── SIDEBAR DIVIDER ─────────────────────────────────── */
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #1a1e26 50%, transparent 100%);
        margin: 12px 0;
    }

    /* ── MENU RADIO (VT323) ──────────────────────────────── */
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {
        display: flex; flex-direction: column; gap: 3px;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
        background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%);
        border: 1px solid #1a1e26;
        border-radius: 6px;
        padding: 7px 12px !important;
        margin: 0 !important;
        transition: all 0.2s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        min-height: auto !important;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
        border-color: #2a3f5f;
        background: linear-gradient(135deg, #1a1e26 0%, #11141a 100%);
        transform: translateX(2px);
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child { display: none !important; }

    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label span,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        color: #666 !important;
        font-size: 1.25rem !important;
        font-weight: 400 !important;
        font-family: 'VT323', monospace !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        line-height: 1.2 !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
        background: linear-gradient(135deg, #1a3a2f 0%, #0f2a1f 100%);
        border-color: #00ffad;
        box-shadow: 0 0 12px rgba(0, 255, 173, 0.12);
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] p,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] div[data-testid="stMarkdownContainer"] p {
        color: #00ffad !important;
        font-family: 'VT323', monospace !important;
        text-shadow: 0 0 6px #00ffad66;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"]::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 2px;
        background: #00ffad;
        box-shadow: 0 0 6px #00ffad;
    }

    /* ── LOGOUT BUTTON ───────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #1a1e26 0%, #11141a 100%) !important;
        border: 1px solid #f23645 !important;
        color: #f23645 !important;
        border-radius: 6px !important;
        padding: 7px !important;
        font-size: 0.72rem !important;
        font-family: 'VT323', monospace !important;
        letter-spacing: 1px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        background: rgba(242, 54, 69, 0.1) !important;
        box-shadow: 0 0 10px rgba(242, 54, 69, 0.25) !important;
    }

    /* ── HIDE RADIO CIRCLE ───────────────────────────────── */
    .stRadio > div > div > div > div { display: none; }

    /* ── SCROLLBAR ───────────────────────────────────────── */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: #0c0e12; }
    ::-webkit-scrollbar-thumb { background: #1a1e26; border-radius: 2px; }
    ::-webkit-scrollbar-thumb:hover { background: #00ffad44; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def get_market_status():
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    hour, minute, weekday = ny_time.hour, ny_time.minute, ny_time.weekday()
    if weekday < 5:
        if (hour == 9 and minute >= 30) or (10 <= hour < 16):
            return True, "OPEN"
    return False, "CLOSED"

def get_clock_times():
    now = datetime.now(pytz.UTC)
    markets = {
        'NY':  'America/New_York',
        'LON': 'Europe/London',
        'TKY': 'Asia/Tokyo',
        'MAD': 'Europe/Madrid',
        'SYD': 'Australia/Sydney'
    }
    return {city: now.astimezone(pytz.timezone(tz)).strftime('%H:%M') for city, tz in markets.items()}

def format_session_time():
    if "last_activity" not in st.session_state or st.session_state["last_activity"] is None:
        return "30:00"
    try:
        elapsed = datetime.now() - st.session_state["last_activity"]
        remaining = timedelta(minutes=30) - elapsed
        if remaining.total_seconds() <= 0:
            return "00:00"
        m = int(remaining.total_seconds() // 60)
        s = int(remaining.total_seconds() % 60)
        return f"{m:02d}:{s:02d}"
    except Exception:
        return "30:00"

def get_active_visitors():
    return 42  # Reemplazar con lógica real

# ============================================================
# INICIALIZAR MOTORES
# ============================================================
if 'rsrw_engine' not in st.session_state:
    try:
        from modules.rsrw import RSRWEngine
        st.session_state.rsrw_engine = RSRWEngine()
    except Exception:
        st.session_state.rsrw_engine = None

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:

    # LOGO CON GLOW
    st.markdown(get_logo_html("assets/logo.png"), unsafe_allow_html=True)
    st.markdown('<div class="brand-name">RSU</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-tagline">[ TRADING PLATFORM // v2.0 ]</div>', unsafe_allow_html=True)

    # CONTADOR DE VISITANTES
    st.markdown(f"""
        <div class="visitor-counter">
            ● {get_active_visitors()} USUARIOS ACTIVOS
        </div>
    """, unsafe_allow_html=True)

    # SESIÓN
    st.markdown(f"""
        <div class="user-info">
            <div class="user-status">🟢 SESIÓN ACTIVA</div>
            <div class="session-timer">⏱ {format_session_time()}</div>
        </div>
    """, unsafe_allow_html=True)

    # RELOJES GLOBALES
    is_open, status = get_market_status()
    times = get_clock_times()
    status_class = "market-open" if is_open else "market-closed"
    status_icon  = "🟢" if is_open else "🔴"

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

    # MENÚ
    menu = st.radio("", [
        "📊 DASHBOARD", "📜 MANIFEST", "♣️ RSU CLUB", "📈 SCANNER RS/RW",
        "🤖 ALGORITMO RSU", "⚡ EMA EDGE", "🎯 CAN SLIM", "🗄️ RSU DB",
        "📅 EARNINGS", "💼 CARTERA", "📝 TESIS", "🤖 AI REPORT",
        "🎓 ACADEMY", "🏆 TRADE GRADER", "🚀 SPXL STRATEGY",
        "₿ BTC STRATUM", "🗺️ ROADMAP 2026", "🇺🇸 TRUMP PLAYBOOK",
        "👥 COMUNIDAD", "⚠️ DISCLAIMER"
    ], label_visibility="collapsed")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # LOGOUT
    if st.button("🔒 CERRAR SESIÓN", use_container_width=True, type="secondary"):
        auth_module.logout()

# ============================================================
# NAVEGACIÓN
# ============================================================
modules = {
    "📊 DASHBOARD":        market_module,
    "📜 MANIFEST":         manifest_module,
    "♣️ RSU CLUB":         rsu_club_module,
    "📈 SCANNER RS/RW":    rsrw_module,
    "🤖 ALGORITMO RSU":    rsu_algoritmo_module,
    "⚡ EMA EDGE":          ema_edge_module,
    "🎯 CAN SLIM":         canslim_module,
    "🗄️ RSU DB":           rsudb_module,
    "📅 EARNINGS":         earnings_module,
    "💼 CARTERA":          cartera_module,
    "📝 TESIS":            tesis_module,
    "🤖 AI REPORT":        ia_report_module,
    "🎓 ACADEMY":          academy_module,
    "🏆 TRADE GRADER":     trade_grader_module,
    "🚀 SPXL STRATEGY":    spxl_strategy_module,
    "₿ BTC STRATUM":       btc_stratum_module,
    "🗺️ ROADMAP 2026":     roadmap_2026_module,
    "🇺🇸 TRUMP PLAYBOOK":  trump_playbook_module,
    "👥 COMUNIDAD":        comunidad_module,
    "⚠️ DISCLAIMER":       disclaimer_module,
}

if menu in modules:
    try:
        modules[menu].render()
    except Exception as e:
        st.error(f"Error cargando módulo: {e}")



