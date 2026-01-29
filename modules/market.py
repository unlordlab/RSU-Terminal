# app.py
import os
# modules/market.py
import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd

from config import set_style, get_cnn_fear_greed
import modules.auth as auth
import modules.market as market
import modules.ia_report as ia_report
import modules.cartera as cartera
import modules.tesis as tesis
import modules.trade_grader as trade_grader
import modules.academy as academy

# --- ESTILO GLOBAL ---
set_style()

# --- LOGIN ---
if not auth.login():
    st.stop()

# --- SIDEBAR con Fear & Greed COMPACTO ---
with st.sidebar:
    # Logo
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)

    # Menú principal
    menu = st.radio(
        "",
        [
            "📊 DASHBOARD",
            "🤖 IA REPORT",
            "💼 CARTERA",
            "📄 TESIS",
            "⚖️ TRADE GRADER",
            "🎥 ACADEMY",
        ],
    )

    st.write("---")

    # Fear & Greed GAUGE COMPACTO (como tu imagen)
    fng = get_cnn_fear_greed()
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fng,
        number={"font": {"size": 20, "color": "white"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#2962ff"},
            'steps': [
                {'range': [0, 25], 'color': "#d32f2f"},
                {'range': [25, 45], 'color': "#f57c00"},
                {'range': [45, 55], 'color': "#ff9800"},
                {'range': [55, 75], 'color': "#4caf50"},
                {'range': [75, 100], 'color': "#00ffad"},
            ]
        }
    ))
    fig.update_layout(
        height=140,  # Compacto como tu imagen
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Label descriptivo debajo
    if fng < 25:
        st.caption("🟥 Extreme Fear")
    elif fng < 45:
        st.caption("🟧 Fear")
    elif fng < 55:
        st.caption("🟡 Neutral")
    elif fng < 75:
        st.caption("🟩 Greed")
    else:
        st.caption("🟩 Extreme Greed")

# --- ROUTING DE PÁGINAS ---
if menu == "📊 DASHBOARD":
    market.render()
elif menu == "🤖 IA REPORT":
    ia_report.render()
elif menu == "💼 CARTERA":
    cartera.render()
elif menu == "📄 TESIS":
    tesis.render()
elif menu == "⚖️ TRADE GRADER":
    trade_grader.render()
elif menu == "🎥 ACADEMY":
    academy.render()
from config import get_market_index

def render():
    """Función principal del dashboard - NO poner nada fuera de esta función"""
    st.title("Market Overview")
    
    # 4 cards principales
    idx = {
        "S&P 500": "^GSPC", 
        "NASDAQ": "^IXIC", 
        "VIX": "^VIX", 
        "BTC": "BTC-USD"
    }
    
    cols = st.columns(4)
    for i, (name, symbol) in enumerate(idx.items()):
        with cols[i]:
            price, change = get_market_index(symbol)
            
            # Color y emoji dinámicos
            if name == "VIX":
                color = "#00ffad" if change < 0 else "#f23645"
                trend_emoji = "📉" if change < 0 else "📈"
            else:
                color = "#00ffad" if change >= 0 else "#f23645"
                trend_emoji = "📈" if change >= 0 else "📉"
            
            # Card estilo pro
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 12px; opacity: 0.8; margin-bottom: 8px;">{name}</div>
                <div style="font-size: 28px; font-weight: bold; margin-bottom: 8px;">${price:,.0f}</div>
                <div style="font-size: 14px; color: {color}; font-weight: bold;">
                    {trend_emoji} {change:+.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Tabs noticias/earnings
    t1, t2 = st.tabs(["📰 NOTICIAS", "💰 EARNINGS"])
    
    with t1:
        try:
            df = pd.read_csv(st.secrets["URL_NOTICIAS"])
            st.dataframe(df[["Fecha", "Ticker", "Título", "Impacto"]], 
                        use_container_width=True, hide_index=True)
        except:
            st.info("🔄 Configura URL_NOTICIAS en Secrets")
    
    with t2:
        st.info("💼 Próximos Earnings Calendar - En desarrollo")

# FIN DEL ARCHIVO - NADA FUERA DE LA FUNCIÓN render()

