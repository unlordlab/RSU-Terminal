"""
RSU News Feed — financial news aggregator page.
Add to a multipage Streamlit app under pages/.
"""
import streamlit as st
from datetime import datetime

from utils.data import fetch_all_sources, fetch_all_prices
from utils.sources import SOURCES, SECTORS
from utils.theme import TERMINAL_CSS

st.set_page_config(page_title="RSU News Feed", layout="wide", page_icon="📡")
st.markdown(TERMINAL_CSS, unsafe_allow_html=True)


# ── CACHED DATA ────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def load_news():
    return fetch_all_sources()

@st.cache_data(ttl=60, show_spinner=False)
def load_prices():
    return fetch_all_prices()


# ── HEADER ─────────────────────────────────────────────────────
def fmt_price(label, d):
    p = d["price"]
    if p > 10000:
        pf = f"{p:,.0f}"
    elif p > 100:
        pf = f"{p:.2f}"
    elif p > 1:
        pf = f"{p:.4f}"
    else:
        pf = f"{p:.6f}"
    if d.get("chg") is not None:
        up = d["chg"] >= 0
        arrow = "▲" if up else "▼"
        cls = "tk-up" if up else "tk-down"
        return f"{label} <b>{pf}</b> <span class='{cls}'>{arrow}{d['chg']:+.2f}%</span>"
    return f"{label} <b>{pf}</b>"


def render_ticker():
    prices = load_prices()
    order = ["S&P 500", "NASDAQ", "DOW", "VIX", "EUR/USD", "GBP/USD",
             "USD/JPY", "BTC/USD", "ETH/USD", "SOL/USD", "GOLD", "OIL WTI", "10Y UST"]
    parts = [fmt_price(lbl, prices[lbl]) for lbl in order if lbl in prices]
    if parts:
        st.markdown(f"<div class='ticker-strip'>{'  ·  '.join(parts)}</div>",
                    unsafe_allow_html=True)


col_logo, col_refresh = st.columns([4, 1])
with col_logo:
    st.markdown("<div class='rsu-logo'>RSU NEWS FEED</div>"
                "<div class='rsu-sub'>FINANCIAL INTELLIGENCE FEED · TIEMPO REAL</div>",
                unsafe_allow_html=True)
with col_refresh:
    if st.button("⟳ ACTUALIZAR", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

render_ticker()

# ── DATA ───────────────────────────────────────────────────────
items, status = load_news()
active = sum(1 for s in status.values() if s["ok"])

# ── SIDEBAR FILTERS ────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ FILTROS")
    impact_sel = st.multiselect("Impacto", ["high", "med", "low"],
                                default=["high", "med", "low"],
                                format_func=lambda x: {"high": "🔴 Alto", "med": "🟡 Medio",
                                                       "low": "🟢 Bajo"}[x])
    src_options = ["(todas)"] + [s["label"] for s in SOURCES]
    src_sel = st.selectbox("Fuente", src_options)
    search = st.text_input("Buscar palabra clave")
    ticker_filter = st.text_input("Filtrar por ticker (ej: NVDA)").upper().strip()

    st.markdown("---")
    st.markdown("### ◈ SENTIMIENTO 1H")
    recent = [it for it in items if it["minutes_ago"] <= 60]
    bull = sum(1 for it in recent if it["sentiment"]["label"] == "bullish")
    bear = sum(1 for it in recent if it["sentiment"]["label"] == "bearish")
    if bull + bear:
        net = (bull - bear) / (bull + bear)
        if net > 0.2:
            st.markdown(f"<span class='sent-bull'>RISK-ON</span> · {bull}↑ / {bear}↓",
                        unsafe_allow_html=True)
        elif net < -0.2:
            st.markdown(f"<span class='sent-bear'>RISK-OFF</span> · {bull}↑ / {bear}↓",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"MIXTO · {bull}↑ / {bear}↓", unsafe_allow_html=True)
        st.progress((net + 1) / 2)
    else:
        st.caption("Sin datos suficientes")

    st.markdown("---")
    st.markdown("### ◈ ESTADO FUENTES")
    for s in SOURCES:
        st_ = status.get(s["id"], {"count": 0, "ok": False})
        dot = "🟢" if st_["ok"] else "🔴"
        st.caption(f"{dot} {s['label']}: {st_['count']}")

# ── APPLY FILTERS ──────────────────────────────────────────────
filtered = [it for it in items if it["impact"] in impact_sel]
if src_sel != "(todas)":
    filtered = [it for it in filtered if it["src_label"] == src_sel]
if search:
    q = search.lower()
    filtered = [it for it in filtered if q in (it["title"] + it["desc"]).lower()]
if ticker_filter:
    filtered = [it for it in filtered if ticker_filter in it["tickers"]]

# ── STATUS STRIP ───────────────────────────────────────────────
nh = sum(1 for i in filtered if i["impact"] == "high")
nm = sum(1 for i in filtered if i["impact"] == "med")
nl = sum(1 for i in filtered if i["impact"] == "low")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🔴 Alto", nh)
c2.metric("🟡 Medio", nm)
c3.metric("🟢 Bajo", nl)
c4.metric("Fuentes activas", f"{active}/{len(SOURCES)}")
c5.metric("Total", len(filtered))

# ── TIMELINE (expander) ────────────────────────────────────────
with st.expander("📊 Timeline — últimas 24h"):
    import pandas as pd
    buckets = [0] * 24
    for it in items:
        h = it["minutes_ago"] // 60
        if 0 <= h < 24:
            buckets[23 - h] += 1
    df = pd.DataFrame({"hora": [f"-{23 - i}h" for i in range(24)], "noticias": buckets})
    st.bar_chart(df.set_index("hora"), height=160)

# ── FEED ───────────────────────────────────────────────────────
st.markdown("---")
if not filtered:
    st.info("◌ Sin noticias en este filtro")
else:
    for it in filtered[:120]:
        mins = it["minutes_ago"]
        tstr = f"{mins}m" if mins < 60 else f"{mins // 60}h{mins % 60}m"
        sent = it["sentiment"]["label"]
        sent_html = ""
        if sent == "bullish":
            sent_html = " <span class='sent-bull'>▲</span>"
        elif sent == "bearish":
            sent_html = " <span class='sent-bear'>▼</span>"
        tickers_html = "".join(f"<span class='tk-tag'>${t}</span>" for t in it["tickers"])
        title = (f"<a href='{it['link']}' target='_blank'>{it['title']}</a>"
                 if it["link"] else it["title"])
        st.markdown(
            f"<div class='news-card {it['impact']}'>"
            f"<div class='nc-meta'><span class='nc-time'>{tstr}</span> · "
            f"<span class='nc-src'>{it['src_label']}</span> · {it['sector']} · "
            f"impacto {it['score']}/10{sent_html}</div>"
            f"<div class='nc-title'>{title}</div>"
            f"<div class='nc-desc'>{it['desc'][:200]}</div>"
            f"<div style='margin-top:6px'>{tickers_html}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.caption(f"↺ Última actualización: {datetime.now().strftime('%H:%M:%S')} · "
           f"caché 120s · pulsa ACTUALIZAR para forzar recarga")


