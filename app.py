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
# CONFIGURACIÓN DE PÁGINA
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
# HELPER: Logo cuadrado con glow estático multicapa
# ============================================================
def get_logo_html(logo_path: str) -> str:
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = logo_path.split(".")[-1].lower()
        mime = "image/png" if ext == "png" else f"image/{ext}"
        return f"""
        <div class="logo-sq-wrapper">
            <img src="data:{mime};base64,{b64}" class="logo-sq-img" alt="RSU Logo"/>
        </div>
        """
    else:
        return """
        <div class="logo-sq-wrapper">
            <div class="logo-sq-fallback">RSU</div>
        </div>
        """

# ============================================================
# CSS GLOBAL
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    /* ── BASE ─────────────────────────────────────────────── */
    html, body, .stApp {
        background-color: #0c0e12 !important;
    }

    /* ── SCANLINES CRT ───────────────────────────────────── */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none;
        z-index: 1;
        background: repeating-linear-gradient(
            to bottom,
            transparent 0px,
            transparent 3px,
            rgba(0, 0, 0, 0.05) 3px,
            rgba(0, 0, 0, 0.05) 4px
        );
    }

    /* ── HEADINGS ────────────────────────────────────────── */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'VT323', monospace !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    h1 { font-size: 3.5rem !important; color: #00ffad !important; text-shadow: 0 0 20px #00ffad66; border-bottom: 2px solid #00ffad; padding-bottom: 15px; margin-bottom: 30px !important; }
    h2 { font-size: 2.2rem !important; color: #00d9ff !important; border-left: 4px solid #00d9ff; padding-left: 15px; margin-top: 40px !important; text-shadow: 0 0 12px #00d9ff44; }
    h3 { font-size: 1.8rem !important; color: #ff9800 !important; margin-top: 30px !important; }
    h4 { font-size: 1.5rem !important; color: #9c27b0 !important; }

    p, li { font-family: 'Courier New', monospace; color: #ccc !important; line-height: 1.8; font-size: 0.95rem; }
    strong { color: #00ffad; font-weight: bold; }
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00d9ff55, #00ffad, #00d9ff55, transparent); margin: 40px 0; }

    /* ── SIDEBAR + PARTÍCULAS ────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0c10 0%, #11141a 50%, #0c0e12 100%);
        border-right: 1px solid #00d9ff22;
        position: relative;
        overflow: hidden;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 1rem 0.8rem;
        position: relative;
        z-index: 2;
    }
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        z-index: 0;
        pointer-events: none;
        background-image:
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00d9ff 1px, transparent 1px),
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00d9ff 1px, transparent 1px),
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00d9ff 1px, transparent 1px),
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00ffad 1px, transparent 1px),
            radial-gradient(circle, #00d9ff 1px, transparent 1px);
        background-size:
            180px 180px, 220px 220px, 160px 200px,
            200px 240px, 140px 180px, 260px 200px,
            190px 210px, 230px 170px, 150px 230px,
            210px 190px, 170px 250px, 240px 160px;
        background-position:
            20px 30px,   80px 120px,  140px 60px,
            50px 200px,  110px 280px, 170px 160px,
            30px 350px,  90px 430px,  150px 310px,
            60px 500px,  130px 580px, 180px 460px;
        opacity: 0.12;
        animation: particlesDrift 20s linear infinite;
    }
    @keyframes particlesDrift {
        0%   { background-position:
                20px 30px,   80px 120px,  140px 60px,
                50px 200px,  110px 280px, 170px 160px,
                30px 350px,  90px 430px,  150px 310px,
                60px 500px,  130px 580px, 180px 460px; }
        50%  { opacity: 0.18; }
        100% { background-position:
                20px -570px,   80px -480px,  140px -540px,
                50px -400px,  110px -320px, 170px -440px,
                30px -250px,  90px -170px,  150px -290px,
                60px -100px,  130px  -20px, 180px -140px; }
    }

    /* ── LOGO CUADRADO CON GLOW ESTÁTICO ─────────────────── */
    .logo-sq-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
        width: 100px;
        height: 100px;
        border-radius: 16px;
        box-shadow:
            0 0 0 1px #00ffad55,
            0 0 10px  #00ffadaa,
            0 0 22px  #00ffad66,
            0 0 40px  #00ffad33,
            0 0 8px   #b044ff99,
            0 0 20px  #b044ff44;
        background: #0a0c10;
    }
    .logo-sq-img {
        width: 100px;
        height: 100px;
        border-radius: 16px;
        object-fit: cover;
        display: block;
        filter: drop-shadow(0 0 6px #00ffad88) drop-shadow(0 0 14px #b044ff55);
    }
    .logo-sq-fallback {
        font-family: 'VT323', monospace;
        font-size: 3rem;
        color: #00ffad;
        text-shadow: 0 0 10px #00ffad, 0 0 25px #00ffad88, 0 0 5px #b044ff;
        line-height: 1;
    }

    /* ── BRAND ───────────────────────────────────────────── */
    .brand-name {
        text-align: center; font-family: 'VT323', monospace;
        font-size: 1.3rem; color: #00ffad; letter-spacing: 4px;
        text-shadow: 0 0 10px #00ffad66; margin-bottom: 2px;
    }
    .brand-tagline {
        text-align: center; font-family: 'Courier New', monospace;
        font-size: 0.48rem; color: #00d9ff55; letter-spacing: 2px; margin-bottom: 10px;
    }

    /* ── VISITOR COUNTER ─────────────────────────────────── */
    .visitor-counter {
        background: rgba(0, 217, 255, 0.04);
        border: 1px solid rgba(0, 217, 255, 0.2);
        border-radius: 20px; padding: 3px 10px; margin: 8px 0 12px 0;
        text-align: center; font-size: 0.6rem; color: #00d9ff;
        font-family: 'Courier New', monospace; letter-spacing: 0.5px;
        opacity: 0.85; transition: opacity 0.2s;
    }
    .visitor-counter:hover { opacity: 1; border-color: rgba(0, 217, 255, 0.4); }

    /* ── USER INFO ───────────────────────────────────────── */
    .user-info {
        background: rgba(0, 217, 255, 0.04);
        border: 1px solid rgba(0, 217, 255, 0.18);
        border-radius: 8px; padding: 8px 12px; margin: 8px 0;
    }
    .user-status {
        color: #00ffad; font-size: 0.75rem; font-weight: 600;
        font-family: 'VT323', monospace; letter-spacing: 1px;
        display: flex; align-items: center; gap: 5px;
    }
    .session-timer { color: #00d9ff88; font-size: 0.62rem; margin-top: 3px; font-family: 'Courier New', monospace; }

    /* ── WORLD CLOCKS ────────────────────────────────────── */
    .clocks-container {
        background: rgba(0, 217, 255, 0.02); border-radius: 8px;
        padding: 10px; margin: 8px 0; border: 1px solid #00d9ff1a;
    }
    .clocks-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
    .clock-item {
        text-align: center; padding: 5px 2px;
        background: rgba(26, 30, 38, 0.5); border-radius: 4px;
        border: 1px solid transparent; transition: all 0.2s;
    }
    .clock-item:hover { border-color: #00d9ff33; background: rgba(0, 217, 255, 0.05); }
    .clock-item:first-child .clock-time { color: #00ffad; }
    .clock-label { color: #00d9ff66; font-size: 0.52rem; font-weight: bold; letter-spacing: 1px; margin-bottom: 1px; font-family: 'VT323', monospace; }
    .clock-time  { color: #00d9ff; font-size: 0.85rem; font-family: 'Courier New', monospace; font-weight: bold; }
    .market-status { text-align: center; margin-top: 8px; padding-top: 6px; border-top: 1px solid #00d9ff1a; }
    .market-badge  { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 10px; font-size: 0.65rem; font-weight: bold; font-family: 'VT323', monospace; letter-spacing: 2px; }
    .market-open   { background: rgba(0, 255, 173, 0.08); color: #00ffad; border: 1px solid rgba(0, 255, 173, 0.3); box-shadow: 0 0 8px #00ffad22; }
    .market-closed { background: rgba(242, 54, 69, 0.08); color: #f23645; border: 1px solid rgba(242, 54, 69, 0.3); box-shadow: 0 0 8px #f2364522; }

    /* ── SIDEBAR DIVIDER ─────────────────────────────────── */
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #00d9ff33 50%, transparent 100%);
        margin: 12px 0;
    }

    /* ── MENU RADIO ──────────────────────────────────────── */
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] { display: flex; flex-direction: column; gap: 3px; }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
        background: linear-gradient(135deg, #11141a 0%, #0c0e12 100%);
        border: 1px solid #1a1e26; border-radius: 6px; padding: 7px 12px !important;
        margin: 0 !important; transition: all 0.2s ease; cursor: pointer;
        position: relative; overflow: hidden; min-height: auto !important;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
        border-color: #00d9ff33;
        background: linear-gradient(135deg, #0d1520 0%, #0a0f18 100%);
        transform: translateX(2px);
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child { display: none !important; }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label span,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        color: #555 !important; font-size: 1.25rem !important; font-weight: 400 !important;
        font-family: 'VT323', monospace !important; text-transform: uppercase !important;
        letter-spacing: 1px !important; line-height: 1.2 !important; margin: 0 !important;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover p,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover div[data-testid="stMarkdownContainer"] p {
        color: #00d9ff !important;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] {
        background: linear-gradient(135deg, #112a1f 0%, #0c1e16 100%);
        border-color: #00ffad55;
        box-shadow: 0 0 12px rgba(0, 255, 173, 0.08), inset 0 0 20px rgba(0, 255, 173, 0.03);
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] p,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] div[data-testid="stMarkdownContainer"] p {
        color: #00ffad !important; font-family: 'VT323', monospace !important; text-shadow: 0 0 8px #00ffad55;
    }
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"]::before {
        content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
        background: linear-gradient(180deg, #00d9ff, #00ffad); box-shadow: 0 0 6px #00ffad;
    }
    .stRadio > div > div > div > div { display: none; }

    /* ── LOGOUT BUTTON ───────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #1a1e26 0%, #11141a 100%) !important;
        border: 1px solid #f2364566 !important; color: #f23645 !important;
        border-radius: 6px !important; padding: 7px !important; font-size: 0.78rem !important;
        font-family: 'VT323', monospace !important; letter-spacing: 2px !important;
        font-weight: 400 !important; transition: all 0.2s !important;
    }
    .stButton > button:hover {
        background: rgba(242, 54, 69, 0.08) !important;
        border-color: #f23645 !important; box-shadow: 0 0 10px rgba(242, 54, 69, 0.2) !important;
    }

    /* ══════════════════════════════════════════════════════
       INPUTS, SELECTS, DROPDOWNS
       ══════════════════════════════════════════════════════ */
    input, textarea, select,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: #11141a !important; color: #cccccc !important;
        border-color: #2a3040 !important; caret-color: #00ffad !important;
    }
    input:focus, textarea:focus {
        border-color: #00ffad55 !important; box-shadow: 0 0 0 1px #00ffad22 !important; outline: none !important;
    }
    input::placeholder, textarea::placeholder { color: #444 !important; }
    [data-baseweb="select"] > div, [data-baseweb="popover"],
    [data-baseweb="menu"], [role="listbox"] {
        background-color: #11141a !important; color: #cccccc !important; border-color: #2a3040 !important;
    }
    [role="option"] { background-color: #11141a !important; color: #cccccc !important; }
    [role="option"]:hover, [aria-selected="true"] { background-color: rgba(0, 255, 173, 0.08) !important; color: #00ffad !important; }
    [data-baseweb="tag"] { background-color: rgba(0, 255, 173, 0.1) !important; color: #00ffad !important; border: 1px solid #00ffad33 !important; }

    /* ══════════════════════════════════════════════════════
       EXPANDERS, TABS, ALERTS, TOOLTIPS, PROGRESS
       ══════════════════════════════════════════════════════ */
    [data-testid="stExpander"] { background-color: #11141a !important; border: 1px solid #1a1e26 !important; border-radius: 6px !important; }
    [data-testid="stExpander"] summary { color: #00d9ff !important; font-family: 'VT323', monospace !important; font-size: 1.1rem !important; }
    [data-testid="stTabs"] [role="tablist"] { background-color: transparent !important; border-bottom: 1px solid #1a1e26 !important; }
    [data-testid="stTabs"] [role="tab"] { color: #555 !important; background-color: transparent !important; }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #00ffad !important; border-bottom: 2px solid #00ffad !important; }
    [data-testid="stAlert"] { background-color: #11141a !important; border-color: #2a3040 !important; color: #cccccc !important; }
    [data-baseweb="tooltip"] > div { background-color: #1a1e26 !important; color: #cccccc !important; border: 1px solid #2a3040 !important; }
    [data-testid="stProgressBar"] > div { background-color: #1a1e26 !important; }
    [data-testid="stProgressBar"] > div > div { background-color: #00ffad !important; }

    /* ── SCROLLBAR ───────────────────────────────────────── */
    ::-webkit-scrollbar { width: 3px; }
    ::-webkit-scrollbar-track { background: #0c0e12; }
    ::-webkit-scrollbar-thumb { background: #00d9ff22; border-radius: 2px; }
    ::-webkit-scrollbar-thumb:hover { background: #00d9ff66; }

    /* ══════════════════════════════════════════════════════
       RESPONSIVE
       ══════════════════════════════════════════════════════ */
    .main .block-container {
        min-width: 0; max-width: 100% !important;
        padding-left: 1.5rem !important; padding-right: 1.5rem !important;
        box-sizing: border-box;
    }
    [data-testid="column"] { min-width: 0; overflow: visible !important; }

    @media screen and (min-width: 640px) {
        [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: stretch; gap: 0.75rem; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] { flex-shrink: 1 !important; min-width: 120px !important; }
    }
    @media screen and (max-width: 639px) {
        [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] { flex: 1 1 100% !important; min-width: 100% !important; }
    }

    [data-testid="stMetric"] { min-width: 100px; overflow: visible !important; }
    [data-testid="stMetricValue"] { white-space: nowrap !important; overflow: visible !important; text-overflow: unset !important; font-size: clamp(1rem, 1.8vw, 1.6rem) !important; }
    [data-testid="stMetricLabel"] { white-space: nowrap !important; font-size: clamp(0.6rem, 1.1vw, 0.85rem) !important; }
    [data-testid="stMetricDelta"] { white-space: nowrap !important; font-size: clamp(0.55rem, 0.9vw, 0.75rem) !important; }

    .js-plotly-plot, .plotly, [data-testid="stPlotlyChart"] { min-height: 300px; width: 100% !important; }

    [data-testid="stDataFrame"], .stDataFrame { overflow-x: auto !important; max-width: 100%; }

    [data-testid="stTabs"] [role="tab"] { white-space: nowrap; font-size: clamp(0.7rem, 1.2vw, 0.9rem) !important; }

    [data-testid="stSelectbox"], [data-testid="stMultiSelect"],
    [data-testid="stTextInput"] { min-width: 0 !important; max-width: 100% !important; }

    /* Sidebar ancho fijo universal */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child {
        width: 238px !important; min-width: 238px !important;
        max-width: 238px !important; box-sizing: border-box !important;
    }
    @media screen and (min-width: 640px) and (max-width: 1280px) {
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child {
            width: 210px !important; min-width: 210px !important; max-width: 210px !important;
        }
        .main .block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    }
    @media screen and (max-width: 639px) {
        .main { margin-left: 0 !important; padding-left: 0 !important; width: 100% !important; max-width: 100% !important; }
        .main .block-container { padding-left: 0.6rem !important; padding-right: 0.6rem !important; max-width: 100% !important; }
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child { width: auto !important; min-width: 0 !important; max-width: 85vw !important; }
    }
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

    st.markdown(get_logo_html("assets/logo.png"), unsafe_allow_html=True)
    st.markdown('<div class="brand-name">RSU</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-tagline">[ TRADING PLATFORM // v2.0 ]</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="visitor-counter">● {get_active_visitors()} USUARIOS ACTIVOS</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="user-info">
            <div class="user-status">🟢 SESIÓN ACTIVA</div>
            <div class="session-timer">⏱ {format_session_time()}</div>
        </div>
    """, unsafe_allow_html=True)

    is_open, status = get_market_status()
    times = get_clock_times()
    status_class = "market-open" if is_open else "market-closed"
    status_icon  = "🟢" if is_open else "🔴"

    st.markdown(f"""
        <div class="clocks-container">
            <div class="clocks-grid">
                <div class="clock-item"><div class="clock-label">NY</div><div class="clock-time">{times['NY']}</div></div>
                <div class="clock-item"><div class="clock-label">LON</div><div class="clock-time">{times['LON']}</div></div>
                <div class="clock-item"><div class="clock-label">MAD</div><div class="clock-time">{times['MAD']}</div></div>
                <div class="clock-item"><div class="clock-label">SYD</div><div class="clock-time">{times['SYD']}</div></div>
            </div>
            <div class="market-status">
                <span class="market-badge {status_class}">{status_icon} MARKET {status}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    menu = st.radio("", [
        "📊 DASHBOARD", "📜 MANIFEST", "♣️ RSU CLUB", "📈 SCANNER RS/RW",
        "🤖 ALGORITMO RSU", "⚡ EMA EDGE", "🎯 CAN SLIM", "🗄️ RSU DB",
        "🔬 RSU RESEARCH", "💼 CARTERA", "📝 TESIS", "🤖 AI REPORT",
        "🎓 ACADEMY", "🏆 TRADE GRADER", "🚀 SPXL STRATEGY",
        "₿ BTC STRATUM", "🗺️ ROADMAP 2026", "🇺🇸 TRUMP PLAYBOOK",
        "👥 COMUNIDAD", "⚠️ DISCLAIMER"
    ], label_visibility="collapsed")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

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
    "🔬 RSU RESEARCH":     earnings_module,
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


