import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os

def render():
    # 1. ESTILOS CSS AVANZADOS (Efecto Glow en tarjetas e imágenes)
    st.markdown("""
        <style>
        /* Contenedor principal de la tarjeta */
        .tesis-card {
            background-color: #0e1117;
            border: 1px solid #333;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 25px;
            transition: all 0.4s ease-in-out;
            text-align: left;
        }
        
        /* Efecto Glow al pasar el ratón (Hover) */
        .tesis-card:hover {
            border-color: #00ffad;
            box-shadow: 0px 0px 25px rgba(0, 255, 173, 0.5);
            transform: translateY(-8px);
        }

        /* Glow específico para la imagen interna */
        .tesis-card img {
            border-radius: 10px;
            margin-bottom: 15px;
            transition: box-shadow 0.4s ease;
        }
        .tesis-card:hover img {
            box-shadow: 0px 0px 15px rgba(0, 255, 173, 0.7);
        }

        /* Estilo de los Badges de Rating */
        .rating-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .buy { background-color: rgba(0, 255, 173, 0.2); color: #00ffad; border: 1px solid #00ffad; }
        .hold { background-color: rgba(255, 165, 0, 0.2); color: #ffa500; border: 1px solid #ffa500; }
        .sell { background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; border: 1px solid #ff4b4b; }
        </style>
    """, unsafe_allow_html=True)

    # Inicializar el control de navegación
    if 'vista' not in st.session_state:
        st.session_state.vista = "galeria"

    # --- VISTA 1: GALERÍA ---
    if st.session_state.vista == "galeria":
        st.markdown('<h2 style="color: #00ffad;">🔍 Terminal de Análisis</h2>', unsafe_allow_html=True)
        
        CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

        try:
            @st.cache_data(ttl=60)
            def load_data(url):
                data = pd.read_csv(url)
                data.columns = [c.strip().lower().replace(" ", "").replace("_", "") for c in data.columns]
                if 'fecha' in data.columns:
                    data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
                return data

            df = load_data(CSV_URL)

            # Buscador y Filtro (Sugerencias Estructurales)
            c1, c2 = st.columns([2, 1])
            with c1: busqueda = st.text_input("Buscar activo:", "").lower()
            with c2: filtro = st.selectbox("Rating:", ["Todos"] + sorted(list(df['rating'].unique())))

            # Filtrado
            df_view = df.copy()
            if busqueda: df_view = df_view[df_view['ticker'].str.contains(busqueda) | df_view['nombre'].str.contains(busqueda)]
            if filtro != "Todos": df_view = df_view[df_view['rating'] == filtro]
            if 'fecha_dt' in df_view.columns: df_view = df_view.sort_values(by='fecha_dt', ascending=False)

            st.write("---")
            
            # Grid de tarjetas con efecto Glow
            cols = st.columns(3)
            for idx, row in df_view.reset_index(drop=True).iterrows():
                with cols[idx % 3]:
                    # Contenedor HTML para aplicar los estilos CSS personalizados
                    st.markdown(f'<div class="tesis-card">', unsafe_allow_html=True)
                    
                    # Imagen Local (assets/)
                    t_clean = str(row['ticker']).lower().strip()
                    img_file = f"assets/{t_clean}.png"
                    if os.path.exists(img_file):
                        st.image(img_file, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/400x225?text=Sin+Imagen", use_container_width=True)
                    
                    # Badge de Rating y Datos
                    rt = str(row['rating']).upper()
                    cls = "buy" if "BUY" in rt else "hold" if "HOLD" in rt else "sell"
                    st.markdown(f'<span class="rating-badge {cls}">{rt}</span>', unsafe_allow_html=True)
                    st.markdown(f"**{row['ticker']}**")
                    st.caption(f"📅 {row.get('fecha', 'S/D')}")
                    
                    # Botón para cambiar de vista
                    if st.button(f"Leer Tesis", key=f"btn_{row['ticker']}", use_container_width=True):
                        st.session_state.tesis_activa = row['ticker']
                        st.session_state.vista = "lector"
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error cargando datos: {e}")

    # --- VISTA 2: LECTOR ---
    elif st.session_state.vista == "lector":
        if st.button("⬅️ Volver a la Terminal"):
            st.session_state.vista = "galeria"
            st.rerun()

        # Recargar el link del doc para la tesis seleccionada
        CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"
        df_docs = pd.read_csv(CSV_URL)
        df_docs.columns = [c.strip().lower().replace(" ", "").replace("_", "") for c in df_docs.columns]
        sel = df_docs[df_docs['ticker'].str.lower() == st.session_state.tesis_activa.lower()].iloc[0]

        st.markdown(f"## 🔍 Análisis: {sel.get('nombre', sel['ticker'])}")
        st.write("---")

        url = str(sel.get('urldoc', '')).strip()
        # Forzar modo publicación pura para evitar botones de edición
        if "/pub" in url:
            url = url.split("?")[0].split("&")[0] + "?embedded=true"
        
        with st.spinner("Sincronizando con el servidor de análisis..."):
            components.iframe(url, height=1000, scrolling=True)
