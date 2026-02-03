

import streamlit as st
from datetime import datetime
from config import get_market_index

# --- FUNCIONES DE OBTENCIÓN DE DATOS (MOCKED/SCRAPED) ---

def get_economic_calendar():
    """Eventos económicos clave del día."""
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

def get_fed_policy_data():
    """
    Datos simulados para la política de la Fed e índice de riesgo.
    Basado en las capturas de pantalla proporcionadas.
    """
    # Cambia estos valores para probar los diferentes estados (QE/QT)
    return {
        "vix": 17.03,           # Valor visto en imagen_d34e7d.png
        "liquidity_status": "QT", # "QE" para Inyectando, "QT" para Drenando
        "liquidity_label": "Drenando",
        "weekly_delta": "-15.00B" # Valor visto en imagen_d34e7d.png
    }

def get_crypto_prices():
    """Precios de referencia de criptoactivos."""
    return [
        ("BTC", "104,231.50", "+2.4%"),
        ("ETH", "3,120.12", "-1.1%"),
        ("SOL", "245.88", "+5.7%"),
    ]

def get_earnings_calendar():
    """Empresas que reportan beneficios próximamente."""
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("GOOGL", "Feb 06", "Before Bell", "High"),
        ("TSLA", "Feb 07", "After Market", "High"),
    ]

def get_insider_trading():
    """Rastreador de movimientos de directivos."""
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K"),
        ("TSLA", "DIR", "SELL", "$2.1M"),
    ]

def get_market_news():
    """Titulares de última hora para el Terminal."""
    return [
        ("17:45", "Fed's Powell hints at steady rates for Q1."),
        ("17:10", "Tech sector rallies on AI chip demand."),
        ("16:30", "Oil prices jump after inventory drawdown."),
        ("15:50", "EU markets close higher on easing inflation."),
    ]

def render():
    # Estilos CSS adicionales para los componentes específicos de las capturas
    st.markdown("""
        <style>
        .info-circle {
            background: #222;
            color: #888;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            cursor: help;
            border: 1px solid #444;
        }
        .header-with-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- CONFIGURACIÓN DE ALTURAS MAESTRAS ---
    H_MAIN = "340px" 
    H_BOTTOM = "270px"

    # ================= FILA 1 =================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Market Indices
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        # Economic Calendar
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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        # Mejora Visual: RISK & FED POLICY
        fed_data = get_fed_policy_data()
        is_qe = fed_data["liquidity_status"] == "QE"
        # Estilo dinámico según QE (verde) o QT (rojo)
        status_color = "#00ffad" if is_qe else "#f23645"
        bg_status = "rgba(0, 255, 173, 0.1)" if is_qe else "rgba(242, 54, 69, 0.1)"
        
        fed_html = f'''
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; text-align:center; padding:20px;">
                <div style="color:#888; font-size:0.75rem; letter-spacing:1px; margin-bottom:10px;">VIX INDEX</div>
                <div style="font-size:3.5rem; font-weight:bold; color:#00ffad; margin-bottom:20px; line-height:1;">{fed_data["vix"]}</div>
                <div style="width:80%; height:1px; background:#1a1e26; margin-bottom:25px;"></div>
                <div style="color:#888; font-size:0.75rem; margin-bottom:15px;">LIQUIDEZ DE LA FED</div>
                <div style="background:{bg_status}; color:{status_color}; border:1px solid {status_color}55; padding:10px 25px; border-radius:8px; font-weight:bold; font-size:1.1rem; letter-spacing:0.5px;">
                    {fed_data["liquidity_status"]} ({fed_data["liquidity_label"]})
                </div>
                <div style="color:#444; font-size:11px; margin-top:15px; font-weight:500;">Weekly Delta: {fed_data["weekly_delta"]}</div>
            </div>
        '''
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header">
                    <div class="header-with-info">
                        <span class="group-title">RISK & FED POLICY</span>
                        <div class="info-circle">?</div>
                    </div>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; border-radius: 0 0 10px 10px;">
                    {fed_html}
                </div>
            </div>
        ''', unsafe_allow_html=True)

    # ================= FILA 2 =================
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Fear & Greed Index con gradiente visual
        val = 65
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">Fear & Greed (CNN)</p></div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                    <div style="font-size:3.5rem; font-weight:bold; color:white;">{val}</div>
                    <div style="color:#888; font-size:0.8rem; letter-spacing:2px; font-weight:bold; margin-bottom:20px;">GREED</div>
                    <div style="width:80%; background:#0c0e12; height:8px; border-radius:5px; border:1px solid #1a1e26; position:relative; overflow:hidden;">
                        <div style="width:{val}%; background:linear-gradient(90deg, #f23645, #ffa500, #00ffad); height:100%; border-radius:5px;"></div>
                    </div>
                </div>
            </div>''', unsafe_allow_html=True)

    with c2:
        # Market Sectors Heatmap
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        # Crypto Pulse
        cryptos = get_crypto_prices()
        crypto_html = "".join([f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">TOKEN</div></div>
            <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px; font-weight:bold;">{c}</div></div>
            </div>''' for s, p, c in cryptos])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 3 =================
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    
    with f3c1:
        # Earnings Calendar
        earnings = get_earnings_calendar()
        earn_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</div><div style="color:#444; font-size:9px; font-weight:bold;">{d}</div></div>
            <div style="text-align:right;"><div style="color:#888; font-size:9px;">{tm}</div><span style="color:{"#f23645" if i=="High" else "#888"}; font-size:8px; font-weight:bold;">● {i}</span></div>
            </div>''' for t, d, tm, i in earnings])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        # Insider Tracker
        insiders = get_insider_trading()
        insider_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
            <div><div style="color:white; font-weight:bold; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div>
            <div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-weight:bold; font-size:10px;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div>
            </div>''' for t, p, ty, a in insiders])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        # Live News Terminal
        news = get_market_news()
        news_html = "".join([f'''<div style="padding:10px; border-bottom:1px solid #1a1e26;">
            <div style="display:flex; justify-content:space-between;"><span style="color:#00ffad; font-size:9px; font-weight:bold;">NEWS</span><span style="color:#444; font-size:9px;">{time}</span></div>
            <div style="color:white; font-size:11px; margin-top:4px; line-height:1.3;">{text}</div>
            </div>''' for time, text in news])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Live News Terminal</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; overflow-y:auto;">{news_html}</div></div>', unsafe_allow_html=True)

