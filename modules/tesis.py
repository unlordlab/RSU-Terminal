import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Galería de Tesis</h2>', unsafe_allow_html=True)

    # URL de tu Sheet publicado como CSV
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            # Normalización total de nombres de columnas
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            
            # Convertir fecha para ordenar (asumiendo formato DD/MM/YYYY)
            if 'fecha' in data.columns:
                data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
            return data
            
        df = load_index(CSV_URL)

        # 1. ORDENAR POR FECHA (Más reciente primero)
        if 'fecha_dt' in df.columns:
            df = df.sort_values(by='fecha_dt', ascending=False)

        # 2. GALERÍA DE MINIATURAS (GRID)
        st.write("---")
        cols = st.columns(3) # Tres miniaturas por fila
        
        for idx, row in df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                # --- PROCESAMIENTO FORZADO DE IMAGEN ---
                img_url = str(row.get('imagen', '')).strip()
                
                # Si es un link de GitHub, forzamos el formato RAW real
                if "github.com" in img_url:
                    img_url = img_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                    if "?raw=true" in img_url:
                        img_url = img_url.replace("?raw=true", "")
                
                # Mostrar imagen con fallback si falla
                try:
                    st.image(img_url, use_container_width=True)
                except:
                    st.image("https://via.placeholder.com/400x225?text=Error+Carga+Imagen", use_container_width=True)
                
                # Información de la Tesis
                st.markdown(f"**{row['ticker']}**")
                st.caption(f"📅 {row.get('fecha', 'S/D')} | Rating: {row.get('rating', 'N/A')}")
                
                # Botón para abrir
                if st.button(f"Abrir Tesis {row['ticker']}", key=f"btn_{row['ticker']}"):
                    st.session_state.tesis_seleccionada = row['ticker']

        # 3. LECTOR DE DOCUMENTO (GOOGLE DOCS MODO LIMPIO)
        if 'tesis_seleccionada' in st.session_state:
            st.write("---")
            sel_row = df[df['ticker'] == st.session_state.tesis_seleccionada].iloc[0]
            
            st.subheader(f"🔍 Analizando: {sel_row.get('nombre', sel_row['ticker'])}")
            
            url_doc = str(sel_row.get('urldoc', '')).strip()
            if url_doc.startswith("http"):
                # Transformamos el link para que sea un volcado limpio sin interfaz de edición
                if "/pub" in url_doc:
                    # Forzamos parámetro embedded
                    sep = "&" if "?" in url_doc else "?"
                    if "embedded=true" not in url_doc:
                        url_doc += f"{sep}embedded=true"
                
                # Iframe que respeta imágenes y tablas del Word/Doc original
                components.iframe(url_doc, height=1000, scrolling=True)
            else:
                st.warning("Enlace de documento no válido.")

    except Exception as e:
        st.error(f"Error en Galería: {e}")
