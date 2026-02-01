import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)

    # Tu URL de publicación CSV
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            # Leemos el CSV
            data = pd.read_csv(url)
            # LIMPIEZA CRÍTICA: Quitamos espacios vacíos al principio/final de los nombres de columnas
            data.columns = [col.strip() for col in data.columns]
            return data
            
        df = load_index(CSV_URL)
        
        # Validar si las columnas necesarias existen (Case Sensitive)
        columnas_requeridas = ['Ticker', 'Nombre', 'Rating', 'Precio_Objetivo', 'URL_Doc']
        columnas_actuales = df.columns.tolist()
        
        faltantes = [c for c in columnas_requeridas if c not in columnas_actuales]
        
        if faltantes:
            st.error(f"⚠️ Faltan columnas en tu Excel: {', '.join(faltantes)}")
            st.info(f"Columnas detectadas actualmente: {', '.join(columnas_actuales)}")
            return

        # Selector
        sel = st.selectbox("Selecciona un activo:", df['Ticker'].unique())
        data = df[df['Ticker'] == sel].iloc[0]

        # --- CABECERA ---
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.subheader(data['Nombre'])
        with c2:
            st.metric("Rating", data['Rating'])
        with c3:
            st.metric("Target", f"${data['Precio_Objetivo']}")

        st.divider()

        # --- VISOR DEL DOCUMENTO ---
        url_doc = str(data['URL_Doc']).strip()
        if url_doc.startswith("http"):
            components.iframe(url_doc, height=1000, scrolling=True)
        else:
            st.warning("La URL del documento no es válida.")

    except Exception as e:
        st.error(f"Error crítico al cargar el índice: {e}")
