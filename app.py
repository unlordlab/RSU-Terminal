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

# --- SIDEBAR MEJORADO ---
with st.sidebar:
    # Logo
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)

    # Menú
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

   # --- SIDEBAR con Fear & Greed + ETIQUETAS ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)

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

    # ETIQUETAS DE COLOR DEBAJO (nueva parte)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown('<div style="background-color:#d32f2f;padding:4px;border-radius:3px;text-align:center;"><small>Extreme Fear</small></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="background-color:#f57c00;padding:4px;border-radius:3px;text-align:center;"><small>Fear</small></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div style="background-color:#ff9800;padding:4px;border-radius:3px;text-align:center;"><small>Neutral</small></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div style="background-color:#4caf50;padding:4px;border-radius:3px;text-align:center;"><small>Greed</small></div>', unsafe_allow_html=True)
    with col5:
        st.markdown('<div style="background-color:#00ffad;padding:4px;border-radius:3px;text-align:center;"><small>Extreme Greed</small></div>', unsafe_allow_html=True)

    st.caption(f"Current: {fng} pts")
    
    # TÍTULO GRANDE + layout optimizado
    fig.update_layout(
        height=240,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"},
        title={
            'text': "FEAR & GREED INDEX",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': 'white', 'family': 'Arial Black'},
            'pad': {'t': 10}
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Label descriptivo
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric("Actual", f"{fng}", "0 pts")
    with col2:
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

