# modules/rsrw.py  v4.0
# ═══════════════════════════════════════════════════════════════
# RSRW Scanner — Metodología de Percentil RS (anti-ruido)
# ─────────────────────────────────────────────────────────────
# CAMBIOS vs v3.x:
#   · RS Score → Percentil 0-99 dentro del universo (como IBD)
#   · Períodos: 21d, 63d, 126d (elimina el dominio del 5d)
#   · Pesos: 20% corto / 35% medio / 45% largo (liderazgo sostenido)
#   · EMA suavizado sobre la serie RS diaria (elimina spikes earnings)
#   · RS Momentum: diferencia 21d vs 63d (¿acelerando o frenando?)
#   · RS Trend: pendiente de regresión lineal del RS (¿subiendo o bajando?)
#
# MODO A: Gist pre-computado por GitHub Actions (RSRW_GIST_ID en secrets)
# MODO B: Scan on-demand con botón + cache session_state 30 min
# ═══════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests, json, time
from datetime import datetime, timezone, timedelta
from scipy import stats as scipy_stats
import yfinance as yf

# ─────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────
GIST_FILE       = "rsrw_scan.json"
GIST_CACHE_TTL  = 300
SCAN_CACHE_MINS = 30
BENCHMARK       = "SPY"
PERIODS         = [21, 63, 126]
WEIGHTS         = {21: 0.20, 63: 0.35, 126: 0.45}
EMA_SMOOTH      = 10
TREND_WIN       = 21
BATCH_SIZE      = 80
LOOKBACK        = "200d"

C_GREEN  = "#00ffad"
C_CYAN   = "#00d9ff"
C_RED    = "#f23645"
C_ORANGE = "#ff9800"
C_PURPLE = "#b044ff"
C_BG     = "#0c0e12"
C_BG2    = "#1a1e26"

SECTOR_ETFS = {
    "Tecnología":"XLK","Salud":"XLV","Financieros":"XLF",
    "Consumo Discrecional":"XLY","Consumo Básico":"XLP","Industriales":"XLI",
    "Energía":"XLE","Materiales":"XLB","Servicios Públicos":"XLU",
    "Bienes Raíces":"XLRE","Comunicaciones":"XLC",
}
GICS_MAP = {
    "Information Technology":"Tecnología","Health Care":"Salud",
    "Financials":"Financieros","Consumer Discretionary":"Consumo Discrecional",
    "Consumer Staples":"Consumo Básico","Industrials":"Industriales",
    "Energy":"Energía","Materials":"Materiales","Utilities":"Servicios Públicos",
    "Real Estate":"Bienes Raíces","Communication Services":"Comunicaciones",
}

# ─────────────────────────────────────────────────────────────
# MODO A — GIST
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=GIST_CACHE_TTL, show_spinner=False)
def _load_gist(gist_id: str) -> dict | None:
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}",
            timeout=10, headers={"Accept":"application/vnd.github.v3+json"})
        r.raise_for_status()
        data = json.loads(r.json()["files"][GIST_FILE]["content"])
        return data if data.get("stocks") and len(data["stocks"]) > 10 else None
    except Exception:
        return None

def _parse_gist(data: dict):
    meta, stocks, sectors = data.get("meta",{}), data.get("stocks",{}), data.get("sectors",{})

    if stocks:
        df = pd.DataFrame.from_dict(stocks, orient="index")
        df.index.name = "Ticker"
        rename = {
            "rs_percentile":"RS_Pct","rs_score_raw":"RS_Score",
            "rs_21d":"RS_21d","rs_63d":"RS_63d","rs_126d":"RS_126d",
            "rs_momentum":"RS_Mom","rs_trend":"RS_Trend",
            "rs_vs_sector":"RS_vs_Sector","rvol":"RVOL",
            "sector":"Sector","price":"Precio",
        }
        df = df.rename(columns=rename)
        for c in ["RS_Pct","RS_Score","RS_21d","RS_63d","RS_126d","RS_Mom","RS_Trend","RS_vs_Sector","RVOL","Precio"]:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=["RS_Pct","RVOL"])
    else:
        df = pd.DataFrame()

    if sectors:
        sdf = pd.DataFrame.from_dict(sectors, orient="index")
        sdf.index.name = "Sector"
        for c in ["RS","Return_63d","RS_trend"]:
            if c in sdf.columns: sdf[c] = pd.to_numeric(sdf[c], errors="coerce")
    else:
        sdf = pd.DataFrame()

    return df, sdf, meta

# ─────────────────────────────────────────────────────────────
# MODO B — ON-DEMAND ENGINE
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def _get_sp500_tickers():
    try:
        df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", match="Symbol")[0]
        tickers = df["Symbol"].str.replace(".", "-", regex=False).tolist()
        smap = dict(zip(df["Symbol"].str.replace(".", "-", regex=False), df["GICS Sector"]))
        if len(tickers) >= 490:
            return tickers, smap
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
        "SO","DUK","AEP","SRE","EXC","XEL","ED","WEC","AWK",
    ]
    return list(dict.fromkeys(fallback)), {}

def _rs_smooth(prices, spy, period):
    """RS diario rolling suavizado con EMA."""
    rs = prices.pct_change(period) - spy.pct_change(period)
    return rs.ewm(span=EMA_SMOOTH, min_periods=3).mean()

def _rs_trend_slope(rs_series):
    """Pendiente normalizada de regresión lineal del RS."""
    recent = rs_series.dropna().iloc[-TREND_WIN:]
    if len(recent) < 5: return 0.0
    x = np.arange(len(recent))
    slope, *_ = scipy_stats.linregress(x, recent.values)
    std = recent.std()
    return round(float(slope/std) if std > 0 else 0.0, 4)

