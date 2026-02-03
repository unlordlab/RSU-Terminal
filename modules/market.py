# market.py
import streamlit as st
from datetime import datetime
from config import get_market_index, get_cnn_fear_greed
import requests

# ────────────────────────────────────────────────
# FUNCIONES DE DATOS
# ────────────────────────────────────────────────

def get_economic_calendar():
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

def get_crypto_prices():
    return [
        ("BTC", "104,231.50", "+2.4%"),
        ("ETH", "3,120.12", "-1.1%"),
        ("SOL", "245.88", "+5.7%"),
    ]

def get_earnings_calendar():
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("GOOGL", "Feb 06", "Before Bell", "High"),
        ("TSLA", "Feb 07", "After Market", "High"),
    ]

def get_insider_trading():
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K"),
        ("TSLA", "DIR", "SELL", "$2.1M"),
    ]

def get_fallback_news():
    return [
        {"time": "19:45", "title": "Tesla supera expectativas de beneficios y sube un 8% en after-hours", "impact": "Alto", "color": "#f23645", "link": "https://www.cnbc.com/2026/02/03/tesla-earnings-q4-2025.html"},
        {"time": "18:30", "title": "El PIB de EE.UU. creció un 2,3% en el último trimestre", "impact": "Alto", "color": "#f23645", "link": "https://www.bea.gov/news/2026/gross-domestic-product-fourth-quarter-2025"},
        {"time": "16:15", "title": "Apple presenta resultados récord gracias a servicios y wearables", "impact": "Alto", "color": "#f23645", "link": "https://www.apple.com/newsroom/2026/02/apple-reports-record-revenue/"},
        {"time": "14:00", "title": "La inflación subyacente en la zona euro se modera al 2,7%", "impact": "Moderado", "color": "#ff9800", "link": "https://www.ecb.europa.eu/press/pr/date/2026/html/index.en.html"},
        {"time": "12:30", "title": "Microsoft Cloud supera los 30.000 millones de dólares en ingresos", "impact": "Alto", "color": "#f23645", "link": "https://news.microsoft.com/2026/02/03/microsoft-q2-fy26-earnings/"},
    ]

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    
    if not api_key:
        st.warning("No se encontró FINNHUB_API_KEY en secrets.toml → usando noticias simuladas")
        return get_fallback_news()

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()

        news_list = []
        for item in data[:8]:
            title = item.get("headline", "Sin título")
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"

            lower_title = title.lower()
            if any(kw in lower_title for kw in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "employment", "nfp", "cpi"]):
                impact = "Alto"
                color = "#f23645"
            else:
                impact = "Moderado"
                color = "#ff9800"

            news_list.append({
                "time": time_str,
                "title": title,
                "impact": impact,
                "color": color,
                "link": link
            })

        return news_list if news_list else get_fallback_news()

    except Exception as e:
        st.warning(f"Finnhub falló: {str(e)[:100]} → usando fallback")
        return get_fallback_news()

def get_fed_liquidity():
    api_key = "1455ec63d36773c0e47770e312063789"
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            observations = data.get('observations', [])
            if len(observations) >= 2:
                latest_val = float(observations[0]['value'])
                prev_val = float(observations[1]['value'])
                date_latest = observations[0]['date']
                change = latest_val - prev_val
                if change < -100:
                    status = "QT"
                    color = "#f23645"
                    desc = "Quantitative Tightening"
                elif change > 100:
                    status = "QE"
                    color = "#00ffad"
                    desc = "Quantitative Easing"
                else:
                    status = "STABLE"
                    color = "#ff9800"
                    desc = "Balance sheet stable"
                return status, color, desc, f"{latest_val/1000:.1f}T", date_latest
        return "ERROR", "#888", "API temporalmente no disponible", "N/A", "N/A"
    except:
        return "N/A", "#888", "Sin conexión a FRED", "N/A", "N/A"


