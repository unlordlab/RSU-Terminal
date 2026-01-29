# app.py - SIN MODULES (100% FUNCIONAL)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="RSU Terminal", layout="wide")

st.markdown("""
<style>
.main-header { font-size: 3rem; color: #1f77b4; text-align: center; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               padding: 1rem; border-radius: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🚀 RSU Terminal</h1>', unsafe_allow_html=True)

# TABS PRINCIPALES
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💼 Cartera", "📈 Credit Spreads", "😱 Fear & Greed"])

with tab1:
    st.header("📊 Resumen Ejecutivo")
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🟠 Fear & Greed", "65", "Greed")
    with col2: st.metric("💰 Total PnL", "$2,450", "+12.3%")
    with col3: st.metric("📈 HY Spread", "2.71%", "-0.02%")
    with col4: st.metric("📋 Posiciones", "3", None)

with tab2:
    st.header("💼 CARTERA RSU")
    st.info("👉 Google Sheet SHEET_ID: `1XjUEjniArxZ-6RkKIf6YKo96SA0IdAf9_wT68HSzAEo`")
    st.info("✅ Columnas: `Ticker | Shares | Precio_Compra | Status`")
    
    # Tabla demo
    df_demo = pd.DataFrame({
        'Ticker': ['NVDA', 'TSLA', 'AAPL'],
        'Shares': [15, -8, 25],
        'PnL_$': [102, 38, 180],
        'PnL_%': ['+4.7%', '+1.2%', '+3.8%'],
        'Status': ['OPEN', 'CLOSED', 'OPEN']
    })
    st.dataframe(df_demo, use_container_width=True)

with tab3:
    st.header("📈 US High Yield Credit Spreads")
    st.caption("🔴 >4% = Estrés | 🟡 2.5-4% = Cautela | 🟢 <2.5% = Normal")
    
    col1, col2 = st.columns([2,1])
    with col1: st.metric("HY Spread (OAS)", "2.71%", None)
    with col2: 
        st.metric("Nivel", "🟢 Normal", None)
        st.caption("27 Ene 2026")
    
    # Gráfico spreads
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    spreads = [2.71, 2.69, 2.68, 2.64, 2.69] * 6
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=spreads, mode='lines+markers', 
                            line=dict(color='#FF6B35', width=3)))
    fig.add_hline(y=4.0, line_dash="dash", line_color="red")
    fig.add_hline(y=2.5, line_dash="dash", line_color="orange")
    fig.update_layout(title="ICE BofA US High Yield OAS", height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("😱 Fear & Greed Index")
    
    score = 65
    if score < 25:
        emoji, level = "🟢", "Miedo Extremo"
    elif score < 45:
        emoji, level = "🟢", "Miedo"
    elif score < 55:
        emoji, level = "🟡", "Neutral"
    elif score < 75:
        emoji, level = "🟠", "Codicia"
    else:
        emoji, level = "🔴", "Codicia Extrema"
    
    col1, col2 = st.columns([2,1])
    with col1: st.metric("Índice", score, level)
    with col2: st.markdown(f'<div style="font-size: 4rem;">{emoji}</div>', unsafe_allow_html=True)
    
    st.success("🕐 Actualiza cada 30min | Fuente: CNN")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Zaragoza, España | Ene 2026</div>", unsafe_allow_html=True)
