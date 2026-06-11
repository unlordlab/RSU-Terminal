
# modules/newsfeed.py
"""
RSU News Feed — financial news aggregator.
Módulo integrado en RSU Terminal (app.py).
Sin dependencias externas de utils/ — completamente autocontenido.
"""
import re
import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════

SOURCES = [
    {"id": "reuters",      "label": "Reuters",       "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"id": "marketwatch",  "label": "MarketWatch",   "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    {"id": "cnbc",         "label": "CNBC",          "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html"},
    {"id": "yahoofinance", "label": "Yahoo Finance", "url": "https://finance.yahoo.com/rss/topstories"},
    {"id": "wsj",          "label": "WSJ Markets",   "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"},
    {"id": "investing",    "label": "Investing.com", "url": "https://www.investing.com/rss/news.rss"},
    {"id": "benzinga",     "label": "Benzinga",      "url": "https://www.benzinga.com/feed"},
    {"id": "ft",           "label": "FT",            "url": "https://www.ft.com/rss/home/uk"},
]

SECTORS_MAP = {
    "tech":    ["nvidia", "apple", "microsoft", "google", "meta", "tesla", "amd", "intel",
                "nvda", "aapl", "msft", "googl", "chip", "semiconductor", "ai", "cloud", "software"],
    "finance": ["jpmorgan", "goldman", "bank", "federal reserve", "interest rate",
                "yield", "treasury", "fomc", "jpm", "gs", "bac"],
    "energy":  ["oil", "gas", "opec", "crude", "wti", "brent", "energy", "xom", "cvx"],
    "health":  ["pharma", "fda", "drug", "biotech", "clinical", "vaccine", "pfizer", "jnj", "merck"],
    "macro":   ["gdp", "cpi", "jobs", "unemployment", "recession", "inflation", "economy"],
    "crypto":  ["bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain", "sol", "solana", "xrp"],
}

HIGH_KW = [
    "fed", "fomc", "rate cut", "rate hike", "inflation", "cpi", "gdp", "recession",
    "crash", "crisis", "emergency", "bankrupt", "default", "collapse", "surge", "plunge",
    "earnings beat", "earnings miss", "acquisition", "merger", "sec", "tariff", "ban",
    "war", "sanction", "breakout", "breakdown",
]
MED_KW = [
    "rally", "selloff", "upgrade", "downgrade", "ipo", "dividend", "buyback",
    "layoff", "forecast", "outlook", "deal", "revenue", "profit", "loss", "quarterly",
]
BULL_KW = [
    "surge", "rally", "beats", "upgrade", "bullish", "growth", "record high",
    "breakout", "strong", "profit", "gain", "rise", "boost", "soar", "jump", "outperform",
]
BEAR_KW = [
    "plunge", "crash", "miss", "downgrade", "bearish", "recession", "default",
    "crisis", "collapse", "loss", "decline", "fall", "weak", "layoff", "slump", "underperform",
]
KNOWN_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "NVDA", "AMD", "INTC",
    "JPM", "GS", "BAC", "MS", "C", "WFC", "XOM", "CVX", "JNJ", "PFE", "MRK",
    "SPY", "QQQ", "IWM", "DIA", "TLT", "GLD", "SLV", "HYG", "VXX", "BTC", "ETH", "SOL",
    "UBER", "LYFT", "NFLX", "DIS", "PYPL", "SQ", "SHOP", "CRM", "SNOW", "PLTR",
    "HOOD", "COIN", "MSTR", "SMCI", "ARM", "AVGO", "QCOM", "MU", "ASML", "SOFI",
    "RIVN", "NIO", "BABA", "JD", "PDD", "ROKU", "ZM", "DOCU",
}
PRICE_TICKERS = {
    "S&P 500":  "^GSPC",
    "NASDAQ":   "^IXIC",
    "DOW":      "^DJI",
    "VIX":      "^VIX",
    "EUR/USD":  "EURUSD=X",
    "GBP/USD":  "GBPUSD=X",
    "USD/JPY":  "USDJPY=X",
    "BTC/USD":  "BTC-USD",
    "ETH/USD":  "ETH-USD",
    "SOL/USD":  "SOL-USD",
    "GOLD":     "GC=F",
    "OIL WTI":  "CL=F",
    "10Y UST":  "^TNX",
}

