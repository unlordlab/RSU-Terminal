# modules/rsrw.py
# ============================================================
# RSRW Scanner v3.0
# ============================================================
# Los datos RS son pre-computados por GitHub Actions cada 30 min
# y almacenados en un GitHub Gist. Este módulo solo lee el Gist
# (fetch instantáneo) y renderiza la UI para los 100 usuarios.
#
# El VWAP intradía sigue siendo on-demand (1 ticker, ok).
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timezone, timedelta
import yfinance as yf

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

GIST_FILENAME  = "rsrw_scan.json"
CACHE_TTL_SECS = 300          # 5 min cache del Gist en Streamlit
BENCHMARK      = "SPY"

# Colores del sistema RSU
C_GREEN  = "#00ffad"
C_CYAN   = "#00d9ff"
C_RED    = "#f23645"
C_ORANGE = "#ff9800"
C_BG     = "#0c0e12"
C_BG2    = "#1a1e26"
C_BORDER = "#00ffad33"

# =============================================================================
# CARGA DE DATOS DESDE GIST
# =============================================================================

@st.cache_data(ttl=CACHE_TTL_SECS, show_spinner=False)
def load_gist_data(gist_id: str) -> dict | None:
    """
    Descarga el JSON pre-computado del Gist.
    Cache de 5 min en Streamlit — todos los usuarios comparten el mismo fetch.
    """
    try:
        url = f"https://api.github.com/gists/{gist_id}"
        r   = requests.get(url, timeout=10, headers={"Accept": "application/vnd.github.v3+json"})
        r.raise_for_status()
        content = r.json()["files"][GIST_FILENAME]["content"]
        return json.loads(content)
    except Exception as e:
        return None


def get_scan_data() -> dict | None:
    """Obtiene datos del scan con fallback informativo."""
    gist_id = st.secrets.get("RSRW_GIST_ID", "")
    if not gist_id:
        return None
    return load_gist_data(gist_id)


