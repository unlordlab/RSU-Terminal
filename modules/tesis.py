import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timedelta

def render():
    # CSS simplificado - solo estilos básicos sin conflictos
    st.markdown("""
    <style>
        .badge-buy {
            background-color: rgba(0, 255, 173, 0.15);
            color: #00ffad;
            border: 1px solid #00ffad44;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            display: inline-block;
        }
        
        .badge-hold {
            background-color: rgba(255, 152, 0, 0.15);
            color: #ff9800;
            border: 1px solid #ff980044;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            display: inline-block;
        }
        
        .badge-sell {
            background-color: rgba(242, 54, 69, 0.15);
            color: #f23645;
            border: 1px solid #f2364544;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            display: inline-block;
        }
        
        .badge-new {
            background-color: rgba(0, 150, 255, 0.15);
            color: #0096ff;
            border: 1px solid #0096ff44;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            display: inline-block;
        }
        
        .tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            margin-right: 4px;
            background: #1a1e26;
            color: #888;
            border: 1px solid #2a2e36;
        }
        
        /* Botón Leer Tesis - Verde iluminado */
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
            box-shadow: 0 0 20px rgba(0, 255, 173, 0.5) !important;
            border-color: #00ffad !important;
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
        
        .metric-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        
        .tesis-card {
            background: #11141a;
            border: 1px solid #1a1e26;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 20px;
            transition: box-shadow 0.2s ease;
        }
        
        .tesis-card:hover {
            box-shadow: 0px 0px 15px rgba(0, 255, 173, 0.1);
            border-color: #00ffad44;
        }
    </style>
    """, unsafe_allow_html=True)

    # Inicializar estado
    if 'vista_actual' not in st.session_state:
        st.session_state.vista_actual = "galeria"
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

            # Filtros simples en el área principal (NO en sidebar)
            col_search, col_rating, col_items = st.columns([2, 1, 1])
            
            with col_search:
                busqueda = st.text_input("🔍 Buscar activo:", "", placeholder="Ej: AAPL, Tesla...").lower()
            
            with col_rating:
                ratings_disponibles = ["Todos"] + sorted(list(df['rating'].unique())) if 'rating' in df.columns else ["Todos"]
                filtro_rating = st.selectbox("Rating:", ratings_disponibles)
            
            with col_items:
                st.session_state.tesis_por_pagina = st.selectbox("Mostrar:", [6, 9, 12, 15], index=1)

            # Aplicar filtros
            df_view = df.copy()
            
            if busqueda and 'ticker' in df_view.columns and 'nombre' in df_view.columns:
                mask = (df_view['ticker'].str.contains(busqueda, case=False, na=False) | 
                       df_view['nombre'].str.contains(busqueda, case=False, na=False))
                df_view = df_view[mask]
            
            if filtro_rating != "Todos" and 'rating' in df_view.columns:
                df_view = df_view[df_view['rating'] == filtro_rating]
            
            # Ordenar por fecha
            if 'fecha_dt' in df_view.columns:
                df_view = df_view.sort_values(by='fecha_dt', ascending=False)

            st.markdown("---")

            if len(df_view) > 0:
                total_paginas = max(1, (len(df_view) + st.session_state.tesis_por_pagina - 1) // st.session_state.tesis_por_pagina)
                
                if st.session_state.pagina > total_paginas:
                    st.session_state.pagina = 1
                
                inicio = (st.session_state.pagina - 1) * st.session_state.tesis_por_pagina
                fin = inicio + st.session_state.tesis_por_pagina
                df_pagina = df_view.iloc[inicio:fin]
                
                # Grid de tarjetas
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
                        
                        # Card
                        st.markdown('<div class="tesis-card">', unsafe_allow_html=True)
                        
                        # Imagen
                        img_url = str(row.get('imagenencabezado', '')).strip()
                        
                        if img_url and img_url.startswith('http'):
                            try:
                                st.image(img_url, use_container_width=True)
                            except:
                                st.markdown(f'<div style="height:180px; background:linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); display:flex; align-items:center; justify-content:center;"><span style="color:#00ffad; font-size:3rem; font-weight:bold;">{ticker}</span></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="height:180px; background:linear-gradient(135deg, #1a1e26 0%, #0c0e12 100%); display:flex; align-items:center; justify-content:center;"><span style="color:#00ffad; font-size:3rem; font-weight:bold;">{ticker}</span></div>', unsafe_allow_html=True)
                        
                        # Badges
                        badge_cols = st.columns([1, 1, 2])
                        with badge_cols[0]:
                            st.markdown(f'<span class="{badge_class}">{badge_text}</span>', unsafe_allow_html=True)
                        with badge_cols[1]:
                            if es_nuevo:
                                st.markdown('<span class="badge-new">NEW</span>', unsafe_allow_html=True)
                        
                        # Info
                        st.markdown(f"""
                        <div style="padding:0 15px; margin-top:10px;">
                            <div style="color:#00ffad; font-size:1.2rem; font-weight:bold;">{ticker}</div>
                            <div style="color:#888; font-size:0.85rem;">{nombre}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Tags
                        if sector or autor:
                            tags_html = ""
                            if sector:
                                tags_html += f'<span class="tag">{sector}</span>'
                            if autor:
                                tags_html += f'<span class="tag">👤 {autor}</span>'
                            st.markdown(f'<div style="padding:0 15px; margin-top:8px;">{tags_html}</div>', unsafe_allow_html=True)
                        
                        # Fecha
                        st.markdown(f'<div style="padding:0 15px; color:#555; font-size:0.75rem; font-family:monospace; margin-top:8px; margin-bottom:10px;">📅 {fecha}</div>', unsafe_allow_html=True)
                        
                        # Botón Leer Tesis - Verde iluminado
                        if st.button(f"Leer Tesis →", key=f"btn_{ticker}_{idx}"):
                            st.session_state.tesis_seleccionada = ticker
                            st.session_state.vista_actual = "lector"
                            st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                
                # Paginación
                if total_paginas > 1:
                    st.markdown("---")
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
                if st.button("⭐ Fav"):
                    st.toast("Añadido a favoritos", icon="⭐")
            
            st.markdown("---")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                rating = str(sel_row.get('rating', 'N/A')).upper()
                rating_color = "#00ffad" if "BUY" in rating else "#f23645" if "SELL" in rating else "#ff9800"
                st.markdown(f'<div class="metric-card"><div style="font-size:2rem; font-weight:bold; color:{rating_color};">{rating}</div><div style="color:#888; font-size:0.9rem; margin-top:5px;">Rating</div></div>', unsafe_allow_html=True)
            
            with col2:
                fecha = str(sel_row.get('fecha', 'N/A'))
                st.markdown(f'<div class="metric-card"><div style="font-size:2rem; font-weight:bold; color:white;">{fecha}</div><div style="color:#888; font-size:0.9rem; margin-top:5px;">Fecha</div></div>', unsafe_allow_html=True)
            
            with col3:
                sector = str(sel_row.get('sector', 'N/A'))
                st.markdown(f'<div class="metric-card"><div style="font-size:2rem; font-weight:bold; color:#0096ff;">{sector}</div><div style="color:#888; font-size:0.9rem; margin-top:5px;">Sector</div></div>', unsafe_allow_html=True)
            
            with col4:
                autor = str(sel_row.get('autor', 'N/A'))
                st.markdown(f'<div class="metric-card"><div style="font-size:2rem; font-weight:bold; color:#ff9800;">{autor}</div><div style="color:#888; font-size:0.9rem; margin-top:5px;">Analista</div></div>', unsafe_allow_html=True)
            
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
                        st.markdown(f'<div class="metric-card"><div style="font-size:2rem; font-weight:bold; color:{color};">{value}</div><div style="color:#888; font-size:0.9rem; margin-top:5px;">{label}</div></div>', unsafe_allow_html=True)
            
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
