# modules/rsrw.py
# ============================================================
# RSRW Scanner v3.1 — Modo Híbrido
# ============================================================
# MODO A (recomendado): Lee JSON pre-computado de GitHub Gist.
#   → Configura RSRW_GIST_ID en Streamlit secrets.
#   → GitHub Actions actualiza el Gist 2x/día.
#   → 0 carga de yfinance para los 100 usuarios.
#
# MODO B (fallback): Scan on-demand con botón.
#   → Activo si RSRW_GIST_ID no está configurado.
#   → Resultados cacheados en session_state (TTL 30 min).
#   → Solo el primer usuario en 30 min descarga datos.
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import json
import time
from datetime import datetime, timezone, timedelta
import yfinance as yf

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

GIST_FILENAME   = "rsrw_scan.json"
GIST_CACHE_TTL  = 300       # segundos — cache del Gist en Streamlit
SCAN_CACHE_MINS = 30        # minutos — cache del scan on-demand
BENCHMARK       = "SPY"
PERIODS         = [5, 20, 60]
WEIGHTS         = {5: 0.50, 20: 0.30, 60: 0.20}
BATCH_SIZE      = 80

C_GREEN  = "#00ffad"
C_CYAN   = "#00d9ff"
C_RED    = "#f23645"
C_ORANGE = "#ff9800"
C_BG     = "#0c0e12"
C_BG2    = "#1a1e26"

SECTOR_ETFS = {
    "Tecnología":           "XLK",
    "Salud":                "XLV",
    "Financieros":          "XLF",
    "Consumo Discrecional": "XLY",
    "Consumo Básico":       "XLP",
    "Industriales":         "XLI",
    "Energía":              "XLE",
    "Materiales":           "XLB",
    "Servicios Públicos":   "XLU",
    "Bienes Raíces":        "XLRE",
    "Comunicaciones":       "XLC",
}

GICS_MAP = {
    "Information Technology": "Tecnología",
    "Health Care":            "Salud",
    "Financials":             "Financieros",
    "Consumer Discretionary": "Consumo Discrecional",
    "Consumer Staples":       "Consumo Básico",
    "Industrials":            "Industriales",
    "Energy":                 "Energía",
    "Materials":              "Materiales",
    "Utilities":              "Servicios Públicos",
    "Real Estate":            "Bienes Raíces",
    "Communication Services": "Comunicaciones",
}

# =============================================================================
# MODO A — CARGA DESDE GIST
# =============================================================================

