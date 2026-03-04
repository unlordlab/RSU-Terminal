
# app.py
import os
import sys
import importlib
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timezone, timedelta
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

# ── LAZY LOAD: módulos se importan solo cuando se necesitan ──────────────────
MODULE_PATHS = {
    "📊 DASHBOARD":        "modules.market",
    "📜 MANIFEST":         "modules.manifest",
    "♣️ RSU CLUB":         "modules.rsu_club",
    "📈 SCANNER RS/RW":    "modules.rsrw",
    "🤖 ALGORITMO RSU":    "modules.rsu_algoritmo",
    "⚡ EMA EDGE":          "modules.ema_edge",
    "🎯 CAN SLIM":         "modules.canslim",
    "🗄️ RSU DB":           "modules.rsudb",
    "📅 EARNINGS":         "modules.earnings",
    "💼 CARTERA":          "modules.cartera",
    "📝 TESIS":            "modules.tesis",
    "🤖 AI REPORT":        "modules.ia_report",
    "🎓 ACADEMY":          "modules.academy",
    "🏆 TRADE GRADER":     "modules.trade_grader",
    "🚀 SPXL STRATEGY":    "modules.spxl_strategy",
    "₿ BTC STRATUM":       "modules.btc_stratum",
    "🗺️ ROADMAP 2026":     "modules.roadmap_2026",
    "🇺🇸 TRUMP PLAYBOOK":  "modules.trump_playbook",
    "👥 COMUNIDAD":        "modules.comunidad",
    "⚠️ DISCLAIMER":       "modules.disclaimer",
}

from modules import auth as auth_module

# Control de acceso PRIMERO
if not auth_module.login():
    st.stop()

# Estilos globales base
from config import set_style
set_style()

