# config.py
import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

st.set_page_config(
    page_title="RSU Terminal",
    layout="wide",
    page_icon="📊"
)

def set_style():
    st.markdown("""
        <style>
        .stApp { background-color: #0c0e12; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
        
        /* Contenidor principal gris fosc per agrupar targetes */
        .group-container {
            background-color: #11141a;
            border: 1px solid #2d3439;
            border-radius: 12px;
            padding: 20px;
            height: 100%;
        }
        
        .group-title {
            color: #e0e0e0;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Targetes d'índexs horitzontals */
        .index-card {
            background-color: #1a1e26;
            border: 1px solid #2d3439;
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .index-name-container { display: flex; flex-direction: column; }
        .index-ticker { color: #e0e0e0; font-weight: bold; font-size: 14px; margin: 0; }
        .index-fullname { color: #888; font-size: 11px; margin: 0; }
        .index-price-container { text-align: right; }
        .index-price { font-weight: bold; font-size: 16px; color: white; margin: 0; }
        .index-delta { font-size: 11px; border-radius: 4px; padding: 1px 6px; font-weight: bold; margin-top: 4px; display: inline-block; }
        .pos { background-color: rgba(0, 255, 173, 0.1); color: #00ffad; }
        .neg { background-color: rgba(242, 54, 69, 0.1); color: #f23645; }
        
        /* Footer de la caixa */
        .container-footer {
            color: #555;
            font-size: 10px;
            margin-top: 10px;
            text-align: center;
            border-top: 1px solid #2d3439;
            padding-top: 8px;
        }
        </style>
        """, unsafe_allow_html=True)

# Manté les teves funcions existents: get_ia_model, obtener_prompt_github, get_cnn_fear_greed, get_market_index
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
