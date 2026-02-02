
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

# Aplicar estilos
set_style()
st.markdown("<style>h3 {text-align: center !important;}</style>", unsafe_allow_html=True)

# Control de acceso
if not auth.login():
    st.stop()

if 'rsrw_engine' not in st.session_state:
    st.session_state.rsrw_engine = rsrw.RSRWEngine()

# --- SIDEBAR UNIFICADO ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        col_l, col_c, col_r = st.columns([1, 2, 1])
        with col_c:
            st.image("assets/logo.png", use_container_width=True)
    
    usuarios_activos = actualizar_contador_usuarios()
    st.markdown(f"""
        <div style="background-color: #1e222d; padding: 5px; border-radius: 5px; border: 0.5px solid #2962ff; text-align: center; margin-top: 10px;">
            <p style="margin: 0; font-size: 0.7rem; color: #ccc; letter-spacing: 1px;">LIVE USERS: <span style="color: #00ffad; font-weight: bold;">{usuarios_activos}</span></p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    menu = st.radio("NAVIGATION", [
        "📊 DASHBOARD", "📜 MANIFEST", "♣️ RSU CLUB", "📈 SCANNER RS/RW", 
        "🤖 ALGORITMO RSU", "⚡ EMA EDGE", "📅 EARNINGS", "💼 CARTERA", 
        "📝 TESIS", "🤖 AI REPORT", "🎓 ACADEMY", "🏆 TRADE GRADER", 
        "🚀 SPXL STRATEGY", "🗺️ ROADMAP 2026", "🇺🇸 TRUMP PLAYBOOK", 
        "👥 COMUNIDAD", "⚠️ DISCLAIMER"
    ])

    st.write("---")
    
    # 3. FEAR & GREED CON AGUJA REAL DE VELOCÍMETRO
   # 3. FEAR & GREED CON AGUJA DE VELOCÍMETRO
st.subheader("CNN Fear & Greed")
fng = get_cnn_fear_greed()

if fng is not None:
    # Cálculo para la rotación de la aguja (de 180° a 0°)
    # 0 en el índice = 180 grados (Izquierda - Rojo)
    # 100 en el índice = 0 grados (Derecha - Verde)
    posicion_grados = 180 - (fng * 1.8)
    radio = 0.35
    x_punta = 0.5 + radio * math.cos(math.radians(posicion_grados))
    y_punta = 0.3 + radio * math.sin(math.radians(posicion_grados))

    fig = go.Figure()

    # El arco de colores (Gauge)
    fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = fng,
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': "rgba(0,0,0,0)"}, # Barra invisible
            'steps': [
                {'range': [0, 25], 'color': "#d32f2f"},
                {'range': [25, 45], 'color': "#f57c00"},
                {'range': [45, 55], 'color': "#ff9800"},
                {'range': [55, 75], 'color': "#4caf50"},
                {'range': [75, 100], 'color': "#00ffad"}
            ]
        }
    ))

    # Dibujar la aguja física
    fig.update_layout(
        shapes=[dict(
            type='line',
            x0=0.5, y0=0.3, # Centro del velocímetro
            x1=x_punta, y1=y_punta, # Punta rotando según fng
            line=dict(color='white', width=5)
        )],
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "white", 'family': "Arial"},
        height=160,
        margin=dict(l=25, r=25, t=10, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # Estado y color dinámico
    if fng < 25: estado, color = "🟥 Extreme Fear", "#d32f2f"
    elif fng < 45: estado, color = "🟧 Fear", "#f57c00"
    elif fng < 55: estado, color = "🟨 Neutral", "#ff9800"
    elif fng < 75: estado, color = "🟩 Greed", "#4caf50"
    else: estado, color = "🟩 Extreme Greed", "#00ffad"

    st.markdown(f'<p style="text-align:center; color:{color}; font-weight:bold; margin-top:-20px; font-size:1.1rem;">{estado}</p>', unsafe_allow_html=True)

    # Leyenda compacta
    legend_items = [("#d32f2f", "Ex. Fear"), ("#f57c00", "Fear"), ("#ff9800", "Neutral"), ("#4caf50", "Greed"), ("#00ffad", "Ex. Greed")]
    cols_leg = st.columns(2)
    for i, (col, txt) in enumerate(legend_items):
        cols_leg[i % 2].markdown(f'<div style="display:flex; align-items:center; font-size:10px;"><div style="width:8px; height:8px; background:{col}; margin-right:5px;"></div>{txt}</div>', unsafe_allow_html=True)

# --- LÓGICA DE NAVEGACIÓN ---
if menu == "📊 DASHBOARD": market.render()
elif menu == "📜 MANIFEST": manifest.render()
elif menu == "♣️ RSU CLUB": rsu_club.render()
elif menu == "📈 SCANNER RS/RW": rsrw.render()
elif menu == "🤖 ALGORITMO RSU": rsu_algoritmo.render()
elif menu == "⚡ EMA EDGE": ema_edge.render()
elif menu == "📅 EARNINGS": earnings.render()
elif menu == "💼 CARTERA": cartera.render()
elif menu == "📝 TESIS": tesis.render()
elif menu == "🤖 AI REPORT": ia_report.render()
elif menu == "🎓 ACADEMY": academy.render()
elif menu == "🏆 TRADE GRADER": trade_grader.render()
elif menu == "🚀 SPXL STRATEGY": spxl_strategy.render()
elif menu == "🗺️ ROADMAP 2026": roadmap_2026.render()
elif menu == "🇺🇸 TRUMP PLAYBOOK": trump_playbook.render()
elif menu == "👥 COMUNIDAD": comunidad.render()
elif menu == "⚠️ DISCLAIMER": disclaimer.render()