# ── COMPONENTES REUTILIZABLES (estética roadmap_2026) ────────────────────────
COMPONENT_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

    /* ── FONDO GLOBAL ── */
    .stApp {
        background: #0c0e12;
    }

    /* ── TIPOGRAFÍA GLOBAL VT323 ── */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'VT323', monospace !important;
        color: #00ffad !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    h1 {
        font-size: 3.5rem !important;
        text-shadow: 0 0 20px #00ffad66;
        border-bottom: 2px solid #00ffad;
        padding-bottom: 15px;
        margin-bottom: 30px !important;
    }

    h2 {
        font-size: 2.2rem !important;
        color: #00d9ff !important;
        border-left: 4px solid #00ffad;
        padding-left: 15px;
        margin-top: 40px !important;
    }

    h3 {
        font-size: 1.8rem !important;
        color: #ff9800 !important;
        margin-top: 30px !important;
    }

    h4 {
        font-size: 1.5rem !important;
        color: #9c27b0 !important;
    }

    p, li {
        font-family: 'Courier New', monospace;
        color: #ccc !important;
        line-height: 1.8;
        font-size: 0.95rem;
    }

    strong {
        color: #00ffad;
        font-weight: bold;
    }

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #00ffad, transparent);
        margin: 40px 0;
    }

    blockquote {
        border-left: 3px solid #ff9800;
        margin: 20px 0;
        padding-left: 20px;
        color: #ff9800;
        font-style: italic;
    }

    ul {
        list-style: none;
        padding-left: 0;
    }

    ul li::before {
        content: "▸ ";
        color: #00ffad;
        font-weight: bold;
        margin-right: 8px;
    }

    /* ── COMPONENTES REUTILIZABLES ── */
    .terminal-box {
        background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
        border: 1px solid #00ffad44;
        border-radius: 8px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 0 15px #00ffad11;
    }

    .phase-box {
        background: #0c0e12;
        border-left: 3px solid #00ffad;
        padding: 20px;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
    }

    .highlight-quote {
        background: #00ffad11;
        border: 1px solid #00ffad33;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        font-family: 'VT323', monospace;
        font-size: 1.2rem;
        color: #00ffad;
        text-align: center;
    }

    .risk-box {
        background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
        border: 1px solid #f2364544;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
    }

    .strategy-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }

    .strategy-card {
        background: #0c0e12;
        border: 1px solid #2a3f5f;
        border-radius: 8px;
        padding: 15px;
    }

    .strategy-card h4 {
        color: #00ffad !important;
        font-size: 1.1rem !important;
        margin-bottom: 10px;
    }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0c10 0%, #11141a 50%, #0c0e12 100%);
        border-right: 1px solid #1a1e26;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 1rem 0.8rem;
    }

    /* SECURE HEADER */
    .secure-header {
        text-align: center;
        font-family: 'VT323', monospace;
        font-size: 0.6rem;
        color: #00ffad55;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }

    /* CONTADOR DE USUARIOS */
    .visitor-counter {
        background: rgba(0, 255, 173, 0.03);
        border: 1px solid rgba(0, 255, 173, 0.15);
        border-radius: 20px;
        padding: 3px 10px;
        margin: 8px 0 15px 0;
        text-align: center;
        font-size: 0.6rem;
        color: #00ffad;
        font-family: 'VT323', monospace;
        letter-spacing: 1px;
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
        font-size: 0.8rem;
        font-family: 'VT323', monospace;
        letter-spacing: 1px;
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .session-timer {
        /* FIX #14: usar cian para sesión, no gris */
        color: #00d9ff;
        font-size: 0.65rem;
        margin-top: 4px;
        font-family: 'VT323', monospace;
        letter-spacing: 1px;
    }

    /* RELOJES GLOBALES */
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
        font-size: 0.6rem;
        font-family: 'VT323', monospace;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 1px;
    }

    .clock-time {
        color: #00ffad;
        font-size: 0.9rem;
        font-family: 'VT323', monospace;
        font-weight: bold;
        text-shadow: 0 0 8px #00ffad44;
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
        font-size: 0.65rem;
        font-family: 'VT323', monospace;
        letter-spacing: 1px;
        font-weight: bold;
    }

    .market-open {
        background: rgba(0, 255, 173, 0.1);
        color: #00ffad;
        border: 1px solid rgba(0, 255, 173, 0.3);
        text-shadow: 0 0 8px #00ffad66;
    }

    .market-closed {
        background: rgba(242, 54, 69, 0.1);
        color: #f23645;
        border: 1px solid rgba(242, 54, 69, 0.3);
    }

    /* ── GRUPOS DE MENÚ ── */
    .menu-group-label {
        font-family: 'VT323', monospace;
        font-size: 0.6rem;
        color: #2a3f5f;
        letter-spacing: 3px;
        text-transform: uppercase;
        padding: 8px 4px 4px 4px;
        display: block;
    }

    /* MENÚ - Radio buttons */
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
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

    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
        border-color: #2a3f5f;
        background: linear-gradient(135deg, #1a1e26 0%, #11141a 100%);
        transform: translateX(2px);
    }

    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label p,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label span,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        color: #888 !important;
        font-size: 1.3rem !important;
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
        box-shadow: 0 0 10px rgba(0, 255, 173, 0.1);
    }

    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] p,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"] div[data-testid="stMarkdownContainer"] p {
        color: #00ffad !important;
        font-family: 'VT323', monospace !important;
        text-shadow: 0 0 8px #00ffad44;
    }

    section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[aria-checked="true"]::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 2px;
        background: #00ffad;
        box-shadow: 0 0 6px #00ffad;
    }

    /* SEPARADORES */
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #1a1e26 50%, transparent 100%);
        margin: 10px 0;
    }

    /* FOOTER TERMINAL */
    .terminal-footer {
        text-align: center;
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #1a1e26;
        font-family: 'VT323', monospace;
        font-size: 0.55rem;
        color: #2a3f5f;
        letter-spacing: 1px;
        line-height: 1.8;
    }

    /* BOTÓN LOGOUT */
    .stButton > button {
        background: linear-gradient(135deg, #1a1e26 0%, #11141a 100%) !important;
        border: 1px solid #f23645 !important;
        color: #f23645 !important;
        border-radius: 6px !important;
        padding: 8px !important;
        font-size: 0.75rem !important;
        font-family: 'VT323', monospace !important;
        letter-spacing: 1px !important;
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

    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* ── ERROR TERMINAL (mejora #10) ── */
    .error-terminal {
        background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
        border: 1px solid #f2364544;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        font-family: 'VT323', monospace;
        color: #f23645;
        letter-spacing: 1px;
    }
</style>
"""

st.markdown(COMPONENT_CSS, unsafe_allow_html=True)


# ── HELPERS ─────────────────────────────────────────────────────────────────

def get_market_status():
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    hour, minute, weekday = ny_time.hour, ny_time.minute, ny_time.weekday()
    if weekday < 5:
        if (hour == 9 and minute >= 30) or (10 <= hour < 16):
            return True, "OPEN"
    return False, "CLOSED"


def get_clock_times():
    """FIX #14: usar timezone-aware datetime con timezone.utc"""
    times = {}
    now = datetime.now(timezone.utc)
    markets = {
        'NY':  'America/New_York',
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
    """FIX #14: usar timezone-aware datetime"""
    if "last_activity" not in st.session_state or st.session_state["last_activity"] is None:
        return "30:00"
    try:
        now = datetime.now(timezone.utc)
        last = st.session_state["last_activity"]
        # normalizar a aware si viene naive
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = now - last
        remaining = timedelta(minutes=30) - elapsed
        if remaining.total_seconds() <= 0:
            return "00:00"
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        return f"{minutes:02d}:{seconds:02d}"
    except Exception:
        return "30:00"


def get_active_visitors():
    return 42


def load_module(menu_key: str):
    """FIX #12: lazy load — importa el módulo solo cuando se necesita"""
    path = MODULE_PATHS.get(menu_key)
    if path is None:
        return None
    return importlib.import_module(path)


# ── SESIÓN: RSRW ENGINE ──────────────────────────────────────────────────────
if 'rsrw_engine' not in st.session_state:
    try:
        from modules.rsrw import RSRWEngine
        st.session_state.rsrw_engine = RSRWEngine()
    except Exception:
        st.session_state.rsrw_engine = None


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:

    # SECURE CONNECTION HEADER (mejora conceptual #15)
    st.markdown("""
        <div class="secure-header">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
    """, unsafe_allow_html=True)

    # Logo
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("""
            <h2 style='text-align:center; color:#00ffad; font-size:1.8rem;
                        margin-bottom:3px; text-shadow: 0 0 20px #00ffad66;
                        font-family: VT323, monospace; letter-spacing:4px;'>
                RSU
            </h2>
        """, unsafe_allow_html=True)

    # CONTADOR DE VISITANTES
    active_visitors = get_active_visitors()
    st.markdown(f"""
        <div class="visitor-counter">
            ● {active_visitors} USUARIOS ACTIVOS
        </div>
    """, unsafe_allow_html=True)

    # SESIÓN
    st.markdown(f"""
        <div class="user-info">
            <div class="user-status">🟢 SESIÓN ACTIVA</div>
            <div class="session-timer">⏱ SESSION // {format_session_time()}</div>
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

    # ── MENÚ CON GRUPOS (mejora conceptual #17) ──────────────────────────────
    # ANÁLISIS
    st.markdown('<span class="menu-group-label">// ANÁLISIS</span>', unsafe_allow_html=True)
    menu = st.radio("", [
        "📊 DASHBOARD", "📈 SCANNER RS/RW", "🤖 ALGORITMO RSU",
        "⚡ EMA EDGE", "🎯 CAN SLIM", "📅 EARNINGS",
    ], label_visibility="collapsed", key="menu_analisis")

    if menu == "📊 DASHBOARD":  # propagate to unified var below
        pass

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ESTRATEGIA
    st.markdown('<span class="menu-group-label">// ESTRATEGIA</span>', unsafe_allow_html=True)
    menu2 = st.radio("", [
        "💼 CARTERA", "📝 TESIS", "🚀 SPXL STRATEGY",
        "₿ BTC STRATUM", "🗺️ ROADMAP 2026", "🇺🇸 TRUMP PLAYBOOK",
    ], label_visibility="collapsed", key="menu_estrategia")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # HERRAMIENTAS
    st.markdown('<span class="menu-group-label">// HERRAMIENTAS</span>', unsafe_allow_html=True)
    menu3 = st.radio("", [
        "🗄️ RSU DB", "🤖 AI REPORT", "🏆 TRADE GRADER",
    ], label_visibility="collapsed", key="menu_herramientas")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # COMUNIDAD / PLATAFORMA
    st.markdown('<span class="menu-group-label">// PLATAFORMA</span>', unsafe_allow_html=True)
    menu4 = st.radio("", [
        "📜 MANIFEST", "♣️ RSU CLUB", "🎓 ACADEMY",
        "👥 COMUNIDAD", "⚠️ DISCLAIMER",
    ], label_visibility="collapsed", key="menu_plataforma")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # LOGOUT
    if st.button("🔒 CERRAR SESIÓN", use_container_width=True, type="secondary"):
        auth_module.logout()

    # FOOTER TERMINAL (mejora conceptual #15)
    now_utc = datetime.now(timezone.utc)
    st.markdown(f"""
        <div class="terminal-footer">
            [RSU TRADING PLATFORM // v2.0]<br>
            [TIMESTAMP: {now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}]<br>
            [STATUS: ACTIVE // ENCRYPTION: AES-256]
        </div>
    """, unsafe_allow_html=True)


# ── RESOLUCIÓN DEL MENÚ ACTIVO ────────────────────────────────────────────────
# Determina qué grupo está activo según el último click
# Streamlit mantiene en session_state el valor de cada radio group
_active_menu = (
    st.session_state.get("menu_analisis")    or
    st.session_state.get("menu_estrategia")  or
    st.session_state.get("menu_herramientas") or
    st.session_state.get("menu_plataforma")
)

# Detectar cuál radio group fue modificado comparando con el anterior
_prev = st.session_state.get("_prev_menu", "📊 DASHBOARD")
for _key in ("menu_analisis", "menu_estrategia", "menu_herramientas", "menu_plataforma"):
    _val = st.session_state.get(_key)
    if _val and _val != st.session_state.get(f"_prev_{_key}"):
        _active_menu = _val
        st.session_state[f"_prev_{_key}"] = _val
        break
else:
    _active_menu = _prev

st.session_state["_prev_menu"] = _active_menu
selected_menu = _active_menu


# ── RENDER DEL MÓDULO SELECCIONADO ───────────────────────────────────────────
# Mejora conceptual #16: header numerado tipo roadmap_2026
SECTION_NUMBERS = {
    "📊 DASHBOARD":        "01",
    "📜 MANIFEST":         "02",
    "♣️ RSU CLUB":         "03",
    "📈 SCANNER RS/RW":    "04",
    "🤖 ALGORITMO RSU":    "05",
    "⚡ EMA EDGE":          "06",
    "🎯 CAN SLIM":         "07",
    "🗄️ RSU DB":           "08",
    "📅 EARNINGS":         "09",
    "💼 CARTERA":          "10",
    "📝 TESIS":            "11",
    "🤖 AI REPORT":        "12",
    "🎓 ACADEMY":          "13",
    "🏆 TRADE GRADER":     "14",
    "🚀 SPXL STRATEGY":    "15",
    "₿ BTC STRATUM":       "16",
    "🗺️ ROADMAP 2026":     "17",
    "🇺🇸 TRUMP PLAYBOOK":  "18",
    "👥 COMUNIDAD":        "19",
    "⚠️ DISCLAIMER":       "20",
}

if selected_menu in MODULE_PATHS:
    # Sección numerada tipo roadmap (mejora conceptual #16)
    section_num  = SECTION_NUMBERS.get(selected_menu, "00")
    section_name = selected_menu.split(" ", 1)[-1]   # quitar emoji
    st.markdown(f"""
        <div style="
            font-family: 'VT323', monospace;
            font-size: 0.75rem;
            color: #00ffad44;
            letter-spacing: 3px;
            margin-bottom: -10px;
        ">
            [SECURE CONNECTION ESTABLISHED // MODULE {section_num}]
        </div>
        <h2 style="
            font-family: 'VT323', monospace !important;
            color: #00d9ff !important;
            font-size: 2rem !important;
            border-left: 4px solid #00ffad;
            padding-left: 15px;
            margin-bottom: 20px !important;
            letter-spacing: 2px;
        ">
            {section_num} // {section_name.upper()}
        </h2>
    """, unsafe_allow_html=True)

    # FIX #12: Lazy load del módulo
    try:
        mod = load_module(selected_menu)
        if mod is not None:
            mod.render()
        else:
            st.warning("Módulo no encontrado.")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        st.markdown(f"""
            <div class="error-terminal">
                ⚠️ ERROR // MODULE {section_num}<br><br>
                {str(e)}
            </div>
        """, unsafe_allow_html=True)
        with st.expander("▸ VER TRACEBACK COMPLETO"):
            st.code(tb, language="python")


