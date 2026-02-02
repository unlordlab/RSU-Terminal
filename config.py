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

        .index-card {
            background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 8px;
            padding: 12px 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;
        }
        .index-ticker { color: white; font-weight: bold; font-size: 14px; margin: 0; }
        .index-fullname { color: #555; font-size: 10px; margin: 0; text-transform: uppercase; }
        .index-price { font-weight: bold; font-size: 16px; color: white; margin: 0; }
        .index-delta { font-size: 11px; border-radius: 4px; padding: 2px 6px; font-weight: bold; }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }
        
        .prompt-container { background-color: #1a1e26; border-left: 5px solid #2962ff; padding: 20px; border-radius: 5px; white-space: pre-wrap; }
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

@st.cache_data(ttl=600)
def get_cnn_fear_greed():
    """Obtiene el valor real del Fear & Greed Index de CNN Business."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        r = requests.get("https://edition.cnn.com/markets/fear-and-greed", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Selectores actualizados (CNN cambia clases a menudo)
        val = soup.select_one(".fng-header__indicator-value")
        if not val:
            val = soup.select_one(".market-fng-gauge__dial-number-value")
            
        return int(val.text.strip()) if val else 50
    except Exception:
        return 50 # Retorno seguro en caso de error de conexión o scraping
        
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
