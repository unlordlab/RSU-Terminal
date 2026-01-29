# app.py
import os
import streamlit as st
import plotly.graph_objects as go

from config import set_style, get_cnn_fear_greed
from modules import auth, market, ia_report, cartera, tesis, trade_grader, academy

set_style()

# --- LOGIN ---
if not auth.login():
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)

    menu = st.radio(
        "",
        ["📊 DASHBOARD", "🤖 IA REPORT", "💼 CARTERA",
         "📄 TESIS", "⚖️ TRADE GRADER", "🎥 ACADEMY"]
    )

    st.write("---")
    fng = get_cnn_fear_greed()
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=fng,
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#2962ff"},
            'steps': [
                {'range': [0, 30], 'color': "#f23645"},
                {'range': [30, 70], 'color': "#444"},
                {'range': [70, 100], 'color': "#00ffad"},
            ],
        },
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"},
    )
    st.plotly_chart(fig, use_container_width=True)

# --- ROUTING ---
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
