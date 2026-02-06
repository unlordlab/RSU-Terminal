import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import html
from datetime import datetime, timedelta

def render():
    # CSS Global - Mejorado con responsive y nuevos componentes
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
        
        /* Badges */
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
        
        .badge-new {
            background-color: rgba(0, 150, 255, 0.15);
            color: #0096ff;
            border: 1px solid #0096ff44;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0, 150, 255, 0.4); }
            70% { box-shadow: 0 0 0 6px rgba(0, 150, 255, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 150, 255, 0); }
        }
        
        /* Tags */
        .tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            margin-right: 4px;
            margin-top: 4px;
            background: #1a1e26;
            color: #888;
            border: 1px solid #2a2e36;
        }
        
        /* Inputs */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stDateInput > div > div > input {
            background-color: #0c0e12 !important;
            color: white !important;
            border: 1px solid #1a1e26 !important;
            border-radius: 6px !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus,
        .stDateInput > div > div > input:focus {
            border-color: #00ffad !important;
            box-shadow: 0 0 0 1px #00ffad !important;
        }
        
        /* Botones */
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
        
        /* Toggle vista */
        .view-toggle {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
            margin-bottom: 20px;
        }
        
        .view-btn {
            background: #1a1e26;
            border: 1px solid #333;
            color: #888;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .view-btn.active {
            background: #00ffad22;
            border-color: #00ffad;
            color: #00ffad;
        }
        
        /* Lista compacta */
        .list-item {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
        }
        
        .list-item:hover {
            border-color: #00ffad44;
            background: #151920;
        }
        
        /* Skeleton loading */
        .skeleton {
            background: linear-gradient(90deg, #1a1e26 25%, #252a33 50%, #1a1e26 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: 4px;
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
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
        
        .sector-icon {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            margin-right: 12px;
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
        
        /* Paginación */
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 30px;
            align-items: center;
        }
        
        .page-btn {
            background: #1a1e26;
            border: 1px solid #333;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
        }
        
        .page-btn:disabled {
            opacity: 0.3;
            cursor: not-allowed;
        }
        
        .page-info {
            color: #888;
            font-size: 14px;
        }
        
        /* Métricas cards */
        .metric-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #00ffad;
        }
        
        .metric-label {
            color: #888;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .stColumns > div {
                width: 100% !important;
                flex: 0 0 100% !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Inicializar estado
    if 'vista_actual' not in st.session_state:
        st.session_state.vista_actual = "galeria"
    if 'vista_tipo' not in st.session_state:
        st.session_state.vista_tipo = "grid"
    if 'pagina' not in st.session_state:
        st.session_state.pagina = 1
    if 'tesis_por_pagina' not in st.session_state:
        st.session_state.tesis_por_pagina = 9

    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

    # --- VISTA 1: GALERÍA ---
    if st.session_state.vista_actual == "galeria":
        st.markdown('<h1 style="text-align:center; margin-bottom:10px; color:white;">📄 Terminal de Análisis</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#666; margin-bottom:30px;">Análisis técnicos y fundamentales de activos</p>', unsafe_allow_html=True)

        try:
            @st.cache_data(ttl=300)
            def load_index(url):
                data = pd.read_csv(url)
                data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
                if 'fecha' in data.columns:
                    data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
                    data['dias_desde'] = (datetime.now() - data['fecha_dt']).dt.days
                    data['es_nuevo'] = data['dias_desde'] <= 7
                return data
                
            df = load_index(CSV_URL)

            # Sidebar con filtros avanzados
            with st.sidebar:
                st.markdown("### 🔍 Filtros Avanzados")
                
                # Búsqueda
                busqueda = st.text_input("Buscar activo:", "", 
                                        placeholder="Ej: AAPL, Tesla...").lower()
                
                # Filtro Rating
                ratings_disponibles = ["Todos"] + sorted(list(df['rating'].unique())) if 'rating' in df.columns else ["Todos"]
                filtro_rating = st.selectbox("Rating:", ratings_disponibles)
                
                # Filtro Sector
                if 'sector' in df.columns:
                    sectores = ["Todos"] + sorted(list(df['sector'].unique()))
                    filtro_sector = st.selectbox("Sector:", sectores)
                else:
                    filtro_sector = "Todos"
                
                # Filtro Fecha
                st.markdown("**Fecha:**")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_desde = st.date_input("Desde", value=None, key="fecha_desde")
                with col_f2:
                    fecha_hasta = st.date_input("Hasta", value=None, key="fecha_hasta")
                
                # Solo nuevos
                solo_nuevos = st.checkbox("Solo análisis nuevos (7 días)", value=False)
                
                st.markdown("---")
                
                # Configuración de vista
                st.markdown("### ⚙️ Configuración")
                st.session_state.tesis_por_pagina = st.selectbox(
                    "Tesis por página:", 
                    [6, 9, 12, 15, 24],
                    index=1
                )
                
                # Ordenamiento
                orden_opciones = {
                    "Fecha ↓": ("fecha_dt", False),
                    "Fecha ↑": ("fecha_dt", True),
                    "Ticker A-Z": ("ticker", True),
                    "Ticker Z-A": ("ticker", False),
                    "Rating": ("rating", True)
                }
                orden_seleccionado = st.selectbox("Ordenar por:", list(orden_opciones.keys()))
                
                # Exportar
                st.markdown("---")
                if st.button("📥 Exportar CSV"):
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Descargar datos",
                        data=csv,
                        file_name=f"tesis_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

            # Aplicar filtros
            df_view = df.copy()
            
            if busqueda and 'ticker' in df_view.columns and 'nombre' in df_view.columns:
                mask = (df_view['ticker'].str.contains(busqueda, case=False, na=False) | 
                       df_view['nombre'].str.contains(busqueda, case=False, na=False))
                df_view = df_view[mask]
            
            if filtro_rating != "Todos" and 'rating' in df_view.columns:
                df_view = df_view[df_view['rating'] == filtro_rating]
            
            if filtro_sector != "Todos" and 'sector' in df_view.columns:
                df_view = df_view[df_view['sector'] == filtro_sector]
            
            if fecha_desde and 'fecha_dt' in df_view.columns:
                df_view = df_view[df_view['fecha_dt'] >= pd.Timestamp(fecha_desde)]
            
            if fecha_hasta and 'fecha_dt' in df_view.columns:
                df_view = df_view[df_view['fecha_dt'] <= pd.Timestamp(fecha_hasta)]
            
            if solo_nuevos and 'es_nuevo' in df_view.columns:
                df_view = df_view[df_view['es_nuevo'] == True]
            
            # Aplicar ordenamiento
            sort_col, sort_asc = orden_opciones[orden_seleccionado]
            if sort_col in df_view.columns:
                df_view = df_view.sort_values(by=sort_col, ascending=sort_asc, na_position='last')

            # Toggle vista Grid/Lista
            col_stats, col_toggle = st.columns([3, 1])
            
            with col_stats:
                st.markdown(f"<p style='color:#888; margin:0;'>Mostrando {len(df_view)} análisis</p>", unsafe_allow_html=True)
            
            with col_toggle:
                col_g, col_l = st.columns(2)
                with col_g:
                    if st.button("⊞ Grid", key="btn_grid"):
                        st.session_state.vista_tipo = "grid"
                        st.rerun()
                with col_l:
                    if st.button("☰ Lista", key="btn_lista"):
                        st.session_state.vista_tipo = "list"
                        st.rerun()

            st.markdown("---")

            if len(df_view) > 0:
                # Paginación
                total_paginas = max(1, (len(df_view) + st.session_state.tesis_por_pagina - 1) // st.session_state.tesis_por_pagina)
                
                # Asegurar página válida
                if st.session_state.pagina > total_paginas:
                    st.session_state.pagina = 1
                
                inicio = (st.session_state.pagina - 1) * st.session_state.tesis_por_pagina
                fin = inicio + st.session_state.tesis_por_pagina
                df_pagina = df_view.iloc[inicio:fin]
                
                # Vista GRID
                if st.session_state.vista_tipo == "grid":
                    cols = st.columns(3)
                    for idx, row in df_pagina.reset_index(drop=True).iterrows():
                        with cols[idx % 3]:
                            ticker = str(row.get('ticker', 'N/A')).upper()
                            nombre = str(row.get('nombre', ''))
                            fecha = str(row.get('fecha', 'S/D'))
                            rating = str(row.get('rating', 'HOLD')).upper()
                            sector = str(row.get('sector', ''))
                            autor = str(row.get('autor', ''))
                            es_nuevo = row.get('es_nuevo', False)
                            
                            # Badge rating
                            if 'BUY' in rating:
                                badge_class = "badge-buy"
                                badge_text = "BUY"
                            elif 'SELL' in rating:
                                badge_class = "badge-sell"
                                badge_text = "SELL"
                            else:
                                badge_class = "badge-hold"
                                badge_text = "HOLD"
                            
                            # Imagen - ESCAPAR URL PARA EVITAR PROBLEMAS
                            img_url = str(row.get('imagenencabezado', '')).strip()
                            
                            if img_url and img_url.startswith('http'):
                                # Escapar la URL para el HTML
                                img_url_escaped = html.escape(img_url)
                                ticker_escaped = html.escape(ticker)
                                
                                # Usar un div con background image en lugar de img tag para mejor control
                                img_html = f'''
                                <div style="width:100%; height:180px; overflow:hidden; border-bottom:1px solid #1a1e26; position:relative; background:#0c0e12;">
                                    <img src="{img_url_escaped}" 
                                         style="width:100%; height:100%; object-fit:cover; display:block;" 
                                         alt="{ticker_escaped}"
                                         onerror="this.onerror=null; this.src=''; this.style.display='none'; this.parentElement.style.background='linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%)'; this.parentElement.innerHTML='<div style=\\'width:100%; height:100%; display:flex; align-items:center; justify-content:center;\\'><span style=\\'color:#00ffad; font-size:3rem; font-weight:bold;\\'>{ticker_escaped}</span></div>';"
                                         loading="lazy">
                                    {'<span class="badge badge-new" style="position:absolute; top:10px; left:10px;">NEW</span>' if es_nuevo else ''}
                                </div>
                                '''
                            else:
                                img_html = f'''
                                <div style="width:100%; height:180px; background:linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); 
                                            display:flex; align-items:center; justify-content:center; border-bottom:1px solid #1a1e26; position:relative;">
                                    <span style="color:#00ffad; font-size:3rem; font-weight:bold;">{html.escape(ticker)}</span>
                                    {'<span class="badge badge-new" style="position:absolute; top:10px; left:10px;">NEW</span>' if es_nuevo else ''}
                                </div>
                                '''
                            
                            # Tags
                            tags_html = ""
                            if sector:
                                tags_html += f'<span class="tag">{html.escape(sector)}</span>'
                            if autor:
                                tags_html += f'<span class="tag">👤 {html.escape(autor)}</span>'
                            
                            # Tooltip
                            tooltip_text = f"Análisis técnico y fundamental de {nombre}. Fecha: {fecha}"
                            if 'resumen' in row and pd.notna(row['resumen']):
                                tooltip_text += f"\n\nResumen: {str(row['resumen'])[:100]}..."
                            
                            # Escapar todo el contenido dinámico
                            ticker_escaped = html.escape(ticker)
                            nombre_escaped = html.escape(nombre)
                            fecha_escaped = html.escape(fecha)
                            tooltip_escaped = html.escape(tooltip_text)
                            
                            card_html = f'''
                            <div class="group-container" style="margin-bottom:20px;">
                                <div style="position:relative;">
                                    {img_html}
                                    <div style="position:absolute; top:10px; right:10px;">
                                        <span class="badge {badge_class}">{badge_text}</span>
                                    </div>
                                </div>
                                <div style="padding:15px;">
                                    <div class="ticker-title">{ticker_escaped}</div>
                                    <div class="company-name">{nombre_escaped}</div>
                                    <div style="margin-top:8px;">{tags_html}</div>
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
                                        <span class="date-text">📅 {fecha_escaped}</span>
                                        <div class="tooltip-container">
                                            <div class="tooltip-icon" style="width:20px; height:20px; font-size:12px;">?</div>
                                            <div class="tooltip-text">{tooltip_escaped}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            '''
                            
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            if st.button(f"Ver Análisis →", key=f"btn_{ticker}_{idx}"):
                                st.session_state.tesis_seleccionada = ticker
                                st.session_state.vista_actual = "lector"
                                st.rerun()
                
                # Vista LISTA
                else:
                    for idx, row in df_pagina.iterrows():
                        ticker = str(row.get('ticker', 'N/A')).upper()
                        nombre = str(row.get('nombre', ''))
                        fecha = str(row.get('fecha', 'S/D'))
                        rating = str(row.get('rating', 'HOLD')).upper()
                        sector = str(row.get('sector', ''))
                        es_nuevo = row.get('es_nuevo', False)
                        
                        # Color según sector
                        sector_colors = {
                            'Tecnología': '#00ffad', 'Technology': '#00ffad',
                            'Energía': '#ff9800', 'Energy': '#ff9800',
                            'Salud': '#f23645', 'Healthcare': '#f23645',
                            'Finanzas': '#0096ff', 'Financials': '#0096ff',
                            'Consumo': '#ff5722', 'Consumer': '#ff5722'
                        }
                        sector_color = sector_colors.get(sector, '#888')
                        
                        # Badge rating
                        if 'BUY' in rating:
                            badge_class = "badge-buy"
                        elif 'SELL' in rating:
                            badge_class = "badge-sell"
                        else:
                            badge_class = "badge-hold"
                        
                        col1, col2, col3, col4 = st.columns([0.5, 2, 1, 1])
                        
                        with col1:
                            st.markdown(f'''
                            <div style="width:40px; height:40px; background:{sector_color}22; border:1px solid {sector_color}44; 
                                        border-radius:8px; display:flex; align-items:center; justify-content:center; color:{sector_color};
                                        font-weight:bold; font-size:14px;">
                                {html.escape(ticker[:2])}
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        with col2:
                            nuevo_badge = '<span class="badge badge-new" style="margin-left:8px;">NEW</span>' if es_nuevo else ''
                            st.markdown(f'''
                            <div style="display:flex; align-items:center;">
                                <span style="color:white; font-weight:bold; font-size:16px;">{html.escape(ticker)}</span>
                                {nuevo_badge}
                            </div>
                            <div style="color:#888; font-size:13px;">{html.escape(nombre)}</div>
                            ''', unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f'<span class="badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)
                            if sector:
                                st.markdown(f'<div style="color:#666; font-size:11px; margin-top:4px;">{html.escape(sector)}</div>', unsafe_allow_html=True)
                        
                        with col4:
                            st.markdown(f'<div style="color:#555; font-size:12px; text-align:right;">{html.escape(fecha)}</div>', unsafe_allow_html=True)
                            if st.button("Ver →", key=f"btn_list_{ticker}_{idx}"):
                                st.session_state.tesis_seleccionada = ticker
                                st.session_state.vista_actual = "lector"
                                st.rerun()
                        
                        st.markdown("<hr style='margin:10px 0; opacity:0.3;'>", unsafe_allow_html=True)
                
                # Controles de paginación
                if total_paginas > 1:
                    col_prev, col_info, col_next = st.columns([1, 2, 1])
                    
                    with col_prev:
                        if st.button("← Anterior", disabled=st.session_state.pagina <= 1, key="btn_prev"):
                            st.session_state.pagina -= 1
                            st.rerun()
                    
                    with col_info:
                        st.markdown(f"<p style='text-align:center; color:#888;'>Página {st.session_state.pagina} de {total_paginas}</p>", unsafe_allow_html=True)
                    
                    with col_next:
                        if st.button("Siguiente →", disabled=st.session_state.pagina >= total_paginas, key="btn_next"):
                            st.session_state.pagina += 1
                            st.rerun()
            
            else:
                st.markdown('''
                <div style="text-align:center; padding:60px 20px; color:#555;">
                    <div style="font-size:3rem; margin-bottom:15px;">🔍</div>
                    <div style="font-size:1.2rem; color:#888;">No se encontraron resultados</div>
                    <div style="font-size:0.9rem; margin-top:10px;">Intenta ajustar los filtros de búsqueda</div>
                </div>
                ''', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            st.exception(e)

    # --- VISTA 2: LECTOR ---
    elif st.session_state.vista_actual == "lector":
        try:
            df = pd.read_csv(CSV_URL)
            df.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in df.columns]
            
            sel_row = df[df['ticker'].str.lower() == st.session_state.tesis_seleccionada.lower()].iloc[0]
            
            # Header
            col_back, col_title, col_actions = st.columns([1, 4, 1])
            
            with col_back:
                st.markdown('<div class="back-button">', unsafe_allow_html=True)
                if st.button("⬅️ Volver"):
                    st.session_state.vista_actual = "galeria"
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_title:
                nombre = sel_row.get('nombre', st.session_state.tesis_seleccionada)
                ticker = str(sel_row.get('ticker', '')).upper()
                st.markdown(f'<h2 style="color:#00ffad; margin:0;">{html.escape(nombre)} <span style="color:#444; font-size:0.6em;">({html.escape(ticker)})</span></h2>', unsafe_allow_html=True)
            
            with col_actions:
                # Botón favoritos (placeholder para futura funcionalidad)
                if st.button("⭐"):
                    st.toast("Añadido a favoritos", icon="⭐")
            
            st.markdown("---")
            
            # Info cards mejoradas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                rating = str(sel_row.get('rating', 'N/A')).upper()
                rating_color = "#00ffad" if "BUY" in rating else "#f23645" if "SELL" in rating else "#ff9800"
                st.markdown(f'''
                <div class="group-container">
                    <div class="group-header">
                        <span class="group-title">Rating</span>
                    </div>
                    <div class="group-content" style="padding:20px; text-align:center;">
                        <div style="font-size:2rem; font-weight:bold; color:{rating_color};">{html.escape(rating)}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                fecha = str(sel_row.get('fecha', 'N/A'))
                st.markdown(f'''
                <div class="group-container">
                    <div class="group-header">
                        <span class="group-title">Fecha</span>
                    </div>
                    <div class="group-content" style="padding:20px; text-align:center;">
                        <div style="font-size:1.2rem; font-weight:bold; color:white;">{html.escape(fecha)}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                sector = str(sel_row.get('sector', 'N/A'))
                st.markdown(f'''
                <div class="group-container">
                    <div class="group-header">
                        <span class="group-title">Sector</span>
                    </div>
                    <div class="group-content" style="padding:20px; text-align:center;">
                        <div style="font-size:1.2rem; font-weight:bold; color:#0096ff;">{html.escape(sector)}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col4:
                autor = str(sel_row.get('autor', 'N/A'))
                st.markdown(f'''
                <div class="group-container">
                    <div class="group-header">
                        <span class="group-title">Analista</span>
                    </div>
                    <div class="group-content" style="padding:20px; text-align:center;">
                        <div style="font-size:1.2rem; font-weight:bold; color:#ff9800;">{html.escape(autor)}</div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            # Resumen ejecutivo si existe
            if 'resumen' in sel_row and pd.notna(sel_row['resumen']):
                st.markdown("---")
                st.markdown("### 📝 Resumen Ejecutivo")
                resumen_text = html.escape(str(sel_row['resumen']))
                st.markdown(f"<div style='background:#11141a; padding:20px; border-radius:8px; border-left:3px solid #00ffad; color:#ccc; line-height:1.6;'>{resumen_text}</div>", unsafe_allow_html=True)
            
            # Métricas clave si existen
            metricas_cols = []
            if 'precioobjetivo' in sel_row and pd.notna(sel_row['precioobjetivo']):
                metricas_cols.append(("🎯 Precio Objetivo", f"${sel_row['precioobjetivo']}", "#00ffad"))
            if 'precioactual' in sel_row and pd.notna(sel_row['precioactual']):
                metricas_cols.append(("💵 Precio Actual", f"${sel_row['precioactual']}", "#888"))
            if 'upside' in sel_row and pd.notna(sel_row['upside']):
                upside_val = sel_row['upside']
                upside_color = "#00ffad" if upside_val > 0 else "#f23645"
                metricas_cols.append(("📈 Upside", f"{upside_val:+.1f}%", upside_color))
            if 'riesgo' in sel_row and pd.notna(sel_row['riesgo']):
                riesgo = str(sel_row['riesgo']).upper()
                riesgo_color = "#00ffad" if "BAJO" in riesgo else "#ff9800" if "MEDIO" in riesgo else "#f23645"
                metricas_cols.append(("⚠️ Riesgo", riesgo, riesgo_color))
            
            if metricas_cols:
                st.markdown("---")
                st.markdown("### 📊 Métricas Clave")
                cols_metricas = st.columns(len(metricas_cols))
                for i, (label, value, color) in enumerate(metricas_cols):
                    with cols_metricas[i]:
                        st.markdown(f'''
                        <div class="metric-card">
                            <div class="metric-value" style="color:{color};">{html.escape(value)}</div>
                            <div class="metric-label">{html.escape(label)}</div>
                        </div>
                        ''', unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📄 Documento Completo")
            
            # Documento embedido
            url_doc = str(sel_row.get('urldoc', '')).strip()
            if url_doc:
                if "/pub" in url_doc:
                    url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
                
                with st.spinner("Cargando documento..."):
                    components.iframe(url_doc, height=800, scrolling=True)
            else:
                st.warning("No hay documento disponible para este análisis.")
                
        except Exception as e:
            st.error(f"Error al cargar el análisis: {e}")
            if st.button("← Volver a la galería"):
                st.session_state.vista_actual = "galeria"
                st.rerun()
