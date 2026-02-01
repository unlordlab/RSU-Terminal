import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Galería de Tesis</h2>', unsafe_allow_html=True)

    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            # Convertir fecha a objeto datetime para ordenar
            if 'fecha' in data.columns:
                data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
            return data
            
        df = load_index(CSV_URL)

        # 1. ORDENAR POR FECHA (Más reciente primero)
        if 'fecha_dt' in df.columns:
            df = df.sort_values(by='fecha_dt', ascending=False)

        # 2. VISUALIZACIÓN DE MINIATURAS (GRID)
        st.markdown("### Tesis Disponibles")
        
        # Crear filas de 3 columnas para las miniaturas
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                # Procesar imagen de GitHub
                img_url = str(row.get('imagen', '')).strip()
                if "github.com" in img_url and "/blob/" in img_url:
                    img_url = img_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                
                # Card de la tesis
                st.image(img_url if img_url.startswith("http") else "https://via.placeholder.com/300x150?text=Sin+Imagen", use_container_width=True)
                st.markdown(f"**{row['ticker']}** - {row.get('nombre', '')}")
                st.caption(f"📅 {row.get('fecha', 'S/D')} | Rating: {row.get('rating', 'N/A')}")
                
                # Botón para abrir esta tesis
                if st.button(f"Ver Tesis {row['ticker']}", key=f"btn_{row['ticker']}"):
                    st.session_state.tesis_seleccionada = row['ticker']

        # 3. LECTOR DE DOCUMENTO (Se activa al elegir una)
        if 'tesis_seleccionada' in st.session_state:
            st.divider()
            tesis_data = df[df['ticker'] == st.session_state.tesis_seleccionada].iloc[0]
            
            st.markdown(f"## 🔍 Analizando: {tesis_data['nombre']}")
            
            url_doc = str(tesis_data.get('urldoc', '')).strip()
            if url_doc.startswith("http"):
                # Forzar modo visualización limpia de Google Docs
                if "/edit" in url_doc:
                    url_doc = url_doc.split("/edit")[0] + "/pub?embedded=true"
                
                components.iframe(url_doc, height=1200, scrolling=True)

    except Exception as e:
        st.error(f"Error en la galería: {e}")