# CSS específico del módulo (el base CRT ya lo inyecta app.py)
_FEED_CSS = """
<style>
.nf-header {
    font-family: 'VT323', monospace;
    font-size: 2.6rem;
    color: #00ffad;
    text-shadow: 0 0 20px #00ffad66;
    letter-spacing: 4px;
    margin-bottom: 2px;
}
.nf-sub {
    font-family: 'Courier New', monospace;
    font-size: 0.62rem;
    color: #00d9ff55;
    letter-spacing: 3px;
    margin-bottom: 16px;
    text-transform: uppercase;
}
.ticker-strip {
    background: linear-gradient(90deg, #0a0c10, #0d1117, #0a0c10);
    border: 1px solid #00d9ff22;
    border-radius: 6px;
    padding: 8px 16px;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #aaa;
    overflow-x: auto;
    white-space: nowrap;
    margin-bottom: 14px;
}
.ticker-strip b { color: #e0e0e0; }
.tk-up   { color: #00ffad; }
.tk-down { color: #f23645; }
.news-card {
    background: #0d1117;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 10px;
    border-left: 3px solid #2a3040;
}
.news-card.high { border-left-color: #f23645; background: rgba(242,54,69,0.04); }
.news-card.med  { border-left-color: #ff9800; background: rgba(255,152,0,0.03); }
.news-card.low  { border-left-color: #00ffad22; }
.nc-meta {
    font-size: 0.65rem;
    color: #555;
    font-family: 'Courier New', monospace;
    margin-bottom: 5px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.nc-time { color: #00d9ff88; }
.nc-src  { color: #00ffad88; }
.nc-title {
    font-family: 'VT323', monospace;
    font-size: 1.25rem;
    color: #ddd;
    line-height: 1.3;
    margin-bottom: 4px;
}
.nc-title a { color: #ddd; text-decoration: none; }
.nc-title a:hover { color: #00ffad; }
.nc-desc {
    font-size: 0.78rem;
    color: #666;
    font-family: 'Courier New', monospace;
    line-height: 1.5;
}
.tk-tag {
    display: inline-block;
    background: rgba(0,255,173,0.08);
    color: #00ffad99;
    border: 1px solid #00ffad22;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 0.65rem;
    font-family: 'Courier New', monospace;
    margin-right: 4px;
}
.sent-bull { color: #00ffad; font-weight: bold; }
.sent-bear { color: #f23645; font-weight: bold; }
</style>
"""

# ══════════════════════════════════════════════════════════════════════
# NLP HELPERS
# ══════════════════════════════════════════════════════════════════════

def _classify_impact(text: str) -> str:
    t = text.lower()
    if any(k in t for k in HIGH_KW):
        return "high"
    if any(k in t for k in MED_KW):
        return "med"
    return "low"


def _sentiment(text: str) -> dict:
    t = text.lower()
    b = sum(1 for k in BULL_KW if k in t)
    e = sum(1 for k in BEAR_KW if k in t)
    if b > e:
        return {"label": "bullish", "score": b}
    if e > b:
        return {"label": "bearish", "score": e}
    return {"label": "neutral", "score": 0}


def _sector(text: str) -> str:
    t = text.lower()
    for sec, kws in SECTORS_MAP.items():
        if any(k in t for k in kws):
            return sec
    return "general"


def _score(text: str) -> int:
    t = text.lower()
    s = 3
    s += sum(2 for k in HIGH_KW if k in t)
    s += sum(1 for k in MED_KW  if k in t)
    return min(10, s)


def _extract_tickers(text: str) -> list:
    words = re.findall(r'\b[A-Z]{2,5}\b', text)
    return sorted({w for w in words if w in KNOWN_TICKERS})


def _minutes_ago_feedparser(entry) -> int:
    import calendar
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                dt = datetime.fromtimestamp(calendar.timegm(val), tz=timezone.utc)
                return max(0, int((datetime.now(timezone.utc) - dt).total_seconds() / 60))
            except Exception:
                pass
    return 30


