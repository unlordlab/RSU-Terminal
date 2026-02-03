# config.py
import os
import time
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# --- CREDENCIALES DE ALPACA ---
ALPACA_API_KEY = "PK5F3ZYQ5V5OMMN2XWUB64GB4Q"
ALPACA_SECRET_KEY = "5BsiRC9kqEoi3wWahzKJrLdgGWPvP5vy3gSySSBbitWC"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets/v2"
ALPACA_WS_URL = "wss://stream.data.alpaca.markets/v2/iex"

# Configuración de página única
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📊")
    st.session_state.page_config_set = True

def set_style():
    st.markdown("""
        <style>
        .semaforo-luz {
            border-radius: 50%;
            background-color: #222; /* Color apagado por defecto */
            border: 4px solid #333;
            box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
            transition: all 0.3s ease;
        }
        .luz-roja.luz-on { 
            background-color: #ff4b4b; 
            box-shadow: 0 0 40px #ff4b4b, inset 0 0 20px rgba(0,0,0,0.2); 
        }
        .luz-ambar.luz-on { 
            background-color: #ffaa00; 
            box-shadow: 0 0 40px #ffaa00, inset 0 0 20px rgba(0,0,0,0.2); 
        }
        .luz-verde.luz-on { 
            background-color: #00ffad; 
            box-shadow: 0 0 40px #00ffad, inset 0 0 20px rgba(0,0,0,0.2); 
        }
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Centrado de títulos en Sidebar */
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] .stSubheader {
            text-align: center !important;
            width: 100%;
        }

        /* Contenedores del Dashboard */
        .group-container {
            background-color: #11141a; 
            border: 1px solid #2d3439;
            border-radius: 12px; 
            padding: 0px; 
            height: 100%;
            overflow: hidden;
            margin-bottom: 20px;
        }
        
        .group-header {
            background-color: #1a1e26;
            padding: 12px 20px;
            border-bottom: 1px solid #2d3439;
            position: relative;
        }
        
        .group-title { 
            color: #888; 
            font-size: 12px; 
            font-weight: bold; 
            text-transform: uppercase; 
            letter-spacing: 1px;
            margin: 0 !important;
        }

        .group-content { padding: 20px; }

        /* Tooltip mejorado */
        .tooltip-container {
            position: absolute;
            top: 50%;
            right: 12px;
            transform: translateY(-50%);
            cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 140%;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
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
                live = t.fast_info.last_price
                if live: current = live
            except: pass
            change = ((current - prev) / prev) * 100
            return current, change
        return 0.0, 0.0
    except: return 0.0, 0.0

@st.cache_data(ttl=300)  # 5 minutos
def get_cnn_fear_greed():
    """Intenta obtener el Fear & Greed real con varios selectores"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        r = requests.get("https://edition.cnn.com/markets/fear-and-greed", headers=headers, timeout=12)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        selectors = [
            ".fng-header__indicator-value",
            ".market-fng-gauge__dial-number-value",
            '[data-testid="fng-gauge-value"]',
            "div[class*='fng-gauge'] span",
            ".fng-gauge-value",
            ".fear-and-greed-value",
        ]
        
        for sel in selectors:
            val = soup.select_one(sel)
            if val and val.text.strip().isdigit():
                return int(val.text.strip())
        
        # Intento final: buscar número cerca de "Fear & Greed"
        for elem in soup.find_all(string=lambda t: t and "Fear & Greed" in t):
            parent = elem.find_parent()
            if parent:
                num = parent.find(string=lambda s: s and s.strip().isdigit())
                if num:
                    return int(num.strip())
        
        return None
    except Exception:
        return None

def actualizar_contador_usuarios():
    if not os.path.exists("sessions"):
        os.makedirs("sessions")
    try:
        session_id = st.runtime.scriptrunner.add_script_run_ctx().streamlit_script_run_ctx.session_id
        session_file = f"sessions/{session_id}"
        with open(session_file, "w") as f:
            f.write(str(time.time()))
    except: pass
    
    count = 0
    ahora = time.time()
    for f in os.listdir("sessions"):
        f_path = os.path.join("sessions", f)
        if ahora - os.path.getmtime(f_path) > 30:
            try: os.remove(f_path)
            except: pass
        else:
            count += 1
    return count
    
# --- CONFIGURACIÓN DE IA (GEMINI) ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    if not API_KEY: 
        return None, None, "API Key missing"
    
    genai.configure(api_key=API_KEY)
    
    try:
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
            model = genai.GenerativeModel('gemini-pro')
            return model, "gemini-pro", None
        except:
            return None, None, f"Error: {str(e)}"

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        r = requests.get("https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt")
        return r.text if r.status_code == 200 else ""
    except: return ""



