import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render():
    st.markdown('<h2 style="color: #00ffad;">📄 Galería de Tesis</h2>', unsafe_allow_html=True)

    # URL de tu Sheet CSV
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            # Normalización: minúsculas y quitar espacios/guiones en nombres de columnas
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            
            # Convertir fecha para poder ordenar (DD/MM/YYYY)
            if 'fecha' in data.columns:
                data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
            return data
            
        df = load_index(CSV_URL)

        # 1. ORDENAR POR FECHA (Más reciente arriba)
        if 'fecha_dt' in df.columns:
            df = df.sort_values(by='fecha_dt', ascending=False)

        # 2. INTERFAZ DE GALERÍA (MINIATURAS)
        st.write("---")
        
        # Creamos una cuadrícula de 3 columnas
        cols = st.columns(3)
        
        for idx, row in df.reset_index(drop=True).iterrows():
            with cols[idx % 3]:
                # --- PROCESAMIENTO DE IMAGEN ---
                img_url = str(row.get('imagen', '')).strip()
                
                # Si es un enlace de GitHub normal, lo convertimos a RAW
                if "github.com" in img_url and "/blob/" in img_url:
                    img_url = img_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                
                # Si pusiste una ruta relativa como /assets/plab.png, la convertimos a URL completa de tu repo
                elif img_url.startswith("/assets/") or img_url.startswith("assets/"):
                    ruta = img_url.lstrip("/")
                    img_url = f"https://raw.githubusercontent.com/unlordlab/RSU-Terminal/main/{ruta}"

                # Mostrar miniatura con estilo
                st.image(img_url if img_url.startswith("http") else "https://via.placeholder.com/400x225?text=Sin+Imagen", use_container_width=True)
                
                st.markdown(f"**{row['ticker']}** - {row.get('nombre', '')}")
                st.caption(f"📅 {row.get('fecha', 'S/F')} | {row.get('rating', 'N/A')}")
                
                # Botón para seleccionar tesis
                if st.button(f"Leer Tesis {row['ticker']}", key=f"btn_{row['ticker']}"):
                    st.session_state.tesis_activa = row['ticker']

        # 3. LECTOR DE DOCUMENTO (GOOGLE DOCS)
        if 'tesis_activa' in st.session_state:
            st.write("---")
            selected = df[df['ticker'] == st.session_state.tesis_activa].iloc[0]
            
            st.subheader(f"🔍 Tesis: {selected.get('nombre', selected['ticker'])}")
            
            url_doc = str(selected.get('urldoc', '')).strip()
            
            if url_doc.startswith("http"):
                # Forzar el modo embebido de Google Docs para que no pida permisos ni muestre menús
                if "/pub" in url_doc:
                    if "embedded=true" not in url_doc:
                        url_doc += "&embedded=true" if "?" in url_doc else "?embedded=true"
                
                # Iframe de alta fidelidad (respeta imágenes del Word)
                components.iframe(url_doc, height=900, scrolling=True)
            else:
                st.warning("Enlace al documento no disponible.")

    except Exception as e:
        st.error(f"Error al cargar la galería: {e}")
