import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
import os

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="RSU Master Terminal", layout="wide", page_icon="📊")

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
    """, unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN IA (SISTEMA ANTI-BLOQUEO) ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(model_name=sel, safety_settings=safety_settings), sel, None
    except Exception as e: return None, None, str(e)

@st.cache_data(ttl=3600) # Se actualiza cada hora para no saturar GitHub
def obtener_prompt_github():
    try:
        # ⚠️ REEMPLAZA CON TU URL RAW DE GITHUB
        url_raw = "https://github.com/unlordlab/RSU-Terminal/blob/df1305016e5028c9db6cc5c0a689ddd661434272/prompt_report.txt"
        response = requests.get(url_raw)
        return response.text if response.status_code == 200 else ""
    except: return ""

model_ia, modelo_nombre, error_ia = conectar_ia()

# --- 3. FUNCIONES DE MERCADO ---
@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    try:
        url = "https://edition.cnn.com/markets/fear-and-greed"
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')
        # Buscamos el valor numérico en el gauge de CNN
        val = soup.find("span", class_="market-fng-gauge__dial-number-value").text
        return int(val)
    except: return 50 # Valor neutral si falla el scraping

def get_market_index(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).fast_info
        p = data['last_price']
        c = ((p - data['previous_close']) / data['previous_close']) * 100
        return p, c
    except: return 0.0, 0.0

def calificar_trade(t, v, c, r):
    score = 0
    if t == "A favor": score += 30
    if v == "Inusual / Alto": score += 25
    if c == "Fuerte (Earnings/FDA)": score += 25
    if r >= 3: score += 20
    grados = {90: ("A+", "#00ffad"), 75: ("A", "#a2ff00"), 60: ("B", "#ffea00"), 40: ("C", "#ff9100"), 0: ("D", "#f23645")}
    for s, g in grados.items():
        if score >= s: return g

# --- 4. ACCESO ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center;'>RSU MASTER TERMINAL</h3>", unsafe_allow_html=True)
        password = st.text_input("ACCESS KEY", type="password")
        if st.button("UNLOCK TERMINAL", use_container_width=True):
            if password == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    st.stop
