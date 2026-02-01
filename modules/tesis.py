import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os

def render():
    # 1. REFINAMIENTO ESTÉTICO: CSS para Tarjetas, Imágenes y Badges
    st.markdown("""
        <style>
        /* Contenedor de la tarjeta con efecto Glow */
        .tesis-container {
            border: 1px solid #333;
            border-radius: 15px;
            padding: 20px;
            background-color: #0e1117;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        
        /* Efecto Glow al pasar el ratón sobre la tarjeta */
        .tesis-container:hover {
            border-color: #00ffad;
            box-shadow: 0px 0px 20px rgba(0, 255, 173, 0.4);
            transform: translateY(-5px);
        }

        /* Estilo específico para que la imagen dentro también tenga glow */
        .tesis-container img {
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        
        .tesis-container:hover img {
            box-shadow: 0px 0px 15px rgba(0, 255, 173, 0.6);
        }

        /* Estilo de los Badges de Rating */
        .badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 10px;
        }
        .buy { background-color: rgba(0, 255, 173, 0.15); color: #00ffad; border: 1px solid #00ffad; }
        .hold { background-color: rgba(255, 165, 0, 0.15); color: #ffa500; border: 1px solid #ffa500; }
        .sell { background-color: rgba(255, 75, 75, 0.15); color: #ff4b4b; border: 1px solid #ff4b4b; }
        
        /* Botón personalizado */
        .stButton button {
            background-color: #00ffad !important;
            color: #000 !important;
            font-weight: bold !important;
            border: none !important;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    # Inicializar el estado de navegación
    if 'vista_actual' not in st.session_state:
        st.session_state.vista_actual = "galeria"

    # --- VISTA 1: GALERÍA (No se abre el lector por defecto) ---
    if st.session_state.vista_actual == "galeria":
        st.markdown('<h2 style="color: #00ffad;">📄 Terminal de Análisis</h2>', unsafe_allow_html=True)
        
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

            # Buscador y Filtros (Sugerencia Estructural)
            col_search, col_filtro = st.columns([2, 1])
            with col_search:
                busqueda = st.text_input("🔍 Buscar activo:", "").lower()
            with col_filtro:
                filtro_rating = st.selectbox("Rating:", ["Todos"] + sorted(list(df['rating'].unique())))

            # Filtrado y Orden por fecha reciente
            df_view = df.copy()
            if busqueda:
                df_view = df_view[df_view['ticker'].str.contains(busqueda) | df_view['nombre'].str.contains(busqueda)]
            if filtro_rating != "Todos":
                df_view = df_view[df_view['rating'] == filtro_rating]
            if 'fecha_dt' in df_view.columns:
                df_view = df_view.sort_values(by='fecha_dt', ascending=False)

            st.write("---")
            
            # Grid de tarjetas
            cols = st.columns(3)
            for idx, row in df_view.reset_index(drop=True).iterrows():
                with cols[idx % 3]:
                    # Envolvemos todo en un div con la clase tesis-container para el efecto Glow
                    with st.container():
                        st.markdown('<div class="tesis-container">', unsafe_allow_html=True)
                        
                        # Lógica de Imagen Local
                        ticker_clean = str(row['ticker']).lower().strip()
                        img_path = f"assets/{ticker_clean}.png"
                        
                        if os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/400x225?text=Img+Missing", use_container_width=True)
                        
                        # Badges de Rating dinámicos
                        rt = str(row['rating']).upper()
                        cls = "buy" if "BUY" in rt else "hold" if "HOLD" in rt else "sell"
                        
                        st.markdown(f"<span class='badge {cls}'>{rt}</span>", unsafe_allow_html=True)
                        st.markdown(f"#### {row['ticker']}")
                        st.caption(f"📅 {row.get('fecha', 'S/D')}")
                        
                        # Botón para entrar al lector
                        if st.button(f"Leer Tesis", key=f"btn_{row['ticker']}"):
                            st.session_state.tesis_seleccionada = row['ticker']
                            st.session_state.vista_actual = "lector"
                            st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error cargando terminal: {e}")

    # --- VISTA 2: LECTOR (Solo se activa al elegir una tesis) ---
    elif st.session_state.vista_actual == "lector":
        if st.button("⬅️ Volver a la Galería"):
            st.session_state.vista_actual = "galeria"
            st.rerun()

        # Recarga mínima para obtener la URL del doc
        CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"
        df_doc = pd.read_csv(CSV_URL)
        df_doc.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in df_doc.columns]
        sel_row = df_doc[df_doc['ticker'].str.lower() == st.session_state.tesis_seleccionada.lower()].iloc[0]

        st.markdown(f"## 🔍 Análisis: {sel_row.get('nombre', sel_row['ticker'])}")
        st.write("---")

        url_doc = str(sel_row.get('urldoc', '')).strip()
        # Forzar el modo embedded limpio sin interfaz de Google
        if "/pub" in url_doc:
            url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
        
        components.iframe(url_doc, height=1000, scrolling=True)
