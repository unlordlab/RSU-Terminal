import streamlit as st
import pandas as pd

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)
    
    # Intentar cargar la URL desde secrets
    try:
        url = st.secrets["URL_TESIS"]
        # Limpiamos caché cada 10 min para ver actualizaciones del Sheet
        @st.cache_data(ttl=600)
        def load_data(url):
            data = pd.read_csv(url)
            # Limpiar espacios en blanco en los nombres de columnas y tickers
            data.columns = data.columns.str.strip()
            data['Ticker'] = data['Ticker'].str.strip()
            return data

        df = load_data(url)
        
        # Selector de Activo
        ticker_list = df['Ticker'].tolist()
        sel = st.selectbox("Selecciona un Activo para ver la Tesis:", ticker_list)
        
        # Filtrado de datos
        data = df[df['Ticker'] == sel].iloc[0]

        # --- DISEÑO DE LA PÁGINA ---
        col_main, col_side = st.columns([2, 1])

        with col_main:
            st.markdown(f"### {data['Nombre']}")
            st.markdown(f"**Resumen:** {data['Tesis_Corta']}")
            st.divider()
            st.markdown("#### 🔍 Análisis Detallado")
            st.markdown(data['Tesis_Completa'])

        with col_side:
            st.markdown("""<div style="background-color:#1a1e26; padding:15px; border-radius:10px; border:1px solid #2962ff;">""", unsafe_allow_html=True)
            st.metric("Rating", data['Rating'])
            st.metric("Target Price", f"${data['Precio_Objetivo']}")
            st.write(f"**Sector:** {data['Sector']}")
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error("No se pudo conectar con la base de datos de tesis.")
        st.info("Verifica que la URL en Secrets sea el enlace de 'Publicar como CSV' de Google Sheets.")
