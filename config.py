# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# 1. CONFIGURACIÓN DE PÁGINA (Debe ser la primera instrucción)
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📊")
    st.session_state.page_config_set = True

def set_style():
    """Estilos CSS optimizados para evitar renderizado de texto plano."""
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Estilos para el contenido interno de las tarjetas */
        .index-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #1a1e26;
        }
        
        .pos { color: #00ffad; font-weight: bold; }
        .neg { color: #f23645; font-weight: bold; }
        
        /* Ajuste de títulos dentro de contenedores */
        .card-header-text {
            color: #888; font-size: 11px; font-weight: bold; 
            text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_market_index(ticker_symbol):
    """Obtención de datos financieros con fallback."""
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period="5d")
        if not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change = ((current - prev) / prev) * 100
            return current, change
        return 0.0, 0.0
    except:
        return 0.0, 0.0

@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    """Scraping del Fear & Greed Index con bypass de bloqueo."""
    try:
        url = "https://edition.cnn.com/markets/fear-and-greed"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        val = soup.find("span", class_="market-fng-gauge__dial-number-value")
        return int(val.text.strip()) if val else 50
    except:
        return 50

# --- LÓGICA DE IA ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
@st.cache_resource
def get_ia_model():
    if not API_KEY: return None, None, "API Key missing"
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model, "Gemini 1.5 Flash", None

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        r = requests.get("https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt")
        return r.text if r.status_code == 200 else ""
    except: return ""
