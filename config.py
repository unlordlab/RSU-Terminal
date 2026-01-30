# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# Configuración de página única
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📊")
    st.session_state.page_config_set = True

def set_style():
    """Define la estética oscura y las clases para las cajas del Dashboard."""
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Caja contenedora para Índices */
        .market-box {
            background-color: #11141a;
            border: 1px solid #2d3439;
            border-radius: 12px;
            padding: 20px;
            height: 450px;
        }
        
        /* Filas de cada índice */
        .index-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            border-bottom: 1px solid #1a1e26;
        }
        
        .pos { color: #00ffad; font-weight: bold; }
        .neg { color: #f23645; font-weight: bold; }
        
        /* Estilo para el Fear & Greed en la barra lateral */
        .fng-container { text-align: center; padding: 10px; }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_market_index(ticker_symbol):
    """Obtiene precio y cambio porcentual de yfinance."""
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
    """Extrae el índice Fear & Greed de CNN Business."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get("https://edition.cnn.com/markets/fear-and-greed", headers=headers, timeout=5)
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
    except:
        return ""
