# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# Configuració de la pàgina
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📊")
    st.session_state.page_config_set = True

def set_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* TARGETES D'ÍNDEXS (Dashboard superior) */
        .index-card {
            background-color: #151921; border: 1px solid #2d3439; border-radius: 10px;
            padding: 15px; margin-bottom: 15px; display: flex;
            justify-content: space-between; align-items: center;
        }
        .index-ticker { color: #e0e0e0; font-weight: bold; font-size: 16px; margin: 0; }
        .index-fullname { color: #888; font-size: 11px; margin: 0; }
        .index-price { font-weight: bold; font-size: 18px; color: white; margin: 0; }
        .index-delta { font-size: 12px; border-radius: 4px; padding: 2px 6px; font-weight: bold; margin-top: 4px; }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }

        /* OVERVIEW & IA BOXES */
        .overview-box { background-color: #151921; border: 1px solid #2d3439; border-radius: 8px; padding: 20px; }
        .valuation-card {
            background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 6px;
            padding: 15px; margin-bottom: 15px; height: 130px;
        }
        .val-label { color: #888; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .val-value { color: white; font-size: 22px; font-weight: bold; margin: 5px 0; }
        .val-tag { background-color: #242933; color: #a0a0a0; font-size: 10px; padding: 2px 8px; border-radius: 4px; float: right; border: 1px solid #3d444b; }
        .prompt-container { background-color: #1a1e26; border-left: 5px solid #2962ff; padding: 20px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap; }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_market_index(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="2d")
        if not hist.empty and len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            previous = hist['Close'].iloc[-2]
            change_pct = ((current - previous) / previous) * 100
            return current, change_pct
        return 0.0, 0.0
    except: return 0.0, 0.0

def render_index_cards():
    """Funció recuperada per mostrar els 4 índexs principals"""
    indices = [
        {"name": "S&P 500", "ticker": "^GSPC", "fullname": "US 500 Index"},
        {"name": "NASDAQ 100", "ticker": "^IXIC", "fullname": "Nasdaq Composite"},
        {"name": "DOW JONES", "ticker": "^DJI", "fullname": "Industrial Average"},
        {"name": "RUSSELL 2000", "ticker": "^RUT", "fullname": "Small Cap Index"}
    ]
    
    cols = st.columns(4)
    for i, idx in enumerate(indices):
        price, delta = get_market_index(idx['ticker'])
        delta_class = "pos" if delta >= 0 else "neg"
        delta_sign = "+" if delta >= 0 else ""
        
        with cols[i]:
            st.markdown(f"""
                <div class="index-card">
                    <div class="index-name-container">
                        <p class="index-ticker">{idx['name']}</p>
                        <p class="index-fullname">{idx['fullname']}</p>
                    </div>
                    <div class="index-price-container">
                        <p class="index-price">{price:,.2f}</p>
                        <div class="index-delta {delta_class}">{delta_sign}{delta:.2f}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- ALTRES FUNCIONS (IA, CNN...) ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    if not API_KEY: return None, None, "Falta API KEY"
    genai.configure(api_key=API_KEY)
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
    return genai.GenerativeModel(model_name=sel), sel, None

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        r = requests.get("https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt")
        return r.text if r.status_code == 200 else ""
    except: return ""

@st.cache_data(ttl=1800)
def get_cnn_fear_greed():
    # El teu codi existent de scraping de CNN aquí...
    return 55
