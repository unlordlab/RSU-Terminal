import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="RSU Master Terminal", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    .stApp { background-color: #0c0e12; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #151921; border-right: 1px solid #2962ff; }
    .metric-card { background-color: #151921; padding: 20px; border-radius: 10px; border: 1px solid #2d3439; text-align: center; }
    .prompt-container { background-color: #1a1e26; border-left: 5px solid #2962ff; padding: 20px; border-radius: 5px; margin-top: 10px; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURACIÓN IA ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None, "Falta API KEY"
    try:
        genai.configure(api_key=API_KEY)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(sel), sel, None
    except Exception as e: return None, None, str(e)

@st.cache_data(ttl=300)
def obtener_prompt_github():
    try:
        # ⚠️ REEMPLAZA ESTO CON TU URL RAW REAL
        url_raw = "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/prompt_report.txt"
        res = requests.get(url_raw)
        return res.text if res.status_code == 200 else ""
    except: return ""

model_ia, modelo_nombre, error_ia = conectar_ia()

# --- ACCESO ---
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

# --- SIDEBAR ---
with st.sidebar:
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
    if st.button("Refrescar GitHub/Caché"): st.cache_data.clear()

# --- LÓGICA DE MENÚ ---
if menu == "📊 DASHBOARD":
    st.title("Market Overview")
    # (Aquí iría tu lógica de índices que ya funciona)

elif menu == "🤖 IA REPORT":
    ticker_input = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR REPORTE RSU"):
        if error_ia: st.error(error_ia)
        else:
            with st.spinner(f"Analizando {ticker_input}..."):
                # 1. Traemos las instrucciones del .txt
                instrucciones = obtener_prompt_github()
                
                # 2. Verificación de seguridad: si no hay {t}, lo forzamos al inicio
                if "{t}" in instrucciones:
                    prompt_final = instrucciones.replace("{t}", ticker_input)
                else:
                    prompt_final = f"Analitza el ticker {ticker_input}. Instruccions adicionals: {instrucciones}"
                
                try:
                    # 3. Llamada real y visualización
                    response = model_ia.generate_content(prompt_final)
                    st.markdown("### 📝 REPORTE GENERADO")
                    st.markdown(f'<div class="prompt-container">{response.text}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error de IA: {e}")

# (Resto de secciones: Cartera, Tesis, etc., respetando v1)
elif menu == "⚖️ TRADE GRADER":
    st.write("Scorecard activo")
