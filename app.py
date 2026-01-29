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

# --- 2. CONFIGURACIÓN IA (VERSIÓN 1.3 ANTI-BLOQUEO) ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        # Configuración para saltar bloqueos de seguridad por palabras técnicas
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

@st.cache_data(ttl=60)
def obtener_prompt_github():
    try:
        # ⚠️ PON AQUÍ TU URL RAW DE GITHUB
        url_raw = "https://github.com/unlordlab/RSU-Terminal/blob/df1305016e5028c9db6cc5c0a689ddd661434272/prompt_report.txt"
        response = requests.get(url_raw)
        return response.text if response.status_code == 200 else ""
    except: return ""

model_ia, modelo_nombre, error_ia = conectar_ia()

# --- 3. ACCESO ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h3 style='text-align:center;'>RSU MASTER TERMINAL</h3>", unsafe_allow_html=True)
        password = st.text_input("ACCESS KEY", type="password")
        if st.button("UNLOCK"):
            if password == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
    if st.button("🔄 Refrescar Instrucciones"):
        st.cache_data.clear()
        st.success("GitHub actualizado")

# --- 5. LÓGICA DE MENÚ ---
if menu == "📊 DASHBOARD":
    st.title("Market Overview")
    # Lógica de índices aquí...

elif menu == "🤖 IA REPORT":
    ticker_input = st.text_input("Introduce Ticker", "NVDA").upper()
    if st.button("EJECUTAR ANÁLISIS"):
        if error_ia: st.error(error_ia)
        else:
            with st.spinner(f"Analizando {ticker_input} (esto puede tardar 10-15 segundos)..."):
                template = obtener_prompt_github()
                if not template:
                    st.error("No se pudo leer GitHub.")
                else:
                    # Sustitución del marcador que usas en tu txt
                    instrucciones = template.replace("[TICKER]", ticker_input)
                    
                    # Prompt reforzado para evitar bloqueos por 'Safety'
                    prompt_final = f"Actúa como un analista de datos informativos. No des consejos de inversión, solo resume la información pública del ticker {ticker_input} siguiendo estas reglas: {instrucciones}"
                    
                    try:
                        response = model_ia.generate_content(prompt_final)
                        
                        # Manejo del error "Invalid Operation / Part"
                        if response.candidates and response.candidates[0].content.parts:
                            st.markdown(f"### 📋 Informe RSU: {ticker_input}")
                            st.markdown(f'<div class="prompt-container">{response.text}</div>', unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ La IA bloqueó la respuesta por motivos de seguridad. He intentado saltar el filtro pero el prompt es demasiado sensible. Intenta suavizar el lenguaje en tu archivo .txt (menos palabras como 'comprar', 'vender' o 'beneficio asegurado').")
                    except Exception as e:
                        st.error(f"Error técnico: {e}")

elif menu == "🎥 ACADEMY":
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

st.caption(f"v1.3 | Engine: {modelo_nombre}")

