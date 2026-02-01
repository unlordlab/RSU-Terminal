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
        .group-container { background-color: #11141a; border: 1px solid #2d3439; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }
        .group-header { background-color: #1a1e26; padding: 12px 20px; border-bottom: 1px solid #2d3439; }
        .group-title { color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin: 0 !important; }
        .group-content { padding: 20px; }
        .index-card { background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 8px; padding: 12px 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }
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
            change = ((current - prev) / prev) * 100
            return current, change
        return 0.0, 0.0
    except: return 0.0, 0.0

@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    try:
        r = requests.get("https://edition.cnn.com/markets/fear-and-greed")
        soup = BeautifulSoup(r.text, 'html.parser')
        val = soup.find("span", class_="market-fng-gauge__dial-number-value")
        return int(val.text.strip()) if val else 50
    except: return 50

def actualizar_contador_usuarios():
    if not os.path.exists("sessions"): os.makedirs("sessions")
    session_id = st.runtime.scriptrunner.add_script_run_ctx().streamlit_script_run_ctx.session_id
    session_file = f"sessions/{session_id}"
    with open(session_file, "w") as f: f.write(str(time.time()))
    count = 0
    ahora = time.time()
    for f in os.listdir("sessions"):
        f_path = os.path.join("sessions", f)
        if ahora - os.path.getmtime(f_path) > 30: os.remove(f_path)
        else: count += 1
    return count

# --- MEJORA SISTEMA DE IA ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    """Busca el modelo disponible para evitar el error 404."""
    if not API_KEY: return None, None, "API Key missing"
    genai.configure(api_key=API_KEY)
    
    # Lista de modelos en orden de preferencia
    modelos_disponibles = [
        'gemini-1.5-flash',       # Versión estándar
        'gemini-1.5-flash-latest',# Versión más nueva
        'gemini-pro'              # Versión estable anterior
    ]
    
    for nombre in modelos_disponibles:
        try:
            model = genai.GenerativeModel(nombre)
            # Prueba rápida de inicialización
            return model, nombre, None
        except Exception:
            continue
            
    return None, None, "No se encontró ningún modelo Gemini compatible."

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        r = requests.get("https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt")
        return r.text if r.status_code == 200 else ""
    except: return ""
