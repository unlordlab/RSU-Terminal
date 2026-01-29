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
    .metric-card { background-color: #151921; padding: 20px; border-radius: 10px; border: 1px solid #2d3439; text-align: center; }
    .prompt-container { background-color: #1a1e26; border-left: 5px solid #2962ff; padding: 20px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN IA (SISTEMA ROBUSTO v1.2) ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(sel), sel, None
    except Exception as e: return None, None, str(e)

@st.cache_data(ttl=60)
def obtener_prompt_github():
    try:
        # ⚠️ REEMPLAZA CON TU URL "RAW" DE GITHUB (DEBE EMPEZAR CON raw.githubusercontent.com)
        url_raw = "https://github.com/unlordlab/RSU-Terminal/blob/df1305016e5028c9db6cc5c0a689ddd661434272/prompt_report.txt"
        response = requests.get(url_raw)
        if response.status_code == 200:
            return response.text
        return ""
    except: return ""

model_ia, modelo_nombre, error_ia = conectar_ia()

# --- 3. ACCESO ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h3 style='text-align:center;'>RSU MASTER TERMINAL</h3>", unsafe_allow_html=True)
        password = st.text_input("ACCESS KEY", type="password")
        if st.button("UNLOCK", use_container_width=True):
            if password == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
    st.stop()

# --- 4. FUNCIONES DE MERCADO ---
def get_market_index(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).fast_info
        p, c = data['last_price'], ((data['last_price'] - data['previous_close']) / data['previous_close']) * 100
        return p, c
    except: return 0.0, 0.0

# --- 5. SIDEBAR ---
with st.sidebar:
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
    if st.button("🔄 Refrescar Instrucciones"):
        st.cache_data.clear()
        st.success("GitHub actualizado")

# --- 6. LÓGICA DE MENÚ ---
if menu == "📊 DASHBOARD":
    st.title("Market Overview")
    idx = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "VIX": "^VIX", "BTC": "BTC-USD"}
    cols = st.columns(4)
    for i, (n, s) in enumerate(idx.items()):
        p, c = get_market_index(s)
        color = "#00ffad" if (c >= 0 and n != "VIX") or (c < 0 and n == "VIX") else "#f23645"
        cols[i].markdown(f"""<div class="metric-card"><small>{n}</small><h3>{p:,.1f}</h3><p style="color:{color}">{c:.2f}%</p></div>""", unsafe_allow_html=True)

elif menu == "🤖 IA REPORT":
    ticker_input = st.text_input("Introduce Ticker", "NVDA").upper()
    if st.button("EJECUTAR ANÁLISIS"):
        if error_ia: st.error(error_ia)
        else:
            with st.spinner(f"Analizando {ticker_input}..."):
                # 1. Obtenemos el texto de GitHub
                template = obtener_prompt_github()
                
                if not template:
                    st.error("No se pudo leer GitHub. Revisa la URL RAW.")
                else:
                    # 2. Reemplazamos [TICKER] por el valor real
                    # Tu archivo usa [TICKER], así que somos específicos
                    instrucciones_limpias = template.replace("[TICKER]", ticker_input)
                    
                    # 3. ENVOLVEMOS EL PROMPT (Esto evita que la IA se limite a leerlo)
                    prompt_final = f"""
                    EJECUTA EL SIGUIENTE ANÁLISIS PROFESIONAL PARA LA ACCIÓN: {ticker_input}.
                    SIGUE ESTAS INSTRUCCIONES ESTRICTAMENTE:
                    
                    {instrucciones_limpias}
                    
                    RESPONDE EN FORMATO MARKDOWN PROFESIONAL.
                    """
                    
                    try:
                        # 4. Llamada a Gemini
                        res = model_ia.generate_content(prompt_final)
                        st.markdown(f"### 📋 Informe RSU: {ticker_input}")
                        st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error: {e}")

elif menu == "💼 CARTERA":
    st.info("Sección Cartera conectada a Sheets.")

elif menu == "📄 TESIS":
    st.info("Sección Tesis conectada a Sheets.")

elif menu == "⚖️ TRADE GRADER":
    st.title("RSU Scorecard")

elif menu == "🎥 ACADEMY":
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

st.caption(f"v1.2 | Engine: {modelo_nombre}")


