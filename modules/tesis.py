import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Galería de Tesis</h2>', unsafe_allow_html=True)

    # Tu URL del Sheet CSV
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            # Limpiamos nombres de columnas: minúsculas y sin espacios
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            
            # Convertimos la columna 'fecha' a formato fecha real para poder ordenar
            if 'fecha' in data.columns:
                data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
            return data
            
        df = load_index(CSV_URL)

        # 1. ORDENAR POR FECHA (Lo más nuevo primero)
        if 'fecha_dt' in df.columns:
            df = df.sort_values(by='fecha_dt', ascending=False)

        # 2. RENDERIZAR GALERÍA DE MINIATURAS
        st.write("---")
        
        # Creamos una cuadrícula de 3 columnas para las "cards"
        cols = st.columns(3)
        
        for idx, row in df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                # Usar la URL de imagen que tienes en el Excel
                img_url = str(row.get('imagen', '')).strip()
                
                # Mostrar miniatura
                if img_url.startswith("http"):
                    st.image(img_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/400x225?text=Imagen+No+Encontrada", use_container_width=True)
                
                # Info de la Card
                st.markdown(f"### {row['ticker']}")
                st.markdown(f"**{row.get('nombre', '')}**")
                st.caption(f"📅 {row.get('fecha', 'S/F')} | Rating: {row.get('rating', 'N/A')}")
                
                # Botón para activar el lector
                if st.button(f"Abrir Tesis {row['ticker']}", key=f"btn_{row['ticker']}"):
                    st.session_state.tesis_seleccionada = row['ticker']

        # 3. LECTOR DE GOOGLE DOCS (Aparece al hacer clic)
        if 'tesis_seleccionada' in st.session_state:
            st.write("---")
            seleccion = df[df['ticker'] == st.session_state.tesis_seleccionada].iloc[0]
            
            st.subheader(f"🔍 Análisis Detallado: {seleccion.get('nombre', seleccion['ticker'])}")
            
            url_doc = str(seleccion.get('urldoc', '')).strip()
            
            if url_doc.startswith("http"):
                # Limpiar link de Google Docs para modo embebido
                if "/pub" in url_doc:
                    if "embedded=true" not in url_doc:
                        url_doc += "&embedded=true" if "?" in url_doc else "?embedded=true"
                
                # El iframe respeta el 100% de tu diseño en el Word original
                components.iframe(url_doc, height=1000, scrolling=True)
            else:
                st.warning("No se encontró el enlace del documento para este activo.")

    except Exception as e:
        st.error(f"Error al cargar la galería: {e}")
