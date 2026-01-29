# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="RSU Master Terminal",
    layout="wide",
    page_icon="📊"
)

# Estilos globales
def set_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        .metric-card {
            background-color: #151921; padding: 20px; border-radius: 10px;
            border: 1px solid #2d3439; text-align: center;
        }
        .prompt-container {
            background-color: #1a1e26; border-left: 5px solid #2962ff;
            padding: 20px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

@st.cache_resource
def get_ia_model():
    if not API_KEY:
        return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        modelos = [m.name for m in genai.list_models()
                   if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(model_name=sel, safety_settings=safety_settings), sel, None
    except Exception as e:
        return None, None, str(e)

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        url_raw = "https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/prompt_report.txt"
        r = requests.get(url_raw)
        return r.text if r.status_code == 200 else ""
    except:
        return ""

@st.cache_data(ttl=1800)  # Cache 30min
def get_cnn_fear_greed():
    try:
        # API directa CNN (más estable)
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2026-01-01"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            current_value = data['fear_and_greed_historical']['data'][-1]['y']
            return round(float(current_value), 1)
        
        # Fallback scraping mejorado
        url_scrape = "https://edition.cnn.com/markets/fear-and-greed"
        soup = BeautifulSoup(requests.get(url_scrape, headers=headers).content, 'html.parser')
        
        selectors = [
            "span.market-fng-gauge__dial-number-value",
            ".js-fg-current-value",
            "[data-fng-value]",
            ".fear-greed__current-value",
            ".fng-gauge__dial-number-value"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return int(element.get_text().strip())
        
        return 50
    except Exception:
        return 50

@st.cache_data(ttl=3600)
def get_market_index(ticker_symbol):
    try:
        import yfinance as yf
        data = yf.Ticker(ticker_symbol).fast_info
        p = data['last_price']
        c = ((p - data['previous_close']) / data['previous_close']) * 100
        return p, c
    except:
        return 0.0, 0.0
