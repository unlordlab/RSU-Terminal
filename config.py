# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go

# Configuració de la pàgina (NOMÉS UNA VEGADA AQUÍ)
if 'page_config_set' not in st.session_state:
    st.set_page_config(
        page_title="RSU Master Terminal",
        layout="wide",
        page_icon="📊"
    )
    st.session_state.page_config_set = True

def set_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Estils de les targetes de valoració */
        .overview-box { background-color: #151921; border: 1px solid #2d3439; border-radius: 8px; padding: 20px; margin-top: 10px; }
        .valuation-card {
            background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 6px;
            padding: 15px; margin-bottom: 15px; height: 130px;
        }
        .val-label { color: #888; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .val-value { color: white; font-size: 22px; font-weight: bold; margin: 5px 0; }
        .val-sub-label { color: #555; font-size: 10px; margin-top: 2px; }
        .val-tag { 
            background-color: #242933; color: #a0a0a0; font-size: 10px; 
            padding: 2px 8px; border-radius: 4px; float: right; border: 1px solid #3d444b;
        }
        .prompt-container {
            background-color: #1a1e26; border-left: 5px solid #2962ff;
            padding: 20px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap;
        }
        </style>
        """, unsafe_allow_html=True)

# --- IA CONFIG ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    try:
        if not API_KEY: return None, None, "API Key no trobada"
        genai.configure(api_key=API_KEY)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(model_name=sel), sel, None
    except Exception as e:
        return None, None, str(e)

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        url_raw = "https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt"
        r = requests.get(url_raw)
        return r.text if r.status_code == 200 else ""
    except: return ""

# --- MARKET DATA HELPERS ---
@st.cache_data(ttl=300)
def get_market_index(ticker_symbol):
    try:
        import yfinance as yf
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="2d")
        if not hist.empty and len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            previous = hist['Close'].iloc[-2]
            change_pct = ((current - previous) / previous) * 100
            return current, change_pct
        return 0.0, 0.0
    except:
        return 0.0, 0.0

def get_cnn_fear_greed():
    return 55 # Simulat per estabilitat
