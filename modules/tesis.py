import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime

# ─────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVyU3x2DEQVczsqgmUwMSS1SS99Npe8LO-Om5n-VmXKuT-PYxuX65YinMg5XcGZehYE2df6jQuCzTo/pub?output=csv"

TESIS_POR_PAGINA_DEFAULT = 9
REQUIRED_COLS = ['ticker', 'rating', 'fecha']

RATING_CONFIG = {
    "BUY":  {"class": "badge-buy",  "color": "#00ffad", "label": "BUY"},
    "SELL": {"class": "badge-sell", "color": "#f23645", "label": "SELL"},
    "HOLD": {"class": "badge-hold", "color": "#ff9800", "label": "HOLD"},
}

def get_rating_cfg(rating: str) -> dict:
    r = rating.upper()
    if "BUY"  in r: return RATING_CONFIG["BUY"]
    if "SELL" in r: return RATING_CONFIG["SELL"]
    return RATING_CONFIG["HOLD"]

def upside_bar(value: float, width: int = 10) -> str:
    """Genera una barra de bloques estilo terminal para el upside."""
    clamped = max(-100, min(100, value))
    filled = round(abs(clamped) / 100 * width)
    bar = "▰" * filled + "▱" * (width - filled)
    color = "#00ffad" if value >= 0 else "#f23645"
    return f'<span style="color:{color}; font-family:monospace; letter-spacing:2px;">{bar}</span>'

# ─────────────────────────────────────────
# CARGA DE DATOS (fuera de render — caché real)
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data(url: str) -> pd.DataFrame:
    data = pd.read_csv(url)
    data.columns = [col.strip().lower().replace(" ", "").replace("_", "") for col in data.columns]
    missing = [c for c in REQUIRED_COLS if c not in data.columns]
    if missing:
        raise ValueError(f"Columnas requeridas no encontradas: {missing}")
    data['fecha_dt'] = pd.to_datetime(data['fecha'], dayfirst=True, errors='coerce')
    data['dias_desde'] = (datetime.now() - data['fecha_dt']).dt.days
    data['es_nuevo'] = data['dias_desde'] <= 7
    return data

# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

        .stApp {
            background: #0c0e12;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'VT323', monospace !important;
            color: #00ffad !important;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        h1 {
            font-size: 3.2rem !important;
            text-shadow: 0 0 20px #00ffad66;
            border-bottom: 2px solid #00ffad;
            padding-bottom: 12px;
            margin-bottom: 20px !important;
        }

        h2 {
            font-size: 1.8rem !important;
            color: #00d9ff !important;
            border-left: 4px solid #00ffad;
            padding-left: 12px;
            margin-top: 30px !important;
        }

        p, li {
            font-family: 'Courier New', monospace;
            color: #ccc !important;
            line-height: 1.7;
            font-size: 0.9rem;
        }

        strong { color: #00ffad; }

        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #00ffad44, transparent);
            margin: 30px 0;
        }

        ul { list-style: none; padding-left: 0; }
        ul li::before { content: "▸ "; color: #00ffad; font-weight: bold; margin-right: 6px; }

        /* ── Badges ── */
        .badge-buy, .badge-sell, .badge-hold, .badge-new {
            padding: 3px 10px;
            border-radius: 4px;
            font-family: 'VT323', monospace;
            font-size: 1rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: inline-block;
        }
        .badge-buy  { background: rgba(0,255,173,0.12); color:#00ffad; border:1px solid #00ffad44; }
        .badge-sell { background: rgba(242,54,69,0.12);  color:#f23645; border:1px solid #f2364544; }
        .badge-hold { background: rgba(255,152,0,0.12);  color:#ff9800; border:1px solid #ff980044; }
        .badge-new  { background: rgba(0,150,255,0.12);  color:#0096ff; border:1px solid #0096ff44; }

        /* ── Tags ── */
        .tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 4px;
            background: #1a1e26;
            color: #888;
            border: 1px solid #2a2e36;
        }

        /* ── Tarjeta de galería ── */
        .tesis-card {
            background: #0c0e12;
            border: 1px solid #1a2030;
            border-radius: 6px;
            overflow: hidden;
            margin-bottom: 20px;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .tesis-card:hover {
            border-color: #00ffad44;
            box-shadow: 0 0 18px rgba(0,255,173,0.08);
        }
        .tesis-card-body { padding: 14px 16px; }

        /* ── Terminal box (lector) ── */
        .terminal-box {
            background: linear-gradient(135deg, #0c0e12 0%, #1a1e26 100%);
            border: 1px solid #00ffad33;
            border-radius: 6px;
            padding: 22px 24px;
            margin: 16px 0;
            box-shadow: 0 0 12px #00ffad0a;
        }

        /* ── Metric cards (lector) ── */
        .strategy-card {
            background: #0c0e12;
            border: 1px solid #1a2a3a;
            border-radius: 6px;
            padding: 16px;
            text-align: center;
        }
        .strategy-card .metric-val {
            font-family: 'VT323', monospace;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 4px;
        }
        .strategy-card .metric-label {
            font-family: 'Courier New', monospace;
            font-size: 0.75rem;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* ── Phase box ── */
        .phase-box {
            background: #0c0e12;
            border-left: 3px solid #00ffad;
            padding: 16px 20px;
            margin: 12px 0;
            border-radius: 0 6px 6px 0;
        }

        /* ── Risk box ── */
        .risk-box {
            background: linear-gradient(135deg, #1a0f0f 0%, #261a1a 100%);
            border: 1px solid #f2364533;
            border-radius: 6px;
            padding: 18px 22px;
            margin: 12px 0;
        }

        /* ── Highlight quote ── */
        .highlight-quote {
            background: #00ffad0d;
            border: 1px solid #00ffad22;
            border-radius: 6px;
            padding: 18px;
            margin: 16px 0;
            font-family: 'VT323', monospace;
            font-size: 1.2rem;
            color: #00ffad;
            text-align: center;
            letter-spacing: 1px;
        }

        /* ── Botones ── */
        .stButton > button {
            width: 100%;
            background: #0c0e12 !important;
            color: #00ffad !important;
            border: 1px solid #00ffad44 !important;
            border-radius: 4px !important;
            padding: 8px 16px !important;
            font-family: 'VT323', monospace !important;
            font-size: 1.05rem !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover {
            background: #00ffad !important;
            color: #0c0e12 !important;
            box-shadow: 0 0 18px rgba(0,255,173,0.4) !important;
        }

        .back-btn button {
            background: #1a1e26 !important;
            color: #ccc !important;
            border: 1px solid #333 !important;
        }
        .back-btn button:hover {
            background: #f23645 !important;
            color: white !important;
            border-color: #f23645 !important;
            box-shadow: none !important;
        }

        /* ── Inputs ── */
        .stTextInput input, .stSelectbox div[data-baseweb] {
            background: #11141a !important;
            border-color: #1a2030 !important;
            color: #ccc !important;
            font-family: 'Courier New', monospace !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
# VISTA: GALERÍA
# ─────────────────────────────────────────
def vista_galeria(df: pd.DataFrame):
    # Header
    st.markdown("""
    <div style="text-align:center; margin-bottom:30px;">
        <div style="font-family:'VT323',monospace; font-size:0.95rem; color:#444; margin-bottom:8px; letter-spacing:2px;">
            [SECURE CONNECTION ESTABLISHED // ENCRYPTION: AES-256]
        </div>
        <h1>📄 TERMINAL DE ANÁLISIS</h1>
        <div style="font-family:'VT323',monospace; color:#00d9ff; font-size:1.1rem; letter-spacing:3px;">
            BASE DE DATOS DE TESIS // ANÁLISIS TÉCNICO & FUNDAMENTAL
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filtros
    col_search, col_rating, col_items = st.columns([2, 1, 1])
    with col_search:
        busqueda = st.text_input("🔍 Buscar activo:", "", placeholder="Ej: AAPL, Tesla...").lower()
    with col_rating:
        ratings_disponibles = ["Todos"] + sorted(df['rating'].dropna().unique().tolist()) if 'rating' in df.columns else ["Todos"]
        filtro_rating = st.selectbox("Rating:", ratings_disponibles)
    with col_items:
        tesis_por_pagina = st.selectbox("Mostrar:", [6, 9, 12, 15], index=1)

    # Resetear página si cambian filtros
    filtro_key = f"{busqueda}_{filtro_rating}_{tesis_por_pagina}"
    if st.session_state.get('_last_filter') != filtro_key:
        st.session_state.pagina = 1
        st.session_state['_last_filter'] = filtro_key

    # Aplicar filtros
    df_view = df.copy()
    if busqueda:
        mask = (
            df_view.get('ticker', pd.Series(dtype=str)).str.contains(busqueda, case=False, na=False) |
            df_view.get('nombre', pd.Series(dtype=str)).str.contains(busqueda, case=False, na=False)
        )
        df_view = df_view[mask]
    if filtro_rating != "Todos" and 'rating' in df_view.columns:
        df_view = df_view[df_view['rating'] == filtro_rating]
    if 'fecha_dt' in df_view.columns:
        df_view = df_view.sort_values('fecha_dt', ascending=False)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Contador
    total = len(df_view)
    st.markdown(
        f'<p style="color:#555; font-family:monospace; font-size:0.8rem; margin-bottom:16px;">'
        f'▸ {total} ANÁLISIS ENCONTRADOS</p>',
        unsafe_allow_html=True
    )

    if total == 0:
        st.markdown("""
        <div class="risk-box" style="text-align:center;">
            <p style="color:#f23645 !important;">⚠ SIN RESULTADOS — Ajusta los filtros de búsqueda</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Paginación
    total_paginas = max(1, (total + tesis_por_pagina - 1) // tesis_por_pagina)
    pagina = st.session_state.pagina
    inicio = (pagina - 1) * tesis_por_pagina
    df_pagina = df_view.iloc[inicio: inicio + tesis_por_pagina]

    # Grid
    cols = st.columns(3)
    for idx, row in df_pagina.reset_index(drop=True).iterrows():
        ticker  = str(row.get('ticker', 'N/A')).upper()
        nombre  = str(row.get('nombre', ''))
        fecha   = str(row.get('fecha', 'S/D'))
        rating  = str(row.get('rating', 'HOLD')).upper()
        sector  = str(row.get('sector', ''))
        autor   = str(row.get('autor', ''))
        es_nuevo = bool(row.get('es_nuevo', False))
        img_url  = str(row.get('imagenencabezado', '')).strip()
        rcfg     = get_rating_cfg(rating)

        with cols[idx % 3]:
            st.markdown('<div class="tesis-card">', unsafe_allow_html=True)

            # Imagen / fallback
            if img_url and img_url.startswith('http'):
                try:
                    st.image(img_url, use_container_width=True)
                except:
                    _card_fallback(ticker)
            else:
                _card_fallback(ticker)

            # Cuerpo
            new_badge = '<span class="badge-new">NEW</span>&nbsp;' if es_nuevo else ''
            tags_html = ""
            if sector: tags_html += f'<span class="tag">{sector}</span>'
            if autor:  tags_html += f'<span class="tag">👤 {autor}</span>'

            st.markdown(f"""
            <div class="tesis-card-body">
                <div style="margin-bottom:8px;">
                    <span class="{rcfg['class']}">{rcfg['label']}</span>&nbsp;{new_badge}
                </div>
                <div style="font-family:'VT323',monospace; color:#00ffad; font-size:1.4rem; letter-spacing:1px;">{ticker}</div>
                <div style="font-family:'Courier New',monospace; color:#888; font-size:0.8rem; margin-bottom:8px;">{nombre}</div>
                <div style="margin-bottom:8px;">{tags_html}</div>
                <div style="font-family:monospace; color:#444; font-size:0.72rem;">📅 {fecha}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("LEER TESIS →", key=f"btn_{ticker}_{idx}"):
                st.session_state.tesis_row = row.to_dict()
                st.session_state.vista_actual = "lector"
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # Controles de paginación
    if total_paginas > 1:
        st.markdown("<hr>", unsafe_allow_html=True)
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("← ANTERIOR", disabled=pagina <= 1, key="btn_prev"):
                st.session_state.pagina -= 1
                st.rerun()
        with col_info:
            st.markdown(
                f'<p style="text-align:center; font-family:\'VT323\',monospace; color:#555; font-size:1.1rem;">'
                f'PÁGINA {pagina} / {total_paginas}</p>',
                unsafe_allow_html=True
            )
        with col_next:
            if st.button("SIGUIENTE →", disabled=pagina >= total_paginas, key="btn_next"):
                st.session_state.pagina += 1
                st.rerun()

def _card_fallback(ticker: str):
    st.markdown(
        f'<div style="height:160px; background:linear-gradient(135deg,#1a1e26,#0c0e12); '
        f'display:flex; align-items:center; justify-content:center;">'
        f'<span style="font-family:\'VT323\',monospace; color:#00ffad; font-size:3rem; '
        f'text-shadow:0 0 20px #00ffad66; letter-spacing:4px;">{ticker}</span></div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────
# VISTA: LECTOR
# ─────────────────────────────────────────
def vista_lector():
    row = st.session_state.tesis_row

    ticker  = str(row.get('ticker', '')).upper()
    nombre  = str(row.get('nombre', ticker))
    rating  = str(row.get('rating', 'N/A')).upper()
    fecha   = str(row.get('fecha', 'N/A'))
    sector  = str(row.get('sector', 'N/A'))
    autor   = str(row.get('autor', 'N/A'))
    rcfg    = get_rating_cfg(rating)

    # Header de conexión
    st.markdown(f"""
    <div style="font-family:'VT323',monospace; font-size:0.9rem; color:#444; letter-spacing:2px; margin-bottom:4px;">
        [LOADING ANALYSIS // TICKER: {ticker}]
    </div>
    """, unsafe_allow_html=True)

    # Título + botón volver
    col_back, col_title = st.columns([1, 5])
    with col_back:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("⬅ VOLVER"):
            st.session_state.vista_actual = "galeria"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col_title:
        st.markdown(
            f'<h1 style="border-bottom:none; padding-bottom:0; font-size:2.2rem !important;">'
            f'{nombre} <span style="color:#333; font-size:1rem;">// {ticker}</span></h1>',
            unsafe_allow_html=True
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Métricas principales — 4 strategy-cards
    col1, col2, col3, col4 = st.columns(4)
    _metric_card(col1, rating,  "RATING",   rcfg['color'])
    _metric_card(col2, fecha,   "FECHA",    "#ccc")
    _metric_card(col3, sector,  "SECTOR",   "#00d9ff")
    _metric_card(col4, autor,   "ANALISTA", "#ff9800")

    # Resumen ejecutivo
    resumen = row.get('resumen', None)
    if resumen and pd.notna(resumen) and str(resumen).strip():
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<h2>📝 RESUMEN EJECUTIVO</h2>', unsafe_allow_html=True)
        st.markdown(f'<div class="terminal-box"><p style="color:#fff !important; font-size:0.95rem;">{resumen}</p></div>', unsafe_allow_html=True)

    # Métricas clave
    metricas = _build_metricas(row)
    if metricas:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<h2>📊 MÉTRICAS CLAVE</h2>', unsafe_allow_html=True)
        mcols = st.columns(len(metricas))
        for i, (label, value, color, extra_html) in enumerate(metricas):
            with mcols[i]:
                st.markdown(f"""
                <div class="strategy-card">
                    <div class="metric-val" style="color:{color};">{value}</div>
                    {extra_html}
                    <div class="metric-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)

    # Documento
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<h2>📄 DOCUMENTO COMPLETO</h2>', unsafe_allow_html=True)

    url_doc = str(row.get('urldoc', '')).strip()
    if url_doc:
        if "/pub" in url_doc:
            url_doc = url_doc.split("?")[0].split("&")[0] + "?embedded=true"
        with st.spinner("Cargando documento..."):
            components.iframe(url_doc, height=820, scrolling=True)
    else:
        st.markdown("""
        <div class="risk-box" style="text-align:center;">
            <p style="color:#f23645 !important;">⚠ Sin documento disponible para este análisis.</p>
        </div>
        """, unsafe_allow_html=True)

    # Footer de transmisión
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center; padding:16px 0;">
        <p style="font-family:'VT323',monospace; color:#333; font-size:0.85rem; letter-spacing:1px;">
            [END OF ANALYSIS // {ticker}_v1.0]<br>
            [FECHA: {fecha}]<br>
            [STATUS: ACTIVE]
        </p>
    </div>
    """, unsafe_allow_html=True)

def _metric_card(col, value: str, label: str, color: str):
    with col:
        st.markdown(f"""
        <div class="strategy-card">
            <div class="metric-val" style="color:{color}; font-size:1.6rem;">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

def _build_metricas(row: dict) -> list:
    """Construye lista de (label, value, color, extra_html) para métricas clave."""
    items = []

    if _has(row, 'precioobjetivo'):
        items.append(("🎯 PRECIO OBJETIVO", f"${row['precioobjetivo']}", "#00ffad", ""))

    if _has(row, 'precioactual'):
        items.append(("💵 PRECIO ACTUAL", f"${row['precioactual']}", "#ccc", ""))

    if _has(row, 'upside'):
        val = float(row['upside'])
        color = "#00ffad" if val >= 0 else "#f23645"
        bar = upside_bar(val)
        items.append(("📈 UPSIDE", f"{val:+.1f}%", color, f'<div style="margin:6px 0 4px;">{bar}</div>'))

    if _has(row, 'riesgo'):
        riesgo = str(row['riesgo']).upper()
        rcolor = "#00ffad" if "BAJO" in riesgo else "#ff9800" if "MEDIO" in riesgo else "#f23645"
        items.append(("⚠ RIESGO", riesgo, rcolor, ""))

    return items

def _has(row: dict, key: str) -> bool:
    v = row.get(key, None)
    if v is None: return False
    try: return pd.notna(v) and str(v).strip() != ""
    except: return False

# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────
def render():
    inject_css()

    # Inicializar estado
    if 'vista_actual' not in st.session_state:
        st.session_state.vista_actual = "galeria"
    if 'pagina' not in st.session_state:
        st.session_state.pagina = 1
    if 'tesis_row' not in st.session_state:
        st.session_state.tesis_row = None

    # ── VISTA GALERÍA ──
    if st.session_state.vista_actual == "galeria":
        try:
            df = load_data(CSV_URL)
            vista_galeria(df)
        except ValueError as e:
            st.markdown(f"""
            <div class="risk-box">
                <p style="color:#f23645 !important;">⚠ Error de estructura en los datos: {e}</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div class="risk-box">
                <p style="color:#f23645 !important;">⚠ Error al cargar datos: {e}</p>
            </div>
            """, unsafe_allow_html=True)

    # ── VISTA LECTOR ──
    elif st.session_state.vista_actual == "lector":
        if not st.session_state.tesis_row:
            st.session_state.vista_actual = "galeria"
            st.rerun()
        try:
            vista_lector()
        except Exception as e:
            st.markdown(f"""
            <div class="risk-box">
                <p style="color:#f23645 !important;">⚠ Error al cargar análisis: {e}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="back-btn">', unsafe_allow_html=True)
            if st.button("← VOLVER A LA GALERÍA"):
                st.session_state.vista_actual = "galeria"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