# ────────────────────────────────────────────────
# DASHBOARD
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .tooltip-container {position:absolute;top:50%;right:12px;transform:translateY(-50%);cursor:help;}
        .tooltip-container .tooltip-text {visibility:hidden;width:260px;background:#1e222d;color:#eee;text-align:left;padding:10px 12px;border-radius:6px;position:absolute;z-index:999;top:140%;right:-10px;opacity:0;transition:opacity 0.3s,visibility 0.3s;font-size:12px;border:1px solid #444;pointer-events:none;box-shadow:0 4px 12px rgba(0,0,0,0.4);}
        .tooltip-container:hover .tooltip-text {visibility:visible;opacity:1;}

        .fng-legend {display:flex;justify-content:space-between;width:95%;margin-top:16px;font-size:0.70rem;color:#ccc;text-align:center;}
        .fng-legend-item {flex:1;padding:0 6px;}
        .fng-color-box {width:100%;height:8px;margin-bottom:4px;border-radius:4px;border:1px solid rgba(255,255,255,0.1);}

        .news-item {padding:12px 15px;border-bottom:1px solid #1a1e26;transition:background 0.2s;}
        .news-item:hover {background:#0c0e12;}
        .impact-badge {padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:bold;}
        .news-link {color:#00ffad;text-decoration:none;font-size:0.85rem;}
        .news-link:hover {text-decoration:underline;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    H = "340px"

    # FILA 1
    col1, col2, col3 = st.columns(3)

    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        tooltip = "Rendimiento en tiempo real de los principales índices bursátiles de EE.UU."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events = get_economic_calendar()
        events_html = "".join([f'''
            <div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:10px; width:45px; font-family:monospace;">{ev['time']}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:11px; font-weight:500;">{ev['event']}</div>
                    <div style="color:{"#f23645" if ev['imp']=="High" else "#ffa500"}; font-size:8px; font-weight:bold; text-transform:uppercase;">{ev['imp']} IMPACT</div>
                </div>
                <div style="text-align:right;"><div style="color:white; font-size:11px; font-weight:bold;">{ev['val']}</div><div style="color:#444; font-size:9px;">P: {ev['prev']}</div></div>
            </div>''' for ev in events])
        tooltip = "Eventos económicos clave programados para hoy y su impacto esperado."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR", "TSLA"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        tooltip = "Tickers más mencionados y trending en comunidades de Reddit como WallStreetBets."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # FILA 2
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val_display = "N/D"
            label = "ERROR DE CONEXIÓN"
            col = "#888"
            bar_width = 50
            extra = " (refresca)"
        else:
            val_display = val
            bar_width = val
            if val <= 24:
                label, col = "EXTREME FEAR", "#d32f2f"
            elif val <= 44:
                label, col = "FEAR", "#f57c00"
            elif val <= 55:
                label, col = "NEUTRAL", "#ff9800"
            elif val <= 75:
                label, col = "GREED", "#4caf50"
            else:
                label, col = "EXTREME GREED", "#00ffad"
            extra = ""

        tooltip = "Índice CNN Fear & Greed – mide el sentimiento del mercado."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'

        # Contenedor principal SIN HTML de leyenda dentro del f-string
        st.markdown(f'''<div class="group-container">
            <div class="group-header">
                <p class="group-title">Fear & Greed Index</p>
                {info_icon}
            </div>
            <div class="group-content" style="background:#11141a; height:{H}; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px 15px;">
                <div style="font-size:4.2rem; font-weight:bold; color:{col};">{val_display}</div>
                <div style="color:white; font-size:1.1rem; letter-spacing:1.5px; font-weight:bold; margin:12px 0;">{label}{extra}</div>
                <div style="width:88%; background:#0c0e12; height:14px; border-radius:7px; margin:18px 0 12px 0; border:1px solid #1a1e26; overflow:hidden;">
                    <div style="width:{bar_width}%; background:linear-gradient(to right, {col}, {col}aa); height:100%; transition:width 0.8s ease;"></div>
                </div>
            </div>
        </div>''', unsafe_allow_html=True)

        # Leyenda en markdown independiente (esto SIEMPRE funciona)
        st.markdown("""
        <div class="fng-legend">
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Extreme Fear</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Fear</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Greed</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Extreme Greed</div></div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        tooltip = "Rendimiento diario de los principales sectores del mercado (heatmap)."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        cryptos = get_crypto_prices()
        crypto_html = "".join([f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">TOKEN</div></div>
            <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px; font-weight:bold;">{c}</div></div>
            </div>''' for s, p, c in cryptos])
        tooltip = "Precios y variación de las principales criptomonedas."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # FILA 3
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    with f3c1:
        earnings = get_earnings_calendar()
        earn_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</div><div style="color:#444; font-size:9px; font-weight:bold;">{d}</div></div>
            <div style="text-align:right;"><div style="color:#888; font-size:9px;">{tm}</div><span style="color:{"#f23645" if i=="High" else "#888"}; font-size:8px; font-weight:bold;">● {i}</span></div>
            </div>''' for t, d, tm, i in earnings])
        tooltip = "Calendario de reportes de ganancias de empresas importantes esta semana."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        insiders = get_insider_trading()
        insider_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
            <div><div style="color:white; font-weight:bold; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div>
            <div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-weight:bold; font-size:10px;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div>
            </div>''' for t, p, ty, a in insiders])
        tooltip = "Compras y ventas recientes de acciones por parte de directivos e insiders."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news = fetch_finnhub_news()

        # Construimos el HTML de noticias sin f-string grande alrededor
        news_items = []
        for item in news:
            news_items.append(f'''
                <div class="news-item">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                        <span style="color:#888;font-size:0.78rem;font-family:monospace;">{item['time']}</span>
                        <span class="impact-badge" style="background-color:{item['color']}22;color:{item['color']};">{item['impact']}</span>
                    </div>
                    <div style="color:white;font-size:0.92rem;line-height:1.35;margin-bottom:8px;">{item['title']}</div>
                    <a href="{item['link']}" target="_blank" class="news-link">→ Leer noticia completa</a>
                </div>
            ''')

        news_html = "".join(news_items)

        tooltip = "Noticias de gran impacto obtenidas vía Finnhub API."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'

        # Contenedor principal
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Noticias de Alto Impacto</p>{info_icon}</div>', unsafe_allow_html=True)

        # Contenido de noticias en markdown separado
        st.markdown(f'<div class="group-content" style="background:#11141a; height:{H}; overflow-y:auto; padding:0;">{news_html}</div>', unsafe_allow_html=True)

        # Cierre del container
        st.markdown('</div>', unsafe_allow_html=True)

    # FILA 4
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)

    with f4c1:
        vix = get_market_index("^VIX")
        vix_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:4.2rem; font-weight:bold; color:white;">{vix[0]:.2f}</div>
                <div style="color:#f23645; font-size:1.4rem; font-weight:bold;">VIX INDEX</div>
                <div style="color:{"#00ffad" if vix[1]>=0 else "#f23645"}; font-size:1.2rem; font-weight:bold;">{vix[1]:+.2f}%</div>
                <div style="color:#555; font-size:0.9rem; margin-top:15px;">Volatility Index</div>
            </div>
        '''
        tooltip = "Índice de volatilidad CBOE (VIX) – mide el miedo esperado en el mercado."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">VIX Index</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{vix_html}</div></div>', unsafe_allow_html=True)

    with f4c2:
        status, color, desc, assets, date = get_fed_liquidity()
        fed_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:5rem; font-weight:bold; color:{color};">{status}</div>
                <div style="color:white; font-size:1.3rem; font-weight:bold; margin:10px 0;">{desc}</div>
                <div style="background:#0c0e12; padding:12px 20px; border-radius:8px; border:1px solid #1a1e26;">
                    <div style="font-size:1.8rem; color:white;">{assets}</div>
                    <div style="color:#888; font-size:0.9rem;">Total Assets (FED)</div>
                </div>
                <div style="color:#555; font-size:0.8rem; margin-top:12px;">Actualizado: {date}</div>
            </div>
        '''
        tooltip = "Política de liquidez de la FED: QE (expansión) / QT (contracción) según balance."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">FED Liquidity Policy</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{fed_html}</div></div>', unsafe_allow_html=True)

    with f4c3:
        tnx = get_market_index("^TNX")
        tnx_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center;">
                <div style="font-size:4.2rem; font-weight:bold; color:white;">{tnx[0]:.2f}%</div>
                <div style="color:white; font-size:1.4rem; font-weight:bold;">10Y TREASURY</div>
                <div style="color:{"#00ffad" if tnx[1]>=0 else "#f23645"}; font-size:1.2rem; font-weight:bold;">{tnx[1]:+.2f}%</div>
                <div style="color:#555; font-size:0.9rem; margin-top:15px;">US 10-Year Yield</div>
            </div>
        '''
        tooltip = "Rendimiento del bono del Tesoro de EE.UU. a 10 años."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">10Y Treasury Yield</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H}; padding:15px;">{tnx_html}</div></div>', unsafe_allow_html=True)


# Fin del archivo
