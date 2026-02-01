import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Galería de Tesis</h2>', unsafe_allow_html=True)

    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            if 'fecha' in data.columns:
                data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
            return data
            
        df = load_index(CSV_URL)

        if 'fecha_dt' in df.columns:
            df = df.sort_values(by='fecha_dt', ascending=False)

        st.write("---")
        cols = st.columns(3)
        
        for idx, row in df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                # --- SOLUCIÓN LOCAL PARA IMÁGENES ---
                # Buscamos el archivo directamente en tu carpeta assets del repo
                ticker_lower = str(row['ticker']).lower()
                img_path = f"assets/{ticker_lower}.png"
                
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    # Si no existe el .png local, intentamos la URL del Excel
                    img_url = str(row.get('imagen', '')).strip()
                    if "github.com" in img_url:
                        img_url = img_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                        img_url = img_url.split("?")[0]
                    st.image(img_url if len(img_url) > 10 else "https://via.placeholder.com/400x225?text=Subir+PNG", use_container_width=True)
                
                st.markdown(f"**{row['ticker']}**")
                st.caption(f"📅 {row.get('fecha', 'S/D')} | {row.get('rating', 'N/A')}")
                
                if st.button(f"Leer Tesis", key=f"btn_{row['ticker']}"):
                    st.session_state.tesis_seleccionada = row['ticker']

        # --- LECTOR DE GOOGLE DOCS (MODO LIMPIO) ---
        if 'tesis_seleccionada' in st.session_state:
            st.write("---")
            sel_row = df[df['ticker'] == st.session_state.tesis_seleccionada].iloc[0]
            
            # Limpieza del Link de Google Docs para quitar "Solicitar permiso"
            url_doc = str(sel_row.get('urldoc', '')).strip()
            if "/pub" in url_doc:
                # Forzamos la vista de publicación pura
                url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
            
            st.subheader(f"🔍 Tesis: {sel_row.get('nombre', sel_row['ticker'])}")
            components.iframe(url_doc, height=1000, scrolling=True)

    except Exception as e:
        st.error(f"Error: {e}")
