import streamlit as st

def render():
    st.title("⚡ EMA Edge System")
    st.markdown('<div class="group-container">', unsafe_allow_html=True)
    st.markdown('<div class="group-header"><p class="group-title">Estrategia de Medias Móviles Exponenciales</p></div>', unsafe_allow_html=True)
    st.write("Análisis de convergencia y divergencia de EMAs rápidas para entradas en tendencia.")
    st.markdown('</div>', unsafe_allow_html=True)