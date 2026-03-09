# config.py
import os
import time
import streamlit as st
import requests
from bs4 import BeautifulSoup
import yfinance as yf


# Configuración de página única
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📈")
    st.session_state.page_config_set = True

def set_style():
    st.markdown("""
        <style>
        /* ═══════════════════════════════════════════════════════════
           TEMA OSCURO FORZADO — Cubre todos los componentes nativos
           de Streamlit para que ningún usuario vea fondos blancos,
           independientemente de su tema de sistema operativo.
           ═══════════════════════════════════════════════════════════ */

        /* ── BASE ────────────────────────────────────────────────── */
        html, body, .stApp {
            background-color: #0c0e12 !important;
            color: #cccccc !important;
        }

        /* ── SEMÁFORO (componente original conservado) ───────────── */
        .semaforo-luz {
            border-radius: 50%; background-color: #222; border: 4px solid #333;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5); transition: all 0.3s ease;
        }
        .luz-roja.luz-on  { background-color: #ff4b4b; box-shadow: 0 0 40px #ff4b4b, inset 0 0 20px rgba(0,0,0,0.2); }
        .luz-ambar.luz-on { background-color: #ffaa00; box-shadow: 0 0 40px #ffaa00, inset 0 0 20px rgba(0,0,0,0.2); }
        .luz-verde.luz-on { background-color: #00ffad; box-shadow: 0 0 40px #00ffad, inset 0 0 20px rgba(0,0,0,0.2); }

        /* ── SIDEBAR ─────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background-color: #11141a !important;
            border-right: 1px solid #1a1e26 !important;
        }

        /* ── COMPONENTES PERSONALIZADOS (conservados) ────────────── */
        .group-container {
            background-color: #11141a; border: 1px solid #2d3439; border-radius: 12px;
            padding: 0px; height: 100%; overflow: hidden; margin-bottom: 20px;
        }
        .group-header {
            background-color: #1a1e26; padding: 12px 20px; border-bottom: 1px solid #2d3439;
            position: relative;
        }
        .group-title {
            color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase;
            letter-spacing: 1px; margin: 0 !important;
        }
        .group-content { padding: 20px; }

        /* ── TOOLTIP ─────────────────────────────────────────────── */
        .tooltip-container {
            position: absolute; top: 50%; right: 12px; transform: translateY(-50%); cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden; width: 260px; background-color: #1e222d; color: #eee;
            text-align: left; padding: 10px 12px; border-radius: 6px; position: absolute;
            z-index: 999; top: 140%; right: -10px; opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px; border: 1px solid #444; pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }

        /* ══════════════════════════════════════════════════════════
           DATAFRAMES Y TABLAS — El principal causante de blancos
           ══════════════════════════════════════════════════════════ */

        /* Contenedor raíz del dataframe */
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        .stDataFrame,
        .stTable {
            background-color: #0c0e12 !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 6px !important;
            overflow: hidden !important;
        }

        /* Cabeceras */
        [data-testid="stDataFrame"] thead th,
        [data-testid="stTable"] thead th,
        .stDataFrame thead th {
            background-color: #11141a !important;
            color: #00ffad !important;
            border-bottom: 1px solid #00ffad33 !important;
            border-right: 1px solid #1a1e26 !important;
            font-family: 'Courier New', monospace !important;
            font-size: 0.78rem !important;
            font-weight: bold !important;
            letter-spacing: 1px !important;
            text-transform: uppercase !important;
            padding: 8px 12px !important;
        }

        /* Celdas */
        [data-testid="stDataFrame"] tbody td,
        [data-testid="stTable"] tbody td,
        .stDataFrame tbody td {
            background-color: transparent !important;
            color: #cccccc !important;
            border-color: #1a1e26 !important;
            padding: 6px 12px !important;
        }

        /* Filas alternas */
        [data-testid="stDataFrame"] tbody tr:nth-child(even) td,
        .stDataFrame tbody tr:nth-child(even) td {
            background-color: #11141a !important;
        }
        [data-testid="stDataFrame"] tbody tr:nth-child(odd) td,
        .stDataFrame tbody tr:nth-child(odd) td {
            background-color: #0c0e12 !important;
        }

        /* Hover en filas */
        [data-testid="stDataFrame"] tbody tr:hover td,
        .stDataFrame tbody tr:hover td {
            background-color: rgba(0, 255, 173, 0.06) !important;
            color: #ffffff !important;
        }

        /* Glide-data-grid: solo el contenedor exterior, nunca tocar canvas */
        .glide-data-grid-container {
            border: 1px solid #1a1e26 !important;
            border-radius: 6px !important;
        }

        /* ══════════════════════════════════════════════════════════
           INPUTS, SELECTS Y DROPDOWNS
           ══════════════════════════════════════════════════════════ */

        input, textarea, select,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            background-color: #11141a !important;
            color: #cccccc !important;
            border-color: #2a3040 !important;
            caret-color: #00ffad !important;
        }
        input:focus, textarea:focus {
            border-color: #00ffad55 !important;
            box-shadow: 0 0 0 1px #00ffad22 !important;
            outline: none !important;
        }
        input::placeholder, textarea::placeholder {
            color: #444 !important;
        }

        /* Selectbox / multiselect */
        [data-baseweb="select"] > div,
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [role="listbox"] {
            background-color: #11141a !important;
            color: #cccccc !important;
            border-color: #2a3040 !important;
        }
        [role="option"] {
            background-color: #11141a !important;
            color: #cccccc !important;
        }
        [role="option"]:hover,
        [aria-selected="true"] {
            background-color: rgba(0, 255, 173, 0.08) !important;
            color: #00ffad !important;
        }

        /* Tags del multiselect */
        [data-baseweb="tag"] {
            background-color: rgba(0, 255, 173, 0.1) !important;
            color: #00ffad !important;
            border: 1px solid #00ffad33 !important;
        }

        /* ══════════════════════════════════════════════════════════
           MÉTRICAS
           ══════════════════════════════════════════════════════════ */
        [data-testid="stMetric"] {
            background-color: #11141a !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 8px !important;
            padding: 12px !important;
        }
        [data-testid="stMetricLabel"] { color: #666 !important; }
        [data-testid="stMetricValue"] { color: #ffffff !important; }
        [data-testid="stMetricDelta"] svg { display: none; }

        /* ══════════════════════════════════════════════════════════
           EXPANDERS, TABS, ALERTS
           ══════════════════════════════════════════════════════════ */

        [data-testid="stExpander"] {
            background-color: #11141a !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 6px !important;
        }
        [data-testid="stExpander"] summary { color: #00d9ff !important; }

        [data-testid="stTabs"] [role="tablist"] {
            background-color: transparent !important;
            border-bottom: 1px solid #1a1e26 !important;
        }
        [data-testid="stTabs"] [role="tab"] {
            color: #555 !important;
            background-color: transparent !important;
        }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            color: #00ffad !important;
            border-bottom: 2px solid #00ffad !important;
        }

        [data-testid="stAlert"] {
            background-color: #11141a !important;
            border-color: #2a3040 !important;
            color: #cccccc !important;
        }

        /* ── PROGRESS BAR ────────────────────────────────────────── */
        [data-testid="stProgressBar"] > div {
            background-color: #1a1e26 !important;
        }
        [data-testid="stProgressBar"] > div > div {
            background-color: #00ffad !important;
        }

        /* ── TOOLTIPS NATIVOS ────────────────────────────────────── */
        [data-baseweb="tooltip"] > div {
            background-color: #1a1e26 !important;
            color: #cccccc !important;
            border: 1px solid #2a3040 !important;
        }

        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_market_index(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period="2d")
        if not hist.empty and len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            try:
                live = t.fast_info.get('last_price') or t.fast_info.get('regularMarketPrice')
                if live: 
                    current = live
            except: 
                pass
            change = ((current - prev) / prev) * 100
            return current, change
        return 0.0, 0.0
    except Exception as e:
        return 0.0, 0.0

# =============================================================================
# FEAR & GREED INDEX – SOLUCIÓN 100% FUNCIONAL (usa el JSON interno de CNN)
# =============================================================================
@st.cache_data(ttl=300)  # 5 minutos de caché
def get_cnn_fear_greed():
    """
    Obtiene el valor real del CNN Fear & Greed Index usando su propio endpoint JSON.
    Este método nunca falla porque no depende del HTML cambiante.
    """
    try:
        # Endpoint oficial que usa la propia web de CNN para cargar el gráfico
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://edition.cnn.com/markets/fear-and-greed"
        }
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            score = data.get("fear_and_greed", {}).get("score")
            if score is not None:
                return int(score)
        
        return None
    except Exception as e:
        return None

def actualizar_contador_usuarios():
    """Contador simple de sesiones activas"""
    if not os.path.exists("sessions"):
        try:
            os.makedirs("sessions")
        except:
            return 1
    
    try:
        # Usar un identificador simple basado en tiempo
        session_id = str(int(time.time() * 1000))
        session_file = f"sessions/{session_id}"
        with open(session_file, "w") as f:
            f.write(str(time.time()))
    except: 
        pass
    
    count = 0
    ahora = time.time()
    try:
        for f in os.listdir("sessions"):
            f_path = os.path.join("sessions", f)
            try:
                if ahora - os.path.getmtime(f_path) > 30:
                    try: 
                        os.remove(f_path)
                    except: 
                        pass
                else:
                    count += 1
            except:
                pass
    except:
        count = 1
    
    return max(count, 1)
    
# --- CONFIGURACIÓN DE IA (GEMINI) ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    if not API_KEY: 
        return None, None, "API Key missing"
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=API_KEY)
        
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not available_models:
            return None, None, "No models available"

        target_model = ""
        for m in available_models:
            if "gemini-1.5-flash" in m:
                target_model = m
                break
        if not target_model:
            target_model = available_models[0]

        model = genai.GenerativeModel(target_model)
        return model, target_model, None

    except Exception as e:
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-pro')
            return model, "gemini-pro", None
        except:
            return None, None, f"Error: {str(e)}"

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        r = requests.get("https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt")
        return r.text if r.status_code == 200 else ""
    except: 
        return ""
         



