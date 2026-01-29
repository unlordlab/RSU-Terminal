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

# --- 2. CONFIGURACIÓN IA (ANTI-BLOQUEO) ---
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

@st.cache_data(ttl=600)
def obtener_prompt_github():
    try:
        # ⚠️ REEMPLAZA CON TU URL RAW DE GITHUB
        url_raw = "https://github.com/unlordlab/RSU-Terminal/blob/839f5be5065f917e728787e363fe06b33cdbc306/prompt_report.txt"
        response = requests.get(url_raw)
        return response.text if response.status_code == 200 else ""
    except: return ""

model_ia, modelo_nombre, error_ia = conectar_ia()

# --- 3. FUNCIONES DE MERCADO ---
@st.cache_data(ttl=3600)
def get_cnn_fear_greed():
    try:
        url = "https://edition.cnn.com/markets/fear-and-greed"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')
        val = soup.find("span", class_="market-fng-gauge__dial-number-value").text
        return int(val)
    except: return 50

def get_market_index(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).fast_info
        p = data['last_price']
        c = ((p - data['previous_close']) / data['previous_close']) * 100
        return p, c
    except: return 0.0, 0.0

# --- 4. LOGIN SISTEMA ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        st.markdown("<h4 style='text-align:center;'>RSU TERMINAL ACCESS</h4>", unsafe_allow_html=True)
        password = st.text_input("PASSWORD", type="password")
        if st.button("UNLOCK", use_container_width=True):
            if password == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    st.stop() # Aquí es donde el código se detiene si no hay login

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=150)
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
    
    st.write("---")
    fng = get_cnn_fear_greed()
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=fng,
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2962ff"},
               'steps': [{'range': [0, 30], 'color': "#f23645"}, 
                         {'range': [30, 70], 'color': "#444"},
                         {'range': [70, 100], 'color': "#00ffad"}]},
    ))
    fig.update_layout(height=180, margin=dict(l=20,r=20,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True)

# --- 6. LÓGICA DE MENÚS ---

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
        except: st.info("Falta URL_NOTICIAS en Secrets.")

elif menu == "🤖 IA REPORT":
    t_in = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR REPORTE RSU"):
        if error_ia: st.error(error_ia)
        else:
            with st.spinner(f"Analizando {t_in}..."):
                template = obtener_prompt_github()
                prompt_final = f"Analitza {t_in} seguint això: {template.replace('[TICKER]', t_in)}"
                try:
                    res = model_ia.generate_content(prompt_final)
                    if res.candidates and res.candidates[0].content.parts:
                        st.markdown(f"### 📋 Informe: {t_in}")
                        st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Error de IA: {e}")

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
    st.subheader("RSU Scorecard")
    ten = st.selectbox("Tendencia", ["A favor", "Neutral", "En contra"])
    rrr = st.slider("RRR", 1.0, 5.0, 2.0)
    if st.button("CALCULAR"):
        st.success(f"Grado calculado para tendencia {ten}")

elif menu == "🎥 ACADEMY":
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

st.write("---")
st.caption(f"v1.4 | Engine: {modelo_nombre}")


