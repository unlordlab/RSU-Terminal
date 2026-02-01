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
import modules.ia_report as ia_report
import modules.cartera as cartera
import modules.tesis as tesis
import modules.trade_grader as trade_grader
import modules.academy as academy
import modules.rsrw as rsrw  

# --- NUEVOS MÓDULOS ---
import modules.spxl_strategy as spxl_strategy
import modules.roadmap_2026 as roadmap_2026
import modules.trump_playbook as trump_playbook
import modules.earnings as earnings # <--- Nuevo módulo integrado

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
    
    menu = st.radio(
        "MENÚ PRINCIPAL",
        [
            "📊 DASHBOARD", 
            "📈 RS/RW ALGO", 
            "📅 EARNINGS", # <--- Opción añadida
            "📝 TESIS", 
            "💼 CARTERA", 
            "🤖 IA REPORT", 
            "🎯 TRADE GRADER", 
            "🚀 SPXL STRATEGY", 
            "🗺️ ROADMAP 2026", 
            "🇺🇸 TRUMP PLAYBOOK", 
            "🎓 ACADEMY"
        ]
    )

    st.write("---")
    
    # --- FEAR & GREED INDEX ---
    st.subheader("CNN Fear & Greed")
    fng = get_cnn_fear_greed()
    
    # Gauge Chart
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
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': fng
            }
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

    st.markdown("**Legend:**")
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

# --- NAVEGACIÓN ---
if menu == "📊 DASHBOARD":
    market.render()

elif menu == "📈 RS/RW ALGO":
    rsrw.render()

elif menu == "📅 EARNINGS": # <--- Lógica de navegación nueva
    earnings.render()

elif menu == "📝 TESIS":
    tesis.render()

elif menu == "💼 CARTERA":
    cartera.render()

elif menu == "🤖 IA REPORT":
    ia_report.render()

elif menu == "🎯 TRADE GRADER":
    trade_grader.render()

elif menu == "🚀 SPXL STRATEGY":
    spxl_strategy.render()

elif menu == "🗺️ ROADMAP 2026":
    roadmap_2026.render()

elif menu == "🇺🇸 TRUMP PLAYBOOK":
    trump_playbook.render()

elif menu == "🎓 ACADEMY":
    academy.render()
