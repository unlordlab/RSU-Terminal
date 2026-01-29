# app.py - RSU Terminal COMPLETO con LOGIN
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import yaml

# Configuración
st.set_page_config(page_title="RSU Terminal", layout="wide")

# ==================== LOGIN ====================
def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def check_credentials(username, password):
    config = load_config()
    if username in config['credentials']['usernames']:
        return config['credentials']['usernames'][username]['password'] == password
    return False

# Login Screen
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 RSU Terminal - Acceso Autorizado")
    
    with st.form("login"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.success("✅ Bienvenido!")
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas")
    st.stop()

# ==================== DASHBOARD ====================
st.markdown('<h1 style="text-align:center;color:#1f77b4">🚀 RSU Terminal</h1>', unsafe_allow_html=True)

# Sidebar con módulos
st.sidebar.title("📂 Módulos")
modules = {
    "📚 Academy": "academy",
    "💼 Cartera": "cartera", 
    "📈 Credit Spreads": "credit_spreads",
    "😱 Fear & Greed": "fear_greed",
    "🤖 IA Report": "ia_report",
    "📊 Market": "market",
    "📝 Tesis": "tesis",
    "🎯 Trade Grader": "trade_grader"
}

selected_module = st.sidebar.selectbox("Selecciona módulo:", list(modules.keys()))

# ==================== RESUMEN EJECUTIVO ====================
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("🟠 Fear & Greed", "65", "Greed")
with col2: st.metric("💰 PnL Total", "$2,450", "+12.3%")
with col3: st.metric("📈 HY Spread", "2.71%", "🟢")
with col4: st.metric("📋 Posiciones", "3", None)
with col5: st.metric("🎯 Win Rate", "67%", "+5pp")

# ==================== MÓDULOS ====================
module_map = {
    "academy": lambda: st.info("📚 Academy - En desarrollo"),
    "cartera": lambda: render_cartera(),
    "credit_spreads": lambda: render_credit_spreads(),
    "fear_greed": lambda: render_fear_greed(),
    "ia_report": lambda: st.info("🤖 IA Report - Análisis Gemini"),
    "market": lambda: render_market(),
    "tesis": lambda: st.info("📝 Tesis - Google Sheets"),
    "trade_grader": lambda: st.info("🎯 Trade Grader - Scoring automático")
}

try:
    module_map[modules[selected_module]]()
except:
    st.error("Módulo temporalmente no disponible")

# Logout
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.authenticated = False
    st.rerun()

# ==================== FUNCIONES MÓDULOS ====================
def render_cartera():
    st.subheader("💼 CARTERA RSU")
    df = pd.DataFrame({
        'Ticker': ['NVDA', 'TSLA', 'AAPL'],
        'Shares': [15, -8, 25],
        'PnL_$': [102, 38, 180],
        'PnL_%': ['+4.7%', '+1.2%', '+3.8%']
    })
    st.dataframe(df)

def render_credit_spreads():
    st.subheader("📈 Credit Spreads")
    dates = pd.date_range(end=datetime.now(), periods=30)
    fig = go.Figure([go.Scatter(x=dates, y=[2.71]*30, name="HY Spread")])
    fig.add_hline(y=4.0, line_dash="dash", line_color="red")
    st.plotly_chart(fig)

def render_fear_greed():
    st.subheader("😱 Fear & Greed")
    st.metric("Índice", 65, "🟠 Codicia")

def render_market():
    st.subheader("📊 Market Overview")
    col1, col2 = st.columns(2)
    with col1: st.metric("S&P 500", "5,890", "+1.2%")
    with col2: st.metric("VIX", "15.2", "-0.8")