def _run_scan_engine(prog_ph):
    tickers, smap = _get_sp500_tickers()
    all_syms = list(dict.fromkeys([BENCHMARK] + list(SECTOR_ETFS.values()) + tickers))
    batches  = [all_syms[i:i+BATCH_SIZE] for i in range(0, len(all_syms), BATCH_SIZE)]
    close_d, vol_d = {}, {}
    bar = prog_ph.progress(0, text="Iniciando descarga (200 días de historia)...")

    for idx, batch in enumerate(batches):
        bar.progress((idx+1)/len(batches), text=f"Lote {idx+1}/{len(batches)} · {len(batch)} símbolos")
        for attempt in range(3):
            try:
                if idx > 0: time.sleep(0.5)
                raw = yf.download(batch, period=LOOKBACK, interval="1d",
                    progress=False, threads=True, timeout=30, auto_adjust=True)
                if raw.empty: raise ValueError("Empty")
                if isinstance(raw.columns, pd.MultiIndex):
                    for t in raw.get("Close", pd.DataFrame()).columns:
                        s = raw["Close"][t].dropna()
                        if len(s) > 10: close_d[t] = s
                    for t in raw.get("Volume", pd.DataFrame()).columns:
                        s = raw["Volume"][t].dropna()
                        if len(s) > 10: vol_d[t] = s
                else:
                    if "Close" in raw.columns:
                        close_d[batch[0]] = raw["Close"].dropna()
                        vol_d[batch[0]]   = raw.get("Volume", pd.Series()).dropna()
                break
            except Exception:
                if attempt < 2: time.sleep(1)

    bar.progress(1.0, text="Calculando percentiles RS...")
    if not close_d:
        prog_ph.empty()
        return pd.DataFrame(), pd.DataFrame(), 0.0, {}

    close  = pd.DataFrame(close_d).sort_index().dropna(how="all")
    volume = pd.DataFrame(vol_d).reindex(close.index).fillna(0)

    if BENCHMARK not in close.columns:
        prog_ph.empty()
        return pd.DataFrame(), pd.DataFrame(), 0.0, {}

    spy      = close[BENCHMARK].dropna()
    spy_perf = float((spy.iloc[-1]/spy.iloc[-20])-1) if len(spy) >= 20 else 0.0

    # Sector RS (63d suavizado)
    sector_rs = {}
    for sname, etf in SECTOR_ETFS.items():
        if etf not in close.columns: continue
        s   = close[etf].dropna()
        sa  = spy.reindex(s.index).ffill()
        if len(s) < 63: continue
        rs_s = _rs_smooth(s, sa, 63)
        sector_rs[sname] = {
            "RS":         round(float(rs_s.iloc[-1]), 6),
            "RS_trend":   _rs_trend_slope(rs_s),
            "Return_63d": round(float((s.iloc[-1]/s.iloc[-63])-1), 6),
            "ETF":        etf,
        }

    exclude   = {BENCHMARK} | set(SECTOR_ETFS.values())
    raw_scores = {}

    for ticker in [t for t in close.columns if t not in exclude]:
        prices = close[ticker].dropna()
        spy_a  = spy.reindex(prices.index).ffill()
        if len(prices) < max(PERIODS): continue
        try:
            rs_by_p = {}
            rs_63_series = None
            for p in PERIODS:
                if len(prices) < p: continue
                rs_s = _rs_smooth(prices, spy_a, p)
                if len(rs_s.dropna()) < 5: continue
                rs_by_p[f"RS_{p}d"] = round(float(rs_s.iloc[-1]), 6)
                if p == 63: rs_63_series = rs_s
            if not rs_by_p: continue

            avail    = [p for p in PERIODS if f"RS_{p}d" in rs_by_p]
            w_total  = sum(WEIGHTS[p] for p in avail)
            score    = sum(rs_by_p[f"RS_{p}d"] * (WEIGHTS[p]/w_total) for p in avail)
            mom      = round(rs_by_p.get("RS_21d",0) - rs_by_p.get("RS_63d",0), 6)
            trend    = _rs_trend_slope(rs_63_series) if rs_63_series is not None else 0.0
            rvol     = 1.0
            if ticker in volume.columns:
                vs = volume[ticker].replace(0, np.nan).dropna()
                if len(vs) >= 5:
                    avg = float(vs.iloc[-20:].mean() if len(vs) >= 20 else vs.mean())
                    cur = float(vs.iloc[-1])
                    rvol = round(min(max(cur/avg if avg > 0 else 1.0, 0.1), 20.0), 4)
            raw_scores[ticker] = {
                **rs_by_p, "score_raw":score, "RS_Mom":mom,
                "RS_Trend":trend, "RVOL":rvol,
                "Sector":GICS_MAP.get(smap.get(ticker,""),"Otros"),
                "Precio":round(float(prices.iloc[-1]),4),
            }
        except Exception:
            continue

    if not raw_scores:
        prog_ph.empty()
        return pd.DataFrame(), pd.DataFrame(), spy_perf, {}

    # Convertir a percentil
    scores_arr   = np.array([v["score_raw"] for v in raw_scores.values()])
    tickers_list = list(raw_scores.keys())
    results = {}
    for ticker in tickers_list:
        d    = raw_scores[ticker]
        pct  = round(min(float(scipy_stats.percentileofscore(scores_arr, d["score_raw"], kind="rank")), 99.0), 1)
        sector = d["Sector"]
        rs_vs_s = round(d.get("RS_63d",0) - sector_rs.get(sector,{}).get("RS",0), 6) if sector in sector_rs else 0.0
        results[ticker] = {
            "RS_Pct":      pct,
            "RS_Score":    round(d["score_raw"],6),
            "RS_21d":      d.get("RS_21d",0),
            "RS_63d":      d.get("RS_63d",0),
            "RS_126d":     d.get("RS_126d",0),
            "RS_Mom":      d["RS_Mom"],
            "RS_Trend":    d["RS_Trend"],
            "RS_vs_Sector":rs_vs_s,
            "RVOL":        d["RVOL"],
            "Sector":      sector,
            "Precio":      d["Precio"],
        }

    prog_ph.empty()
    df  = pd.DataFrame.from_dict(results, orient="index"); df.index.name = "Ticker"
    sdf = pd.DataFrame.from_dict(sector_rs, orient="index") if sector_rs else pd.DataFrame()
    if not sdf.empty: sdf.index.name = "Sector"
    meta = {"timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "tickers_total":len(tickers),"tickers_scored":len(df),
            "spy_perf_20d":round(spy_perf,6),"source":"on-demand","version":"4.0",
            "methodology":"percentile_ema_smoothed"}
    return df, sdf, spy_perf, meta

# ─────────────────────────────────────────────────────────────
# HELPERS UI
# ─────────────────────────────────────────────────────────────
def _freshness(meta):
    ts = meta.get("timestamp_utc","")
    if not ts: return "Sin timestamp", False
    try:
        dt  = datetime.fromisoformat(ts.replace("Z","+00:00"))
        age = datetime.now(timezone.utc) - dt
        m   = int(age.total_seconds()/60)
        lbl = f"hace {m} min" if m < 60 else f"hace {m//60}h {m%60}m"
        return lbl, age < timedelta(hours=3)
    except: return ts[:16], True

def _mc(value, label, color="white", sub=""):
    s = f'<div class="metric-sub" style="color:{color};">{sub}</div>' if sub else ""
    return f'<div class="metric-card"><div class="metric-value" style="color:{color};">{value}</div><div class="metric-label">{label}</div>{s}</div>'

def _pct_color(pct):
    if pct >= 90: return C_GREEN
    if pct >= 70: return "#7fff00"
    if pct >= 50: return C_ORANGE
    if pct >= 30: return "#ff6600"
    return C_RED

def _trend_icon(trend):
    if trend >  0.3: return "↑↑"
    if trend >  0.1: return "↑"
    if trend < -0.3: return "↓↓"
    if trend < -0.1: return "↓"
    return "→"

def _mom_icon(mom):
    if mom >  0.01: return "▲ Acelerando"
    if mom < -0.01: return "▼ Frenando"
    return "● Estable"

def _vwap_alert(ticker, dev):
    if   dev >  2:   st.success(f"**{ticker}** — {dev:+.1f}% sobre VWAP · Presión compradora · Stop en VWAP")
    elif dev >  0.5: st.info   (f"**{ticker}** — {dev:+.1f}% sobre VWAP · Sesgo alcista · Pullback al VWAP como entrada")
    elif dev > -0.5: st.warning(f"**{ticker}** — {dev:+.1f}% · Equilibrio · Esperar breakout con volumen >1.5×")
    elif dev > -2:   st.warning(f"**{ticker}** — {dev:.1f}% bajo VWAP · Presión vendedora · Reducir o esperar")
    else:            st.error  (f"**{ticker}** — {dev:.1f}% bajo VWAP · Vendedores dominan · Evitar largos")

