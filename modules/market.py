# market.py
import streamlit as st
from datetime import datetime
from config import get_market_index, get_cnn_fear_greed
import requests

# ────────────────────────────────────────────────
# FUNCIONES AUXILIARES DE DATOS
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

def get_market_news():
    return [
        ("17:45", "Fed's Powell hints at steady rates for Q1."),
        ("17:10", "Tech sector rallies on AI chip demand."),
        ("16:30", "Oil prices jump after inventory drawdown."),
        ("15:50", "EU markets close higher on easing inflation."),
    ]

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
        return "N/A", "#888", "Sin conexión", "N/A", "N/A"


# ────────────────────────────────────────────────
# DASHBOARD PRINCIPAL
# ────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
        .tooltip-container {
            position: absolute;
            top: 50%;
            right: 12px;
            transform: translateY(-50%);
            cursor: help;
        }
        .tooltip-container .tooltip-text {
            visibility: hidden;
            width: 260px;
            background-color: #1e222d;
            color: #eee;
            text-align: left;
            padding: 10px 12px;
            border-radius: 6px;
            position: absolute;
            z-index: 999;
            top: 140%;
            right: -10px;
            opacity: 0;
            transition: opacity 0.3s, visibility 0.3s;
            font-size: 12px;
            border: 1px solid #444;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .tooltip-container:hover .tooltip-text {
            visibility: visible;
            opacity: 1;
        }
        .fng-legend {
            display: flex;
            justify-content: space-between;
            width: 95%;
            margin-top: 16px;
            font-size: 0.70rem;
            color: #ccc;
            text-align: center;
        }
        .fng-legend-item {
            flex: 1;
            padding: 0 6px;
        }
        .fng-color-box {
            width: 100%;
            height: 8px;
            margin-bottom: 4px;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.1);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    H_MAIN = "340px"
    H_BOTTOM = "270px"

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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR", "TSLA"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        tooltip = "Tickers más mencionados y trending en comunidades de Reddit como WallStreetBets."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

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

        tooltip = "Índice CNN Fear & Greed – mide el sentimiento del mercado (datos reales vía endpoint oficial)."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'

        st.markdown(f'''<div class="group-container">
            <div class="group-header">
                <p class="group-title">Fear & Greed Index</p>
                {info_icon}
            </div>
            <div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:25px 15px;">
                <div style="font-size:4.2rem; font-weight:bold; color:{col};">{val_display}</div>
                <div style="color:white; font-size:1.1rem; letter-spacing:1.5px; font-weight:bold; margin:12px 0;">{label}{extra}</div>
                <div style="width:88%; background:#0c0e12; height:14px; border-radius:7px; margin:20px 0; border:1px solid #1a1e26; overflow:hidden; position:relative;">
                    <div style="width:{bar_width}%; background:linear-gradient(to right, {col}, {col}aa); height:100%; transition:width 0.8s ease;"></div>
                </div>
            </div>
        </div>''', unsafe_allow_html=True)

        # ── Leyenda separada ──
        st.markdown("""
        <div class="fng-legend">
            <div class="fng-legend-item">
                <div class="fng-color-box" style="background:#d32f2f;"></div>
                <div>Extreme Fear</div>
            </div>
            <div class="fng-legend-item">
                <div class="fng-color-box" style="background:#f57c00;"></div>
                <div>Fear</div>
            </div>
            <div class="fng-legend-item">
                <div class="fng-color-box" style="background:#ff9800;"></div>
                <div>Neutral</div>
            </div>
            <div class="fng-legend-item">
                <div class="fng-color-box" style="background:#4caf50;"></div>
                <div>Greed</div>
            </div>
            <div class="fng-legend-item">
                <div class="fng-color-box" style="background:#00ffad;"></div>
                <div>Extreme Greed</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        tooltip = "Rendimiento diario de los principales sectores del mercado (heatmap)."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        cryptos = get_crypto_prices()
        crypto_html = "".join([f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">TOKEN</div></div>
            <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px; font-weight:bold;">{c}</div></div>
            </div>''' for s, p, c in cryptos])
        tooltip = "Precios y variación de las principales criptomonedas."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        insiders = get_insider_trading()
        insider_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
            <div><div style="color:white; font-weight:bold; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div>
            <div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-weight:bold; font-size:10px;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div>
            </div>''' for t, p, ty, a in insiders])
        tooltip = "Compras y ventas recientes de acciones por parte de directivos e insiders."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news = get_market_news()
        news_html = "".join([f'''<div style="padding:10px; border-bottom:1px solid #1a1e26;">
            <div style="display:flex; justify-content:space-between;"><span style="color:#00ffad; font-size:9px; font-weight:bold;">NEWS</span><span style="color:#444; font-size:9px;">{time}</span></div>
            <div style="color:white; font-size:11px; margin-top:4px; line-height:1.3;">{text}</div>
            </div>''' for time, text in news])
        tooltip = "Titulares financieros y noticias de última hora."
        info_icon = f'<div class="tooltip-container"><div style="width:26px;height:26px;border-radius:50%;background:#1a1e26;border:2px solid #555;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:16px;font-weight:bold;">?</div><div class="tooltip-text">{tooltip}</div></div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Live News Terminal</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; overflow-y:auto;">{news_html}</div></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">VIX Index</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{vix_html}</div></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">FED Liquidity Policy</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{fed_html}</div></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">10Y Treasury Yield</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{tnx_html}</div></div>', unsafe_allow_html=True)


# Fin del archivo market.py