@st.cache_data(ttl=GIST_CACHE_TTL, show_spinner=False)
def _load_gist(gist_id: str) -> dict | None:
    try:
        r = requests.get(
            f"https://api.github.com/gists/{gist_id}",
            timeout=10,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        r.raise_for_status()
        content = r.json()["files"][GIST_FILENAME]["content"]
        data = json.loads(content)
        if data.get("stocks") and len(data["stocks"]) > 10:
            return data
        return None
    except Exception:
        return None


def _parse_gist(data: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    meta    = data.get("meta", {})
    stocks  = data.get("stocks", {})
    sectors = data.get("sectors", {})

    if stocks:
        df = pd.DataFrame.from_dict(stocks, orient="index")
        df.index.name = "Ticker"
        rename = {
            "rs_score": "RS_Score", "rs_5d": "RS_5d", "rs_20d": "RS_20d",
            "rs_60d": "RS_60d", "rs_vs_sector": "RS_vs_Sector",
            "rvol": "RVOL", "sector": "Sector", "price": "Precio",
        }
        df = df.rename(columns=rename)
        for col in ["RS_Score","RS_5d","RS_20d","RS_60d","RS_vs_Sector","RVOL","Precio"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["RS_Score", "RVOL"])
    else:
        df = pd.DataFrame()

    if sectors:
        sdf = pd.DataFrame.from_dict(sectors, orient="index")
        sdf.index.name = "Sector"
        for col in ["RS", "Return"]:
            if col in sdf.columns:
                sdf[col] = pd.to_numeric(sdf[col], errors="coerce")
    else:
        sdf = pd.DataFrame()

    return df, sdf, meta


# =============================================================================
# MODO B — SCAN ON-DEMAND (engine limpio)
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def _get_sp500_tickers() -> tuple[list, dict]:
    try:
        df = pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            match="Symbol"
        )[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        sector_map = dict(zip(
            df["Symbol"].str.replace(".", "-", regex=False),
            df["GICS Sector"]
        ))
        if len(tickers) >= 490:
            return tickers, sector_map
    except Exception:
        pass
    fallback = [
        "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","AVGO","JPM",
        "LLY","V","UNH","XOM","MA","JNJ","PG","HD","MRK","COST","ABBV","CVX",
        "BAC","KO","CRM","PEP","TMO","WFC","NFLX","ORCL","AMD","ACN","ADBE","LIN",
        "MCD","PM","WMT","CSCO","IBM","GS","GE","HON","DIS","CAT","RTX","AMGN",
        "VZ","T","CMCSA","PFE","ABT","TXN","MS","NEE","BMY","SPGI","DHR","UNP",
        "LOW","BLK","ISRG","GILD","SYK","CI","BSX","ELV","ITW","DE","NOC","LMT",
        "EMR","ETN","PH","GD","USB","TFC","SCHW","COF","MCO","ICE","CME","PGR",
        "COP","EOG","SLB","OXY","PSX","MPC","VLO","WMB","FCX","NEM","DOW","ECL",
        "PLD","AMT","CCI","EQIX","PSA","O","DLR","SPG","VICI","CRWD","PANW",
        "SNOW","PLTR","NET","UBER","ABNB","DXCM","ZTS","IQV","EW","IDXX","BIIB",
        "MRNA","HUM","YUM","SBUX","BKNG","MAR","TTWO","EA","NKE","LULU",
        "TGT","DG","DLTR","TJX","UPS","FDX","NSC","CSX","DAL","UAL","LUV",
        "INTC","QCOM","MU","KLAC","LRCX","AMAT","SNPS","CDNS","ADI","MCHP",
        "K","HSY","GIS","MDLZ","KHC","TSN","BG","NUE","VMC","PPG","ALB",
        "NEE","SO","DUK","AEP","SRE","EXC","XEL","ED","WEC","AWK",
    ]
    return list(dict.fromkeys(fallback)), {}


def _run_scan_engine(prog_ph) -> tuple[pd.DataFrame, pd.DataFrame, float, dict]:
    tickers, sector_map = _get_sp500_tickers()
    all_symbols = list(dict.fromkeys([BENCHMARK] + list(SECTOR_ETFS.values()) + tickers))
    batches = [all_symbols[i:i+BATCH_SIZE] for i in range(0, len(all_symbols), BATCH_SIZE)]

    close_dict  = {}
    volume_dict = {}
    prog_bar    = prog_ph.progress(0, text="Iniciando descarga...")

    for idx, batch in enumerate(batches):
        prog_bar.progress(
            (idx + 1) / len(batches),
            text=f"Descargando lote {idx+1}/{len(batches)} ({len(batch)} símbolos)..."
        )
        for attempt in range(3):
            try:
                if idx > 0:
                    time.sleep(0.5)
                raw = yf.download(
                    batch, period="70d", interval="1d",
                    progress=False, threads=True, timeout=30, auto_adjust=True,
                )
                if raw.empty:
                    raise ValueError("Empty")
                if isinstance(raw.columns, pd.MultiIndex):
                    if "Close" in raw.columns.get_level_values(0):
                        for t in raw["Close"].columns:
                            s = raw["Close"][t].dropna()
                            if len(s) > 5:
                                close_dict[t] = s
                    if "Volume" in raw.columns.get_level_values(0):
                        for t in raw["Volume"].columns:
                            s = raw["Volume"][t].dropna()
                            if len(s) > 5:
                                volume_dict[t] = s
                else:
                    if "Close" in raw.columns and len(batch) == 1:
                        close_dict[batch[0]]  = raw["Close"].dropna()
                        volume_dict[batch[0]] = raw["Volume"].dropna()
                break
            except Exception:
                if attempt < 2:
                    time.sleep(1)

    prog_bar.progress(1.0, text="Calculando métricas RS...")

    if not close_dict:
        prog_ph.empty()
        return pd.DataFrame(), pd.DataFrame(), 0.0, {}

    close  = pd.DataFrame(close_dict).sort_index().dropna(how="all")
    volume = pd.DataFrame(volume_dict).reindex(close.index).fillna(0)

    if BENCHMARK not in close.columns:
        prog_ph.empty()
        return pd.DataFrame(), pd.DataFrame(), 0.0, {}

    spy = close[BENCHMARK].dropna()
    spy_perf = float((spy.iloc[-1] / spy.iloc[-20]) - 1) if len(spy) >= 20 else 0.0

    sector_rs = {}
    for sname, etf in SECTOR_ETFS.items():
        if etf not in close.columns:
            continue
        s = close[etf].dropna()
        if len(s) < 20:
            continue
        sector_rs[sname] = {
            "RS":     round(float((s.iloc[-1]/s.iloc[-20])-1) - float((spy.iloc[-1]/spy.iloc[-20])-1), 6),
            "Return": round(float((s.iloc[-1]/s.iloc[-20])-1), 6),
            "ETF":    etf,
        }

    exclude = {BENCHMARK} | set(SECTOR_ETFS.values())
    results = {}

    for ticker in [t for t in close.columns if t not in exclude]:
        prices = close[ticker].dropna()
        if len(prices) < max(PERIODS):
            continue
        try:
            rs_by_p = {}
            for p in PERIODS:
                if len(prices) >= p and len(spy) >= p:
                    rs_by_p[f"RS_{p}d"] = round(
                        float((prices.iloc[-1]/prices.iloc[-p])-1) -
                        float((spy.iloc[-1]/spy.iloc[-p])-1), 6
                    )
            if not rs_by_p:
                continue

            avail    = [p for p in PERIODS if f"RS_{p}d" in rs_by_p]
            w_total  = sum(WEIGHTS[p] for p in avail)
            rs_score = sum(rs_by_p[f"RS_{p}d"] * (WEIGHTS[p]/w_total) for p in avail)

            sector       = GICS_MAP.get(sector_map.get(ticker, ""), "Otros")
            rs_vs_sector = 0.0
            if sector in sector_rs and "RS_20d" in rs_by_p:
                rs_vs_sector = round(rs_by_p["RS_20d"] - sector_rs[sector]["RS"], 6)

            rvol = 1.0
            if ticker in volume.columns:
                vs = volume[ticker].replace(0, np.nan).dropna()
                if len(vs) >= 5:
                    avg = float(vs.iloc[-20:].mean()) if len(vs) >= 20 else float(vs.mean())
                    cur = float(vs.iloc[-1])
                    rvol = round(min(max(cur/avg if avg > 0 else 1.0, 0.1), 20.0), 4)

            results[ticker] = {
                **rs_by_p,
                "RS_Score":     round(rs_score, 6),
                "RS_vs_Sector": rs_vs_sector,
                "RVOL":         rvol,
                "Sector":       sector,
                "Precio":       round(float(prices.iloc[-1]), 4),
            }
        except Exception:
            continue

    prog_ph.empty()

    df  = pd.DataFrame.from_dict(results, orient="index")
    df.index.name = "Ticker"
    sdf = pd.DataFrame.from_dict(sector_rs, orient="index") if sector_rs else pd.DataFrame()
    if not sdf.empty:
        sdf.index.name = "Sector"

    meta = {
        "timestamp_utc":  datetime.now(timezone.utc).isoformat(),
        "tickers_total":  len(tickers),
        "tickers_scored": len(df),
        "spy_perf_20d":   round(spy_perf, 6),
        "source":         "on-demand",
        "version":        "3.1",
    }
    return df, sdf, spy_perf, meta


# =============================================================================
# HELPERS UI
# =============================================================================

def _freshness_badge(meta: dict) -> tuple[str, bool]:
    ts = meta.get("timestamp_utc", "")
    if not ts:
        return "Sin timestamp", False
    try:
        dt   = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        age  = datetime.now(timezone.utc) - dt
        mins = int(age.total_seconds() / 60)
        label = f"hace {mins} min" if mins < 60 else f"hace {mins//60}h {mins%60}m"
        return label, age < timedelta(hours=3)
    except Exception:
        return ts[:16], True


def _metric_card(value, label, color="white", sub=""):
    sub_html = (
        f'<div style="font-family:Courier New,monospace;color:{color};'
        f'font-size:11px;margin-top:5px;letter-spacing:1px;">{sub}</div>'
    ) if sub else ""
    return f"""<div class="metric-card">
        <div class="metric-value" style="color:{color};">{value}</div>
        <div class="metric-label">{label}</div>{sub_html}
    </div>"""


def _vwap_alert(ticker, dev):
    if dev > 2:
        st.success(f"**{ticker}** — {dev:+.1f}% sobre VWAP · Presión compradora · Stop en VWAP")
    elif dev > 0.5:
        st.info(f"**{ticker}** — {dev:+.1f}% sobre VWAP · Sesgo alcista · Buscar pullback al VWAP")
    elif dev > -0.5:
        st.warning(f"**{ticker}** — {dev:+.1f}% · Zona equilibrio · Esperar breakout con volumen >1.5×")
    elif dev > -2:
        st.warning(f"**{ticker}** — {dev:.1f}% bajo VWAP · Presión vendedora · Reducir o esperar")
    else:
        st.error(f"**{ticker}** — {dev:.1f}% bajo VWAP · Vendedores dominan · Evitar largos")


def _render_footer():
    st.markdown("""
    <div style="text-align:center;margin-top:60px;padding:20px;border-top:1px solid #00ffad22;">
        <p style="font-family:'VT323',monospace;color:#444;font-size:.9rem;letter-spacing:2px;">
            [END OF TRANSMISSION // RSRW_SCANNER_v3.1]<br>
            [BENCHMARK: SPY // UNIVERSE: S&amp;P500 // TIMEFRAMES: 5D · 20D · 60D]<br>
            [COMPUTE: GITHUB ACTIONS 2×/DAY // STATUS: ACTIVE]
        </p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# CSS
# =============================================================================

RSRW_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
.stApp{background:#0c0e12}
h1,h2,h3,h4,h5,h6{font-family:'VT323',monospace!important;color:#00ffad!important;text-transform:uppercase;letter-spacing:2px}
h1{font-size:3.5rem!important;text-shadow:0 0 20px #00ffad66;border-bottom:2px solid #00ffad;padding-bottom:15px;margin-bottom:30px!important}
p,li{font-family:'Courier New',monospace;color:#ccc!important;line-height:1.8;font-size:.95rem}
strong{color:#00ffad;font-weight:bold}
ul{list-style:none;padding-left:0}ul li::before{content:"▸ ";color:#00ffad;font-weight:bold;margin-right:8px}
hr{border:none;height:1px;background:linear-gradient(90deg,transparent,#00ffad,transparent);margin:40px 0}
.main-header{text-align:center;margin-bottom:30px;padding:20px 0}
.main-title{font-family:'VT323',monospace!important;color:#00ffad!important;font-size:3.5rem;text-shadow:0 0 20px #00ffad66;border-bottom:2px solid #00ffad;padding-bottom:15px;margin-bottom:10px;text-transform:uppercase;letter-spacing:3px}
.main-subtitle{font-family:'Courier New',monospace;color:#00d9ff;font-size:1rem;max-width:700px;margin:0 auto;letter-spacing:3px;text-transform:uppercase}
.section-header{font-family:'VT323',monospace;color:#00ffad;font-size:1.6rem;text-transform:uppercase;letter-spacing:3px;margin-bottom:15px;border-left:4px solid #00ffad;padding-left:15px}
.group-container{border:1px solid #00ffad33;border-radius:8px;overflow:hidden;background:#0c0e12;margin-bottom:20px;box-shadow:0 0 10px #00ffad0a}
.group-header{background:linear-gradient(135deg,#0c0e12 0%,#1a1e26 100%);padding:15px 20px;border-bottom:1px solid #00ffad33;display:flex;justify-content:space-between;align-items:center}
.group-title{font-family:'VT323',monospace!important;margin:0;color:#00ffad!important;font-size:1.3rem!important;text-transform:uppercase;letter-spacing:2px}
.metric-card{background:linear-gradient(135deg,#0c0e12 0%,#1a1e26 100%);border:1px solid #00ffad33;border-radius:8px;padding:20px 15px;text-align:center;box-shadow:0 0 10px #00ffad0a}
.metric-value{font-family:'VT323',monospace;font-size:2.2rem;color:white;margin-bottom:5px;letter-spacing:1px}
.metric-label{font-family:'Courier New',monospace;font-size:.65rem;color:#666;text-transform:uppercase;letter-spacing:2px}
.badge{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:4px;font-family:'VT323',monospace;font-size:.95rem;text-transform:uppercase;letter-spacing:1px}
.badge-hot{background:rgba(242,54,69,.15);color:#f23645;border:1px solid rgba(242,54,69,.4)}
.badge-strong{background:rgba(0,255,173,.15);color:#00ffad;border:1px solid rgba(0,255,173,.4)}
.badge-info{background:rgba(0,217,255,.1);color:#00d9ff;border:1px solid rgba(0,217,255,.3)}
.badge-warn{background:rgba(255,152,0,.1);color:#ff9800;border:1px solid rgba(255,152,0,.3)}
.help-box{background:#0c0e12;border-left:4px solid #00ffad;padding:15px 20px;margin:10px 0;border-radius:0 8px 8px 0}
.help-title{font-family:'VT323',monospace;color:#00ffad;font-size:1.1rem;text-transform:uppercase;letter-spacing:2px;margin-bottom:5px}
.help-text{font-family:'Courier New',monospace;color:#aaa;font-size:12px;line-height:1.6}
.mode-banner{background:linear-gradient(135deg,#0c0e12,#1a1e26);border:1px solid #00d9ff33;border-radius:8px;padding:12px 20px;margin-bottom:20px;font-family:'Courier New',monospace;font-size:12px;color:#888}
.mode-banner b{color:#00d9ff}
.stButton>button[kind="secondary"]{background-color:transparent!important;border:1px solid #00ffad!important;color:#00ffad!important;font-family:'VT323',monospace!important;font-size:1.2rem!important;letter-spacing:3px!important;text-transform:uppercase!important}
.stButton>button[kind="secondary"]:hover{background-color:rgba(0,255,173,.1)!important;box-shadow:0 0 15px #00ffad33!important}
</style>"""


# =============================================================================
# RENDER
# =============================================================================

def render():
    st.markdown(RSRW_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="main-header">
        <div style="font-family:'VT323',monospace;font-size:1rem;color:#666;margin-bottom:10px;letter-spacing:2px;">
            [ANÁLISIS INSTITUCIONAL // S&amp;P 500 UNIVERSE]
        </div>
        <div class="main-title">🔍 SCANNER RS/RW PRO</div>
        <div class="main-subtitle">FUERZA RELATIVA // ROTACIÓN SECTORIAL</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Detectar modo ─────────────────────────────────────────────────────────
    gist_id   = st.secrets.get("RSRW_GIST_ID", "")
    gist_mode = bool(gist_id)

    results     = pd.DataFrame()
    sector_data = pd.DataFrame()
    meta        = {}
    spy_perf    = 0.0

    # ── MODO A: Gist ──────────────────────────────────────────────────────────
    if gist_mode:
        with st.spinner("Cargando datos..."):
            raw = _load_gist(gist_id)
        if raw:
            results, sector_data, meta = _parse_gist(raw)
            spy_perf = float(meta.get("spy_perf_20d", 0.0))
            freshness, is_fresh = _freshness_badge(meta)
            fc = C_GREEN if is_fresh else C_RED
            fi = "●" if is_fresh else "⚠"
            source_label = "GITHUB ACTIONS"
        else:
            # Gist configurado pero vacío → caer a on-demand
            gist_mode = False

    # ── MODO B: On-demand ─────────────────────────────────────────────────────
    if not gist_mode:
        source_label = "ON-DEMAND"
        freshness, is_fresh, fc, fi = "", False, C_ORANGE, "◎"

        st.markdown("""<div class="mode-banner">
            <b>MODO ON-DEMAND</b> — Los resultados se cachean 30 min entre usuarios.
            Configura <b>RSRW_GIST_ID</b> en Streamlit secrets para activar
            actualizaciones automáticas vía GitHub Actions.
        </div>""", unsafe_allow_html=True)

        # ¿Hay caché válido en session_state?
        cache_valid = False
        if "rsrw_cache" in st.session_state:
            cache    = st.session_state["rsrw_cache"]
            age_mins = (datetime.now(timezone.utc) - cache["ts"]).total_seconds() / 60
            if age_mins < SCAN_CACHE_MINS and not cache["results"].empty:
                results     = cache["results"]
                sector_data = cache["sectors"]
                meta        = cache["meta"]
                spy_perf    = float(meta.get("spy_perf_20d", 0.0))
                freshness   = f"Scan hace {int(age_mins)} min · caché {SCAN_CACHE_MINS} min"
                is_fresh, fc, fi = True, C_CYAN, "◉"
                cache_valid = True

        # Botón de scan centrado
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            btn_label = "🔄 Actualizar Scan" if cache_valid else "🔍 Ejecutar Scanner"
            run_scan  = st.button(btn_label, use_container_width=True, type="secondary")

        if run_scan:
            prog_ph = st.empty()
            df_r, df_s, spy_p, mt = _run_scan_engine(prog_ph)
            if df_r.empty:
                st.error("❌ No se obtuvieron resultados. Verifica conexión o intenta más tarde.")
            else:
                st.session_state["rsrw_cache"] = {
                    "results": df_r, "sectors": df_s,
                    "meta": mt, "ts": datetime.now(timezone.utc),
                }
                st.rerun()

        if results.empty:
            st.info("Pulsa **Ejecutar Scanner** para analizar el mercado.")
            _render_footer()
            return

    # ── Badge de estado ───────────────────────────────────────────────────────
    scored  = meta.get("tickers_scored", len(results))
    version = meta.get("version", "3.1")

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:20px;">
        <span class="badge badge-info">▸ {scored} TICKERS &nbsp;|&nbsp; {len(sector_data)} SECTORES &nbsp;|&nbsp; {source_label} v{version}</span>
        &nbsp;&nbsp;
        <span style="font-family:'Courier New',monospace;font-size:12px;color:{fc};">{fi} {freshness}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Guía educativa ────────────────────────────────────────────────────────
    with st.expander("📚 Guía Completa: Dominando el Análisis RS/RW", expanded=False):
        tab1, tab2, tab3 = st.tabs(["🎯 Conceptos", "📊 Estrategias", "⚠️ Riesgos"])
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                ### ¿Qué es la Fuerza Relativa (RS)?
                La Fuerza Relativa **NO es el RSI**. Mide cuánto supera un activo al S&P 500.

                **Fórmula:** `RS = Retorno Stock − Retorno SPY`

                **Score Multi-Timeframe:**

                | Timeframe | Peso |
                |-----------|------|
                | **5 días** | 50% |
                | **20 días** | 30% |
                | **60 días** | 20% |

                > ⚠️ Pondera fuertemente el corto plazo. No es el RS percentil de IBD/O'Neil.
                """)
            with col2:
                st.markdown("""
                ### Relative Volume (RVOL)

                | Rango | Señal |
                |-------|-------|
                | 1.0–1.3 | Normal |
                | 1.5–2.0 | 🔥 Interés institucional |
                | 2.0–3.0 | 💥 Evento significativo |
                | >3.0 | ⚠️ Posible reversión |

                ### RS vs Sector
                - **Positivo** → Líder dentro del sector
                - **Negativo** → Laggard (evitar)
                """)
        with tab2:
            st.markdown("""
            **Setup Largo ideal:**
            SPY > 20 EMA · RS_Score >3% · RVOL >1.5 · ETF sector positivo
            Entrada en pullback al VWAP · Stop −2% · Target 2R–3R

            **Setup Corto:** SPY < 20 EMA · RS_Score <−3% · Rebote al VWAP con rechazo

            **Riesgo:** máx 5% portfolio · máx 3 stocks mismo sector
            """)
        with tab3:
            st.markdown("""
            1. **RS alto sin volumen** (RVOL <1.0) → subida ficticia, sin demanda real
            2. **Solo RS_5d positivo**, RS_20d y RS_60d negativos → rebote en tendencia bajista
            3. **RS positivo vs SPY pero negativo vs sector** → no es fuerza, es el menos malo
            4. **Mercado en corrección >10%** → reducir tamaño aunque el RS sea positivo
            """)

    # ── Configuración ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⚙️ CONFIGURACIÓN DEL SCANNER</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="help-box"><div class="help-title">📊 RVOL Mínimo</div><div class="help-text">Filtra sin interés institucional. <strong>1.5</strong> = confirmación.</div></div>', unsafe_allow_html=True)
        min_rvol = st.slider("RVOL", 1.0, 3.0, 1.2, 0.1, label_visibility="collapsed")
    with c2:
        st.markdown('<div class="help-box"><div class="help-title">🎯 Umbral RS (%)</div><div class="help-text">Outperformance mínimo vs SPY. <strong>3%</strong> = sweet spot.</div></div>', unsafe_allow_html=True)
        rs_threshold = st.slider("RS %", 1, 10, 3, 1, label_visibility="collapsed") / 100.0
    with c3:
        st.markdown('<div class="help-box"><div class="help-title">📈 Top N Resultados</div><div class="help-text"><strong>20</strong> ideal para revisión diaria.</div></div>', unsafe_allow_html=True)
        top_n = st.slider("Top N", 10, 50, 20, 5, label_visibility="collapsed")

    sectores = ["Todos"] + sorted(results["Sector"].unique().tolist()) if "Sector" in results.columns else ["Todos"]
    sector_filter = st.selectbox("Filtrar por sector:", sectores)

    # ── Filtros ───────────────────────────────────────────────────────────────
    rf = results[results["Sector"] == sector_filter].copy() if sector_filter != "Todos" and "Sector" in results.columns else results.copy()

    # ── Métricas ──────────────────────────────────────────────────────────────
    mc = st.columns(5)
    with mc[0]:
        col = C_GREEN if spy_perf >= 0 else C_RED
        st.markdown(_metric_card(f"{spy_perf:+.2%}", "SPY // 20D", col, ("▲" if spy_perf>=0 else "▼")+" TENDENCIA"), unsafe_allow_html=True)
    with mc[1]:
        n = len(rf[rf["RS_Score"] > rs_threshold]) if "RS_Score" in rf.columns else 0
        st.markdown(_metric_card(str(n), "STRONG RS", C_GREEN, f"▸ >{rs_threshold:.0%} vs SPY"), unsafe_allow_html=True)
    with mc[2]:
        n = len(rf[rf["RVOL"] > 1.5]) if "RVOL" in rf.columns else 0
        st.markdown(_metric_card(str(n), "HIGH RVOL", C_ORANGE, "▸ >1.5× VOLUMEN"), unsafe_allow_html=True)
    with mc[3]:
        n = 0
        if "RS_Score" in rf.columns and "RVOL" in rf.columns:
            n = len(rf[(rf["RS_Score"] > rs_threshold) & (rf["RVOL"] > min_rvol)])
        st.markdown(_metric_card(str(n), "SETUPS ACTIVOS", C_CYAN, "▸ RS+VOL CONFIRMADO"), unsafe_allow_html=True)
    with mc[4]:
        if not sector_data.empty and "RS" in sector_data.columns:
            ts = sector_data["RS"].idxmax()
            st.markdown(_metric_card(ts, "SECTOR LÍDER", C_GREEN, f"▸ {sector_data.loc[ts,'RS']:+.2%} vs SPY"), unsafe_allow_html=True)
        else:
            st.markdown(_metric_card("—", "SECTOR LÍDER"), unsafe_allow_html=True)

    # ── Rotación sectorial ────────────────────────────────────────────────────
    if not sector_data.empty and "RS" in sector_data.columns:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">🔄 ROTACIÓN SECTORIAL</div>', unsafe_allow_html=True)
        sd = sector_data.sort_values("RS", ascending=False)
        fig_s = go.Figure(go.Bar(
            x=sd.index, y=sd["RS"],
            marker_color=[C_GREEN if v > 0 else C_RED for v in sd["RS"]],
            text=[f"{v:+.1%}" for v in sd["RS"]],
            textposition="outside",
            textfont=dict(family="Courier New", size=11, color="white"),
        ))
        fig_s.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_BG,
            height=300, margin=dict(l=0, r=0, b=60, t=20),
            yaxis=dict(tickformat=".1%", gridcolor="#1a1e26"),
            xaxis=dict(tickfont=dict(family="Courier New", size=10)),
            showlegend=False,
        )
        st.plotly_chart(fig_s, use_container_width=True)

    # ── Tablas RS / RW ────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    fmt = {
        "RS_Score": "{:+.2%}", "RS_5d": "{:+.2%}", "RS_20d": "{:+.2%}",
        "RS_60d": "{:+.2%}", "RVOL": "{:.2f}x", "RS_vs_Sector": "{:+.2%}",
    }
    col_rs, col_rw = st.columns(2)

    with col_rs:
        st.markdown('<div class="group-container"><div class="group-header"><div class="group-title">🚀 TOP RS — FUERZA RELATIVA</div></div></div>', unsafe_allow_html=True)
        if "RS_Score" in rf.columns:
            df_rs = rf[rf["RS_Score"] > rs_threshold].nlargest(top_n, "RS_Score").copy()
        else:
            df_rs = pd.DataFrame()
        if not df_rs.empty:
            df_rs["Setup"] = df_rs.apply(
                lambda x: "🔥 Prime" if x.get("RVOL",0)>1.5 and x.get("RS_vs_Sector",0)>0.02
                else ("💪 Strong" if x.get("RS_vs_Sector",0)>0 else "📈 Momentum"), axis=1
            )
            cols = [c for c in ["RS_Score","RS_5d","RS_20d","RS_60d","RVOL","RS_vs_Sector","Sector","Setup"] if c in df_rs.columns]
            styled = df_rs[cols].style.format({k:v for k,v in fmt.items() if k in cols})
            if "RS_Score" in cols: styled = styled.background_gradient(subset=["RS_Score"], cmap="Greens")
            if "RVOL"     in cols: styled = styled.background_gradient(subset=["RVOL"],     cmap="YlOrBr")
            st.dataframe(styled, use_container_width=True, height=min(400, 35+len(df_rs)*35))
        else:
            st.info("No hay setups con los criterios actuales.")

    with col_rw:
        st.markdown('<div class="group-container"><div class="group-header"><div class="group-title">🔻 TOP RW — DEBILIDAD RELATIVA</div></div></div>', unsafe_allow_html=True)
        if "RS_Score" in rf.columns:
            df_rw = rf[rf["RS_Score"] < -0.01].nsmallest(top_n, "RS_Score").copy()
        else:
            df_rw = pd.DataFrame()
        if not df_rw.empty:
            df_rw["Alerta"] = df_rw.apply(
                lambda x: "🔻 Distribution" if x.get("RVOL",0)>1.5 and x.get("RS_vs_Sector",0)<-0.02
                else ("📉 Weak" if x.get("RS_vs_Sector",0)<0 else "⬇️ Lagging"), axis=1
            )
            cols = [c for c in ["RS_Score","RS_5d","RS_20d","RS_60d","RVOL","RS_vs_Sector","Sector","Alerta"] if c in df_rw.columns]
            styled = df_rw[cols].style.format({k:v for k,v in fmt.items() if k in cols})
            if "RS_Score" in cols: styled = styled.background_gradient(subset=["RS_Score"], cmap="Reds_r")
            if "RVOL"     in cols: styled = styled.background_gradient(subset=["RVOL"],     cmap="OrRd")
            st.dataframe(styled, use_container_width=True, height=min(400, 35+len(df_rw)*35))
        else:
            st.success("✅ No hay debilidad significativa con los filtros actuales.")

    if not rf.empty:
        csv = rf.to_csv().encode("utf-8")
        st.download_button(
            "📥 Exportar CSV", csv,
            f"RS_Scan_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv",
        )

    # ── VWAP Intradía ─────────────────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎯 VALIDACIÓN INTRADÍA CON VWAP</div>', unsafe_allow_html=True)

    with st.expander("💡 Cómo integrar VWAP con el Scanner RS", expanded=False):
        st.markdown("RS alto → VWAP confirma → precio sobre VWAP = entrada en pullback (bajo riesgo).")

    vc1, vc2 = st.columns([3, 1])
    with vc1:
        symbol = st.text_input("Ticker para análisis VWAP:", "NVDA").upper()
    with vc2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_vwap = st.button("📈 Analizar VWAP", use_container_width=True, type="secondary")

    if run_vwap:
        try:
            df_v = yf.download(symbol, period="1d", interval="5m", progress=False)
            if not df_v.empty:
                if isinstance(df_v.columns, pd.MultiIndex):
                    df_v.columns = df_v.columns.get_level_values(0)
                tp = (df_v["High"] + df_v["Low"] + df_v["Close"]) / 3
                df_v["VWAP"] = (tp * df_v["Volume"]).cumsum() / df_v["Volume"].cumsum()
                price = float(df_v["Close"].iloc[-1])
                vwap  = float(df_v["VWAP"].iloc[-1])
                dev   = ((price - vwap) / vwap) * 100
                fig_v = go.Figure()
                fig_v.add_trace(go.Candlestick(
                    x=df_v.index, open=df_v["Open"], high=df_v["High"],
                    low=df_v["Low"], close=df_v["Close"], name=symbol,
                    increasing_line_color=C_GREEN, decreasing_line_color=C_RED,
                ))
                fig_v.add_trace(go.Scatter(
                    x=df_v.index, y=df_v["VWAP"],
                    line=dict(color=C_ORANGE, width=2), name="VWAP",
                ))
                fig_v.add_hrect(y0=vwap*0.995, y1=vwap*1.005,
                    fillcolor="rgba(255,170,0,0.08)", line_width=0,
                    annotation_text="Zona VWAP")
                fig_v.update_layout(
                    template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_BG,
                    height=420, margin=dict(l=0, r=0, b=0, t=30),
                    title=f"{symbol} — ${price:.2f} | VWAP ${vwap:.2f} | {dev:+.2f}%",
                    xaxis_rangeslider_visible=False,
                )
                st.plotly_chart(fig_v, use_container_width=True)
                _vwap_alert(symbol, dev)
            else:
                st.warning("Sin datos intradía. El mercado puede estar cerrado.")
        except Exception as e:
            st.error(f"Error: {e}")

    _render_footer()
