import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Tesis de Inversión</h2>', unsafe_allow_html=True)

    # URL de tu índice CSV
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            # Normalización de columnas para evitar errores de escritura
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            return data
            
        df = load_index(CSV_URL)
        columnas = df.columns.tolist()

        # Selector de activo
        sel = st.selectbox("Selecciona un activo:", df['ticker'].unique())
        # Limpiamos los datos de la fila seleccionada
        data = df[df['ticker'] == sel].iloc[0]

        # --- GESTIÓN DE LA IMAGEN DE CABECERA ---
        # Buscamos la columna de imagen (imagen, img, o header)
        col_img = next((c for c in columnas if c in ['imagen', 'img', 'header']), None)
        
        if col_img and pd.notna(data[col_img]):
            raw_img_url = str(data[col_img]).strip()
            # Forzar el formato raw si es de github (por si se te olvida cambiarlo en el Excel)
            if "github.com" in raw_img_url and "/blob/" in raw_img_url:
                raw_img_url = raw_img_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
            st.image(raw_img_url, use_container_width=True)

        # --- CABECERA DE DATOS (Rating, Target, Fecha) ---
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
            st.markdown(f"<h1 style='margin:0;'>{data.get('nombre', sel)}</h1>", unsafe_allow_html=True)
            if 'fecha' in columnas:
                st.caption(f"📅 {data['fecha']}")
        
        with c2:
            st.metric("Rating", str(data.get('rating', 'N/A')).upper())
            
        with c3:
            precio = data.get('precioobjetivo', data.get('precio', '---'))
            st.metric("Target", f"${precio}")

        st.divider()

        # --- VISOR DEL DOCUMENTO (GOOGLE DOCS) ---
        url_doc = str(data.get('urldoc', '')).strip()
        
        if url_doc.startswith("http"):
            # Si el link no termina en /pub, lo intentamos limpiar para modo lectura
            if "/edit" in url_doc:
                url_doc = url_doc.split("/edit")[0] + "/pub?embedded=true"
            
            components.iframe(url_doc, height=1000, scrolling=True)
        else:
            st.warning("⚠️ No se ha configurado el enlace 'URL_Doc' para este activo.")

    except Exception as e:
        st.error(f"Error en la sección de tesis: {e}")
