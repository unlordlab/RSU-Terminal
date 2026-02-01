import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Galería de Tesis</h2>', unsafe_allow_html=True)

    # URL del Google Sheet (CSV)
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            # Normalización de columnas
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            if 'fecha' in data.columns:
                data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
            return data
            
        df = load_index(CSV_URL)

        # 1. ORDENAR POR FECHA
        if 'fecha_dt' in df.columns:
            df = df.sort_values(by='fecha_dt', ascending=False)

        # 2. GALERÍA DE MINIATURAS
        st.write("---")
        cols = st.columns(3)
        
        for idx, row in df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                # --- LÓGICA DE IMAGEN REFORZADA ---
                img_val = str(row.get('imagen', '')).strip()
                
                if not img_val or img_val == 'nan':
                    img_url = "https://via.placeholder.com/400x225?text=Sin+Imagen"
                else:
                    # Si es GitHub, transformamos al dominio RAW directamente
                    if "github.com" in img_val:
                        # Convertimos: github.com/.../blob/main/assets/cohr.png?raw=true
                        # A: raw.githubusercontent.com/.../main/assets/cohr.png
                        path = img_val.replace("https://github.com/", "").replace("/blob/", "/")
                        path = path.split("?")[0] # Quitamos el ?raw=true
                        img_url = f"https://raw.githubusercontent.com/{path}"
                    else:
                        img_url = img_val

                # Mostramos la imagen con un contenedor de seguridad
                st.image(img_url, use_container_width=True)
                
                st.markdown(f"**{row['ticker']}**")
                st.caption(f"📅 {row.get('fecha', 'S/D')} | {row.get('rating', 'N/A')}")
                
                if st.button(f"Ver Tesis {row['ticker']}", key=f"btn_{row['ticker']}"):
                    st.session_state.tesis_seleccionada = row['ticker']

        # 3. LECTOR DE DOCUMENTO (GOOGLE DOCS)
        if 'tesis_seleccionada' in st.session_state:
            st.write("---")
            sel_row = df[df['ticker'] == st.session_state.tesis_seleccionada].iloc[0]
            
            st.subheader(f"🔍 Tesis: {sel_row.get('nombre', sel_row['ticker'])}")
            
            url_doc = str(sel_row.get('urldoc', '')).strip()
            if url_doc.startswith("http"):
                # Limpieza de link de Google Docs para quitar barras de herramientas
                if "/pub" in url_doc:
                    url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
                
                components.iframe(url_doc, height=1000, scrolling=True)

    except Exception as e:
        st.error(f"Error crítico en galería: {e}")
