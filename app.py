# app.py
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- IMPORTACIÓN DE CONFIGURACIÓN Y MÓDULOS ---
# Se añade la función del contador a las importaciones
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


# Aplicar estilos definidos en config.py
set_style()

# Control de acceso
if not auth.login():
    st.stop()

# Inicializamos el motor del algoritmo en la sesión si no existe
if 'algoritmo_engine' not in st.session_state:
    st.session_state.algoritmo_engine = rsu_algoritmo.RSUAlgoritmo()
    

# --- SIDEBAR UNIFICADO ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)
    
    # --- CONTADOR DE USUARIOS ---
    try:
        usuarios_activos = actualizar_contador_usuarios()
        st.markdown(f"""
            <div style="text-align:center; padding:10px; background-color:#1a1e26; border-radius:10px; border:1px solid #2962ff; margin-bottom:20px;">
                <span style="color:#00ffad; font-weight:bold; font-size:20px;">● {usuarios_activos}</span>
                <span style="color:#888; font-size:12px; margin-left:5px;">USUARIOS ONLINE</span>
            </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        # Falla silenciosa si la función no está en config.py todavía
        pass

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

    # Obtener valor de Fear & Greed
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

    # Lógica de la aguja
    theta = 180 - (fng / 100) * 180
    r = 0.85
    x_head = r * math.cos(math.radians(theta))
    y_head = r * math.sin(math.radians(theta))

    fig.add_shape(type='line', x0=0.5, y0=0.15, x1=0.5 + x_head/2.2, y1=0.15 + y_head/1.2,
                  line=dict(color='white', width=4), xref='paper', yref='paper')
    fig.add_shape(type='circle', x0=0.48, y0=0.12, x1=0.52, y1=0.18,
                  fillcolor='white', line_color='white', xref='paper', yref='paper')

    fig.update_layout(height=180, margin=dict(l=15, r=15, t=5, b=25), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- ESTADO Y LEYENDA ---
    if fng < 25: estado, color = "🟥 Extreme Fear", "#d32f2f"
    elif fng < 45: estado, color = "🟧 Fear", "#f57c00"
    elif fng < 55: estado, color = "🟡 Neutral", "#ff9800"
    elif fng < 75: estado, color = "🟩 Greed", "#4caf50"
    else: estado, color = "🟩 Extreme Greed", "#00ffad"

    st.markdown(f'<div style="text-align:center;padding:8px;"><h4 style="color:{color};margin:0;">{estado}</h4></div>', unsafe_allow_html=True)

    st.markdown("**Legend:**")
    legend_items = [("#d32f2f", "Extreme Fear"), ("#f57c00", "Fear"), ("#ff9800", "Neutral"), ("#4caf50", "Greed"), ("#00ffad", "Extreme Greed")]
    for col, txt in legend_items:
        st.markdown(f'<div style="display:flex; align-items:center; margin-bottom:3px;"><div style="width:12px; height:12px; background-color:{col}; border-radius:2px; margin-right:8px;"></div><span style="font-size:0.8rem; color:#ccc;">{txt}</span></div>', unsafe_allow_html=True)

# --- NAVEGACIÓN (FUERA DEL SIDEBAR) ---
if menu == "📊 DASHBOARD":
    market.render()
elif menu == "📈 ESTRATEGIA SPXL":
    spxl_strategy.render()
elif menu == "🗺️ 2026 ROADMAP":
    roadmap_2026.render()
elif menu == "🇺🇸 TRUMP PLAYBOOK":
    trump_playbook.render()
elif menu == "🤖 RSU ALGORITMO":
    rsu_algoritmo.render()
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



