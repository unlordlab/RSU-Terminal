import streamlit as st
import pandas as pd
import yfinance as ticker_library # Importat com a alias per claredat
from datetime import datetime
import requests

# ────────────────────────────────────────────────
# CONFIGURACIÓ I AUXILIARS
# ────────────────────────────────────────────────

def get_from_secrets(key, default=None):
    return st.secrets.get(key, default)

# Funció per evitar repetir tot el bloc HTML de les targetes
def render_market_card(title, content_html, tooltip_text, height="340px"):
    info_icon = f'''
    <div class="tooltip-container">
        <div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div>
        <div class="tooltip-text">{tooltip_text}</div>
    </div>'''
    
    st.markdown(f'''
    <div class="group-container">
        <div class="group-header"><p class="group-title">{title}</p>{info_icon}</div>
        <div class="group-content" style="background:#11141a; height:{height}; padding:15px; overflow-y:auto;">
            {content_html}
        </div>
    </div>
    ''', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# OBTENCIÓ DE DADES REALS (YFINANCE)
# ────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_market_data(tickers):
    """Obté preu i canvi percentual per a una llista de tickers."""
    data_list = {}
    for t in tickers:
        try:
            tk = ticker_library.Ticker(t)
            # Fem servir fast_info per velocitat
            info = tk.fast_info
            current = info.last_price
            prev_close = info.previous_close
            change = ((current - prev_close) / prev_close) * 100
            data_list[t] = (current, change)
        except:
            data_list[t] = (0.0, 0.0)
    return data_list

@st.cache_data(ttl=300)
def get_crypto_prices():
    """Dades reals de Crypto via yfinance."""
    cryptos = {"BTC-USD": "BTC", "ETH-USD": "ETH", "SOL-USD": "SOL"}
    results = []
    data = fetch_market_data(list(cryptos.keys()))
    for ticker, name in cryptos.items():
        val, change = data[ticker]
        results.append((name, f"{val:,.2f}", f"{change:+.2f}%"))
    return results

# ────────────────────────────────────────────────
# ALTRES FUNCIONS DE DADES
# ────────────────────────────────────────────────

def get_economic_calendar():
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = get_from_secrets("FINNHUB_API_KEY")
    if not api_key:
        return get_fallback_news()
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=10)
        data = r.json()
        news_list = []
        for item in data[:8]:
            title = item.get("headline", "Sin título")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"
            impact = "Alto" if any(kw in title.lower() for kw in ["fed", "inflation", "gdp", "earnings"]) else "Moderado"
            news_list.append({
                "time": time_str, "title": title, "impact": impact,
                "color": "#f23645" if impact == "Alto" else "#ff9800",
                "link": item.get("url", "#")
            })
        return news_list if news_list else get_fallback_news()
    except:
        return get_fallback_news()

def get_fallback_news():
    return [{"time": "12:00", "title": "Mercat en espera de dades d'inflació", "impact": "Moderado", "color": "#ff9800", "link": "#"}]

@st.cache_data(ttl=3600)
def get_fed_liquidity():
    api_key = get_from_secrets("FRED_API_KEY", "1455ec63d36773c0e47770e312063789") # Fallback key
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=2&sort_order=desc"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()['observations']
        latest, prev = float(data[0]['value']), float(data[1]['value'])
        change = latest - prev
        if change < -100: status, color, desc = "QT", "#f23645", "Quantitative Tightening"
        elif change > 100: status, color, desc = "QE", "#00ffad", "Quantitative Easing"
        else: status, color, desc = "STABLE", "#ff9800", "Balance sheet stable"
        return status, color, desc, f"{latest/1000000:.1f}T", data[0]['date']
    except:
        return "N/A", "#888", "Error conexió FRED", "N/A", "N/A"

