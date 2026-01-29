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

# --- 2. CONFIGURACIÓN IA (ANTI-BLOQUEO v1.3) ---
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        # Configuración para evitar bloqueos por contenido técnico/financiero
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        # Cargamos el modelo con los ajustes de seguridad
        return genai.GenerativeModel(model_name=sel, safety_settings=safety_settings), sel, None
    except Exception as e: return None, None, str(e)

@st.cache_data(ttl=60)
def obtener_prompt_github():
    try:
        # ⚠️ REEMPLAZA CON TU URL RAW DE GITHUB
        url_raw = "https://github.com/unlordlab/RSU-Terminal/blob/df1305016e5028c9db6cc5c0a689ddd661434272/prompt_report.txt"
        response = requests.get(url_raw)
        return response.text if response.status_code == 200 else ""
    except: return ""

model_ia, modelo_nombre, error_ia = conectar_ia()

# --- 3. ACCESO CON LOGO ---
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
    st.stop()

# --- 4. FUNCIONES DE MERCADO ---
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

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
    st.write("---")
    if st.button("🔄 Refrescar Datos/GitHub"):
        st.cache_data.clear()
        st.success("Caché Limpia")

# --- 6. LÓGICA DE MENÚ ---

if menu == "📊 DASHBOARD":
    st.title("Market Overview")
    idx = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "VIX": "^VIX", "BTC": "BTC-USD"}
    cols = st.columns(4)
    for i, (n, s) in enumerate(idx.items()):
        p, c = get_market_index(s)
        color = "#00ffad" if (c >= 0 and n != "VIX") or (c < 0 and n == "VIX") else "#f23645"
        cols[i].markdown(f"""<div class="metric-card"><small>{n}</small><h3>{p:,.1f}</h3><p style="color:{color}">{c:.2f}%</p></div>""", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["📰 NOTICIAS", "💰 EARNINGS"])
    with t1:
        try:
            df = pd.read_csv(st.secrets["URL_NOTICIAS"])
            st.dataframe(df, use_container_width=True)
        except: st.info("Configura URL_NOTICIAS en Secrets.")

elif menu == "🤖 IA REPORT":
    t_in = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR REPORTE"):
        if error_ia: st.error(error_ia)
        else:
            with st.spinner(f"Analizando {t_in}..."):
                template = obtener_prompt_github()
                prompt_final = f"No des consejos de inversión. Analiza {t_in} usando estas instrucciones: {template.replace('[TICKER]', t_in)}"
                try:
                    res = model_ia.generate_content(prompt_final)
                    if res.candidates and res.candidates[0].content.parts:
                        st.markdown(f"### 📋 Resultado: {t_in}")
                        st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
                    else: st.warning("IA bloqueada por seguridad. Revisa tu prompt en GitHub.")
                except Exception as e: st.error(f"Error: {e}")

elif menu == "💼 CARTERA":
    try:
        df = pd.read_csv(st.secrets["URL_CARTERA"])
        st.table(df)
    except: st.warning("Configura URL_CARTERA.")

elif menu == "📄 TESIS":
    try:
        df = pd.read_csv(st.secrets["URL_TESIS"])
        sel = st.selectbox("Tesis:", df['Ticker'].tolist())
        st.info(df[df['Ticker'] == sel]['Tesis_Corta'].values[0])
    except: st.info("Configura URL_TESIS.")

elif menu == "⚖️ TRADE GRADER":
    c1, c2 = st.columns(2)
    with c1:
        ten = st.selectbox("Tendencia", ["A favor", "Neutral", "En contra"])
        vol = st.selectbox("Volumen", ["Inusual / Alto", "Normal", "Bajo"])
    with c2:
        cat = st.selectbox("Catalizador", ["Fuerte (Earnings/FDA)", "Especulativo", "Ninguno"])
        rrr = st.slider("RRR", 1.0, 5.0, 2.0)
    if st.button("CALCULAR"):
        g, col = calificar_trade(ten, vol, cat, rrr)
        st.markdown(f'<div style="text-align:center; padding:20px; border:3px solid {col}; border-radius:15px;"><h1 style="color:{col}; font-size:80px;">{g}</h1></div>', unsafe_allow_html=True)

elif menu == "🎥 ACADEMY":
    st.title("RSU Academy")
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

st.write("---")
st.caption(f"v1.3 | Engine: {modelo_nombre}")
