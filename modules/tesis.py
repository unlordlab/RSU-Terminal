import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)

    try:
        # Cargamos el índice (el Sheet con los links a los Docs)
        url_indice = st.secrets["URL_TESIS"]
        df = pd.read_csv(url_indice)
        
        sel = st.selectbox("Selecciona un activo:", df['Ticker'].tolist())
        data = df[df['Ticker'] == sel].iloc[0]

        # 1. Imagen de Encabezado (Opcional, si no está ya en el Doc)
        if pd.notna(data['Imagen_Encabezado']):
            st.image(data['Imagen_Encabezado'], use_container_width=True)

        # 2. Datos Rápidos
        st.markdown(f"### {data['Nombre']} | Rating: {data['Rating']}")
        st.divider()

        # 3. Mostrar el Google Doc (iframe)
        # Ajustamos la altura (height) para que sea cómodo de leer
        components.iframe(data['URL_Doc'], height=800, scrolling=True)

    except Exception as e:
        st.error("Error al cargar el índice de tesis.")
