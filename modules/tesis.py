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
            # Limpieza total: minúsculas, sin espacios, sin guiones
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            return data
            
        df = load_index(CSV_URL)
        
        # Mapeo de columnas necesarias (normalizadas)
        # Buscamos 'precioobjetivo' y 'fecha'
        columnas_actuales = df.columns.tolist()

        # Validación de columnas críticas
        if 'ticker' not in columnas_actuales or 'urldoc' not in columnas_actuales:
            st.error("⚠️ No se encuentran las columnas básicas 'Ticker' y 'URL_Doc'.")
            st.info(f"Columnas detectadas: {columnas_actuales}")
            return

        # Selector
        sel = st.selectbox("Selecciona un activo:", df['ticker'].unique())
        data = df[df['ticker'] == sel].iloc[0]

        # --- CABECERA ---
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        
        with c1:
            nombre = data.get('nombre', sel)
            st.subheader(nombre)
            # Mostrar fecha si existe la columna
            if 'fecha' in columnas_actuales:
                st.caption(f"Publicado el: {data['fecha']}")
        
        with c2:
            rating = data.get('rating', 'N/A')
            st.metric("Rating", rating)
            
        with c3:
            # Buscamos precioobjetivo o precio
            precio = data.get('precioobjetivo', data.get('precio', '---'))
            st.metric("Target", f"${precio}")

        with c4:
            # Añadimos el Ticker en grande para confirmar
            st.metric("Ticker", sel)

        st.divider()

        # --- VISOR DEL DOCUMENTO ---
        url_doc = str(data['urldoc']).strip()
        if url_doc.startswith("http"):
            # Aumentamos un poco el alto para mejorar la lectura
            components.iframe(url_doc, height=1000, scrolling=True)
        else:
            st.warning("La URL del documento no es válida en la columna 'URL_Doc'.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
