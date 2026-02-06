

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime

def render():
    # CSS Global - Mismo estilo que market.py
    st.markdown("""
    <style>
        /* Reset y base */
        .stApp {
            background-color: #0c0e12;
        }
        
        /* Contenedores de grupo (cards) */
        .group-container {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .group-container:hover {
            transform: translateY(-3px);
            box-shadow: 0px 0px 15px rgba(0, 255, 173, 0.1);
            border-color: #00ffad44;
        }
        
        .group-header {
            background: #0c0e12;
            padding: 12px 15px;
            border-bottom: 1px solid #1a1e26;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .group-title {
            margin: 0;
            color: white;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 0.5px;
        }
        
        .group-content {
            padding: 0;
            background: #11141a;
        }
        
        /* Tooltips */
        .tooltip-container {
            position: relative;
            cursor: help;
        }
        
        .tooltip-icon {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #1a1e26;
            border: 2px solid #555;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #aaa;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.2s;
        }
        
        .tooltip-icon:hover {
            border-color: #00ffad;
            color: #00ffad;
        }
        
        .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 35px;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        
        /* Badges de Rating - Estilo market.py */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-buy {
            background-color: rgba(0, 255, 173, 0.15);
            color: #00ffad;
            border: 1px solid #00ffad44;
        }
        
        .badge-hold {
            background-color: rgba(255, 152, 0, 0.15);
            color: #ff9800;
            border: 1px solid #ff980044;
        }
        
        .badge-sell {
            background-color: rgba(242, 54, 69, 0.15);
            color: #f23645;
            border: 1px solid #f2364544;
        }
        
        /* Inputs estilo market.py */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            background-color: #0c0e12 !important;
            color: white !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 6px !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 1px #00ffad !important;
        }
        
        /* Botón Leer Tesis - Estilo consistente */
        .stButton > button {
            width: 100%;
            background-color: #0c0e12 !important;
            color: #00ffad !important;
            border: 1px solid #00ffad44 !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            font-weight: bold !important;
            font-size: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:hover {
            background-color: #00ffad !important;
            color: #0c0e12 !important;
            box-shadow: 0 0 15px rgba(0, 255, 173, 0.3) !important;
        }
        
        /* Botón Volver */
        .back-button button {
            background-color: #1a1e26 !important;
            color: white !important;
            border: 1px solid #444 !important;
        }
        
        .back-button button:hover {
            background-color: #f23645 !important;
            color: white !important;
            border-color: #f23645 !important;
        }
        
        /* Texto y tipografía */
        h1, h2, h3 {
            color: white !important;
            font-weight: bold !important;
        }
        
        .ticker-title {
            color: #00ffad;
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 4px;
        }
        
        .company-name {
            color: #888;
            font-size: 0.85rem;
        }
        
        .date-text {
            color: #555;
            font-size: 0.75rem;
            font-family: monospace;
        }
        
        /* Separadores */
        hr {
            border-color: #1a1e26 !important;
            margin: 20px 0 !important;
        }
        
        /* Spinner */
        .stSpinner > div {
            border-top-color: #00ffad !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Inicializar estado
    if 'vista_actual' not in st.session_state:
        st.session_state.vista_actual = "galeria"

    # --- VISTA 1: GALERÍA ---
    if st.session_state.vista_actual == "galeria":
        # Header estilo market.py
        st.markdown('<h1 style="text-align:center; margin-bottom:30px; color:white;">📄 Terminal de Análisis</h1>', unsafe_allow_html=True)
        
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

            # Filtros en contenedor estilo market.py
            filter_container = st.container()
            with filter_container:
                col_search, col_filtro = st.columns([2, 1])
                
                with col_search:
                    busqueda = st.text_input("🔍 Buscar activo:", "", 
                                           placeholder="Ej: AAPL, Tesla...").lower()
                with col_filtro:
                    ratings_disponibles = ["Todos"] + list(df['rating'].unique()) if 'rating' in df.columns else ["Todos"]
                    filtro_rating = st.selectbox("Filtrar por Rating:", ratings_disponibles)

            st.markdown("---")

            # Filtrado
            df_view = df.copy()
            if busqueda and 'ticker' in df_view.columns and 'nombre' in df_view.columns:
                mask = (df_view['ticker'].str.contains(busqueda, case=False, na=False) | 
                       df_view['nombre'].str.contains(busqueda, case=False, na=False))
                df_view = df_view[mask]
            
            if filtro_rating != "Todos" and 'rating' in df_view.columns:
                df_view = df_view[df_view['rating'] == filtro_rating]
            
            if 'fecha_dt' in df_view.columns:
                df_view = df_view.sort_values(by='fecha_dt', ascending=False)

            # Grid de tarjetas estilo market.py
            if len(df_view) > 0:
                cols = st.columns(3)
                for idx, row in df_view.reset_index(drop=True).iterrows():
                    with cols[idx % 3]:
                        # Card container
                        ticker = str(row.get('ticker', 'N/A')).upper()
                        nombre = str(row.get('nombre', ''))
                        fecha = str(row.get('fecha', 'S/D'))
                        rating = str(row.get('rating', 'HOLD')).upper()
                        
                        # Determinar clase del badge
                        if 'BUY' in rating:
                            badge_class = "badge-buy"
                            badge_text = "BUY"
                        elif 'SELL' in rating:
                            badge_class = "badge-sell"
                            badge_text = "SELL"
                        else:
                            badge_class = "badge-hold"
                            badge_text = "HOLD"
                        
                        # === IMAGEN DESDE URL DEL SHEET (CORREGIDO) ===
                        img_url = str(row.get('imagenencabezado', '')).strip()
                        
                        if img_url and img_url.startswith('http'):
                            # Usar URL de GitHub directamente con fallback visual
                            img_html = f'''
                            <div style="width:100%; height:180px; overflow:hidden; border-bottom:1px solid #1a1e26;">
                                <img src="{img_url}" 
                                     style="width:100%; height:100%; object-fit:cover;" 
                                     onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\'width:100%; height:100%; background:linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); display:flex; align-items:center; justify-content:center;\\'><span style=\\'color:#00ffad; font-size:3rem; font-weight:bold;\\'>{ticker}</span></div>';"
                                     loading="lazy">
                            </div>
                            '''
                        else:
                            # Fallback si no hay URL válida
                            img_html = f'''
                            <div style="width:100%; height:180px; background:linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); 
                                        display:flex; align-items:center; justify-content:center; border-bottom:1px solid #1a1e26;">
                                <span style="color:#00ffad; font-size:3rem; font-weight:bold;">{ticker}</span>
                            </div>
                            '''
                        
                        # Tooltip informativo
                        tooltip_text = f"Análisis técnico y fundamental de {nombre}. Fecha: {fecha}"
                        
                        card_html = f'''
                        <div class="group-container" style="margin-bottom:20px;">
                            <div style="position:relative;">
                                {img_html}
                                <div style="position:absolute; top:10px; right:10px;">
                                    <span class="badge {badge_class}">{badge_text}</span>
                                </div>
                            </div>
                            <div style="padding:15px;">
                                <div class="ticker-title">{ticker}</div>
                                <div class="company-name">{nombre}</div>
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
                                    <span class="date-text">📅 {fecha}</span>
                                    <div class="tooltip-container">
                                        <div class="tooltip-icon" style="width:20px; height:20px; font-size:12px;">?</div>
                                        <div class="tooltip-text">{tooltip_text}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        '''
                        
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Botón de acción
                        if st.button(f"Ver Análisis →", key=f"btn_{ticker}_{idx}"):
                            st.session_state.tesis_seleccionada = ticker
                            st.session_state.vista_actual = "lector"
                            st.rerun()
            else:
                st.markdown('''
                <div style="text-align:center; padding:60px 20px; color:#555;">
                    <div style="font-size:3rem; margin-bottom:15px;">🔍</div>
                    <div style="font-size:1.2rem; color:#888;">No se encontraron resultados</div>
                    <div style="font-size:0.9rem; margin-top:10px;">Intenta con otros términos de búsqueda</div>
                </div>
                ''', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error al cargar datos: {e}")

    # --- VISTA 2: LECTOR ---
    elif st.session_state.vista_actual == "lector":
        # Recargar datos
        CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"
        
        try:
            df = pd.read_csv(CSV_URL)
            df.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in df.columns]
            
            sel_row = df[df['ticker'].str.lower() == st.session_state.tesis_seleccionada.lower()].iloc[0]
            
            # Header con botón volver
            col_back, col_title = st.columns([1, 4])
            
            with col_back:
                st.markdown('<div class="back-button">', unsafe_allow_html=True)
                if st.button("⬅️ Volver"):
                    st.session_state.vista_actual = "galeria"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_title:
                nombre = sel_row.get('nombre', st.session_state.tesis_seleccionada)
                st.markdown(f'<h2 style="color:#00ffad; margin:0;">{nombre}</h2>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Info del análisis en cards tipo market.py
            col1, col2, col3 = st.columns(3)
            
            with col1:
                rating = str(sel_row.get('rating', 'N/A')).upper()
                rating_color = "#00ffad" if "BUY" in rating else "#f23645" if "SELL" in rating else "#ff9800"
                st.markdown(f'''
                <div class="group-container">
                    <div class="group-header">
                        <span class="group-title">Rating</span>
                    </div>
                    <div class="group-content" style="padding:20px; text-align:center;">
                        <div style="font-size:2.5rem; font-weight:bold; color:{rating_color};">{rating}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                fecha = str(sel_row.get('fecha', 'N/A'))
                st.markdown(f'''
                <div class="group-container">
                    <div class="group-header">
                        <span class="group-title">Fecha Análisis</span>
                    </div>
                    <div class="group-content" style="padding:20px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:bold; color:white;">{fecha}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                ticker = str(sel_row.get('ticker', 'N/A'))
                st.markdown(f'''
                <div class="group-container">
                    <div class="group-header">
                        <span class="group-title">Ticker</span>
                    </div>
                    <div class="group-content" style="padding:20px; text-align:center;">
                        <div style="font-size:1.5rem; font-weight:bold; color:#00ffad;">{ticker}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Documento embedido
            url_doc = str(sel_row.get('urldoc', '')).strip()
            if "/pub" in url_doc:
                url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
            
            with st.spinner("Cargando documento..."):
                components.iframe(url_doc, height=800, scrolling=True)
                
        except Exception as e:
            st.error(f"Error al cargar el análisis: {e}")
            if st.button("← Volver a la galería"):
                st.session_state.vista_actual = "galeria"
                st.rerun()
