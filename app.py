# app.py
import os
import streamlit as st
import plotly.graph_objects as go
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

# --- SIDEBAR con Fear & Greed SUTIL ---
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

    # Fear & Greed GAUGE
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
        height=140,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # ETIQUETAS SÚPER SUTIL (pequeñas, fondo transparente, solo texto)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div style="padding:2px;text-align:center;"><small style="color:#d32f2f;font-size:10px;font-weight:500;">Extreme Fear</small></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="padding:2px;text-align:center;"><small style="color:#f57c00;font-size:10px;font-weight:500;">Fear</small></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div style="padding:2px;text-align:center;"><small style="color:#ff9800;font-size:10px;font-weight:500;">Neutral</small></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div style="padding:2px;text-align:center;"><small style="color:#4caf50;font-size:10px;font-weight:500;">Greed</small></div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div style="padding:2px;text-align:center;"><small style="color:#00ffad;font-size:10px;font-weight:500;">Extreme Greed</small></div>', unsafe_allow_html=True)

    st.caption(f"Current: {fng} pts")

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
