import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os

def render():
    # Estilo CSS para mejorar la estética de las tarjetas y el visor
    st.markdown("""
        <style>
        .tesis-card {
            border: 1px solid #333;
            border-radius: 10px;
            padding: 15px;
            background-color: #0e1117;
            transition: transform 0.3s, border-color 0.3s;
        }
        .tesis-card:hover {
            border-color: #00ffad;
            transform: translateY(-5px);
        }
        .rating-buy { color: #00ffad; font-weight: bold; }
        .rating-hold { color: #ff9800; font-weight: bold; }
        .rating-sell { color: #ff4b4b; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h2 style="color: #00ffad;">📄 Terminal de Análisis</h2>', unsafe_allow_html=True)

    # URL del Google Sheet (CSV)
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    try:
        @st.cache_data(ttl=60)
        def load_index(url):
            data = pd.read_csv(url)
            data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
            if 'fecha' in data.columns:
                # Ordenar por fecha de forma técnica
                data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
            return data
            
        df = load_index(CSV_URL)

        # 1. BUSCADOR Y FILTROS (Sugerencia estructural)
        col_search, col_filtro = st.columns([2, 1])
        with col_search:
            busqueda = st.text_input("🔍 Buscar activo (Ticker o Nombre):", "").lower()
        with col_filtro:
            filtro_rating = st.selectbox("Filtrar por Rating:", ["Todos"] + list(df['rating'].unique()))

        # Aplicar filtros
        df_view = df.copy()
        if busqueda:
            df_view = df_view[df_view['ticker'].str.contains(busqueda) | df_view['nombre'].str.contains(busqueda)]
        if filtro_rating != "Todos":
            df_view = df_view[df_view['rating'] == filtro_rating]

        # Ordenar por fecha más reciente
        if 'fecha_dt' in df_view.columns:
            df_view = df_view.sort_values(by='fecha_dt', ascending=False)

        # 2. GALERÍA DE MINIATURAS (GRID)
        st.write("---")
        if df_view.empty:
            st.warning("No se encontraron tesis con esos criterios.")
        else:
            cols = st.columns(3)
            for idx, row in df_view.reset_index(drop=True).iterrows():
                with cols[idx % 3]:
                    # Lógica de Imagen Local
                    ticker_clean = str(row['ticker']).lower().strip()
                    img_path = f"assets/{ticker_clean}.png"
                    
                    # Verificación técnica del archivo
                    if os.path.exists(img_path):
                        st.image(img_path, use_container_width=True)
                    else:
                        st.image("https://via.placeholder.com/400x225?text=Img+Missing", use_container_width=True)
                    
                    # Estética de la Card
                    rating = str(row['rating']).upper()
                    rating_class = "rating-buy" if "BUY" in rating else "rating-hold" if "HOLD" in rating else "rating-sell"
                    
                    st.markdown(f"### {row['ticker']}")
                    st.markdown(f"<span class='{rating_class}'>{rating}</span> • {row.get('nombre', '')}", unsafe_allow_html=True)
                    st.caption(f"📅 {row.get('fecha', 'S/D')}")
                    
                    if st.button(f"Analizar {row['ticker']}", key=f"btn_{row['ticker']}", use_container_width=True):
                        st.session_state.tesis_seleccionada = row['ticker']

        # 3. LECTOR DE GOOGLE DOCS (MODO EMBEDDED LIMPIO)
        if 'tesis_seleccionada' in st.session_state:
            st.write("---")
            sel_row = df[df['ticker'] == st.session_state.tesis_seleccionada].iloc[0]
            
            with st.spinner(f"Abriendo análisis de {sel_row['ticker']}..."):
                url_doc = str(sel_row.get('urldoc', '')).strip()
                
                # Forzar modo publicación pura para evitar botones de edición
                if "/pub" in url_doc:
                    url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
                
                st.subheader(f"🔍 Análisis Detallado: {sel_row.get('nombre', sel_row['ticker'])}")
                
                # Iframe de alta fidelidad
                components.iframe(url_doc, height=1000, scrolling=True)
                
                if st.button("Cerrar análisis"):
                    del st.session_state.tesis_seleccionada
                    st.rerun()

    except Exception as e:
        st.error(f"Error en la terminal: {e}")
