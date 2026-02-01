import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os

def render():
    # 1. REFINAMIENTO ESTÉTICO (CSS Inyectado)
    st.markdown("""
        <style>
        /* Estilo de la tarjeta con efecto Glow al pasar el ratón */
        .stButton button {
            width: 100%;
            background-color: #1a1c23;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 0px;
            height: auto;
        }
        .stButton button:hover {
            border-color: #00ffad !format;
            box-shadow: 0px 0px 15px rgba(0, 255, 173, 0.3);
            transform: translateY(-3px);
            transition: all 0.3s ease;
        }
        /* Badges de Rating */
        .badge {
            padding: 4px 8px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .buy { background-color: rgba(0, 255, 173, 0.2); color: #00ffad; border: 1px solid #00ffad; }
        .hold { background-color: rgba(255, 165, 0, 0.2); color: #ffa500; border: 1px solid #ffa500; }
        .sell { background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; border: 1px solid #ff4b4b; }
        </style>
    """, unsafe_allow_html=True)

    # Inicializar estado de navegación si no existe
    if 'vista_actual' not in st.session_state:
        st.session_state.vista_actual = "galeria"

    # --- LÓGICA DE NAVEGACIÓN ---

    # VISTA 1: GALERÍA (Solo se muestra si no hay una tesis abierta)
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

            # Buscador y Filtros
            col_search, col_filtro = st.columns([2, 1])
            with col_search:
                busqueda = st.text_input("🔍 Buscar activo:", "").lower()
            with col_filtro:
                filtro_rating = st.selectbox("Rating:", ["Todos"] + list(df['rating'].unique()))

            # Filtrado y Orden
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
                    # Contenedor visual de la tarjeta
                    ticker_clean = str(row['ticker']).lower().strip()
                    img_path = f"assets/{ticker_clean}.png"
                    
                    # Imagen con fallback
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/400x225?text=Img+Missing", use_container_width=True)
                    
                    # Rating Badge
                    rt = str(row['rating']).upper()
                    cls = "buy" if "BUY" in rt else "hold" if "HOLD" in rt else "sell"
                    
                    st.markdown(f"### {row['ticker']}")
                    st.markdown(f"<span class='badge {cls}'>{rt}</span> {row.get('nombre', '')}", unsafe_allow_html=True)
                    st.caption(f"📅 {row.get('fecha', 'S/D')}")
                    
                    # Al pulsar, cambiamos el estado para "abrir" el lector
                    if st.button(f"Leer Tesis", key=f"btn_{row['ticker']}"):
                        st.session_state.tesis_seleccionada = row['ticker']
                        st.session_state.vista_actual = "lector"
                        st.rerun()

        except Exception as e:
            st.error(f"Error: {e}")

    # VISTA 2: LECTOR (Se muestra al elegir una tesis)
    elif st.session_state.vista_actual == "lector":
        # Recargar datos para el lector
        CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"
        df = pd.read_csv(CSV_URL)
        df.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in df.columns]
        
        sel_row = df[df['ticker'].str.lower() == st.session_state.tesis_seleccionada.lower()].iloc[0]

        # Botón para volver atrás
        if st.button("⬅️ Volver a la Galería"):
            st.session_state.vista_actual = "galeria"
            st.rerun()

        st.markdown(f"## 🔍 Análisis: {sel_row.get('nombre', sel_row['ticker'])}")
        st.write("---")

        url_doc = str(sel_row.get('urldoc', '')).strip()
        # Limpieza de link para vista pura
        if "/pub" in url_doc:
            url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
        
        with st.spinner("Cargando documento..."):
            components.iframe(url_doc, height=1000, scrolling=True)
