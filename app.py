import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

from config import set_style, get_cnn_fear_greed
import modules.auth as auth
import modules.market as market
import modules.ia_report as ia_report
import modules.cartera as cartera
import modules.tesis as tesis
import modules.trade_grader as trade_grader
import modules.academy as academy

# --- IMPORTACIÓN DE NUEVOS MÓDULOS ---
# Usamos try/except para evitar que la app caiga si aún no has creado los archivos
try:
    import modules.spxl_strategy as spxl_strategy
    import modules.roadmap_2026 as roadmap_2026
    import modules.trump_playbook as trump_playbook
    import modules.rsu_algoritmo as rsu_algoritmo
    NUEVOS_MODULOS_PRESENTES = True
except ImportError:
    NUEVOS_MODULOS_PRESENTES = False

set_style()

if not auth.login():
    st.stop()

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
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fng,
        number={"font": {"size": 24, "color": "white"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#2962ff"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#555",
            'steps': [
                {'range': [0, 25], 'color': '#d32f2f'},
                {'range': [25, 45], 'color': '#f57c00'},
                {'range': [45, 55], 'color': '#ff9800'},
                {'range': [55, 75], 'color': '#4caf50'},
                {'range': [75, 100], 'color': '#00ffad'},
            ],
        }
    ))
    fig.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=0), paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    if fng < 25:
        estado, color = "🟥 Extreme Fear", "#d32f2f"
    elif fng < 45:
        estado, color = "🟧 Fear", "#f57c00"
    elif fng < 55:
        estado, color = "🟡 Neutral", "#ff9800"
    elif fng < 75:
        estado, color = "🟩 Greed", "#4caf50"
    else:
        estado, color = "🟩 Extreme Greed", "#00ffad"

    st.markdown(f'<div style="text-align:center;padding:8px;"><h4 style="color:{color};margin:0;">{estado}</h4></div>', unsafe_allow_html=True)

    # --- LEYENDA ORIGINAL RE-INTEGRADA ---
    st.markdown("**Legend:**")
    legend_items = [
        ("#d32f2f", "Extreme Fear (0-25)"),
        ("#f57c00", "Fear (25-45)"),
        ("#ff9800", "Neutral (45-55)"),
        ("#4caf50", "Greed (55-75)"),
        ("#00ffad", "Extreme Greed (75-100)"),
    ]
    for col, txt in legend_items:
        st.markdown(
            f'<div style="display:flex; align-items:center; margin-bottom:3px;">'
            f'<div style="width:12px;height:12px;background-color:{col};margin-right:8px;border-radius:2px;"></div>'
            f'<span style="font-size:0.8rem;color:#ccc;">{txt}</span></div>', 
            unsafe_allow_html=True
        )

# --- LÓGICA DE NAVEGACIÓN ---
if menu == "📊 DASHBOARD":
    market.show_dashboard()
elif menu == "📈 ESTRATEGIA SPXL":
    if NUEVOS_MODULOS_PRESENTES: spxl_strategy.show()
    else: st.warning("Módulo no encontrado.")
elif menu == "🗺️ 2026 ROADMAP":
    if NUEVOS_MODULOS_PRESENTES: roadmap_2026.show()
    else: st.warning("Módulo no encontrado.")
elif menu == "🇺🇸 TRUMP PLAYBOOK":
    if NUEVOS_MODULOS_PRESENTES: trump_playbook.show()
    else: st.warning("Módulo no encontrado.")
elif menu == "🤖 RSU ALGORITMO":
    if NUEVOS_MODULOS_PRESENTES: rsu_algoritmo.show()
    else: st.warning("Módulo no encontrado.")
elif menu == "🤖 IA REPORT":
    ia_report.show()
elif menu == "💼 CARTERA":
    cartera.show()
elif menu == "📄 TESIS":
    tesis.show()
elif menu == "⚖️ TRADE GRADER":
    trade_grader.show()
elif menu == "🎥 ACADEMY":
    academy.show()
