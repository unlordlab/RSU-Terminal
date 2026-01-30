# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# 1. CONFIGURACIÓN DE PÁGINA ÚNICA
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📊")
    st.session_state.page_config_set = True

def set_style():
    """Estilos CSS simplificados y efectivos"""
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Contenedor de Índices */
        .group-container {
            background-color: #11141a; 
            border: 1px solid #2d3439;
            border-radius: 12px; 
            margin-bottom: 20px;
            overflow: hidden;
        }
        
        .group-header {
            background-color: #1a1e26;
            padding: 12px 20px;
            border-bottom: 1px solid #2d3439;
        }
        
        .group-title { 
            color: #888; font-size: 11px; font-weight: bold; 
            text-transform: uppercase; letter-spacing: 1px; margin: 0 !important;
        }

        .group-content { padding: 15px; }

        /* Tarjetas de Índices */
        .index-card {
            background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 8px;
            padding: 10px 15px; margin-bottom: 8px; display: flex; 
            justify-content: space-between; align-items: center;
        }
        .index-ticker { color: white; font-weight: bold; font-size: 13px; margin: 0; }
        .index-fullname { color: #555; font-size: 9px; margin: 0; }
        .index-price { font-weight: bold; font-size: 15px; color: white; margin: 0; }
        .index-delta { font-size: 10px; border-radius: 4px; padding: 1px 5px; font-weight: bold; }
        
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=60)
def get_market_index(ticker_symbol):
    """Obtiene datos de yfinance con fallback para evitar el valor 0.00"""
    try:
        t = yf.Ticker(ticker_symbol)
        # Pedimos 5 días para asegurar datos incluso en fines de semana o festivos
        hist = t.history(period="5d")
        if not hist.empty and len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            
            # Intentar capturar precio live si está disponible
            try:
                live = t.fast_info.last_price
                if live and live > 0:
                    current = live
            except:
                pass
                
            change = ((current - prev) / prev) * 100
            return current, change
        return 0.0, 0.0
    except:
        return 0.0, 0.0

@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    """Obtiene el Fear & Greed Index usando headers reales para evitar bloqueos"""
    try:
        url = "https://edition.cnn.com/markets/fear-and-greed"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Buscamos el valor en el componente de CNN
        val = soup.find("span", class_="market-fng-gauge__dial-number-value")
        if val:
            return int(val.text.strip())
        return 50 # Valor neutral si falla el scraping
    except:
        return 50

# --- IA Y PROMPTS ---
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
