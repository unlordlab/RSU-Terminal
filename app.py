import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from datetime import datetime
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

# --- 2. CONFIGURACIÓN IA (SISTEMA ROBUSTO v1.1) ---
# Detectamos automáticamente si usas GEMINI_API_KEY o GOOGLE_API_KEY
API_KEY = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

def conectar_ia():
    if not API_KEY: return None, None, "Falta API KEY en Secrets"
    try:
        genai.configure(api_key=API_KEY)
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        sel = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in modelos else modelos[0]
        return genai.GenerativeModel(sel), sel, None
    except Exception as e: return None, None, str(e)

@st.cache_data(ttl=300) # Caché de 5 min para no saturar GitHub
def obtener_prompt_github():
    try:
        # ⚠️ REEMPLAZA ESTA URL POR TU URL "RAW" DE GITHUB
        url_raw = "https://github.com/unlordlab/RSU-Terminal/blob/dd8161ef95a1d48bc491590f0ad965444991fc5c/prompt_report.txt"
        response = requests.get(url_raw)
        if response.status_code == 200:
            return response.text
        return "Actúa como analista financiero. Analiza el ticker {t}."
    except:
        return "Actúa como analista financiero. Analiza el ticker {t}."

model_ia, modelo_nombre, error_ia = conectar_ia()

# --- 3. ACCESO ---
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
@st.cache_data(ttl=600)
def get_cnn_fear_greed():
    try:
        url = "https://edition.cnn.com/markets/fear-and-greed"
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')
        return int(soup.find("span", class_="market-fng-gauge__dial-number-value").text)
    except: return 50

def get_market_index(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).fast_info
        p = data['last_price']
        c = ((p - data['previous_close']) / data['previous_close']) * 100
        return p, c
    except: return 0.0, 0.0

def calificar_trade(tendencia, volumen, catalizador, rrr):
    score = 0
    if tendencia == "A favor": score += 30
    elif tendencia == "Neutral": score += 15
    if volumen == "Inusual / Alto": score += 25
    elif volumen == "Normal": score += 10
    if catalizador == "Fuerte (Earnings/FDA)": score += 25
    elif catalizador == "Especulativo": score += 10
    if rrr >= 3: score += 20
    elif rrr >= 2: score += 10
    grados = {90: ("A+", "#00ffad"), 75: ("A", "#a2ff00"), 60: ("B", "#ffea00"), 40: ("C", "#ff9100"), 0: ("D", "#f23645")}
    for s, g in grados.items():
        if score >= s: return g

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=120)
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
    st.write("---")
    if st.button("Limpiar Caché"): st.cache_data.clear()
    
    fg = get_cnn_fear_greed()
    fig = go.Figure(go.Indicator(mode="gauge+number", value=fg, gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2962ff"}}, title={'text': "SENTIMIENTO", 'font': {'color': 'white', 'size': 14}}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=180, margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig, use_container_width=True)

# --- 6. LÓGICA DE MENÚ ---
if menu == "📊 DASHBOARD":
    t1, t2, t3 = st.tabs(["📈 MERCADO", "📰 NOTICIAS", "💰 EARNINGS"])
    with t1:
        idx = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "VIX": "^VIX", "BTC": "BTC-USD"}
        cols = st.columns(4)
        for i, (n, s) in enumerate(idx.items()):
            p, c = get_market_index(s)
            color = "#00ffad" if (c >= 0 and n != "VIX") or (c < 0 and n == "VIX") else "#f23645"
            cols[i].markdown(f"""<div class="metric-card"><small>{n}</small><h3>{p:,.1f}</h3><p style="color:{color}">{c:.2f}%</p></div>""", unsafe_allow_html=True)
    with t2:
        try:
            df = pd.read_csv(st.secrets["URL_NOTICIAS"])
            st.dataframe(df, use_container_width=True)
        except: st.info("Configura URL_NOTICIAS en Secrets.")
    with t3:
        target = st.selectbox("Ticker:", ["NVDA", "AAPL", "TSLA", "MSFT"])
        if st.button("PREDECIR"):
            if error_ia: st.error(error_ia)
            else:
                res = model_ia.generate_content(f"Próximos earnings de {target}")
                st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)

elif menu == "🤖 IA REPORT":
    ticker_input = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR REPORTE RSU"):
        if error_ia: 
            st.error(f"Error de Configuración: {error_ia}")
        else:
            with st.spinner(f"Solicitando análisis de {ticker_input}..."):
                # 1. Obtenemos el esqueleto del prompt desde GitHub
                prompt_raw = obtener_prompt_github()
                
                # 2. Inyectamos el ticker en el prompt
                prompt_final = prompt_raw.replace("{t}", ticker_input)
                
                try:
                    # 3. Llamada real a la IA enviando el prompt procesado
                    response = model_ia.generate_content(prompt_final)
                    
                    # 4. Verificación de seguridad
                    if response and response.text:
                        st.markdown(f"### 📄 Informe Estratégico: {ticker_input}")
                        st.markdown(f'<div class="prompt-container">{response.text}</div>', unsafe_allow_html=True)
                    else:
                        st.error("La IA no devolvió ninguna respuesta.")
                except Exception as e:
                    st.error(f"Error al generar contenido: {e}")

elif menu == "💼 CARTERA":
    try:
        df = pd.read_csv(st.secrets["URL_CARTERA"])
        st.table(df)
    except: st.warning("Configura URL_CARTERA.")

elif menu == "📄 TESIS":
    try:
        df = pd.read_csv(st.secrets["URL_TESIS"])
        sel = st.selectbox("Tesis:", df['Ticker'].tolist())
        row = df[df['Ticker'] == sel].iloc[0]
        st.info(row['Tesis_Corta'])
        if st.button("AUDITAR"):
            res = model_ia.generate_content(f"Critica esta tesis: {row['Tesis_Corta']}")
            st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
    except: st.info("Configura URL_TESIS.")

elif menu == "⚖️ TRADE GRADER":
    c1, c2 = st.columns(2)
    with c1:
        t_in = st.selectbox("Tendencia", ["A favor", "Neutral", "En contra"])
        v_in = st.selectbox("Volumen", ["Inusual / Alto", "Normal", "Bajo"])
    with c2:
        c_in = st.selectbox("Catalizador", ["Fuerte (Earnings/FDA)", "Especulativo", "Ninguno"])
        r_in = st.slider("RRR", 1.0, 5.0, 2.0)
    if st.button("CALCULAR"):
        g, color = calificar_trade(t_in, v_in, c_in, r_in)
        st.markdown(f'<div style="text-align:center; padding:20px; border:3px solid {color}; border-radius:15px;"><h1 style="color:{color}; font-size:80px;">{g}</h1></div>', unsafe_allow_html=True)

elif menu == "🎥 ACADEMY":
    st.title("RSU Academy")
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

st.write("---")
st.caption(f"v1.1 | Engine: {modelo_nombre}")
