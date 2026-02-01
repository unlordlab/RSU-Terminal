import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)

    try:
        # 1. Cargar el índice desde tus secrets
        url_indice = st.secrets["URL_TESIS"]
        
        @st.cache_data(ttl=600)
        def load_index(url):
            return pd.read_csv(url)
            
        df = load_index(url_indice)
        
        # 2. Selector de Activo
        sel = st.selectbox("Selecciona un activo para ver el análisis:", df['Ticker'].tolist())
        data = df[df['Ticker'] == sel].iloc[0]

        # 3. Encabezado rápido (Rating y Target)
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### {data['Nombre']}")
        with col2:
            st.metric("Rating", data['Rating'])
        with col3:
            st.metric("Target", f"${data['Precio_Objetivo']}")

        st.divider()

        # 4. Mostrar el Google Doc
        # Usamos la URL que pasaste (la de /pub)
        url_doc = data['URL_Doc']
        
        # El componente iframe permite insertar el documento directamente
        components.iframe(url_doc, height=900, scrolling=True)

    except Exception as e:
        st.warning("⚠️ Configura el índice de tesis correctamente.")
        st.info("Asegúrate de que tu Google Sheet tenga una columna llamada 'URL_Doc' con el enlace que me acabas de pasar.")