def parse_scan_data(data: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Convierte el JSON del Gist en DataFrames listos para la UI.
    Retorna (stocks_df, sectors_df, meta_dict).
    """
    meta    = data.get("meta", {})
    stocks  = data.get("stocks", {})
    sectors = data.get("sectors", {})

    # --- DataFrame de stocks ---
    if stocks:
        df = pd.DataFrame.from_dict(stocks, orient="index")
        df.index.name = "Ticker"

        # Renombrar columnas para UI
        rename = {
            "rs_score":     "RS_Score",
            "rs_5d":        "RS_5d",
            "rs_20d":       "RS_20d",
            "rs_60d":       "RS_60d",
            "rs_vs_sector": "RS_vs_Sector",
            "rvol":         "RVOL",
            "sector":       "Sector",
            "price":        "Precio",
        }
        df = df.rename(columns=rename)

        # Asegurar tipos numéricos
        for col in ["RS_Score", "RS_5d", "RS_20d", "RS_60d", "RS_vs_Sector", "RVOL", "Precio"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["RS_Score", "RVOL"])
    else:
        df = pd.DataFrame()

    # --- DataFrame de sectores ---
    if sectors:
        sector_df = pd.DataFrame.from_dict(sectors, orient="index")
        sector_df.index.name = "Sector"
        for col in ["RS", "Return"]:
            if col in sector_df.columns:
                sector_df[col] = pd.to_numeric(sector_df[col], errors="coerce")
    else:
        sector_df = pd.DataFrame()

    return df, sector_df, meta


# =============================================================================
# HELPERS UI
# =============================================================================

def _data_freshness(meta: dict) -> tuple[str, bool]:
    """Devuelve (texto_freshness, is_fresh)."""
    ts = meta.get("timestamp_utc", "")
    if not ts:
        return "Sin timestamp", False
    try:
        dt  = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = now - dt
        mins = int(age.total_seconds() / 60)
        if mins < 60:
            label = f"Actualizado hace {mins} min"
        else:
            label = f"Actualizado hace {mins // 60}h {mins % 60}min"
        fresh = age < timedelta(hours=2)
        return label, fresh
    except:
        return ts[:16], True


def _badge(text: str, kind: str = "info") -> str:
    classes = {"info": "badge-info", "strong": "badge-strong", "hot": "badge-hot"}
    return f'<span class="badge {classes.get(kind,"badge-info)}">{text}</span>'


def _metric_card(value: str, label: str, color: str = "white", sub: str = "") -> str:
    sub_html = f'<div style="font-family:\'Courier New\',monospace;color:{color};font-size:11px;margin-top:5px;letter-spacing:1px;">{sub}</div>' if sub else ""
    return f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{color};">{value}</div>
        <div class="metric-label">{label}</div>
        {sub_html}
    </div>"""


def _compact_alert(ticker: str, dev: float) -> None:
    """Alerta VWAP compacta de una línea."""
    if dev > 2:
        st.success(f"**{ticker}** — {dev:+.1f}% sobre VWAP · Presión compradora sostenida · Stop en VWAP")
    elif dev > 0.5:
        st.info(f"**{ticker}** — {dev:+.1f}% sobre VWAP · Tendencia alcista · Buscar pullback al VWAP")
    elif dev > -0.5:
        st.warning(f"**{ticker}** — {dev:+.1f}% · Zona de equilibrio · Esperar breakout con volumen >1.5x")
    elif dev > -2:
        st.warning(f"**{ticker}** — {dev:.1f}% bajo VWAP · Presión vendedora · Reducir o esperar recuperación")
    else:
        st.error(f"**{ticker}** — {dev:.1f}% bajo VWAP · Vendedores dominan · Evitar largos")


# =============================================================================
# CSS DEL SISTEMA (compacto — referencia roadmap_2026.py)
# =============================================================================

RSRW_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

.stApp { background: #0c0e12; }

h1,h2,h3,h4,h5,h6 {
    font-family:'VT323',monospace !important;
    color:#00ffad !important;
    text-transform:uppercase;
    letter-spacing:2px;
}
h1 {
    font-size:3.5rem !important;
    text-shadow:0 0 20px #00ffad66;
    border-bottom:2px solid #00ffad;
    padding-bottom:15px;
    margin-bottom:30px !important;
}
p,li { font-family:'Courier New',monospace; color:#ccc !important; line-height:1.8; font-size:.95rem; }
strong { color:#00ffad; font-weight:bold; }
ul { list-style:none; padding-left:0; }
ul li::before { content:"▸ "; color:#00ffad; font-weight:bold; margin-right:8px; }
hr { border:none; height:1px; background:linear-gradient(90deg,transparent,#00ffad,transparent); margin:40px 0; }

.main-header  { text-align:center; margin-bottom:30px; padding:20px 0; }
.main-title   { font-family:'VT323',monospace !important; color:#00ffad !important; font-size:3.5rem; text-shadow:0 0 20px #00ffad66; border-bottom:2px solid #00ffad; padding-bottom:15px; margin-bottom:10px; text-transform:uppercase; letter-spacing:3px; }
.main-subtitle{ font-family:'Courier New',monospace; color:#00d9ff; font-size:1rem; max-width:700px; margin:0 auto; letter-spacing:3px; text-transform:uppercase; }

.terminal-box { background:linear-gradient(135deg,#0c0e12 0%,#1a1e26 100%); border:1px solid #00ffad44; border-radius:8px; padding:25px; margin:20px 0; box-shadow:0 0 15px #00ffad11; }
.section-header { font-family:'VT323',monospace; color:#00ffad; font-size:1.6rem; text-transform:uppercase; letter-spacing:3px; margin-bottom:15px; border-left:4px solid #00ffad; padding-left:15px; }
.section-divider { display:block; height:1px; background:linear-gradient(90deg,transparent,#00ffad,transparent); margin:40px 0; border:none; }

.group-container { border:1px solid #00ffad33; border-radius:8px; overflow:hidden; background:#0c0e12; margin-bottom:20px; box-shadow:0 0 10px #00ffad0a; }
.group-header    { background:linear-gradient(135deg,#0c0e12 0%,#1a1e26 100%); padding:15px 20px; border-bottom:1px solid #00ffad33; display:flex; justify-content:space-between; align-items:center; }
.group-title     { font-family:'VT323',monospace !important; margin:0; color:#00ffad !important; font-size:1.3rem !important; text-transform:uppercase; letter-spacing:2px; }
.group-content   { padding:20px; background:#0c0e12; }

.metric-card  { background:linear-gradient(135deg,#0c0e12 0%,#1a1e26 100%); border:1px solid #00ffad33; border-radius:8px; padding:20px 15px; text-align:center; box-shadow:0 0 10px #00ffad0a; }
.metric-value { font-family:'VT323',monospace; font-size:2.2rem; color:white; margin-bottom:5px; letter-spacing:1px; }
.metric-label { font-family:'Courier New',monospace; font-size:.65rem; color:#666; text-transform:uppercase; letter-spacing:2px; }

.badge       { display:inline-flex; align-items:center; gap:5px; padding:4px 12px; border-radius:4px; font-family:'VT323',monospace; font-size:.95rem; text-transform:uppercase; letter-spacing:1px; }
.badge-hot   { background:rgba(242,54,69,.15); color:#f23645; border:1px solid rgba(242,54,69,.4); }
.badge-strong{ background:rgba(0,255,173,.15); color:#00ffad; border:1px solid rgba(0,255,173,.4); }
.badge-info  { background:rgba(0,217,255,.1);  color:#00d9ff; border:1px solid rgba(0,217,255,.3); }
.badge-warn  { background:rgba(255,152,0,.1);  color:#ff9800; border:1px solid rgba(255,152,0,.3); }

.help-box   { background:#0c0e12; border-left:4px solid #00ffad; padding:15px 20px; margin:10px 0; border-radius:0 8px 8px 0; }
.help-title { font-family:'VT323',monospace; color:#00ffad; font-size:1.1rem; text-transform:uppercase; letter-spacing:2px; margin-bottom:5px; }
.help-text  { font-family:'Courier New',monospace; color:#aaa; font-size:12px; line-height:1.6; }

.stButton>button[kind="secondary"] { background-color:transparent !important; border:1px solid #00ffad !important; color:#00ffad !important; font-family:'VT323',monospace !important; font-size:1.2rem !important; letter-spacing:3px !important; text-transform:uppercase !important; }
.stButton>button[kind="secondary"]:hover { background-color:rgba(0,255,173,.1) !important; box-shadow:0 0 15px #00ffad33 !important; }

.freshness-ok  { color:#00ffad; font-family:'Courier New',monospace; font-size:12px; }
.freshness-old { color:#f23645; font-family:'Courier New',monospace; font-size:12px; }
</style>
"""


# =============================================================================
# RENDER PRINCIPAL
# =============================================================================

def render():
    st.markdown(RSRW_CSS, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <div style="font-family:'VT323',monospace;font-size:1rem;color:#666;margin-bottom:10px;letter-spacing:2px;">
            [DATA PRE-COMPUTED BY GITHUB ACTIONS // REFRESH EVERY 30 MIN]
        </div>
        <div class="main-title">🔍 SCANNER RS/RW PRO</div>
        <div class="main-subtitle">
            ANÁLISIS INSTITUCIONAL DE FUERZA RELATIVA // ROTACIÓN SECTORIAL
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── Carga de datos ───────────────────────────────────────────────────────
    with st.spinner("Cargando datos..."):
        raw = get_scan_data()

    if raw is None:
        st.error("❌ No se pudieron obtener los datos del scanner.")
        st.info("""
        **Posibles causas:**
        - `RSRW_GIST_ID` no está configurado en los secrets de Streamlit.
        - El Gist no existe o no es público.
        - El workflow de GitHub Actions aún no ha ejecutado.

        **Para configurar:** añade `RSRW_GIST_ID` en *Settings → Secrets* de Streamlit Cloud.
        """)
        st.stop()

    results, sector_data, meta = parse_scan_data(raw)

    if results.empty:
        st.warning("⚠️ El Gist existe pero no contiene datos de stocks. Espera al próximo ciclo de Actions.")
        st.stop()

    # Badge de freshness + metadata
    freshness_text, is_fresh = _data_freshness(meta)
    freshness_class = "freshness-ok" if is_fresh else "freshness-old"
    freshness_icon  = "●" if is_fresh else "⚠"

    scored  = meta.get("tickers_scored", len(results))
    total   = meta.get("tickers_total",  "—")
    version = meta.get("version", "—")
    spy_perf = float(meta.get("spy_perf_20d", 0.0))

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:20px;">
        <span class="badge badge-info">▸ {scored} TICKERS &nbsp;|&nbsp; {len(sector_data)} SECTORES &nbsp;|&nbsp; v{version}</span>
        &nbsp;
        <span class="{freshness_class}">{freshness_icon} {freshness_text}</span>
    </div>
    """, unsafe_allow_html=True)

    # ─── Guía educativa ───────────────────────────────────────────────────────
    with st.expander("📚 Guía Completa: Dominando el Análisis RS/RW", expanded=False):
        tab1, tab2, tab3 = st.tabs(["🎯 Conceptos", "📊 Estrategias", "⚠️ Riesgos"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                ### ¿Qué es la Fuerza Relativa (RS)?

                La Fuerza Relativa **NO es el RSI**. Mide cuánto un activo supera (o
                subperforma) al benchmark del mercado (S&P 500).

                **Fórmula:**
                ```
                RS = Retorno del Stock − Retorno del SPY
                ```

                **¿Por qué importa?**
                El dinero institucional rota entre sectores. El RS te muestra dónde
                acumulan posiciones **antes** de que sea obvio en los titulares.

                ### Score Compuesto Multi-Timeframe

                | Timeframe | Peso | Qué mide |
                |-----------|------|----------|
                | **5 días** | 50% | Momentum inmediato |
                | **20 días** | 30% | Tendencia mensual |
                | **60 días** | 20% | Contexto trimestral |

                > ⚠️ **Nota**: Este score pondera fuertemente el corto plazo (5d = 50%).
                > No es el RS de O'Neil/IBD (percentil 1-99 sobre 252d). Es un indicador
                > de momentum reciente, no de liderazgo relativo a largo plazo.
                """)
            with col2:
                st.markdown("""
                ### Relative Volume (RVOL)

                El RVOL mide si el volumen actual es anormal vs su media de 20 días.

                **Umbrales clave:**
                - **1.0–1.3**: Volumen normal
                - **1.5–2.0**: 🔥 Interés institucional confirmado
                - **2.0–3.0**: 💥 Evento significativo (earnings, upgrade)
                - **>3.0**: ⚠️ Parabolic move — cuidado con reversión

                ### Contexto Sectorial

                Un stock puede tener RS positivo vs SPY pero negativo vs su sector.
                Eso indica que el sector entero sube y este es el **menos fuerte**.

                **RS vs Sector:**
                - **Positivo** → Líder dentro de su sector
                - **Negativo** → Laggard (evitar)
                """)

        with tab2:
            st.markdown("""
            ### Setup Largo (condiciones ideales)
            1. **Mercado**: SPY > 20 EMA
            2. **Scanner**: RS_Score > 3% + RVOL > 1.5
            3. **Sector**: ETF del sector con RS positivo
            4. **Entrada**: Pullback al VWAP intradía o 9 EMA diaria
            5. **Stop Loss**: Bajo el mínimo del día o −2%
            6. **Target**: 2R–3R o cuando RS cruce a negativo

            ### Setup Corto
            1. **Mercado**: SPY < 20 EMA
            2. **Scanner**: RS_Score < −3%
            3. **Entrada**: Rebote al VWAP con rechazo
            4. **Stop**: Sobre el máximo del día

            ### Gestión de Riesgo
            - Máximo 5% del portfolio por trade
            - Máximo 3 stocks del mismo sector (correlación)
            - Si RS cruza a negativo → reducir 50% automáticamente
            """)

        with tab3:
            st.markdown("""
            ### Trampas comunes

            **1. RS alto sin volumen (RVOL < 1.0)**
            Subida por falta de oferta, no demanda real. Evitar.

            **2. Solo RS_5d positivo, RS_20d y RS_60d negativos**
            Rebote técnico en tendencia bajista. Esperar confirmación en 20d.

            **3. Stock fuerte en sector débil**
            RS vs SPY positivo pero RS vs Sector negativo. No es fuerza real.

            **4. Ignorar el contexto macro**
            En correcciones del 10%+, incluso los líderes RS caen. Reducir tamaño.

            **5. Datos del fin de semana / pre-market**
            El RVOL puede aparecer inflado si el volumen del último día es 0. El worker
            filtra esto, pero ten en cuenta que los datos son de cierre diario.
            """)

    # ─── Configuración del scanner ────────────────────────────────────────────
    st.markdown('<div class="section-header">⚙️ CONFIGURACIÓN DEL SCANNER</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="help-box"><div class="help-title">📊 RVOL Mínimo</div>
        <div class="help-text">Filtra sin interés institucional. <strong>1.5</strong> = confirmación.</div></div>""",
        unsafe_allow_html=True)
        min_rvol = st.slider("RVOL", 1.0, 3.0, 1.2, 0.1, label_visibility="collapsed")

    with c2:
        st.markdown("""<div class="help-box"><div class="help-title">🎯 Umbral RS (%)</div>
        <div class="help-text">Mínimo de outperformance vs SPY. <strong>3%</strong> = sweet spot.</div></div>""",
        unsafe_allow_html=True)
        rs_threshold = st.slider("RS %", 1, 10, 3, 1, label_visibility="collapsed") / 100.0

    with c3:
        st.markdown("""<div class="help-box"><div class="help-title">📈 Top N Resultados</div>
        <div class="help-text"><strong>20</strong> es ideal para revisión diaria.</div></div>""",
        unsafe_allow_html=True)
        top_n = st.slider("Top N", 10, 50, 20, 5, label_visibility="collapsed")

    # Filtro de sector
    sectores_disponibles = ["Todos"] + sorted(results["Sector"].unique().tolist())
    sector_filter = st.selectbox("Filtrar por sector:", sectores_disponibles, index=0)

    # ─── Aplicar filtros ──────────────────────────────────────────────────────
    results_filtered = results.copy()
    if sector_filter != "Todos":
        results_filtered = results_filtered[results_filtered["Sector"] == sector_filter]

    # ─── Dashboard de métricas ────────────────────────────────────────────────
    mc = st.columns(5)

    with mc[0]:
        color = C_GREEN if spy_perf >= 0 else C_RED
        icon  = "▲" if spy_perf >= 0 else "▼"
        st.markdown(_metric_card(f"{spy_perf:+.2%}", "SPY // 20D", color, f"{icon} TENDENCIA"), unsafe_allow_html=True)

    with mc[1]:
        strong = len(results_filtered[results_filtered["RS_Score"] > rs_threshold])
        st.markdown(_metric_card(str(strong), "STRONG RS", C_GREEN, f"▸ >{rs_threshold:.0%} vs SPY"), unsafe_allow_html=True)

    with mc[2]:
        high_rvol = len(results_filtered[results_filtered["RVOL"] > 1.5])
        st.markdown(_metric_card(str(high_rvol), "HIGH RVOL", C_ORANGE, "▸ >1.5× VOLUMEN"), unsafe_allow_html=True)

    with mc[3]:
        setups = len(results_filtered[(results_filtered["RS_Score"] > rs_threshold) & (results_filtered["RVOL"] > min_rvol)])
        st.markdown(_metric_card(str(setups), "SETUPS ACTIVOS", C_CYAN, "▸ RS+VOL CONFIRMADO"), unsafe_allow_html=True)

    with mc[4]:
        if not sector_data.empty and "RS" in sector_data.columns:
            top_sector    = sector_data["RS"].idxmax()
            top_sector_rs = sector_data.loc[top_sector, "RS"]
            st.markdown(_metric_card(top_sector, "SECTOR LÍDER", C_GREEN, f"▸ {top_sector_rs:+.2%} vs SPY"), unsafe_allow_html=True)
        else:
            st.markdown(_metric_card("—", "SECTOR LÍDER"), unsafe_allow_html=True)

    # ─── Rotación sectorial ───────────────────────────────────────────────────
    if not sector_data.empty and "RS" in sector_data.columns:
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🔄 ROTACIÓN SECTORIAL</div>', unsafe_allow_html=True)

        sd_sorted = sector_data.sort_values("RS", ascending=False)
        colors    = [C_GREEN if x > 0 else C_RED for x in sd_sorted["RS"]]

        fig_sector = go.Figure(go.Bar(
            x=sd_sorted.index,
            y=sd_sorted["RS"],
            marker_color=colors,
            text=[f"{v:+.1%}" for v in sd_sorted["RS"]],
            textposition="outside",
            textfont=dict(family="Courier New", size=11, color="white"),
        ))
        fig_sector.update_layout(
            template="plotly_dark",
            paper_bgcolor=C_BG,
            plot_bgcolor=C_BG,
            height=300,
            margin=dict(l=0, r=0, b=60, t=20),
            yaxis=dict(tickformat=".1%", gridcolor="#1a1e26"),
            xaxis=dict(tickfont=dict(family="Courier New", size=10)),
            showlegend=False,
        )
        st.plotly_chart(fig_sector, use_container_width=True)

    # ─── Tablas RS / RW ───────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    col_rs, col_rw = st.columns(2)

    with col_rs:
        st.markdown("""
        <div class="group-container">
            <div class="group-header">
                <div class="group-title">🚀 TOP RS — FUERZA RELATIVA</div>
            </div>
        </div>""", unsafe_allow_html=True)

        df_rs = (
            results_filtered[results_filtered["RS_Score"] > rs_threshold]
            .nlargest(top_n, "RS_Score")
            .copy()
        )
        if not df_rs.empty:
            df_rs["Setup"] = df_rs.apply(
                lambda x: "🔥 Prime" if x["RVOL"] > 1.5 and x["RS_vs_Sector"] > 0.02
                else ("💪 Strong" if x["RS_vs_Sector"] > 0 else "📈 Momentum"),
                axis=1,
            )
            display_cols = ["RS_Score", "RS_5d", "RS_20d", "RS_60d", "RVOL", "RS_vs_Sector", "Sector", "Setup"]
            display_cols = [c for c in display_cols if c in df_rs.columns]

            fmt = {
                "RS_Score":     "{:+.2%}",
                "RS_5d":        "{:+.2%}",
                "RS_20d":       "{:+.2%}",
                "RS_60d":       "{:+.2%}",
                "RVOL":         "{:.2f}x",
                "RS_vs_Sector": "{:+.2%}",
            }
            st.dataframe(
                df_rs[display_cols].style
                .format(fmt)
                .background_gradient(subset=["RS_Score"], cmap="Greens")
                .background_gradient(subset=["RVOL"],     cmap="YlOrBr"),
                use_container_width=True,
                height=min(400, 35 + len(df_rs) * 35),
            )
        else:
            st.info("No hay setups que cumplan los criterios actuales.")

    with col_rw:
        st.markdown("""
        <div class="group-container">
            <div class="group-header">
                <div class="group-title">🔻 TOP RW — DEBILIDAD RELATIVA</div>
            </div>
        </div>""", unsafe_allow_html=True)

        df_rw = (
            results_filtered[results_filtered["RS_Score"] < -0.01]
            .nsmallest(top_n, "RS_Score")
            .copy()
        )
        if not df_rw.empty:
            df_rw["Alerta"] = df_rw.apply(
                lambda x: "🔻 Distribution" if x["RVOL"] > 1.5 and x["RS_vs_Sector"] < -0.02
                else ("📉 Weak" if x["RS_vs_Sector"] < 0 else "⬇️ Lagging"),
                axis=1,
            )
            display_cols = ["RS_Score", "RS_5d", "RS_20d", "RS_60d", "RVOL", "RS_vs_Sector", "Sector", "Alerta"]
            display_cols = [c for c in display_cols if c in df_rw.columns]

            fmt = {
                "RS_Score":     "{:+.2%}",
                "RS_5d":        "{:+.2%}",
                "RS_20d":       "{:+.2%}",
                "RS_60d":       "{:+.2%}",
                "RVOL":         "{:.2f}x",
                "RS_vs_Sector": "{:+.2%}",
            }
            st.dataframe(
                df_rw[display_cols].style
                .format(fmt)
                .background_gradient(subset=["RS_Score"], cmap="Reds_r")
                .background_gradient(subset=["RVOL"],     cmap="OrRd"),
                use_container_width=True,
                height=min(400, 35 + len(df_rw) * 35),
            )
        else:
            st.success("✅ No hay debilidad significativa con los filtros actuales.")

    # Exportar CSV
    if not results_filtered.empty:
        ts_str = datetime.now().strftime("%Y%m%d_%H%M")
        csv = results_filtered.to_csv().encode("utf-8")
        st.download_button(
            "📥 Exportar CSV Completo",
            csv,
            f"RS_Scan_{ts_str}.csv",
            "text/csv",
        )

    # ─── VWAP Intradía ────────────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎯 VALIDACIÓN INTRADÍA CON VWAP</div>', unsafe_allow_html=True)

    with st.expander("💡 Cómo integrar VWAP con el Scanner RS", expanded=False):
        st.markdown("""
        El **VWAP** (Volume Weighted Average Price) es la referencia de "valor justo"
        para los institucionales durante la sesión.

        **Flujo recomendado:**
        1. El scanner identifica un stock con RS alto
        2. Entras aquí y compruebas si el precio está sobre VWAP
        3. Sobre VWAP + RS alto = momentum confirmado → entrada en pullback al VWAP
        4. Bajo VWAP + RS alto = divergencia → esperar recuperación antes de entrar
        """)

    vc1, vc2 = st.columns([3, 1])
    with vc1:
        symbol = st.text_input(
            "Ticker para análisis VWAP:", "NVDA",
            help="Introduce un ticker del scanner o cualquier stock"
        ).upper()
    with vc2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_vwap = st.button("📈 Analizar VWAP", use_container_width=True, type="secondary")

    if run_vwap:
        try:
            df_v = yf.download(symbol, period="1d", interval="5m", progress=False)
            if not df_v.empty:
                if isinstance(df_v.columns, pd.MultiIndex):
                    df_v.columns = df_v.columns.get_level_values(0)

                tp          = (df_v["High"] + df_v["Low"] + df_v["Close"]) / 3
                df_v["VWAP"] = (tp * df_v["Volume"]).cumsum() / df_v["Volume"].cumsum()

                price = float(df_v["Close"].iloc[-1])
                vwap  = float(df_v["VWAP"].iloc[-1])
                dev   = ((price - vwap) / vwap) * 100

                fig_vwap = go.Figure()
                fig_vwap.add_trace(go.Candlestick(
                    x=df_v.index,
                    open=df_v["Open"], high=df_v["High"],
                    low=df_v["Low"],  close=df_v["Close"],
                    name=symbol,
                    increasing_line_color=C_GREEN,
                    decreasing_line_color=C_RED,
                ))
                fig_vwap.add_trace(go.Scatter(
                    x=df_v.index, y=df_v["VWAP"],
                    line=dict(color=C_ORANGE, width=2),
                    name="VWAP",
                ))
                fig_vwap.add_hrect(
                    y0=vwap * 0.995, y1=vwap * 1.005,
                    fillcolor="rgba(255,170,0,0.08)", line_width=0,
                    annotation_text="Zona VWAP",
                )
                fig_vwap.update_layout(
                    template="plotly_dark",
                    paper_bgcolor=C_BG, plot_bgcolor=C_BG,
                    height=420,
                    margin=dict(l=0, r=0, b=0, t=30),
                    title=f"{symbol} — Precio: ${price:.2f} | VWAP: ${vwap:.2f} | Desv: {dev:+.2f}%",
                    xaxis_rangeslider_visible=False,
                )
                st.plotly_chart(fig_vwap, use_container_width=True)
                _compact_alert(symbol, dev)
            else:
                st.warning("Sin datos intradía disponibles. El mercado puede estar cerrado.")
        except Exception as e:
            st.error(f"Error: {e}")

    # ─── Footer ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;margin-top:60px;padding:20px;border-top:1px solid #00ffad22;">
        <p style="font-family:'VT323',monospace;color:#444;font-size:.9rem;letter-spacing:2px;">
            [END OF TRANSMISSION // RSRW_SCANNER_v3.0]<br>
            [BENCHMARK: SPY // UNIVERSE: S&amp;P500 // TIMEFRAMES: 5D · 20D · 60D]<br>
            [DATA: GITHUB ACTIONS CRON // STATUS: ACTIVE]
        </p>
    </div>
    """, unsafe_allow_html=True)
