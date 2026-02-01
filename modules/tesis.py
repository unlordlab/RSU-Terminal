import streamlit as st
import pandas as pd

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)
    
    try:
        # Carga de datos
        df = pd.read_csv(st.secrets["URL_TESIS"])
        
        # Filtros superiores
        col_selector, col_info = st.columns([1, 2])
        
        with col_selector:
            ticker_list = df['Ticker'].tolist()
            sel = st.selectbox("Selecciona un Activo:", ticker_list)
            
        # Extraer datos del activo seleccionado
        data = df[df['Ticker'] == sel].iloc[0]
        
        # --- UI DE LA TESIS ---
        st.markdown("---")
        
        # Fila de Métricas Clave
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Activo", data['Ticker'])
        m2.metric("Sector", data.get('Sector', 'N/A'))
        m3.metric("Rating", data.get('Rating', 'Análisis'), delta_color="normal")
        m4.metric("Target", data.get('Precio_Objetivo', '---'))

        # Resumen Ejecutivo (Caja destacada)
        st.markdown(f"""
            <div style="background-color: #1a1e26; padding: 20px; border-left: 5px solid #2962ff; border-radius: 5px;">
                <h4 style="margin-top:0;">Resumen Ejecutivo</h4>
                <p style="color: #ccc; font-style: italic;">{data['Tesis_Corta']}</p>
            </div>
        """, unsafe_allow_html=True)

        # Cuerpo de la Tesis
        st.markdown("### 🔍 Análisis Profundo")
        if 'Tesis_Completa' in data:
            # Esto permite usar negritas, listas y saltos de línea del CSV
            st.markdown(data['Tesis_Completa'])
        else:
            st.info("Análisis detallado en proceso...")

    except Exception as e:
        st.error(f"Error al cargar las tesis: {e}")
        st.info("Asegúrate de que URL_TESIS en secrets sea un CSV público.")
