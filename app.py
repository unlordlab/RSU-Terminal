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
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)
    
    # --- CONTADOR DE USUARIOS ---
    usuarios_activos = actualizar_contador_usuarios()
    st.markdown(f"""
        <div style="background-color: #1e222d; padding: 10px; border-radius: 5px; border: 1px solid #2962ff; text-align: center;">
            <p style="margin: 0; font-size: 0.8rem; color: #ccc;">USUARIOS CONECTADOS</p>
            <h2 style="margin: 0; color: #00ffad;">{usuarios_activos}</h2>
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
    
    # --- FEAR & GREED INDEX ---
    st.subheader("CNN Fear & Greed")
    fng = get_cnn_fear_greed()
    
    if fng is not None:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fng,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#2962ff"},
                'steps': [
                    {'range': [0, 25], 'color': "#d32f2f"},
                    {'range': [25, 45], 'color': "#f57c00"},
                    {'range': [45, 55], 'color': "#ff9800"},
                    {'range': [55, 75], 'color': "#4caf50"},
                    {'range': [75, 100], 'color': "#00ffad"}
                ]
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "white", 'family': "Arial"},
            height=150,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Estado y Leyenda
        if fng < 25: estado, color = "🟥 Extreme Fear", "#d32f2f"
        elif fng < 45: estado, color = "🟧 Fear", "#f57c00"
        elif fng < 55: estado, color = "🟨 Neutral", "#ff9800"
        elif fng < 75: estado, color = "🟩 Greed", "#4caf50"
        else: estado, color = "🟩 Extreme Greed", "#00ffad"

        st.markdown(f'<div style="text-align:center;padding:8px;"><h4 style="color:{color};margin:0;">{estado}</h4></div>', unsafe_allow_html=True)

    st.markdown("**Leyenda:**")
    legend_items = [
        ("#d32f2f", "Extreme Fear (0-25)"),
        ("#f57c00", "Fear (25-45)"),
        ("#ff9800", "Neutral (45-55)"),
        ("#4caf50", "Greed (55-75)"),
        ("#00ffad", "Extreme Greed (75-100)")
    ]
    for col, txt in legend_items:
        st.markdown(f'''
            <div style="display:flex; align-items:center; margin-bottom:3px;">
                <div style="width:12px; height:12px; background-color:{col}; border-radius:2px; margin-right:8px;"></div>
                <span style="font-size:0.8rem; color:#ccc;">{txt}</span>
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





