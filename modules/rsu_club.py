# modules/rsu_club.py
import streamlit as st

def render():
    st.markdown('<h1 style="margin-top:-50px;">♣️ RSU Elite Club</h1>', unsafe_allow_html=True)
    
    # Contenedor principal
    st.markdown('<div class="group-container">', unsafe_allow_html=True)
    st.markdown('<div class="group-header"><p class="group-title">Beneficios y Herramientas VIP</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="group-content">', unsafe_allow_html=True)
    
    st.write("Bienvenido al círculo interno de RSU. Aquí tienes acceso a recursos avanzados.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏛️ Mentorías")
        st.write("Sesiones grupales semanales de revisión de cartera y análisis de mercado.")
        
    with col2:
        st.markdown("### 🧬 Alpha Signals")
        st.write("Alertas tempranas basadas en flujos institucionales y volumen inusual.")
        
    with col3:
        st.markdown("### 🛠️ Custom Tools")
        st.write("Scripts exclusivos de TradingView y calculadoras de riesgo avanzadas.")
    
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    # Sección de contacto o acceso
    st.success("Estado de suscripción: **ACTIVO (Elite Member)**")