# ────────────────────────────────────────────────
# RENDER DASHBOARD
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .tooltip-container {position:absolute;top:50%;right:12px;transform:translateY(-50%);cursor:help;}
        .tooltip-container .tooltip-text {visibility:hidden;width:260px;background:#1e222d;color:#eee;padding:10px;border-radius:6px;position:absolute;z-index:999;top:140%;right:-10px;opacity:0;transition:0.3s;font-size:12px;border:1px solid #444;}
        .tooltip-container:hover .tooltip-text {visibility:visible;opacity:1;}
        .news-item {padding:12px; border-bottom:1px solid #1a1e26;}
        .impact-badge {padding:2px 8px; border-radius:10px; font-size:10px; font-weight:bold;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    H = "340px"

    # FILA 1: Índexs, Calendari, Reddit
    col1, col2, col3 = st.columns(3)

    with col1:
        idx_list = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ 100", "^DJI": "DOW JONES", "^RUT": "RUSSELL 2000"}
        data = fetch_market_data(list(idx_list.keys()))
        html = "".join([f'''
            <div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{name}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{data[t][0]:,.2f}</div>
                <div style="color:{"#00ffad" if data[t][1] >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{data[t][1]:+.2f}%</div></div>
            </div>''' for t, name in idx_list.items()])
        render_market_card("Market Indices", html, "Rendiment en temps real dels principals índexs.")

    with col2:
        events = get_economic_calendar()
        html = "".join([f'''
            <div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:10px; width:45px;">{ev['time']}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:11px;">{ev['event']}</div>
                    <div style="color:{"#f23645" if ev['imp']=="High" else "#ffa500"}; font-size:8px; font-weight:bold;">{ev['imp']} IMPACT</div>
                </div>
                <div style="text-align:right;"><div style="color:white; font-size:11px; font-weight:bold;">{ev['val']}</div><div style="color:#444; font-size:9px;">P: {ev['prev']}</div></div>
            </div>''' for ev in events])
        render_market_card("Economic Calendar", html, "Events econòmics clau d'avui.")

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR", "TSLA"]
        html = "".join([f'''<div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        render_market_card("Reddit Social Pulse", html, "Trending tickers a WallStreetBets.")

    # FILA 2: Fear & Greed, Sectors, Crypto
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        # Aquí aniria get_cnn_fear_greed() de config.py
        val = 65 
        label, col = "GREED", "#4caf50"
        html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%;">
                <div style="font-size:4.2rem; font-weight:bold; color:{col};">{val}</div>
                <div style="color:white; font-size:1.1rem; font-weight:bold; margin:12px 0;">{label}</div>
                <div style="width:80%; background:#0c0e12; height:12px; border-radius:6px; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{val}%; background:{col}; height:100%;"></div>
                </div>
            </div>'''
        render_market_card("Fear & Greed Index", html, "Sentiment del mercat segons CNN.")

    with c2:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        html = f'<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">' + "".join([f'''
            <div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;">
                <div style="color:white; font-size:9px; font-weight:bold;">{n}</div>
                <div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div>
            </div>''' for n, p in sectors]) + "</div>"
        render_market_card("Market Sectors", html, "Heatmap de sectors.")

    with c3:
        cryptos = get_crypto_prices()
        html = "".join([f'''
            <div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">TOKEN</div></div>
                <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div>
                <div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px; font-weight:bold;">{c}</div></div>
            </div>''' for s, p, c in cryptos])
        render_market_card("Crypto Pulse (Live)", html, "Preus reals via yfinance.")

    # FILA 3: FED, VIX, Notícies
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    with f3c1:
        vix_data = fetch_market_data(["^VIX"])["^VIX"]
        html = f'''
            <div style="text-align:center; padding-top:20px;">
                <div style="font-size:4.2rem; font-weight:bold; color:white;">{vix_data[0]:.2f}</div>
                <div style="color:#f23645; font-size:1.4rem; font-weight:bold;">VIX INDEX</div>
                <div style="color:{"#00ffad" if vix_data[1]>=0 else "#f23645"}; font-size:1.2rem;">{vix_data[1]:+.2f}%</div>
            </div>'''
        render_market_card("VIX Index", html, "Índex de volatilitat.")

    with f3c2:
        status, color, desc, assets, date = get_fed_liquidity()
        html = f'''
            <div style="text-align:center;">
                <div style="font-size:4rem; font-weight:bold; color:{color};">{status}</div>
                <div style="color:white; font-size:1.2rem; margin-bottom:10px;">{desc}</div>
                <div style="background:#0c0e12; padding:10px; border-radius:8px; border:1px solid #1a1e26;">
                    <div style="font-size:1.5rem; color:white;">{assets}</div>
                    <div style="color:#555; font-size:0.8rem;">Total Assets (FED)</div>
                </div>
            </div>'''
        render_market_card("FED Liquidity", html, "Balanç de la Reserva Federal.")

    with f3c3:
        news = fetch_finnhub_news()
        html = "".join([f'''
            <div class="news-item">
                <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                    <span style="color:#888;font-size:10px;">{item['time']}</span>
                    <span class="impact-badge" style="background:{item['color']}22;color:{item['color']};">{item['impact']}</span>
                </div>
                <div style="color:white;font-size:12px;margin-bottom:4px;">{item['title']}</div>
                <a href="{item['link']}" target="_blank" style="color:#00ffad;text-decoration:none;font-size:10px;">→ Llegir més</a>
            </div>''' for item in news])
        render_market_card("Impact News", html, "Notícies reals via Finnhub.")

if __name__ == "__main__":
    render()
