# app.py
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# --- IMPORTACION DE CONFIGURACION Y MODULOS ---
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

# CSS Personalizado para sidebar profesional
st.markdown("""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
        border-right: 1px solid #1a1e26;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    
    /* Logo container */
    .logo-container {
        background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
        padding: 20px;
        border-bottom: 1px solid #2a3f5f;
        margin: -1rem -1rem 0 -1rem;
        text-align: center;
    }
    
    /* Live users badge */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0, 255, 173, 0.1);
        border: 1px solid rgba(0, 255, 173, 0.3);
        padding: 6px 12px;
        border-radius: 20px;
        margin-top: 10px;
    }
    
    .live-dot {
        width: 6px;
        height: 6px;
        background: #00ffad;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    
    /* Menu styling */
    .stRadio > div {
        background: transparent !important;
    }
    
    .stRadio > div[role="radiogroup"] > label {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px 12px;
        margin: 2px 0;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .stRadio > div[role="radiogroup"] > label:hover {
        background: rgba(41, 98, 255, 0.1);
        border-color: rgba(41, 98, 255, 0.3);
    }
    
    .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(41, 98, 255, 0.2) 0%, rgba(0, 255, 173, 0.1) 100%);
        border-left: 3px solid #00ffad;
        border-top: 1px solid rgba(0, 255, 173, 0.2);
        border-bottom: 1px solid rgba(0, 255, 173, 0.2);
        border-right: 1px solid rgba(0, 255, 173, 0.2);
    }
    
    /* Fear & Greed container */
    .fng-container {
        background: linear-gradient(180deg, #0c0e12 0%, #11141a 100%);
        border: 1px solid #1a1e26;
        border-radius: 12px;
        padding: 15px;
        margin-top: 15px;
    }
    
    .fng-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    
    .fng-title {
        color: white;
        font-size: 0.85rem;
        font-weight: bold;
        letter-spacing: 0.5px;
    }
    
    .fng-value {
        background: rgba(41, 98, 255, 0.2);
        color: #00ffad;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    
    /* Separator line */
    .sidebar-separator {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #2a3f5f 50%, transparent 100%);
        margin: 15px 0;
        border: none;
    }
    
    /* Section headers */
    .section-header {
        color: #888;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 15px 0 10px 0;
        padding-left: 5px;
    }
    
    /* Status indicator */
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: rgba(242, 54, 69, 0.1);
        border: 1px solid rgba(242, 54, 69, 0.3);
        border-radius: 8px;
        margin-top: 10px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #f23645;
    }
    
    /* Legend grid */
    .legend-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        margin-top: 10px;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 6px;
        background: rgba(255,255,255,0.03);
        border-radius: 4px;
    }
    
    .legend-color {
        width: 10px;
        height: 10px;
        border-radius: 2px;
    }
    
    .legend-text {
        color: #aaa;
        font-size: 0.65rem;
    }
</style>
""", unsafe_allow_html=True)

# Control de acceso
if not auth.login():
    st.stop()

# Inicializamos el motor del algoritmo RS/RW en la sesion
if 'rsrw_engine' not in st.session_state:
    st    st.session_state.rsr    st    st.session_state.rsrw_engine = rsrw.RSRWEngine()
    st.session_state.algoritmo_engine = rsu_algoritmo.RSUAlgoritmo()

# --- SIDEBAR PROFESIONAL ---
with st.sidebar:
    
    # 1. LOGO Y HEADER
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    else:
        # Fallback si no hay logo
        st.markdown("""
            <div style="text-align: center; padding: 10px;">
                <div style="font-size: 2rem; font-weight: bold; color: #00ffad;">RSU</div>
                <div style="font-size: 0.8rem; color: #888; letter-spacing: 3px;">TERMINAL</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Live users badge
    usuarios_activos = actualizar_contador_usuarios()
    st.markdown(f"""
        <div style="text-align: center;">
            <div class="live-badge">
                <div class="live-dot"></div>
                <span style="color: #00ffad; font-size: 0.75rem; font-weight: 600;">{usuarios_activos} USERS ONLINE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. FEAR & GREED INDEX (Compacto y profesional)
    fng = get_cnn_fear_greed()
    
    if fng is not None:
        # Determinar color y estado
        if fng < 25: 
            estado, color, bg_color = "EXTREME FEAR", "#d32f2f", "rgba(211, 47, 47, 0.1)"
            emoji = "🟥"
        elif fng < 45: 
            estado, color, bg_color = "FEAR", "#f57c00", "rgba(245, 124, 0, 0.1)"
            emoji = "🟧"
        elif fng < 55: 
            estado, color, bg_color = "NEUTRAL", "#ff9800", "rgba(255, 152, 0, 0.1)"
            emoji = "🟨"
        elif fng < 75: 
            estado, color, bg_color = "GREED", "#4caf50", "rgba(76, 175, 80, 0.1)"
            emoji = "🟩"
        else: 
            estado, color, bg_color = "EXTREME GREED", "#00ffad", "rgba(0, 255, 173, 0.1)"
            emoji = "🟩"
        
        st.markdown(f"""
            <div class="fng-container">
                <div class="fng-header">
                    <span class="fng-title">📊 FEAR & GREED</span>
                    <span class="fng-value">{fng}</span>
                </div>
        """, unsafe_allow_html=True)
        
        # Gauge minimalista
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = fng,
            number = {'font': {'size': 0}},  # Ocultar numero duplicado
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 0, 'tickcolor': "transparent"},
                'bar': {'color': "rgba(0,0,0,0)"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 25], 'color': "#d32f2f"},
                    {'range': [25, 45], 'color': "#f57c00"},
                    {'range': [45, 55], 'color': "#ff9800"},
                    {'range': [55, 75], 'color': "#4caf50"},
                    {'range': [75, 100], 'color': "#00ffad"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 3},
                    'thickness': 0.85,
                    'value': fng
                }
            }
        ))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=100,
            margin=dict(l=10, r=10, t=5, b=5)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # Estado con badge
        st.markdown(f"""
                <div style="text-align: center; margin-top: 8px;">
                    <div style="display: inline-block; background: {bg_color}; border: 1px solid {color}; padding: 6px 14px; border-radius: 20px;">
                        <span style="color: {color}; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px;">{emoji} {estado}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Leyenda compacta
        st.markdown("""
            <div class="legend-grid">
                <div class="legend-item">
                    <div class="legend-color" style="background: #d32f2f;"></div>
                    <span class="legend-text">Extreme Fear</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: # #f #f57c00;"></div>
                    <span class="legend-text">Fear</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff9800;"></div>
                    <span class="legend-text">Neutral</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #4caf50;"></div>
                    <span class="legend-text">Greed</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span style="color: #f23645; font-size: 0.75rem;">Fear & Greed Offline</span>
            </div>
        """, unsafe_allow_html=True)
    
    # Separador
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    
    # 3. MENU DE NAVEGACION
    st.markdown('<div class="section-header">Navegacion</div>', unsafe_allow_html=True)
    
    menu = st.radio(
        "",
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
        ],
        label_visibility="collapsed"
    )
    
    # Separador final
    st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)
    
    # Footer info
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <div style="color: #444; font-size: 0.65rem; letter-spacing: 1px;">RSU TERMINAL v2.0</div>
            <div style="color: #333; font-size: 0.6rem; margin-top: 4px;">© 2026 All rights reserved</div>
        </div>
    """, unsafe_allow_html=True)

# --- LOGICA DE NAVEGACION ---
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