def _minutes_ago_pubdate(pub_str: str) -> int:
    import email.utils
    try:
        dt = email.utils.parsedate_to_datetime(pub_str)
        return max(0, int((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 60))
    except Exception:
        return 30


def _build_item(title: str, desc: str, link: str, src: dict, minutes_ago: int) -> dict:
    combined = f"{title} {desc}"
    return {
        "title":       title,
        "desc":        desc[:300],
        "link":        link,
        "src_id":      src["id"],
        "src_label":   src["label"],
        "impact":      _classify_impact(combined),
        "sentiment":   _sentiment(combined),
        "sector":      _sector(combined),
        "score":       _score(combined),
        "tickers":     _extract_tickers(combined),
        "minutes_ago": minutes_ago,
    }

# ══════════════════════════════════════════════════════════════════════
# DATA FETCHING
# ══════════════════════════════════════════════════════════════════════

def _fetch_via_feedparser(src: dict):
    import feedparser
    feed = feedparser.parse(src["url"])
    items = []
    for e in feed.entries[:30]:
        title = getattr(e, "title", "") or ""
        raw   = getattr(e, "summary", None) or getattr(e, "description", "") or ""
        desc  = re.sub(r"<[^>]+>", "", raw)
        link  = getattr(e, "link", "") or ""
        items.append(_build_item(title.strip(), desc.strip(), link.strip(), src,
                                 _minutes_ago_feedparser(e)))
    return items, len(items) > 0


def _fetch_via_requests(src: dict):
    import requests
    import xml.etree.ElementTree as ET
    r = requests.get(src["url"], timeout=8,
                     headers={"User-Agent": "RSU-Terminal/2.0 (RSS reader)"})
    root = ET.fromstring(r.text)
    items = []
    for item in root.findall(".//item")[:30]:
        title = (item.findtext("title") or "").strip()
        desc  = re.sub(r"<[^>]+>", "", (item.findtext("description") or "")).strip()
        link  = (item.findtext("link") or "").strip()
        pub   = item.findtext("pubDate") or ""
        items.append(_build_item(title, desc, link, src, _minutes_ago_pubdate(pub)))
    return items, len(items) > 0


def _fetch_source(src: dict):
    try:
        return _fetch_via_feedparser(src)
    except ImportError:
        pass
    try:
        return _fetch_via_requests(src)
    except Exception:
        return [], False


@st.cache_data(ttl=120, show_spinner=False)
def load_news():
    all_items, status = [], {}
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as ex:
        futures = {ex.submit(_fetch_source, s): s for s in SOURCES}
        for fut in as_completed(futures):
            src = futures[fut]
            try:
                items, ok = fut.result()
                all_items.extend(items)
                status[src["id"]] = {"count": len(items), "ok": ok}
            except Exception:
                status[src["id"]] = {"count": 0, "ok": False}
    all_items.sort(key=lambda x: x["minutes_ago"])
    return all_items, status


@st.cache_data(ttl=60, show_spinner=False)
def load_prices():
    try:
        import yfinance as yf
        prices = {}
        for label, sym in PRICE_TICKERS.items():
            try:
                h = yf.Ticker(sym).history(period="2d", interval="1d")
                if len(h) >= 2:
                    price = float(h["Close"].iloc[-1])
                    prev  = float(h["Close"].iloc[-2])
                    chg   = (price - prev) / prev * 100 if prev else None
                elif len(h) == 1:
                    price = float(h["Close"].iloc[-1])
                    chg   = None
                else:
                    continue
                prices[label] = {"price": price, "chg": chg}
            except Exception:
                pass
        return prices
    except Exception:
        return {}

# ══════════════════════════════════════════════════════════════════════
# UI HELPER
# ══════════════════════════════════════════════════════════════════════

def _fmt_price(label: str, d: dict) -> str:
    p = d["price"]
    if p > 10000:   pf = f"{p:,.0f}"
    elif p > 100:   pf = f"{p:.2f}"
    elif p > 1:     pf = f"{p:.4f}"
    else:           pf = f"{p:.6f}"
    if d.get("chg") is not None:
        arrow = "▲" if d["chg"] >= 0 else "▼"
        cls   = "tk-up" if d["chg"] >= 0 else "tk-down"
        return f"{label} <b>{pf}</b> <span class='{cls}'>{arrow}{d['chg']:+.2f}%</span>"
    return f"{label} <b>{pf}</b>"

# ══════════════════════════════════════════════════════════════════════
# RENDER  ← punto de entrada desde app.py
# ══════════════════════════════════════════════════════════════════════

def render():
    # CSS específico del feed
    st.markdown(_FEED_CSS, unsafe_allow_html=True)

    # ── HEADER ──────────────────────────────────────────────────
    col_logo, col_refresh = st.columns([4, 1])
    with col_logo:
        st.markdown(
            "<div class='nf-header'>📰 NEWS FEED</div>"
            "<div class='nf-sub'>Financial Intelligence Feed · Tiempo Real</div>",
            unsafe_allow_html=True,
        )
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⟳ ACTUALIZAR", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # ── TICKER STRIP ────────────────────────────────────────────
    prices = load_prices()
    order  = ["S&P 500", "NASDAQ", "DOW", "VIX", "EUR/USD", "GBP/USD",
              "USD/JPY", "BTC/USD", "ETH/USD", "SOL/USD", "GOLD", "OIL WTI", "10Y UST"]
    parts  = [_fmt_price(lbl, prices[lbl]) for lbl in order if lbl in prices]
    if parts:
        st.markdown(
            f"<div class='ticker-strip'>{'  ·  '.join(parts)}</div>",
            unsafe_allow_html=True,
        )
    elif not prices:
        st.caption("⚠ Precios no disponibles")

    # ── DATA ────────────────────────────────────────────────────
    with st.spinner("Cargando noticias..."):
        items, status = load_news()
    active = sum(1 for s in status.values() if s["ok"])

    # ── SIDEBAR FILTERS ─────────────────────────────────────────
    with st.sidebar:
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown("**◈ NEWS FILTERS**")

        impact_sel = st.multiselect(
            "Impacto", ["high", "med", "low"],
            default=["high", "med", "low"],
            format_func=lambda x: {"high": "🔴 Alto", "med": "🟡 Medio", "low": "🟢 Bajo"}[x],
            key="nf_impact",
        )
        src_options  = ["(todas)"] + [s["label"] for s in SOURCES]
        src_sel      = st.selectbox("Fuente", src_options, key="nf_src")
        search       = st.text_input("Buscar keyword", key="nf_search")
        ticker_filter = st.text_input("Ticker (ej: NVDA)", key="nf_ticker").upper().strip()

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown("**◈ SENTIMIENTO 1H**")
        recent = [it for it in items if it["minutes_ago"] <= 60]
        bull   = sum(1 for it in recent if it["sentiment"]["label"] == "bullish")
        bear   = sum(1 for it in recent if it["sentiment"]["label"] == "bearish")
        if bull + bear:
            net = (bull - bear) / (bull + bear)
            if net > 0.2:
                label_sent = f"<span class='sent-bull'>RISK-ON</span> · {bull}↑ / {bear}↓"
            elif net < -0.2:
                label_sent = f"<span class='sent-bear'>RISK-OFF</span> · {bull}↑ / {bear}↓"
            else:
                label_sent = f"MIXTO · {bull}↑ / {bear}↓"
            st.markdown(label_sent, unsafe_allow_html=True)
            st.progress((net + 1) / 2)
        else:
            st.caption("Sin datos suficientes")

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown("**◈ ESTADO FUENTES**")
        for s in SOURCES:
            st_ = status.get(s["id"], {"count": 0, "ok": False})
            dot = "🟢" if st_["ok"] else "🔴"
            st.caption(f"{dot} {s['label']}: {st_['count']}")

    # ── APLICAR FILTROS ─────────────────────────────────────────
    filtered = [it for it in items if it["impact"] in impact_sel]
    if src_sel != "(todas)":
        filtered = [it for it in filtered if it["src_label"] == src_sel]
    if search:
        q = search.lower()
        filtered = [it for it in filtered if q in (it["title"] + it["desc"]).lower()]
    if ticker_filter:
        filtered = [it for it in filtered if ticker_filter in it["tickers"]]

    # ── MÉTRICAS ────────────────────────────────────────────────
    nh = sum(1 for i in filtered if i["impact"] == "high")
    nm = sum(1 for i in filtered if i["impact"] == "med")
    nl = sum(1 for i in filtered if i["impact"] == "low")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🔴 Alto",         nh)
    c2.metric("🟡 Medio",        nm)
    c3.metric("🟢 Bajo",         nl)
    c4.metric("Fuentes activas", f"{active}/{len(SOURCES)}")
    c5.metric("Total",           len(filtered))

    # ── TIMELINE ────────────────────────────────────────────────
    with st.expander("📊 Timeline — últimas 24h"):
        buckets = [0] * 24
        for it in items:
            h = it["minutes_ago"] // 60
            if 0 <= h < 24:
                buckets[23 - h] += 1
        df_t = pd.DataFrame({
            "hora":     [f"-{23 - i}h" for i in range(24)],
            "noticias": buckets,
        })
        st.bar_chart(df_t.set_index("hora"), height=160)

    # ── FEED ────────────────────────────────────────────────────
    st.markdown("---")
    if not filtered:
        st.info("◌ Sin noticias en este filtro")
    else:
        for it in filtered[:120]:
            mins = it["minutes_ago"]
            tstr = f"{mins}m" if mins < 60 else f"{mins // 60}h{mins % 60:02d}m"
            sent = it["sentiment"]["label"]
            sent_html = (
                " <span class='sent-bull'>▲ BULL</span>" if sent == "bullish" else
                " <span class='sent-bear'>▼ BEAR</span>" if sent == "bearish" else ""
            )
            tickers_html = "".join(
                f"<span class='tk-tag'>${t}</span>" for t in it["tickers"]
            )
            title_html = (
                f"<a href='{it['link']}' target='_blank' rel='noopener'>{it['title']}</a>"
                if it["link"] else it["title"]
            )
            st.markdown(
                f"<div class='news-card {it['impact']}'>"
                f"  <div class='nc-meta'>"
                f"    <span class='nc-time'>{tstr}</span> · "
                f"    <span class='nc-src'>{it['src_label']}</span> · "
                f"    {it['sector']} · score {it['score']}/10{sent_html}"
                f"  </div>"
                f"  <div class='nc-title'>{title_html}</div>"
                f"  <div class='nc-desc'>{it['desc'][:200]}</div>"
                f"  <div style='margin-top:6px'>{tickers_html}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.caption(
        f"↺ Actualizado: {datetime.now().strftime('%H:%M:%S')} · "
        f"caché 120s · pulsa ⟳ para forzar recarga"
    )

