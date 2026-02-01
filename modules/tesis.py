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
            # Normalizamos nombres de columnas: todo a minúsculas, sin espacios, sin guiones bajos
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            return data
            
        df = load_index(CSV_URL)
        
        # Definimos los mapeos normalizados
        # 'precioobjetivo' buscará tanto 'Precio_Objetivo' como 'Precio Objetivo'
        mapeo = {
            'ticker': 'ticker',
            'nombre': 'nombre',
            'rating': 'rating',
            'precioobjetivo': 'precioobjetivo',
            'urldoc': 'urldoc'
        }

        # Verificamos si las versiones normalizadas existen
        columnas_actuales = df.columns.tolist()
        faltantes = [k for k in mapeo.keys() if k not in columnas_actuales]

        if faltantes:
            st.error(f"⚠️ No se reconoce la columna: {', '.join(faltantes)}")
            st.info(f"Columnas detectadas (normalizadas): {', '.join(columnas_actuales)}")
            return

        # Selector
        sel = st.selectbox("Selecciona un activo:", df['ticker'].unique())
        data = df[df['ticker'] == sel].iloc[0]

        # --- CABECERA ---
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.subheader(data['nombre'])
        with c2:
            st.metric("Rating", data['rating'])
        with c3:
            st.metric("Target", f"${data['precioobjetivo']}")

        st.divider()

        # --- VISOR DEL DOCUMENTO ---
        url_doc = str(data['urldoc']).strip()
        if url_doc.startswith("http"):
            components.iframe(url_doc, height=1000, scrolling=True)
        else:
            st.warning("La URL del documento no es válida.")

    except Exception as e:
        st.error(f"Error crítico: {e}")
