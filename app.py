# app.py
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- IMPORTACIÓN DE CONFIGURACIÓN Y MÓDULOS ---
from config import set_style, get_cnn_fear_greed
import modules.auth as auth
import modules.market as market
import modules.ia_report as ia_report
import modules.cartera as cartera
import modules.tesis as tesis
import modules.trade_grader as trade_grader
import modules.academy as academy

# --- NUEVOS MÓDULOS ---
import modules.spxl_strategy as spxl_strategy
import modules.roadmap_2026 as roadmap_2026
import modules.trump_playbook as trump_playbook
import modules.rsu_algoritmo as rsu_algoritmo

set_style()

if not auth.login():
    st.stop()

# Inicializamos el motor del algoritmo en la sesión si no existe
if 'algoritmo_engine' not in st.session_state:
    st.session_state.algoritmo_engine = rsu_algoritmo.RSUAlgoritmo()

with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)

    menu = st.radio(
        "",
        [
            "📊 DASHBOARD",
            "📈 ESTRATEGIA SPXL",
            "🗺️ 2026 ROADMAP",
            "🇺🇸 TRUMP PLAYBOOK",
            "🤖 RSU ALGORITMO",
            "🤖 IA REPORT",
            "💼 CARTERA",
            "📄 TESIS",
            "⚖️ TRADE GRADER",
            "🎥 ACADEMY",
        ],
    )

    st.write("---")
    st.markdown('<h3 style="color:white;text-align:center;margin-bottom:5px;">FEAR & GREED</h3>', unsafe_allow_html=True)

    fng = get_cnn_fear_greed()
    
    # --- GRÁFICO DE AGUJA ---
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fng,
        number={"font": {"size": 24, "color": "white"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "rgba(0,0,0,0)"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 25], 'color': "#d32f2f"},
                {'range': [25, 45], 'color': "#f57c00"},
                {'range': [45, 55], 'color': "#ff9800"},
                {'range': [55, 75], 'color': "#4caf50"},
                {'range': [75, 100], 'color': "#00ffad"},
            ],
        }
    ))

    # Cálculo de posición de la aguja
    theta = 180 - (fng / 100) * 180
    r = 0.85
    x_head = r * math.cos(math.radians(theta))
    y_head = r * math.sin(math.radians(theta))

    fig.add_shape(
        type='line',
        x0=0.5, y0=0.15,
        x1=0.5 + x_head/2.2, y1=0.15 + y_head/1.2,
        line=dict(color='white', width=4),
        xref='paper', yref='paper'
    )

    fig.add_shape(
        type='circle',
        x0=0.48, y0=0.12, x1=0.52, y1=0.18,
        fillcolor='white', line_color='
