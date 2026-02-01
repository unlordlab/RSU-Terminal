import streamlit as st
import pandas as pd

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)
    
    try:
        # Cargamos el CSV desde la URL de tus secrets
        url = st.secrets["URL_TESIS"]
        
        @st.cache_data(ttl=600)
        def load_tesis(url):
            return pd.read_csv(url)
            
        df = load_tesis(url)
        
        # Selector de Tesis
        sel = st.selectbox("Selecciona un activo para analizar:", df['Ticker'].tolist())
        data = df[df['Ticker'] == sel].iloc[0]

        # --- EXPOSICIÓN DE LA TESIS ---
        
        # 1. Imagen de Encabezado
        if pd.notna(data['Imagen_URL']):
            st.image(data['Imagen_URL'], use_container_width=True)
        
        # 2. Resumen Ejecutivo
        col_txt, col_met = st.columns([2, 1])
        with col_txt:
            st.markdown(f"### {data['Nombre']} ({data['Ticker']})")
            st.info(data['Tesis_Corta'])
            
        with col_met:
            st.markdown(f"""
                <div style="background-color:#1a1e26; padding:15px; border-radius:10px; border:1px solid #2962ff; text-align:center;">
                    <p style="margin:0; color:#888;">RATING</p>
                    <h3 style="margin:0; color:#00ffad;">{data['Rating']}</h3>
                    <hr style="border:0.5px solid #2d3439;">
                    <p style="margin:0; color:#888;">TARGET</p>
                    <h3 style="margin:0; color:white;">${data['Precio_Objetivo']}</h3>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        # 3. Cuerpo del Análisis (Markdown nativo)
        st.markdown(data['Tesis_Completa'])

    except Exception as e:
        st.warning("⚠️ Error al cargar las tesis. Revisa la URL y las columnas del Google Sheet.")
        st.error(f"Detalle: {e}")
