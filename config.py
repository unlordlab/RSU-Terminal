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
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Contenedores con altura sincronizada absoluta */
        .group-container {
            background-color: #11141a; 
            border: 1px solid #2d3439;
            border-radius: 12px; 
            height: 450px; 
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .group-header {
            background-color: #1a1e26;
            padding: 15px 20px;
            border-bottom: 1px solid #2d3439;
            flex-shrink: 0;
        }
        
        .group-title { 
            color: #888; font-size: 11px; font-weight: bold; 
            text-transform: uppercase; margin: 0 !important;
            letter-spacing: 0.5px;
        }

        .group-content { padding: 20px; flex-grow: 1; }
        
        /* Contenido especial para el widget (sin padding para ajuste total) */
        .widget-content { flex-grow: 1; padding: 0px !important; }

        .index-card {
            background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 8px;
            padding: 12px 15px; margin-bottom: 10px; display: flex; 
            justify-content: space-between; align-items: center;
        }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_market_index(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        hist = t.history(period="5d")
        if not hist.empty:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            try:
                live = t.fast_info.last_price
                if live and live > 0: current = live
            except: pass
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

# --- IA LOGIC ---
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
