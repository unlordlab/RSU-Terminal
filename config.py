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
        
        /* Contenedores del Dashboard */
        .group-container {
            background-color: #11141a; border: 1px solid #2d3439;
            border-radius: 12px; padding: 20px; height: 100%;
        }
        
        /* Título DENTRO de la caja */
        .group-title { 
            color: #888; font-size: 12px; font-weight: bold; 
            margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;
        }

        /* Tarjetas de Índices */
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
        ticker = yf.Ticker(ticker_symbol)
        # Usamos history para asegurar que obtenemos datos de cierre previos correctos para el %
        data = ticker.history(period="2d")
        if not data.empty and len(data) >= 2:
            current = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
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

# --- FUNCIONES DE IA ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    try:
        if not API_KEY: return None, None, "API Key no configurada"
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model, "Gemini 1.5 Flash", None
    except Exception as e: return None, None, str(e)

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        r = requests.get("https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt")
        return r.text if r.status_code == 200 else ""
    except: return ""
