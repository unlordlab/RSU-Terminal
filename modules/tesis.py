import streamlit as st
import pandas as pd

def render():
    # Estilo de título con el color corporativo de tu app
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)
    
    try:
        # Carga de datos desde la URL configurada en secrets
        url = st.secrets["URL_TESIS"]
        df = pd.read_csv(url)
        
        # Selector de activo
        sel = st.selectbox("Selecciona un activo:", df['Ticker'].tolist())
        data = df[df['Ticker'] == sel].iloc[0]

        # --- EXPOSICIÓN DE LA TESIS ---
        
        # 1. Imagen de Encabezado (Debe estar en una columna 'Imagen_URL' en tu Excel)
        if 'Imagen_URL' in data and pd.notna(data['Imagen_URL']):
            st.image(data['Imagen_URL'], use_container_width=True)
        
        # 2. Resumen y Datos Clave
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"Análisis de {data['Nombre']}")
            # Tu breve texto introductorio
            st.markdown(f"*{data['Tesis_Corta']}*") 
        
        with col2:
            # Caja de métricas con el estilo definido en config.py
            st.markdown(f"""
                <div style="background-color: #1a1e26; padding: 15px; border-radius: 10px; border: 1px solid #2962ff;">
                    <h4 style="margin:0; color:#00ffad;">{data['Rating']}</h4>
                    <p style="margin:0; font-size: 20px;">Target: ${data['Precio_Objetivo']}</p>
                </div>
            """, unsafe_allow_html=True)

        st.divider()

        # 3. Cuerpo de la Tesis
        st.markdown(data['Tesis_Completa'])

    except Exception:
        st.info("Configura URL_TESIS en los secrets y asegúrate de que el CSV tenga las columnas correctas.")
