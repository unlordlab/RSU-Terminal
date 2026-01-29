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

# Estilos CSS personalizados
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
    .logo-container { text-align: center; padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SISTEMA DE ACCESO (CON LOGO) ---
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

# --- 4. SIDEBAR (CON LOGO) ---
with st.sidebar:
    try:
        st.image("logo.png", width=150)
    except:
        st.markdown("<h2 style='color:#2962ff;'>RSU TERMINAL</h2>", unsafe_allow_html=True)
    
    menu = st.radio("", ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA", "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"])
    st.write("---")
    
    # Sentimiento de Mercado
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
    tab_mkt, tab_news, tab_earn, tab_macro = st.tabs(["📈 MERCADO", "📰 NOTICIAS", "💰 EARNINGS", "🌡️ MACRO"])
    
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
            # Reemplazar con URL de tu Google Sheet (CSV)
            df_n = pd.read_csv(st.secrets["URL_NOTICIAS"]) 
            st.dataframe(df_n, use_container_width=True)
        except: st.info("Configura la URL de Noticias en los Secrets de Streamlit.")

    with tab_earn:
        st.subheader("Calendario de Resultados")
        stock_list = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "META", "GOOGL"]
        target_earn = st.selectbox("Analizar Expectativas:", stock_list)
        if st.button("PREDICCIÓN IA"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"Analiza expectativas de earnings para {target_earn}. Sé breve.")
            st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)

    with tab_macro:
        st.subheader("Análisis de Correlación Macro")
        # Aquí puedes añadir la lógica del Macro-Sync que comentamos antes

elif menu == "🤖 IA REPORT":
    t = st.text_input("Ticker", "NVDA").upper()
    if st.button("GENERAR REPORTE"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"Reporte institucional para {t}. Analiza catalizadores y niveles.")
        st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)

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
        st.info(f"Tesis corta: {row['Tesis_Corta']}")
        if st.button("AUDITAR CON IA"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"Haz de abogado del diablo con esta tesis de inversión: {row['Tesis_Corta']}")
            st.markdown(f'<div class="prompt-container">{res.text}</div>', unsafe_allow_html=True)
    except: st.info("Carga tus tesis en Google Sheets.")

elif menu == "⚖️ TRADE GRADER":
    st.title("RSU Trade Scorecard")
    col_a, col_b = st.columns(2)
    with col_a:
        t_input = st.selectbox("Tendencia", ["A favor", "Neutral", "En contra"])
        v_input = st.selectbox("Volumen", ["Inusual / Alto", "Normal", "Bajo"])
    with col_b:
        c_input = st.selectbox("Catalizador", ["Fuerte (Earnings/FDA)", "Especulativo", "Ninguno"])
        r_input = st.slider("Ratio Riesgo:Beneficio (1:X)", 1.0, 5.0, 2.0)
    
    if st.button("CALCULAR GRADO", use_container_width=True):
        grado, color = calificar_trade(t_input, v_input, c_input, r_input)
        st.markdown(f"""
            <div style="text-align:center; padding:30px; border:3px solid {color}; border-radius:15px; margin-top:20px;">
                <h1 style="color:{color}; font-size:100px; margin:0;">{grado}</h1>
                <p style="color:{color}; letter-spacing: 5px;">CALIFICACIÓN RSU</p>
            </div>
        """, unsafe_allow_html=True)

elif menu == "🎥 ACADEMY":
    st.title("RSU Academy")
    # Puedes usar una lista de videos o uno fijo
    st.video("https://www.youtube.com/watch?v=tu_video_id")
