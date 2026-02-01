import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)

    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            # Limpieza de columnas: minúsculas, sin espacios ni guiones
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            return data
            
        df = load_index(CSV_URL)
        columnas = df.columns.tolist()

        # Selector
        sel = st.selectbox("Selecciona un activo:", df['ticker'].unique())
        data = df[df['ticker'] == sel].iloc[0]

        # --- IMAGEN DE ENCABEZADO ---
        # Busca columnas llamadas 'imagen', 'img' o 'header'
        col_img = next((c for c in columnas if c in ['imagen', 'img', 'header']), None)
        if col_img and pd.notna(data[col_img]):
            st.image(data[col_img], use_container_width=True)

        # --- CABECERA DE DATOS ---
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
            st.subheader(data.get('nombre', sel))
            if 'fecha' in columnas:
                st.caption(f"📅 Fecha: {data['fecha']}")
        
        with c2:
            st.metric("Rating", data.get('rating', 'N/A'))
            
        with c3:
            precio = data.get('precioobjetivo', data.get('precio', '---'))
            st.metric("Target", f"${precio}")

        st.divider()

        # --- VISOR DEL DOCUMENTO ---
        url_doc = str(data.get('urldoc', '')).strip()
        if url_doc.startswith("http"):
            components.iframe(url_doc, height=1000, scrolling=True)
        else:
            st.warning("No se detectó el enlace al Google Doc en la columna 'URL_Doc'.")

    except Exception as e:
        st.error(f"Error: {e}")
