import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timedelta

def render():
    # CSS Global - Agregamos clase para containers estilizados
    st.markdown("""
    <style>
        .stApp {
            background-color: #0c0e12;
        }
        
        /* Estilo para containers de cards */
        div[data-testid="stVerticalBlock"]:has(> div.element-container:nth-child(1) div.card-container) {
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            background: #11141a;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 20px;
        }
        
        div[data-testid="stVerticalBlock"]:has(> div.element-container:nth-child(1) div.card-container):hover {
            transform: translateY(-3px);
            box-shadow: 0px 0px 15px rgba(0, 255, 173, 0.1);
            border-color: #00ffad44;
        }
        
        .card-container {
            display: none; /* Solo para identificación */
        }
        
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
        
        hr {
            border-color: #1a1e26 !important;
            margin: 20px 0 !important;
        }
        
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
        
        /* Fix para sidebar */
        [data-testid="stSidebar"] .element-container {
            margin-bottom: 0.5rem;
        }
        
        [data-testid="stSidebar"] .stMarkdown {
            margin-bottom: 0.5rem;
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
                
                busqueda = st.text_input("Buscar activo:", "", placeholder="Ej: AAPL, Tesla...").lower()
                
                ratings_disponibles = ["Todos"] + sorted(list(df['rating'].unique())) if 'rating' in df.columns else ["Todos"]
                filtro_rating = st.selectbox("Rating:", ratings_disponibles)
                
                if 'sector' in df.columns:
                    sectores = ["Todos"] + sorted(list(df['sector'].unique()))
                    filtro_sector = st.selectbox("Sector:", sectores)
                else:
                    filtro_sector = "Todos"
                
                st.markdown("**Fecha:**")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_desde = st.date_input("Desde", value=None, key="fecha_desde")
                with col_f2:
                    fecha_hasta = st.date_input("Hasta", value=None, key="fecha_hasta")
                
                solo_nuevos = st.checkbox("Solo análisis nuevos (7 días)", value=False)
                
                st.markdown("---")
                st.markdown("### ⚙️ Configuración")
                st.session_state.tesis_por_pagina = st.selectbox("Tesis por página:", [6, 9, 12, 15, 24], index=1)
                
                orden_opciones = {
                    "Fecha ↓": ("fecha_dt", False),
                    "Fecha ↑": ("fecha_dt", True),
                    "Ticker A-Z": ("ticker", True),
                    "Ticker Z-A": ("ticker", False),
                    "Rating": ("rating", True)
                }
                orden_seleccionado = st.selectbox("Ordenar por:", list(orden_opciones.keys()))
                
                st.markdown("---")
                if st.button("📥 Exportar CSV"):
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(label="Descargar datos", data=csv, file_name=f"tesis_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

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
            
            sort_col, sort_asc = orden_opciones[orden_seleccionado]
            if sort_col in df_view.columns:
                df_view = df_view.sort_values(by=sort_col, ascending=sort_asc, na_position='last')

            # Toggle vista
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
                total_paginas = max(1, (len(df_view) + st.session_state.tesis_por_pagina - 1) // st.session_state.tesis_por_pagina)
                
                if st.session_state.pagina > total_paginas:
                    st.session_state.pagina = 1
                
                inicio = (st.session_state.pagina - 1) * st.session_state.tesis_por_pagina
                fin = inicio + st.session_state.tesis_por_pagina
                df_pagina = df_view.iloc[inicio:fin]
                
                # Vista GRID
                if st.session_state.vista_tipo == "grid":
                    cols = st.columns(3)
                    for idx, row in df_pagina.reset_index(drop=True).iterrows():
                        col_idx = idx % 3
                        
                        with cols[col_idx]:
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
                            
                            # Container nativo de Streamlit con estilos CSS
                            card_container = st.container()
                            
                            with card_container:
                                # Marcador invisible para CSS
                                st.markdown('<div class="card-container"></div>', unsafe_allow_html=True)
                                
                                # Imagen
                                img_url = str(row.get('imagenencabezado', '')).strip()
                                
                                if img_url and img_url.startswith('http'):
                                    try:
                                        st.image(img_url, use_container_width=True)
                                    except:
                                        st.markdown(f'''
                                        <div style="width:100%; height:180px; background:linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); 
                                                    display:flex; align-items:center; justify-content:center;">
                                            <span style="color:#00ffad; font-size:3rem; font-weight:bold;">{ticker}</span>
                                        </div>
                                        ''', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'''
                                    <div style="width:100%; height:180px; background:linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); 
                                                display:flex; align-items:center; justify-content:center;">
                                        <span style="color:#00ffad; font-size:3rem; font-weight:bold;">{ticker}</span>
                                    </div>
                                    ''', unsafe_allow_html=True)
                                
                                # Badge de rating (posicionado con columnas)
                                badge_col, new_col = st.columns([1, 1])
                                with badge_col:
                                    st.markdown(f'<span class="badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)
                                with new_col:
                                    if es_nuevo:
                                        st.markdown('<span class="badge badge-new">NEW</span>', unsafe_allow_html=True)
                                
                                # Info
                                st.markdown(f'<div class="ticker-title">{ticker}</div>', unsafe_allow_html=True)
                                st.markdown(f'<div class="company-name">{nombre}</div>', unsafe_allow_html=True)
                                
                                # Tags
                                if sector or autor:
                                    tags_html = ""
                                    if sector:
                                        tags_html += f'<span class="tag">{sector}</span>'
                                    if autor:
                                        tags_html += f'<span class="tag">👤 {autor}</span>'
                                    st.markdown(f'<div>{tags_html}</div>', unsafe_allow_html=True)
                                
                                # Fecha
                                st.markdown(f'<div class="date-text">📅 {fecha}</div>', unsafe_allow_html=True)
                                
                                # Botón
                                if st.button(f"Ver Análisis →", key=f"btn_{ticker}_{idx}"):
                                    st.session_state.tesis_seleccionada = ticker
                                    st.session_state.vista_actual = "lector"
                                    st.rerun()
                                
                                # Espaciado entre cards
                                st.markdown("<br>", unsafe_allow_html=True)
                
                # Vista LISTA
                else:
                    for idx, row in df_pagina.iterrows():
                        ticker = str(row.get('ticker', 'N/A')).upper()
                        nombre = str(row.get('nombre', ''))
                        fecha = str(row.get('fecha', 'S/D'))
                        rating = str(row.get('rating', 'HOLD')).upper()
                        sector = str(row.get('sector', ''))
                        es_nuevo = row.get('es_nuevo', False)
                        
                        sector_colors = {
                            'Tecnología': '#00ffad', 'Technology': '#00ffad',
                            'Energía': '#ff9800', 'Energy': '#ff9800',
                            'Salud': '#f23645', 'Healthcare': '#f23645',
                            'Finanzas': '#0096ff', 'Financials': '#0096ff',
                            'Consumo': '#ff5722', 'Consumer': '#ff5722'
                        }
                        sector_color = sector_colors.get(sector, '#888')
                        
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
                                {ticker[:2]}
                            </div>
                            ''', unsafe_allow_html=True)
                        
                        with col2:
                            nuevo_badge = '<span class="badge badge-new" style="margin-left:8px;">NEW</span>' if es_nuevo else ''
                            st.markdown(f'''
                            <div style="display:flex; align-items:center;">
                                <span style="color:white; font-weight:bold; font-size:16px;">{ticker}</span>
                                {nuevo_badge}
                            </div>
                            <div style="color:#888; font-size:13px;">{nombre}</div>
                            ''', unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f'<span class="badge {badge_class}">{rating}</span>', unsafe_allow_html=True)
                            if sector:
                                st.markdown(f'<div style="color:#666; font-size:11px; margin-top:4px;">{sector}</div>', unsafe_allow_html=True)
                        
                        with col4:
                            st.markdown(f'<div style="color:#555; font-size:12px; text-align:right;">{fecha}</div>', unsafe_allow_html=True)
                            if st.button("Ver →", key=f"btn_list_{ticker}_{idx}"):
                                st.session_state.tesis_seleccionada = ticker
                                st.session_state.vista_actual = "lector"
                                st.rerun()
                        
                        st.markdown("<hr style='margin:10px 0; opacity:0.3;'>", unsafe_allow_html=True)
                
                # Paginación
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
                st.info("No se encontraron resultados. Intenta ajustar los filtros de búsqueda.")

        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            st.exception(e)

    # --- VISTA 2: LECTOR ---
    elif st.session_state.vista_actual == "lector":
        try:
            df = pd.read_csv(CSV_URL)
            df.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in df.columns]
            
            sel_row = df[df['ticker'].str.lower() == st.session_state.tesis_seleccionada.lower()].iloc[0]
            
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
                st.markdown(f'<h2 style="color:#00ffad; margin:0;">{nombre} <span style="color:#444; font-size:0.6em;">({ticker})</span></h2>', unsafe_allow_html=True)
            
            with col_actions:
                if st.button("⭐"):
                    st.toast("Añadido a favoritos", icon="⭐")
            
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                rating = str(sel_row.get('rating', 'N/A')).upper()
                rating_color = "#00ffad" if "BUY" in rating else "#f23645" if "SELL" in rating else "#ff9800"
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color:{rating_color};">{rating}</div>
                    <div class="metric-label">Rating</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                fecha = str(sel_row.get('fecha', 'N/A'))
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color:white;">{fecha}</div>
                    <div class="metric-label">Fecha</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                sector = str(sel_row.get('sector', 'N/A'))
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color:#0096ff;">{sector}</div>
                    <div class="metric-label">Sector</div>
                </div>
                ''', unsafe_allow_html=True)
            
            with col4:
                autor = str(sel_row.get('autor', 'N/A'))
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-value" style="color:#ff9800;">{autor}</div>
                    <div class="metric-label">Analista</div>
                </div>
                ''', unsafe_allow_html=True)
            
            if 'resumen' in sel_row and pd.notna(sel_row['resumen']):
                st.markdown("---")
                st.markdown("### 📝 Resumen Ejecutivo")
                st.info(sel_row['resumen'])
            
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
                            <div class="metric-value" style="color:{color};">{value}</div>
                            <div class="metric-label">{label}</div>
                        </div>
                        ''', unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📄 Documento Completo")
            
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
