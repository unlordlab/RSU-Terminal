
# app.py
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- IMPORTACIÓN DE CONFIGURACIÓN Y MÓDULOS ---
from config import set_style, get_cnn_fear_greed, actualizar_contador_usuarios
import modules.auth as auth
import modules.market as market
import modules.manifest as manifest          
import modules.rsu_club as rsu_club          
import modules.rsrw as rsrw
import modules.rsu_algoritmo as rsu_algoritmo 
import modules.ema_edge as ema_edge          
import modules.earnings as earnings
import modules.cartera as cartera
import modules.tesis as tesis
import modules.ia_report as ia_report
import modules.academy as academy
import modules.trade_grader as trade_grader
import modules.spxl_strategy as spxl_strategy
import modules.roadmap_2026 as roadmap_2026
import modules.trump_playbook as trump_playbook
import modules.comunidad as comunidad          
import modules.disclaimer as disclaimer      

# Aplicar estilos definidos en config.py
set_style()

# Control de acceso
if not auth.login():
    st.stop()

# Inicializamos el motor del algoritmo RS/RW en la sesión
if 'rsrw_engine' not in st.session_state:
    st.session_state.rsrw_engine = rsrw.RSRWEngine()

# --- SIDEBAR UNIFICADO ---
with st.sidebar:
    # 1. LOGO CENTRADO
    if os.path.exists("assets/logo.png"):
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.image("assets/logo.png", use_container_width=True)
    
    # 2. CONTADOR DE USUARIOS (MÁS PEQUEÑO)
    usuarios_activos = actualizar_contador_usuarios()
    st.markdown(f"""
        <div style="background-color: #1e222d; padding: 5px; border-radius: 5px; border: 0.5px solid #2962ff; text-align: center; margin-top: 10px;">
            <p style="margin: 0; font-size: 0.7rem; color: #ccc; letter-spacing: 1px;">LIVE USERS: <span style="color: #00ffad; font-weight: bold;">{usuarios_activos}</span></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # --- MENÚ DE NAVEGACIÓN ---
    menu = st.radio(
        "NAVIGATION",
        [
            "📊 DASHBOARD", 
            "📜 MANIFEST",
            "♣️ RSU CLUB",
            "📈 SCANNER RS/RW", 
            "🤖 ALGORITMO RSU",
            "⚡ EMA EDGE",
            "📅 EARNINGS", 
            "💼 CARTERA", 
            "📝 TESIS",
            "🤖 AI REPORT",
            "🎓 ACADEMY",
            "🏆 TRADE GRADER",
            "🚀 SPXL STRATEGY",
            "🗺️ ROADMAP 2026",
            "🇺🇸 TRUMP PLAYBOOK",
            "👥 COMUNIDAD",
            "⚠️ DISCLAIMER"
        ]
    )

    st.write("---")
    
    # 3. FEAR & GREED INDEX (CON AGUJA REAL)
    st.subheader("CNN Fear & Greed")
    
    # Intentamos obtener datos reales (get_cnn_fear_greed debe estar bien configurado en config.py)
    fng = get_cnn_fear_greed()
    
    if fng is not None:
        # Configuración de la "Aguja" mediante Threshold y Bar transparente
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fng,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white", 'nticks': 5},
                'bar': {'color': "rgba(0,0,0,0)"}, # Barra transparente para que no tape los colores
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 25], 'color': "#d32f2f"},   # Extreme Fear
                    {'range': [25, 45], 'color': "#f57c00"},  # Fear
                    {'range': [45, 55], 'color': "#ff9800"},  # Neutral
                    {'range': [55, 75], 'color': "#4caf50"},  # Greed
                    {'range': [75, 100], 'color': "#00ffad"}  # Extreme Greed
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4}, # ESTA ES LA AGUJA
                    'thickness': 0.75,
                    'value': fng
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white", 'family': "Arial"},
            height=140,
            margin=dict(l=20, r=20, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Estado dinámico basado en el valor real
        if fng < 25: estado, color = "🟥 Extreme Fear", "#d32f2f"
        elif fng < 45: estado, color = "🟧 Fear", "#f57c00"
        elif fng < 55: estado, color = "🟨 Neutral", "#ff9800"
        elif fng < 75: estado, color = "🟩 Greed", "#4caf50"
        else: estado, color = "🟩 Extreme Greed", "#00ffad"

        st.markdown(f'<div style="text-align:center;"><h4 style="color:{color};margin:0;font-size:1rem;">{estado}</h4></div>', unsafe_allow_html=True)
    else:
        st.error("Error cargando datos reales de CNN")

    st.markdown("**Sentimiento:**")
    legend_items = [
        ("#d32f2f", "Extreme Fear"),
        ("#f57c00", "Fear"),
        ("#ff9800", "Neutral"),
        ("#4caf50", "Greed"),
        ("#00ffad", "Extreme Greed")
    ]
    
    cols_leg = st.columns(2)
    for i, (col, txt) in enumerate(legend_items):
        target_col = cols_leg[i % 2]
        target_col.markdown(f'''
            <div style="display:flex; align-items:center; margin-bottom:2px;">
                <div style="width:8px; height:8px; background-color:{col}; border-radius:1px; margin-right:5px;"></div>
                <span style="font-size:0.65rem; color:#ccc;">{txt}</span>
            </div>
        ''', unsafe_allow_html=True)

# --- LÓGICA DE NAVEGACIÓN ---
if menu == "📊 DASHBOARD":
    market.render()
elif menu == "📜 MANIFEST":
    manifest.render()
elif menu == "♣️ RSU CLUB":
    rsu_club.render()
elif menu == "📈 SCANNER RS/RW":
    rsrw.render()
elif menu == "🤖 ALGORITMO RSU":
    rsu_algoritmo.render()
elif menu == "⚡ EMA EDGE":
    ema_edge.render()
elif menu == "📅 EARNINGS":
    earnings.render()
elif menu == "💼 CARTERA":
    cartera.render()
elif menu == "📝 TESIS":
    tesis.render()
elif menu == "🤖 AI REPORT":
    ia_report.render()
elif menu == "🎓 ACADEMY":
    academy.render()
elif menu == "🏆 TRADE GRADER":
    trade_grader.render()
elif menu == "🚀 SPXL STRATEGY":
    spxl_strategy.render()
elif menu == "🗺️ ROADMAP 2026":
    roadmap_2026.render()
elif menu == "🇺🇸 TRUMP PLAYBOOK":
    trump_playbook.render()
elif menu == "👥 COMUNIDAD":
    comunidad.render()
elif menu == "⚠️ DISCLAIMER":
    disclaimer.render()



