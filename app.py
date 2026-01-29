import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="RSU Master Terminal", layout="wide", page_icon="📊")

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

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
        padding: 20px; border-radius: 5px; margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ACCESO ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h1 style='text-align:center; color:#2962ff;'>RSU LOGIN</h1>", unsafe_allow_html=True)
        password = st.text_input("ACCESS KEY", type="password")
        if st.button("UNLOCK TERMINAL"):
            if password == "RSU2026":
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Clave Incorrecta")
    st.stop()

# --- 3. FUNCIONES ---
@st.cache_data(ttl=600)
def get_cnn_fear_greed():
    try:
        url = "https://edition.cnn.com/markets/fear-and-greed"
        headers = {'User-Agent': 'Mozilla/5.0'}
        soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')
        return int(soup.find("span", class_="market-fng-gauge__dial-number-value").text)
    except: return 50

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#2962ff;'>RSU TERMINAL</h2>", unsafe_allow_html=True)
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "🎥 ACADEMY"])
    st.write("---")
    fg_val = get_cnn_fear_greed()
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=fg_val,
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2962ff"}},
        title={'text': "SENTIMIENTO", 'font': {'color': 'white', 'size': 14}}
    ))
    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=180, margin=dict(l=10,r=10,t=30,b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

# --- 5. LÓGICA DE MENÚ ---
if menu == "📊 DASHBOARD":
    tab_mkt, tab_news, tab_earn = st.tabs(["📈 MERCADO", "📰 NOTICIAS", "💰 EARNINGS"])
    
    with tab_mkt:
        idx = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "VIX": "^VIX", "BTC": "BTC-USD"}
        cols = st.columns(4)
        for i, (name, sym) in enumerate(idx.items()):
            d = yf.Ticker(sym).fast_info
            ch = ((d['last_price'] - d['previous_close']) / d['previous_close']) * 100
            cols[i].markdown(f"""<div class="metric-card"><small>{name}</small><h3>{d['last_price']:,.1f}</h3><p style="color:{'#00ffad' if ch>0 else '#f23645'}">{ch:.2f}%</p></div>""", unsafe_allow_html=True)

    with tab_news:
        st.subheader("Feed de Noticias RSU")
        try:
            df_n = pd.read_csv("URL_NOTICIAS_CSV")
            st.dataframe(df_n, use_container_width=True)
        except: st.info("Configura el CSV de Noticias en Google Sheets.")

    with tab_earn:
        st.subheader("Calendario de Resultados")
        stock_list = ["NVDA", "AAPL", "TSLA", "MSFT"]
        target_earn = st.selectbox("Analizar Expectativas:", stock_list)
        if st.button("PREDICCIÓN IA"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"Analiza expectativas de earnings para {target_earn}")
            st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)

elif menu == "🤖 IA REPORT":
    t = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR REPORTE"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Reporte institucional para {t}")
        st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)

elif menu == "💼 CARTERA":
    try:
        df_c = pd.read_csv("URL_CARTERA_CSV")
        st.table(df_c)
    except: st.warning("Conecta el CSV de tu Cartera.")

elif menu == "📄 TESIS":
    try:
        df_t = pd.read_csv("URL_TESIS_CSV")
        sel = st.selectbox("Selecciona Tesis:", df_t['Ticker'].tolist())
        row = df_t[df_t['Ticker'] == sel].iloc[0]
        st.markdown(f"### {row['Titulo']}")
        st.write(row['Tesis_Corta'])
        if st.button("AUDITAR CON IA"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"Haz de abogado del diablo con esta tesis: {row['Tesis_Corta']}")
            st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
    except: st.info("Carga tus tesis en Google Sheets.")

elif menu == "🎥 ACADEMY":
    st.video("https://www.youtube.com/watch?v=tu_video")








