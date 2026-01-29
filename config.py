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

@st.cache_data(ttl=1800)
def get_cnn_fear_greed():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        # Intentar API primero
        url_api = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        response = requests.get(url_api, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'fear_and_greed_historical' in data and data['fear_and_greed_historical']['data']:
                return round(float(data['fear_and_greed_historical']['data'][-1]['y']), 1)
        
        # Fallback scraping
        url_scrape = "https://edition.cnn.com/markets/fear-and-greed"
        soup = BeautifulSoup(requests.get(url_scrape, headers=headers).content, 'html.parser')
        
        selectors = [
            "span[data-testid*='fear-greed']",
            ".fear-greed-gauge__value",
            ".js-fng-score",
            "span.fng-score"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip().isdigit():
                return int(element.get_text().strip())
        
        return 50
    except:
        return 50

@st.cache_data(ttl=300)  # Cache 5min para precios
def get_market_index(ticker_symbol):
    try:
        import yfinance as yf
        ticker = yf.Ticker(ticker_symbol)
        
        # Método más robusto
        info = ticker.fast_info
        if info and info['last_price'] is not None:
            current = info['last_price']
            previous = info.get('previous_close', current)
            change = ((current - previous) / previous) * 100 if previous != 0 else 0
            return current, change
        
        # Fallback: download histórico
        hist = ticker.history(period="2d")
        if not hist.empty:
            current = hist['Close'][-1]
            previous = hist['Close'][-2]
            change = ((current - previous) / previous) * 100
            return current, change
        
        return 0.0, 0.0
    except Exception as e:
        st.error(f"Error {ticker_symbol}: {e}")
        return 0.0, 0.0
