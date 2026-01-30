# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import yfinance as yf

# Configuració inicial
if 'page_config_set' not in st.session_state:
    st.set_page_config(page_title="RSU Terminal", layout="wide", page_icon="📊")
    st.session_state.page_config_set = True

def set_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Contenidors de Dashboard */
        .group-container {
            background-color: #11141a; border: 1px solid #2d3439;
            border-radius: 12px; padding: 20px; height: 100%;
        }
        .group-title { color: #e0e0e0; font-size: 14px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; }

        /* Targetes d'Índexs */
        .index-card {
            background-color: #1a1e26; border: 1px solid #2d3439; border-radius: 8px;
            padding: 12px 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;
        }
        .index-ticker { color: #e0e0e0; font-weight: bold; font-size: 14px; margin: 0; }
        .index-price { font-weight: bold; font-size: 16px; color: white; margin: 0; }
        .index-delta { font-size: 11px; border-radius: 4px; padding: 1px 6px; font-weight: bold; }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }

        /* Informe IA */
        .prompt-container { background-color: #1a1e26; border-left: 5px solid #2962ff; padding: 20px; border-radius: 5px; white-space: pre-wrap; }
        </style>
        """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    try:
        r = requests.get("https://edition.cnn.com/markets/fear-and-greed")
        soup = BeautifulSoup(r.text, 'html.parser')
        element = soup.find("span", class_="market-fng-gauge__dial-number-value")
        return int(element.text.strip()) if element else 50
    except: return 50

@st.cache_data(ttl=300)
def get_market_index(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.fast_info
        current = info.get('last_price')
        previous = info.get('previous_close')
        if current and previous:
            change = ((current - previous) / previous) * 100
            return current, change
        return 0.0, 0.0
    except: return 0.0, 0.0

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
