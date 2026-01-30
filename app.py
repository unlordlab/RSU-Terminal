
# app.py
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math  # Import necesario para el cálculo de la aguja

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

# --- SIDEBAR con Fear & Greed + LEYENDA LIMPIA ---
with st.sidebar:
    # Logo
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=150)

    # Menú principal
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

    # TÍTULO GRANDE Fear & Greed
    st.markdown('<h3 style="color:white;text-align:center;margin-bottom:5px;">FEAR & GREED</h3>', unsafe_allow_html=True)

    # --- LÓGICA DEL GRÁFICO CON AGUJA ---
    fng = get_cnn_fear_greed()
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fng,
        number={"font": {"size": 24, "color": "white"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "rgba(0,0,0,0)"}, # Hacemos la barra azul invisible
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

    # Cálculo de la posición de la aguja
    # El gauge de Plotly va de 180 grados (valor 0) a 0 grados (valor 100)
    theta = 180 - (fng / 100) * 180
    r = 0.85 # Longitud de la aguja
    x_head = r * math.cos(math.radians(theta))
    y_head = r * math.sin(math.radians(theta))

    # Añadir la aguja (línea blanca)
    fig.add_shape(
        type='line',
        x0=0.5, y0=0.15, # Centro base
        x1=0.5 + x_head/2.2, y1=0.15 + y_head/1.2, # Ajuste de escala
        line=dict(color='white', width=4),
        xref='paper', yref='paper'
    )

    # Añadir el eje central (círculo blanco)
    fig.add_shape(
        type='circle',
        x0=0.48, y0=0.12, x1=0.52, y1=0.18,
        fillcolor='white', line_color='white',
        xref='paper', yref='paper'
    )

    fig.update_layout(
        height=180,
        margin=dict(l=15, r=15, t=5, b=25),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "white"}
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ESTADO ACTUAL
    if fng < 25:
        estado = "🟥 Extreme Fear"
        color = "#d32f2f"
    elif fng < 45:
        estado = "🟧 Fear"
        color = "#f57c00"
    elif fng < 55:
        estado = "🟡 Neutral"
        color = "#ff9800"
    elif fng < 75:
        estado = "🟩 Greed"
        color = "#4caf50"
    else:
        estado = "🟩 Extreme Greed"
        color = "#00ffad"

    st.markdown(f'<div style="text-align:center;padding:8px;"><h4 style="color:{color};margin:0;">{estado}</h4></div>', unsafe_allow_html=True)

    # LEYENDA LIMPIA (una columna, mejor espaciado)
    st.markdown("**Legend:**", help="")
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
            f'<div style="width:12px; height:12px; background-color:{col}; border-radius:2px; margin-right:8px;"></div>'
            f'<span style="font-size:0.8rem; color:#ccc;">{txt}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

# --- ENRUTAMIENTO DE PÁGINAS ---
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