def _footer():
    st.markdown("""<div style="text-align:center;margin-top:60px;padding:20px;border-top:1px solid #00ffad22;">
        <p style="font-family:'VT323',monospace;color:#444;font-size:.9rem;letter-spacing:2px;">
        [END OF TRANSMISSION // RSRW_SCANNER_v4.0]<br>
        [METHODOLOGY: PERCENTILE EMA-SMOOTHED // PERIODS: 21D·63D·126D]<br>
        [BENCHMARK: SPY // UNIVERSE: S&amp;P500]</p></div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

/* ── Base ── */
.stApp{background:#0c0e12}
h1,h2,h3,h4,h5,h6{font-family:'VT323',monospace!important;color:#00ffad!important;text-transform:uppercase;letter-spacing:2px}
p,li{font-family:'Courier New',monospace;color:#ccc!important;line-height:1.8;font-size:.95rem}
strong{color:#00ffad;font-weight:bold}
ul{list-style:none;padding-left:0}ul li::before{content:"▸ ";color:#00ffad;margin-right:8px}
hr{border:none;height:1px;background:linear-gradient(90deg,transparent,#00ffad,transparent);margin:40px 0}
a{color:#00d9ff!important}

/* ── Scanlines overlay ── */
.stApp::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,173,0.015) 2px,rgba(0,255,173,0.015) 4px);
  pointer-events:none;z-index:0}

/* ── Header ── */
.main-header{text-align:center;margin-bottom:30px;padding:30px 0 20px}
.main-tag{font-family:'VT323',monospace;font-size:.95rem;color:#444;letter-spacing:3px;margin-bottom:12px}
.main-title{font-family:'VT323',monospace!important;color:#00ffad!important;font-size:4rem;
  text-shadow:0 0 30px #00ffad88,0 0 60px #00ffad33;
  border-bottom:2px solid #00ffad55;padding-bottom:12px;margin-bottom:8px;
  text-transform:uppercase;letter-spacing:4px}
.main-subtitle{font-family:'Courier New',monospace;color:#00d9ff;font-size:.85rem;
  max-width:700px;margin:0 auto;letter-spacing:4px;text-transform:uppercase;opacity:.8}

/* ── Method banner ── */
.method-box{background:linear-gradient(135deg,#0c0e12,#0d1118);
  border:1px solid #b044ff44;border-radius:6px;padding:12px 18px;margin-bottom:18px;
  font-family:'Courier New',monospace;font-size:11px;color:#777;line-height:1.7}
.method-box b{color:#b044ff}
.method-box span{color:#00ffad}

/* ── Mode banner ── */
.mode-banner{background:linear-gradient(135deg,#0c0e12,#111622);border:1px solid #00d9ff22;
  border-radius:6px;padding:10px 16px;margin-bottom:16px;
  font-family:'Courier New',monospace;font-size:11px;color:#666}
.mode-banner b{color:#00d9ff}

/* ── Section headers ── */
.sec-hdr{font-family:'VT323',monospace;color:#00ffad;font-size:1.5rem;text-transform:uppercase;
  letter-spacing:3px;margin:0 0 14px;padding-left:14px;
  border-left:3px solid #00ffad;display:flex;align-items:center;gap:10px}

/* ── Group containers ── */
.grp-box{border:1px solid #00ffad22;border-radius:6px;overflow:hidden;
  background:#0c0e12;margin-bottom:18px;box-shadow:0 0 20px #00ffad08}
.grp-hdr{background:linear-gradient(135deg,#0e1018 0%,#131824 100%);
  padding:10px 18px;border-bottom:1px solid #00ffad22}
.grp-ttl{font-family:'VT323',monospace!important;color:#00ffad!important;
  font-size:1.15rem!important;text-transform:uppercase;letter-spacing:2px;margin:0}

/* ── Metric cards ── */
.metric-card{background:linear-gradient(135deg,#0e1018 0%,#131824 100%);
  border:1px solid #00ffad22;border-radius:6px;padding:18px 12px;text-align:center;
  box-shadow:0 0 12px #00ffad08;transition:border-color .2s}
.metric-card:hover{border-color:#00ffad55}
.metric-value{font-family:'VT323',monospace;font-size:2.1rem;color:white;margin-bottom:4px;letter-spacing:1px}
.metric-label{font-family:'Courier New',monospace;font-size:.6rem;color:#555;
  text-transform:uppercase;letter-spacing:2px}
.metric-sub{font-family:'Courier New',monospace;font-size:.65rem;margin-top:4px;letter-spacing:1px}

/* ── Badges ── */
.badge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;border-radius:4px;
  font-family:'VT323',monospace;font-size:1rem;text-transform:uppercase;letter-spacing:1px}
.badge-info{background:rgba(0,217,255,.08);color:#00d9ff;border:1px solid rgba(0,217,255,.25)}
.badge-ok{background:rgba(0,255,173,.08);color:#00ffad;border:1px solid rgba(0,255,173,.25)}

/* ── Scan button ── */
.stButton>button[kind="secondary"]{
  background:linear-gradient(135deg,transparent,rgba(0,255,173,.05))!important;
  border:1px solid #00ffad88!important;color:#00ffad!important;
  font-family:'VT323',monospace!important;font-size:1.4rem!important;
  letter-spacing:4px!important;text-transform:uppercase!important;
  padding:12px 0!important;transition:all .2s!important}
.stButton>button[kind="secondary"]:hover{
  background:linear-gradient(135deg,rgba(0,255,173,.08),rgba(0,255,173,.15))!important;
  border-color:#00ffad!important;box-shadow:0 0 20px #00ffad44!important;
  text-shadow:0 0 10px #00ffad!important}

/* ── Dataframe tweaks ── */
.stDataFrame{border:1px solid #00ffad11!important;border-radius:6px}
</style>"""

# ─────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────
def render():
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown("""<div class="main-header">
        <div class="main-tag">[ANÁLISIS INSTITUCIONAL // S&amp;P 500 UNIVERSE]</div>
        <div style="font-size:3rem;margin-bottom:4px;">🔍</div>
        <div class="main-title">SCANNER RS/RW PRO</div>
        <div class="main-subtitle">PERCENTILE RELATIVE STRENGTH // ROTACIÓN SECTORIAL</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="method-box">
        <b>METODOLOGÍA v4.0</b> — RS Score → <span>Percentil 0-99</span> dentro del universo S&amp;P 500 ·
        Períodos <span>21d · 63d · 126d</span> (pesos 20/35/45% — el largo plazo domina) ·
        <b>EMA-suavizado</b> elimina spikes de earnings · <b>RS Momentum</b> detecta aceleración/freno
    </div>""", unsafe_allow_html=True)

    if "rsrw_show" not in st.session_state:
        st.session_state["rsrw_show"] = False

    gist_id   = st.secrets.get("RSRW_GIST_ID", "")
    gist_mode = bool(gist_id)
    results = pd.DataFrame(); sector_data = pd.DataFrame()
    meta = {}; spy_perf = 0.0
    freshness = ""; fc = C_ORANGE; fi = "◎"
    source_label = "ON-DEMAND"

    # ── Modo A: Gist ──────────────────────────────────────────
    if gist_mode:
        with st.spinner("Cargando datos..."):
            raw = _load_gist(gist_id)
        if raw:
            results, sector_data, meta = _parse_gist(raw)
            spy_perf  = float(meta.get("spy_perf_20d",0.0))
            freshness, is_fresh = _freshness(meta)
            fc = C_GREEN if is_fresh else C_RED
            fi = "●" if is_fresh else "⚠"
            source_label = "GITHUB ACTIONS"
        else:
            gist_mode = False

    # ── Modo B: On-demand ─────────────────────────────────────
    if not gist_mode:
        st.markdown("""<div class="mode-banner"><b>MODO ON-DEMAND</b> — Resultados cacheados 30 min.
            Configura <b>RSRW_GIST_ID</b> en Streamlit secrets para actualizaciones automáticas.</div>""",
            unsafe_allow_html=True)

        if "rsrw_cache" in st.session_state:
            cache    = st.session_state["rsrw_cache"]
            age_mins = (datetime.now(timezone.utc) - cache["ts"]).total_seconds()/60
            if age_mins < SCAN_CACHE_MINS and not cache["results"].empty:
                results     = cache["results"]
                sector_data = cache["sectors"]
                meta        = cache["meta"]
                spy_perf    = float(meta.get("spy_perf_20d",0.0))
                freshness   = f"hace {int(age_mins)} min"
                fc, fi      = C_CYAN, "◉"

    # ── En modo Gist con datos, mostrar automáticamente ───────
    if gist_mode and not results.empty:
        st.session_state["rsrw_show"] = True

    scored  = meta.get("tickers_scored", len(results))
    version = meta.get("version","4.0")

    # Badge estado — solo si hay datos
    if not results.empty:
        st.markdown(f"""<div style="text-align:center;margin-bottom:16px;">
            <span class="badge badge-info">▸ {scored} TICKERS &nbsp;|&nbsp; {len(sector_data)} SECTORES &nbsp;|&nbsp; {source_label} v{version}</span>
            &nbsp;&nbsp;<span style="font-family:'Courier New',monospace;font-size:12px;color:{fc};">{fi} {freshness}</span>
        </div>""", unsafe_allow_html=True)

    # Botón siempre visible
    _, col_btn, _ = st.columns([1,2,1])
    with col_btn:
        if results.empty:
            lbl = "🔍 EJECUTAR SCANNER"
        elif gist_mode:
            lbl = "🔄 REFRESCAR DATOS"
        else:
            lbl = "🔄 ACTUALIZAR SCAN"
        run_btn = st.button(lbl, use_container_width=True, type="secondary")

    if run_btn:
        if gist_mode:
            st.cache_data.clear()
            st.session_state["rsrw_show"] = True
            st.rerun()
        else:
            prog_ph = st.empty()
            df_r, df_s, spy_p, mt = _run_scan_engine(prog_ph)
            if df_r.empty:
                st.error("❌ Sin resultados. Verifica conexión o intenta más tarde.")
            else:
                st.session_state["rsrw_cache"] = {
                    "results":df_r,"sectors":df_s,"meta":mt,
                    "ts":datetime.now(timezone.utc)}
                st.session_state["rsrw_show"] = True
                st.rerun()

    # Sin datos: guía y parar
    if results.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        _render_guide()
        _footer()
        return

    # Modo on-demand sin scan ejecutado aún
    if not gist_mode and not st.session_state.get("rsrw_show", False):
        st.info("⬆️ Pulsa el botón para ejecutar el scanner.")
        _render_guide()
        _footer()
        return

    # ═══════════════════════════════════════════════
    # RESULTADOS
    # ═══════════════════════════════════════════════

    _render_guide()

    # ── Configuración ─────────────────────────────
    st.markdown('<div class="sec-hdr">⚙️ CONFIGURACIÓN DEL SCANNER</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div style="font-family:Courier New,monospace;font-size:12px;color:#888;padding:6px 0;">Percentil mínimo · <b style="color:#00ffad">80</b> = top 20% del universo</div>', unsafe_allow_html=True)
        pct_threshold = st.slider("Percentil mínimo RS", 50, 95, 80, 5, label_visibility="collapsed")
    with c2:
        st.markdown('<div style="font-family:Courier New,monospace;font-size:12px;color:#888;padding:6px 0;">RVOL mínimo · <b style="color:#00ffad">1.5</b> = confirmación institucional</div>', unsafe_allow_html=True)
        min_rvol = st.slider("RVOL", 1.0, 3.0, 1.2, 0.1, label_visibility="collapsed")
    with c3:
        st.markdown('<div style="font-family:Courier New,monospace;font-size:12px;color:#888;padding:6px 0;">Top N por categoría · <b style="color:#00ffad">20</b> = revisión diaria óptima</div>', unsafe_allow_html=True)
        top_n = st.slider("Top N", 10, 50, 20, 5, label_visibility="collapsed")

    # Filtros adicionales
    cf1, cf2 = st.columns(2)
    with cf1:
        sectores = ["Todos"] + sorted(results["Sector"].unique().tolist()) if "Sector" in results.columns else ["Todos"]
        sector_filter = st.selectbox("Filtrar por sector:", sectores)
    with cf2:
        mom_filter = st.selectbox("RS Momentum:", ["Todos","▲ Acelerando","● Estable","▼ Frenando"])

    rf = results.copy()
    if sector_filter != "Todos" and "Sector" in rf.columns:
        rf = rf[rf["Sector"] == sector_filter]
    if mom_filter == "▲ Acelerando" and "RS_Mom" in rf.columns:
        rf = rf[rf["RS_Mom"] > 0.01]
    elif mom_filter == "▼ Frenando" and "RS_Mom" in rf.columns:
        rf = rf[rf["RS_Mom"] < -0.01]
    elif mom_filter == "● Estable" and "RS_Mom" in rf.columns:
        rf = rf[(rf["RS_Mom"] >= -0.01) & (rf["RS_Mom"] <= 0.01)]

    # ── Métricas ──────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    mc = st.columns(5)
    col_spy = C_GREEN if spy_perf >= 0 else C_RED
    with mc[0]: st.markdown(_mc(f"{spy_perf:+.2%}","SPY // 20D",col_spy,("▲" if spy_perf>=0 else "▼")+" TENDENCIA"),unsafe_allow_html=True)
    with mc[1]:
        n = len(rf[rf["RS_Pct"] >= pct_threshold]) if "RS_Pct" in rf.columns else 0
        st.markdown(_mc(str(n),"TOP RS",C_GREEN,f"▸ PCT ≥ {pct_threshold}"),unsafe_allow_html=True)
    with mc[2]:
        n = len(rf[rf["RVOL"] > 1.5]) if "RVOL" in rf.columns else 0
        st.markdown(_mc(str(n),"HIGH RVOL",C_ORANGE,"▸ >1.5× VOLUMEN"),unsafe_allow_html=True)
    with mc[3]:
        n = len(rf[(rf["RS_Pct"] >= pct_threshold) & (rf["RVOL"] > min_rvol)]) if all(c in rf.columns for c in ["RS_Pct","RVOL"]) else 0
        st.markdown(_mc(str(n),"SETUPS ACTIVOS",C_CYAN,"▸ PCT+VOL CONFIRMADO"),unsafe_allow_html=True)
    with mc[4]:
        if not sector_data.empty and "RS" in sector_data.columns:
            ts = sector_data["RS"].idxmax()
            st.markdown(_mc(ts,"SECTOR LÍDER",C_GREEN,f"▸ {sector_data.loc[ts,'RS']:+.2%} vs SPY"),unsafe_allow_html=True)
        else:
            st.markdown(_mc("—","SECTOR LÍDER"),unsafe_allow_html=True)

    # ── Rotación sectorial ────────────────────────
    if not sector_data.empty and "RS" in sector_data.columns:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="sec-hdr">🔄 ROTACIÓN SECTORIAL</div>', unsafe_allow_html=True)

        tab_s1, tab_s2 = st.tabs(["📊 Barras", "📈 Barras + Trend"])
        sd = sector_data.sort_values("RS", ascending=False)

        with tab_s1:
            fig_s = go.Figure(go.Bar(
                x=sd.index, y=sd["RS"],
                marker_color=[C_GREEN if v > 0 else C_RED for v in sd["RS"]],
                text=[f"{v:+.1%}" for v in sd["RS"]], textposition="outside",
                textfont=dict(family="Courier New", size=11, color="white"),
            ))
            fig_s.update_layout(template="plotly_dark",paper_bgcolor=C_BG,plot_bgcolor=C_BG,
                height=300,margin=dict(l=0,r=0,b=60,t=20),
                yaxis=dict(tickformat=".1%",gridcolor="#1a1e26"),
                xaxis=dict(tickfont=dict(family="Courier New",size=10)),showlegend=False)
            st.plotly_chart(fig_s, use_container_width=True)

        with tab_s2:
            if "RS_trend" in sector_data.columns:
                fig_s2 = go.Figure()
                fig_s2.add_trace(go.Bar(x=sd.index, y=sd["RS"],
                    marker_color=[C_GREEN if v > 0 else C_RED for v in sd["RS"]],
                    name="RS 63d suavizado", opacity=0.8,
                    text=[f"{v:+.1%}" for v in sd["RS"]], textposition="outside",
                    textfont=dict(family="Courier New",size=10,color="white")))
                # Tendencia como puntos superpuestos
                trend_colors = [C_GREEN if v > 0 else C_RED for v in sd.get("RS_trend", pd.Series())]
                fig_s2.add_trace(go.Scatter(x=sd.index, y=sd.get("RS_trend", pd.Series()),
                    mode="markers", name="RS Trend (pendiente)",
                    marker=dict(size=10, color=trend_colors, symbol="diamond",
                        line=dict(color="#1a1e26",width=1)),
                    yaxis="y2"))
                fig_s2.update_layout(template="plotly_dark",paper_bgcolor=C_BG,plot_bgcolor=C_BG,
                    height=320,margin=dict(l=0,r=60,b=60,t=20),
                    yaxis=dict(tickformat=".1%",gridcolor="#1a1e26",title="RS 63d"),
                    yaxis2=dict(overlaying="y",side="right",title="Trend",
                        gridcolor="rgba(0,0,0,0)",tickfont=dict(size=9)),
                    xaxis=dict(tickfont=dict(family="Courier New",size=10)),
                    legend=dict(font=dict(family="Courier New",size=9)))
                st.plotly_chart(fig_s2, use_container_width=True)
            else:
                st.info("Trend data no disponible en este dataset.")

    # ── Mapa de burbujas RS Percentil vs RVOL ─────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">🫧 MAPA RS PERCENTIL vs RVOL</div>', unsafe_allow_html=True)

    if "RS_Pct" in rf.columns and "RVOL" in rf.columns:
        bdf = rf.copy()
        # Mostrar top/bottom 35 para no saturar
        if len(bdf) > 70:
            bdf = pd.concat([bdf.nlargest(35,"RS_Pct"), bdf.nsmallest(35,"RS_Pct")]).drop_duplicates()

        bdf["size"] = (bdf["RVOL"].clip(1,5) * 10).round(0)

        # Color por momentum para añadir una dimensión más
        mom_colors = []
        for _, row in bdf.iterrows():
            mom = row.get("RS_Mom", 0)
            if   mom >  0.01: mom_colors.append(C_GREEN)
            elif mom < -0.01: mom_colors.append(C_RED)
            else:             mom_colors.append(C_ORANGE)

        fig_b = go.Figure()
        fig_b.add_hline(y=80, line_dash="dot", line_color="rgba(0,255,173,0.27)", line_width=1,
            annotation_text="Umbral PCT 80", annotation_font_color="rgba(0,255,173,0.27)",
            annotation_font_size=10)
        fig_b.add_hline(y=50, line_dash="dot", line_color="rgba(51,51,51,0.53)", line_width=1)
        fig_b.add_vline(x=1.5, line_dash="dot", line_color="rgba(51,51,51,0.53)", line_width=1)

        # Cuadrante prime (PCT>80, RVOL>1.5)
        fig_b.add_shape(type="rect", x0=1.5, x1=bdf["RVOL"].max()*1.1,
            y0=80, y1=100, fillcolor="rgba(0,255,173,0.04)", line_width=0)

        fig_b.add_trace(go.Scatter(
            x=bdf["RVOL"], y=bdf["RS_Pct"],
            mode="markers+text",
            text=bdf.index,
            textposition="top center",
            textfont=dict(family="Courier New", size=9, color="#999"),
            marker=dict(
                size=bdf["size"],
                color=bdf["RS_Pct"],
                colorscale=[[0,C_RED],[0.5,C_ORANGE],[0.8,"#7fff00"],[1,C_GREEN]],
                cmin=0, cmax=99,
                showscale=True,
                colorbar=dict(title="RS Pct",tickformat=".0f",thickness=12,
                    tickfont=dict(family="Courier New",size=9,color="#666")),
                opacity=0.85,
                line=dict(color="#1a1e26",width=1),
            ),
            customdata=bdf[["Sector","RS_Pct","RVOL","RS_Mom","RS_Trend"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "RS Percentil: %{customdata[1]:.0f}<br>"
                "RVOL: %{customdata[2]:.2f}×<br>"
                "Momentum: %{customdata[3]:+.3f}<br>"
                "Trend: %{customdata[4]:+.3f}<br>"
                "Sector: %{customdata[0]}<extra></extra>"
            ),
        ))

        fig_b.add_annotation(x=bdf["RVOL"].max()*0.85, y=95,
            text="🚀 PRIME SETUP", font=dict(family="VT323",size=14,color=C_GREEN),
            showarrow=False, opacity=0.5)
        fig_b.add_annotation(x=0.6, y=10,
            text="🔻 DISTRIBUTION", font=dict(family="VT323",size=14,color=C_RED),
            showarrow=False, opacity=0.5)

        fig_b.update_layout(
            template="plotly_dark", paper_bgcolor=C_BG, plot_bgcolor=C_BG,
            height=520, margin=dict(l=0,r=60,b=60,t=20),
            xaxis=dict(title="RVOL (Volumen Relativo)",gridcolor="#1a1e26",
                tickfont=dict(family="Courier New",size=10)),
            yaxis=dict(title="RS Percentil (0–99)",range=[0,100],gridcolor="#1a1e26",
                tickfont=dict(family="Courier New",size=10)),
            showlegend=False,
        )
        st.plotly_chart(fig_b, use_container_width=True)
        st.markdown("""<div style="font-family:'Courier New',monospace;font-size:11px;color:#555;text-align:center;margin-top:-15px;">
            Eje Y = RS Percentil (0-99, donde 99 = mayor fuerza relativa del universo) ·
            Eje X = RVOL · Tamaño = intensidad RVOL · Color = percentil<br>
            Zona verde superior derecha (PCT >80 + RVOL >1.5) = candidatos prime setup
        </div>""", unsafe_allow_html=True)

    # ── Tablas RS / RW ────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    fmt = {
        "RS_Pct":       "{:.0f}",
        "RS_Score":     "{:+.3f}",
        "RS_21d":       "{:+.2%}",
        "RS_63d":       "{:+.2%}",
        "RS_126d":      "{:+.2%}",
        "RS_Mom":       "{:+.3f}",
        "RS_Trend":     "{:+.3f}",
        "RVOL":         "{:.2f}x",
        "RS_vs_Sector": "{:+.2%}",
    }
    col_rs, col_rw = st.columns(2)

    with col_rs:
        st.markdown('<div class="grp-box"><div class="grp-hdr"><div class="grp-ttl">🚀 TOP RS — LÍDERES (Percentil ≥ umbral)</div></div></div>', unsafe_allow_html=True)
        df_rs = rf[rf["RS_Pct"] >= pct_threshold].nlargest(top_n,"RS_Pct").copy() if "RS_Pct" in rf.columns else pd.DataFrame()
        if not df_rs.empty:
            df_rs["Setup"] = df_rs.apply(lambda x:
                "🔥 Prime"  if x.get("RVOL",0)>1.5 and x.get("RS_Mom",0)>0.01 and x.get("RS_Trend",0)>0
                else ("💪 Strong" if x.get("RS_Mom",0)>0.01 else ("📈 Hold" if x.get("RS_Mom",0)>=-0.01 else "⚠️ Fading")),
                axis=1)
            cols = [c for c in ["RS_Pct","RS_63d","RS_126d","RS_Mom","RS_Trend","RVOL","RS_vs_Sector","Sector","Setup"] if c in df_rs.columns]
            styled = df_rs[cols].style.format({k:v for k,v in fmt.items() if k in cols})
            if "RS_Pct"  in cols: styled = styled.background_gradient(subset=["RS_Pct"],   cmap="Greens",   vmin=50, vmax=99)
            if "RS_Mom"  in cols: styled = styled.background_gradient(subset=["RS_Mom"],   cmap="RdYlGn",   vmin=-0.03, vmax=0.03)
            if "RVOL"    in cols: styled = styled.background_gradient(subset=["RVOL"],     cmap="YlOrBr")
            st.dataframe(styled, use_container_width=True, height=min(420,38+len(df_rs)*38))
        else:
            st.info("No hay stocks con percentil RS ≥ umbral.")

    with col_rw:
        st.markdown('<div class="grp-box"><div class="grp-hdr"><div class="grp-ttl">🔻 TOP RW — REZAGADOS (Percentil ≤ 20)</div></div></div>', unsafe_allow_html=True)
        df_rw = rf[rf["RS_Pct"] <= 20].nsmallest(top_n,"RS_Pct").copy() if "RS_Pct" in rf.columns else pd.DataFrame()
        if not df_rw.empty:
            df_rw["Alerta"] = df_rw.apply(lambda x:
                "🔻 Dist."  if x.get("RVOL",0)>1.5 and x.get("RS_Mom",0)<-0.01
                else ("📉 Weak" if x.get("RS_Mom",0)<-0.01 else "⬇️ Lagging"), axis=1)
            cols = [c for c in ["RS_Pct","RS_63d","RS_126d","RS_Mom","RS_Trend","RVOL","RS_vs_Sector","Sector","Alerta"] if c in df_rw.columns]
            styled = df_rw[cols].style.format({k:v for k,v in fmt.items() if k in cols})
            if "RS_Pct" in cols: styled = styled.background_gradient(subset=["RS_Pct"], cmap="Reds",  vmin=0, vmax=30)
            if "RS_Mom" in cols: styled = styled.background_gradient(subset=["RS_Mom"], cmap="RdYlGn",vmin=-0.03,vmax=0.03)
            if "RVOL"   in cols: styled = styled.background_gradient(subset=["RVOL"],   cmap="OrRd")
            st.dataframe(styled, use_container_width=True, height=min(420,38+len(df_rw)*38))
        else:
            st.success("✅ No hay stocks en zona de debilidad extrema.")

    if not rf.empty:
        st.download_button("📥 Exportar CSV", rf.to_csv().encode("utf-8"),
            f"RS_Scan_v4_{datetime.now().strftime('%Y%m%d_%H%M')}.csv","text/csv")

    # ── Setups prácticos ──────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">📋 SETUPS PRÁCTICOS — CÓMO LEER LOS NUEVOS INDICADORES</div>', unsafe_allow_html=True)

    with st.expander("Ver ejemplos de uso con la metodología de percentiles", expanded=False):
        st.markdown("""
        ### Cómo interpretar RS Percentil + Momentum + Trend

        **Ejemplo A — Setup Prime (ideal para swing 3-5 días):**

        Un stock aparece con: RS_Pct = 94 · RS_Mom = +0.018 · RS_Trend = +0.42 · RVOL = 1.9×

        - **RS_Pct 94** → está en el top 6% del universo S&P 500 por fuerza relativa
        - **RS_Mom +0.018** → el RS de 21d está 1.8 puntos porcentuales *por encima* del RS de 63d → la fuerza relativa está *acelerando*
        - **RS_Trend +0.42** → la pendiente de regresión del RS es positiva y significativa → tendencia al alza sostenida
        - **RVOL 1.9×** → volumen institucional confirmado

        Setup: 🔥 Prime — líder del universo con momentum acelerándose y volumen real.

        ---

        **Ejemplo B — Trampa a evitar (antiguo sistema la habría marcado como oportunidad):**

        RS_Pct = 82 · RS_Mom = −0.024 · RS_Trend = −0.35 · RVOL = 2.1×

        - **RS_Pct 82** → parece fuerte (top 18%)
        - **RS_Mom −0.024** → el RS de 21d está por *debajo* del RS de 63d → la fuerza relativa está *perdiendo impulso*
        - **RS_Trend −0.35** → pendiente negativa → el liderazgo se está erosionando
        - **RVOL 2.1×** → volumen alto, pero puede ser distribución

        Con el sistema anterior (RS_Score ponderando 50% el 5d), este stock habría aparecido arriba si tuvo un buen día. Con percentiles + momentum, aparece como **⚠️ Fading** — se está debilitando dentro del universo, no es momento de entrar.

        ---

        **Ejemplo C — RS Percentil bajo pero con RS_Mom positivo (recuperación temprana):**

        RS_Pct = 35 · RS_Mom = +0.031 · RS_Trend = +0.28 · RVOL = 1.3×

        - Percentil bajo (todavía en la mitad inferior del universo)
        - Pero momentum y trend son positivos → el RS está mejorando
        - Esto es una *señal temprana* de posible rotación hacia este stock/sector

        No es un trade ahora, pero es un candidato a **watchlist** para cuando RS_Pct cruce 60+.
        """)

    # ── Backtest ──────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">📊 BACKTEST RS PERCENTIL — ANÁLISIS HISTÓRICO</div>', unsafe_allow_html=True)

    with st.expander("⚙️ Configurar y ejecutar backtest", expanded=False):
        st.markdown("""<div style="font-family:'Courier New',monospace;font-size:12px;color:#888;padding:6px 0;margin-bottom:10px;">
            Simula: entrar cuando el RS (rolling) de un ticker supera un umbral, mantener N días.
            Compara vs buy &amp; hold SPY. El EMA suavizado se aplica también en el backtest.</div>""",
            unsafe_allow_html=True)

        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1: bt_ticker = st.text_input("Ticker:", "NVDA", key="bt4_ticker").upper().strip()
        with bc2: bt_period = st.selectbox("Histórico:", ["1y","2y","3y","5y"], index=1, key="bt4_period")
        with bc3: bt_rs_win = st.selectbox("Ventana RS:", [21, 63, 126], index=1, key="bt4_rs_win")
        with bc4: bt_hold   = st.selectbox("Holding días:", [5, 10, 21], index=1, key="bt4_hold")

        run_bt = st.button("▶ Ejecutar Backtest", type="secondary", key="run_bt4")

        if run_bt and bt_ticker:
            with st.spinner(f"Descargando {bt_ticker} y SPY..."):
                try:
                    raw_bt = yf.download([bt_ticker,"SPY"], period=bt_period,
                        interval="1d", progress=False, auto_adjust=True)

                    close_bt = raw_bt["Close"] if isinstance(raw_bt.columns, pd.MultiIndex) else raw_bt[["Close"]]
                    if bt_ticker not in close_bt.columns or "SPY" not in close_bt.columns:
                        st.error(f"No se obtuvieron datos de {bt_ticker} o SPY.")
                    else:
                        tk  = close_bt[bt_ticker].dropna()
                        spy = close_bt["SPY"].dropna()
                        idx = tk.index.intersection(spy.index)
                        tk  = tk.loc[idx]; spy = spy.loc[idx]

                        # RS suavizado con EMA (misma lógica del engine)
                        rs_raw    = tk.pct_change(bt_rs_win) - spy.pct_change(bt_rs_win)
                        rs_smooth = rs_raw.ewm(span=EMA_SMOOTH, min_periods=3).mean()

                        # Percentil rolling (aproximado con ventana 126d de historia)
                        roll_pct = rs_smooth.rolling(126, min_periods=30).apply(
                            lambda x: scipy_stats.percentileofscore(x, x.iloc[-1], kind="rank"), raw=False)

                        trades = []
                        i = max(bt_rs_win, 126)
                        while i < len(tk) - bt_hold:
                            if roll_pct.iloc[i] >= 70:  # entrar cuando percentil ≥ 70
                                ep = float(tk.iloc[i]); xp = float(tk.iloc[min(i+bt_hold,len(tk)-1)])
                                se = float(spy.iloc[i]); sx = float(spy.iloc[min(i+bt_hold,len(spy)-1)])
                                rt = (xp/ep)-1; rs = (sx/se)-1
                                trades.append({"Entrada":tk.index[i].strftime("%Y-%m-%d"),
                                    "Salida":tk.index[min(i+bt_hold,len(tk)-1)].strftime("%Y-%m-%d"),
                                    "PCT_entrada":round(float(roll_pct.iloc[i]),1),
                                    "Ret Ticker":rt,"Ret SPY":rs,"Alpha":rt-rs,"Win":rt>rs})
                                i += bt_hold
                            else:
                                i += 1

                        if not trades:
                            st.warning("No se generaron señales. Prueba con ventana RS o umbral diferente.")
                        else:
                            df_bt = pd.DataFrame(trades)
                            n,wr,ar,aa = len(df_bt),df_bt["Win"].mean(),df_bt["Ret Ticker"].mean(),df_bt["Alpha"].mean()

                            bm1,bm2,bm3,bm4 = st.columns(4)
                            with bm1: st.markdown(_mc(str(n),"TOTAL TRADES",C_CYAN),unsafe_allow_html=True)
                            with bm2: st.markdown(_mc(f"{wr:.0%}","WIN RATE",C_GREEN if wr>0.5 else C_RED),unsafe_allow_html=True)
                            with bm3: st.markdown(_mc(f"{ar:+.2%}","RET MEDIO",C_GREEN if ar>0 else C_RED),unsafe_allow_html=True)
                            with bm4: st.markdown(_mc(f"{aa:+.2%}","ALPHA MEDIO",C_GREEN if aa>0 else C_RED,"vs SPY/trade"),unsafe_allow_html=True)

                            df_bt["Cum Ticker"] = df_bt["Ret Ticker"].cumsum()
                            df_bt["Cum SPY"]    = df_bt["Ret SPY"].cumsum()
                            df_bt["Cum Alpha"]  = df_bt["Alpha"].cumsum()

                            fig_bt = go.Figure()
                            fig_bt.add_trace(go.Scatter(x=list(range(n)),y=df_bt["Cum Ticker"],name=bt_ticker,line=dict(color=C_GREEN,width=2)))
                            fig_bt.add_trace(go.Scatter(x=list(range(n)),y=df_bt["Cum SPY"],name="SPY B&H",line=dict(color=C_ORANGE,width=2,dash="dot")))
                            fig_bt.add_trace(go.Scatter(x=list(range(n)),y=df_bt["Cum Alpha"],name="Alpha acum.",line=dict(color=C_CYAN,width=1.5,dash="dash")))
                            fig_bt.add_hline(y=0,line_dash="dot",line_color="#333",line_width=1)
                            fig_bt.update_layout(template="plotly_dark",paper_bgcolor=C_BG,plot_bgcolor=C_BG,
                                height=340,margin=dict(l=0,r=0,b=40,t=30),
                                title=f"Backtest RS Percentil ≥70 — {bt_ticker} vs SPY ({bt_period})",
                                xaxis=dict(title="Trade #",gridcolor="#1a1e26"),
                                yaxis=dict(title="Retorno acumulado",tickformat=".1%",gridcolor="#1a1e26"),
                                legend=dict(font=dict(family="Courier New",size=10)))
                            st.plotly_chart(fig_bt, use_container_width=True)

                            with st.expander(f"Ver {n} trades"):
                                fmt_bt = {"Ret Ticker":"{:+.2%}","Ret SPY":"{:+.2%}","Alpha":"{:+.2%}","PCT_entrada":"{:.0f}"}
                                styled_bt = df_bt[["Entrada","Salida","PCT_entrada","Ret Ticker","Ret SPY","Alpha","Win"]].style.format(fmt_bt)
                                styled_bt = styled_bt.background_gradient(subset=["Alpha"],cmap="RdYlGn",vmin=-0.05,vmax=0.05)
                                st.dataframe(styled_bt, use_container_width=True, height=300)

                            st.markdown(f"""<div style="font-family:'Courier New',monospace;font-size:11px;color:#555;margin-top:8px;">
                                ⚠️ Sin costes de transacción ni slippage · Señal: RS_{bt_rs_win}d EMA-suavizado + Percentil ≥70 ·
                                Salida: {bt_hold} días después · Alpha = Ret {bt_ticker} − Ret SPY
                            </div>""", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error en backtest: {e}")

    # ── VWAP ──────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="sec-hdr">🎯 VALIDACIÓN INTRADÍA CON VWAP</div>', unsafe_allow_html=True)

    with st.expander("💡 Uso del VWAP con la nueva metodología", expanded=False):
        st.markdown("RS Percentil alto confirma liderazgo en días → VWAP confirma si ese liderazgo se mantiene intradía. "
            "Stock con PCT ≥ 85 + precio sobre VWAP + RS_Mom positivo = setup de mayor calidad.")

    vc1, vc2 = st.columns([3,1])
    with vc1:
        vwap_input = st.text_input("Ticker para VWAP:", "NVDA", key="vwap4_input")
        symbol = vwap_input.strip().upper()
    with vc2:
        st.markdown("<br>", unsafe_allow_html=True)
        run_vwap = st.button("📈 Analizar VWAP", use_container_width=True, type="secondary", key="vwap4_btn")

    if run_vwap and symbol:
        try:
            df_v = yf.download(symbol, period="1d", interval="5m", progress=False)
            if df_v is not None and not df_v.empty:
                if isinstance(df_v.columns, pd.MultiIndex):
                    df_v.columns = df_v.columns.get_level_values(0)
                df_v = df_v.dropna(subset=["High","Low","Close","Volume"])
                if len(df_v) < 5:
                    st.warning(f"Datos insuficientes para **{symbol}**. El mercado puede estar cerrado.")
                else:
                    tp = (df_v["High"]+df_v["Low"]+df_v["Close"])/3
                    df_v["VWAP"] = (tp*df_v["Volume"]).cumsum()/df_v["Volume"].cumsum()
                    price = float(df_v["Close"].iloc[-1])
                    vwap  = float(df_v["VWAP"].iloc[-1])
                    dev   = ((price-vwap)/vwap)*100
                    fig_v = go.Figure()
                    fig_v.add_trace(go.Candlestick(x=df_v.index,open=df_v["Open"],high=df_v["High"],
                        low=df_v["Low"],close=df_v["Close"],name=symbol,
                        increasing_line_color=C_GREEN,decreasing_line_color=C_RED))
                    fig_v.add_trace(go.Scatter(x=df_v.index,y=df_v["VWAP"],
                        line=dict(color=C_ORANGE,width=2),name="VWAP"))
                    fig_v.add_hrect(y0=vwap*0.995,y1=vwap*1.005,
                        fillcolor="rgba(255,170,0,0.06)",line_width=0,
                        annotation_text="Zona VWAP ±0.5%",
                        annotation_font=dict(color=C_ORANGE,size=10))
                    fig_v.update_layout(template="plotly_dark",paper_bgcolor=C_BG,plot_bgcolor=C_BG,
                        height=440,margin=dict(l=0,r=0,b=0,t=35),
                        title=f"{symbol} — ${price:.2f} | VWAP ${vwap:.2f} | {dev:+.2f}%",
                        xaxis_rangeslider_visible=False,
                        xaxis=dict(gridcolor="#1a1e26"),yaxis=dict(gridcolor="#1a1e26"))
                    st.plotly_chart(fig_v, use_container_width=True)
                    _vwap_alert(symbol, dev)
                    # Info del ticker en el scanner
                    if symbol in results.index:
                        row = results.loc[symbol]
                        pct = row.get("RS_Pct", 0)
                        mom = row.get("RS_Mom", 0)
                        st.markdown(f"""<div style="font-family:'Courier New',monospace;font-size:12px;color:#888;margin-top:8px;">
                            Scanner: {symbol} → RS Percentil <b style="color:{_pct_color(pct)}">{pct:.0f}</b> ·
                            Momentum <b style="color:{'#00ffad' if mom>0 else '#f23645'}">{_mom_icon(mom)}</b> ·
                            RVOL <b style="color:#ff9800">{row.get('RVOL',1):.2f}×</b>
                        </div>""", unsafe_allow_html=True)
            else:
                st.warning(f"Sin datos intradía para **{symbol}**.")
        except Exception as e:
            st.error(f"Error: {e}")

    _footer()


# ─────────────────────────────────────────────────────────────
def _render_guide():
    with st.expander("📚 Guía: Metodología RS Percentil v4.0", expanded=False):
        tab1, tab2, tab3 = st.tabs(["🎯 Conceptos v4.0", "📊 Estrategias", "⚠️ Riesgos"])
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                ### RS Percentil (0–99)
                En lugar de un valor absoluto, el RS Score se convierte en **percentil** dentro del universo S&P 500.

                - **99** = el stock con mayor fuerza relativa del universo
                - **50** = exactamente en la media del mercado
                - **1** = la mayor debilidad relativa

                Esto hace el score **comparable entre mercados alcistas y bajistas** y elimina la distorsión de valores absolutos.

                ### Períodos y pesos
                | Período | Equivale a | Peso |
                |---------|-----------|------|
                | **21d** | ~1 mes | 20% |
                | **63d** | ~3 meses | 35% |
                | **126d** | ~6 meses | 45% |

                El largo plazo domina → liderazgo sostenido, no spikes de 1 semana.
                """)
            with col2:
                st.markdown("""
                ### EMA Suavizado
                La serie RS diaria se suaviza con EMA(10) antes de calcular el percentil. Esto elimina el impacto de un día de earnings o gap que inflaría artificialmente el RS_5d.

                ### RS Momentum
                ```
                RS_Mom = RS_21d_smooth − RS_63d_smooth
                ```
                - **Positivo** → la fuerza relativa está *acelerando* (el stock supera cada vez más al mercado)
                - **Negativo** → la fuerza relativa está *frenando* (riesgo de reversión)

                ### RS Trend
                Pendiente de regresión lineal del RS suavizado en los últimos 21 días.
                Positivo = tendencia alcista del RS · Negativo = deterioro.

                ### Setup ideal
                RS_Pct ≥ 80 + RS_Mom > 0 + RS_Trend > 0 + RVOL > 1.5
                """)
        with tab2:
            st.markdown("""
            **Setup Largo:** PCT ≥ 80 · RS_Mom > 0 · RS_Trend > 0 · RVOL > 1.5 · SPY > 20 EMA
            Entrada pullback VWAP · Stop −2% · Target 2R–3R

            **Watchlist (recuperación temprana):** PCT 35-60 + RS_Mom > 0.02 → seguir, entrar cuando PCT cruce 70

            **Setup Corto:** PCT ≤ 20 · RS_Mom < 0 · RVOL > 1.5 · SPY < 20 EMA
            """)
        with tab3:
            st.markdown("""
            1. **PCT alto con RS_Mom negativo** → el liderazgo se está erosionando. Señal de salida, no de entrada.
            2. **PCT medio (50-70) sin Trend ni Mom** → stock en zona gris. Esperar señal clara.
            3. **Mercado bajista** → incluso PCT 90+ puede caer. El percentil es relativo al universo, no absoluto.
            4. **Eventos puntuales** → el EMA suaviza, pero un gap del 20% en un día puede distorsionar 10 días de RS. Verificar el catalizador.
            """)

