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

# Configuración segura de la API de Google
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ API Key no configurada en los Secrets de Streamlit.")

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

# --- 2. ACCESO ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.markdown("<h1 style='text-align:center; color:#2962ff;'>RSU</h1>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='text-align:center;'>MASTER TERMINAL</h3>", unsafe_allow_html=True)
        password = st.text_input("ACCESS KEY", type="password")
        if st.button("UNLOCK TERMINAL", use_container_width=True):
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
    
    if score >= 90: return "A+", "#00ffad"
    if score >= 75: return "A", "#a2ff00"
    if score >= 60: return "B", "#ffea00"
    if score >= 40: return "C", "#ff9100"
    return "D", "#f23645"

# --- 4. SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", width=150)
    except:
        st.markdown("<h2 style='color:#2962ff;'>RSU TERMINAL</h2>", unsafe_allow_html=True)
    
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
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
            df_n = pd.read_csv(st.secrets["URL_NOTICIAS"]) 
            st.dataframe(df_n, use_container_width=True)
        except: st.info("Configura la URL de Noticias en los Secrets.")

    with tab_earn:
        st.subheader("Calendario de Resultados")
        stock_list = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "GOOGL"]
        target_earn = st.selectbox("Analizar Expectativas:", stock_list)
        if st.button("PREDICCIÓN IA"):
            try:
                model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
                res = model.generate_content(f"Analiza expectativas de earnings para {target_earn}. Sé breve.")
                st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error de conexión con IA: {e}")

elif menu == "🤖 IA REPORT":
    t = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR REPORTE"):
        try:
            model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
            res = model.generate_content(f"Reporte institucional para {t}. Analiza catalizadores y niveles clave.")
            st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error al generar reporte: {e}")

elif menu == "💼 CARTERA":
    st.title("Cartera Estratégica RSU")
    try:
        df_c = pd.read_csv(st.secrets["URL_CARTERA"])
        st.table(df_c)
    except: st.warning("Conecta la URL de tu Cartera en los Secrets.")

elif menu == "📄 TESIS":
    try:
        df_t = pd.read_csv(st.secrets["URL_TESIS"])
        sel = st.selectbox("Selecciona Tesis:", df_t['Ticker'].tolist())
        row = df_t[df_t['Ticker'] == sel].iloc[0]
        st.markdown(f"### {row['Titulo']}")
        st.info(f"Tesis corta: {row['T
