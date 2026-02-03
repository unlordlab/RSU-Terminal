# market.py
import streamlit as st
from datetime import datetime
from config import get_market_index, get_cnn_fear_greed
import requests

# ────────────────────────────────────────────────
# FUNCIONS DE DADES
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
        {"time": "19:45", "title": "Tesla supera expectatives i puja un 8% després del tancament", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "18:30", "title": "El PIB dels EUA creix un 2,3% al darrer trimestre", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "16:15", "title": "Apple presenta resultats rècord gràcies a serveis", "impact": "Alto", "color": "#f23645", "link": "#"},
        {"time": "14:00", "title": "La inflació subjacent a la zona euro es modera al 2,7%", "impact": "Moderado", "color": "#ff9800", "link": "#"},
        {"time": "12:30", "title": "Microsoft Cloud supera els 30.000 milions en ingressos", "impact": "Alto", "color": "#f23645", "link": "#"},
    ]

@st.cache_data(ttl=300)
def fetch_finnhub_news():
    api_key = st.secrets.get("FINNHUB_API_KEY", None)
    
    if not api_key:
        st.warning("No s'ha trobat FINNHUB_API_KEY → utilitzant notícies simulades")
        return get_fallback_news()

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={api_key}"
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()

        news_list = []
        for item in data[:8]:
            title = item.get("headline", "Sense títol")
            link = item.get("url", "#")
            timestamp = item.get("datetime", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M") if timestamp else "N/A"

            lower = title.lower()
            if any(k in lower for k in ["earnings", "profit", "revenue", "gdp", "fed", "fomc", "inflation", "employment"]):
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
        st.warning(f"Finnhub error: {str(e)[:80]} → fallback")
        return get_fallback_news()


def get_fed_liquidity():
    api_key = "1455ec63d36773c0e47770e312063789"
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=WALCL&api_key={api_key}&file_type=json&limit=10&sort_order=desc"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            obs = data.get('observations', [])
            if len(obs) >= 2:
                latest = float(obs[0]['value'])
                prev = float(obs[1]['value'])
                date_str = obs[0]['date']
                change = latest - prev
                if change < -100:
                    return "QT", "#f23645", "Quantitative Tightening", f"{latest/1000:.1f}T", date_str
                elif change > 100:
                    return "QE", "#00ffad", "Quantitative Easing", f"{latest/1000:.1f}T", date_str
                else:
                    return "STABLE", "#ff9800", "Balance sheet stable", f"{latest/1000:.1f}T", date_str
        return "ERROR", "#888", "API no disponible", "N/A", "N/A"
    except:
        return "N/A", "#888", "Sense connexió", "N/A", "N/A"


# ────────────────────────────────────────────────
# RENDER DEL DASHBOARD
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

    # FILA 1 ────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12;padding:12px 15px;border-radius:10px;margin-bottom:10px;border:1px solid #1a1e26;display:flex;justify-content:space-between;align-items:center;">
                <div><div style="font-weight:bold;color:white;font-size:13px;">{n}</div><div style="color:#555;font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white;font-weight:bold;font-size:13px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"};font-size:11px;font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        tooltip = "Rendiment en temps real dels principals índexs borsaris dels EUA."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p>{info_icon}</div><div class="group-content" style="background:#11141a;height:{H};padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    # (col2 i col3 iguals a la teva versió anterior)

    # FILA 2 ────────────────────────────────────────
    st.write("")
    c1, c2, c3 = st.columns(3)

    with c1:
        val = get_cnn_fear_greed()
        if val is None:
            val_display = "N/D"
            label = "ERROR DE CONNEXIÓ"
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

        tooltip = "Índex CNN Fear & Greed – mesura el sentiment del mercat."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'

        # Contenidor principal (sense la llegenda dins del f-string)
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

        # La llegenda ara en markdown separat → això sí que renderitza correctament
        st.markdown("""
        <div class="fng-legend">
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#d32f2f;"></div><div>Extreme Fear</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#f57c00;"></div><div>Fear</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#ff9800;"></div><div>Neutral</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#4caf50;"></div><div>Greed</div></div>
            <div class="fng-legend-item"><div class="fng-color-box" style="background:#00ffad;"></div><div>Extreme Greed</div></div>
        </div>
        """, unsafe_allow_html=True)

    # (c2 i c3 iguals)

    # FILA 3 ────────────────────────────────────────
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)

    # (f3c1 i f3c2 iguals)

    with f3c3:
        news = fetch_finnhub_news()

        # Construïm les notícies com a llista d'strings separats
        news_blocks = []
        for item in news:
            news_blocks.append(f'''
                <div class="news-item">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;">
                        <span style="color:#888;font-size:0.78rem;font-family:monospace;">{item['time']}</span>
                        <span class="impact-badge" style="background-color:{item['color']}22;color:{item['color']};">{item['impact']}</span>
                    </div>
                    <div style="color:white;font-size:0.92rem;line-height:1.35;margin-bottom:8px;">{item['title']}</div>
                    <a href="{item['link']}" target="_blank" class="news-link">→ Llig la notícia completa</a>
                </div>
            ''')

        news_content = "".join(news_blocks)

        tooltip = "Notícies d'alt impacte obtingudes via Finnhub API."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'

        # Contenidor principal (sense HTML dins del f-string)
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Notícies d\'Alt Impacte</p>{info_icon}</div>', unsafe_allow_html=True)

        # Contingut de notícies separat
        st.markdown(f'<div class="group-content" style="background:#11141a;height:{H};overflow-y:auto;padding:0;">{news_content}</div>', unsafe_allow_html=True)

        # Tancament del contenidor
        st.markdown('</div>', unsafe_allow_html=True)

    # FILA 4 ────────────────────────────────────────
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)

    # (f4c1, f4c2, f4c3 iguals a la teva versió anterior)
