# modules/manifest.py
import streamlit as st

def render():
    st.markdown('<h1 style="margin-top:-50px;">Terminal Manifest</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="group-container">', unsafe_allow_html=True)
    st.markdown('<div class="group-header"><p class="group-title">Nuestra Filosofía de Inversión</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="group-content">', unsafe_allow_html=True)
    
    st.info("“El mercado no se mueve por lógica, sino por flujos de capital y fuerza relativa.”")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Objetivo")
        st.write("""
        Esta terminal ha sido diseñada para identificar instituciones acumulando activos 
        mediante el análisis de Fuerza Relativa (RS/RW), permitiéndonos operar a favor 
        de la tendencia mayoritaria.
        """)
        
    with col2:
        st.subheader("🛡️ Disciplina")
        st.write("""
        No predecimos, reaccionamos. La gestión del riesgo y la preservación del capital 
        son los pilares fundamentales que separan a un trader de un apostador.
        """)
        
    st.markdown('</div></div>', unsafe_allow_html=True)