import streamlit as st
from datetime import datetime
from config import get_market_index, get_cnn_fear_greed
import requests

# --- FUNCIONES DE OBTENCIÓN DE DATOS (MOCKED/SCRAPED) ---

def get_economic_calendar():
    """Eventos económicos clave del día."""
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

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

def get_fed_liquidity():
    """Obtiene el estado actual de política de liquidez FED (QE/QT) vía FRED API."""
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

# ================= RENDER PRINCIPAL =================
def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- CONFIGURACIÓN DE ALTURAS MAESTRAS ---
    H_MAIN = "340px" 
    H_BOTTOM = "270px"

    # ================= FILA 1 =================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Rendimiento en tiempo real de los principales índices bursátiles de EE.UU.">?</div>'
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
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Eventos económicos clave programados para hoy y su impacto esperado.">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR", "TSLA"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Tickers más mencionados y trending en comunidades de Reddit como WallStreetBets.">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 2 =================
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        val = get_cnn_fear_greed() or 50
        if val >= 75:
            label, col = "EXTREME GREED", "#00ffad"
        elif val >= 55:
            label, col = "GREED", "#4caf50"
        elif val >= 45:
            label, col = "NEUTRAL", "#ff9800"
        elif val >= 25:
            label, col = "FEAR", "#f57c00"
        else:
            label, col = "EXTREME FEAR", "#d32f2f"
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Índice Fear & Greed de CNN basado en múltiples indicadores de sentimiento del mercado.">?</div>'
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:3.5rem; font-weight:bold; color:{col};">{val}</div><div style="color:white; font-size:0.8rem; letter-spacing:2px; font-weight:bold;">{label}</div>
            <div style="width:80%; background:#0c0e12; height:10px; border-radius:5px; margin-top:20px; border:1px solid #1a1e26; position:relative;">
                <div style="width:{val}%; background:{col}; height:100%; border-radius:5px; box-shadow:0 0 15px {col}66;"></div>
            </div></div></div>''', unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Mapa de calor con el rendimiento diario de los principales sectores del mercado.">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        cryptos = get_crypto_prices()
        crypto_html = "".join([f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">TOKEN</div></div>
            <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px; font-weight:bold;">{c}</div></div>
            </div>''' for s, p, c in cryptos])
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Precios y cambios de las principales criptomonedas.">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 3 =================
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    
    with f3c1:
        earnings = get_earnings_calendar()
        earn_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</div><div style="color:#444; font-size:9px; font-weight:bold;">{d}</div></div>
            <div style="text-align:right;"><div style="color:#888; font-size:9px;">{tm}</div><span style="color:{"#f23645" if i=="High" else "#888"}; font-size:8px; font-weight:bold;">● {i}</span></div>
            </div>''' for t, d, tm, i in earnings])
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Calendario de reportes de ganancias de empresas clave esta semana.">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        insiders = get_insider_trading()
        insider_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
            <div><div style="color:white; font-weight:bold; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div>
            <div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-weight:bold; font-size:10px;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div>
            </div>''' for t, p, ty, a in insiders])
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Actividad reciente de compra/venta de acciones por parte de insiders (directivos).">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news = get_market_news()
        news_html = "".join([f'''<div style="padding:10px; border-bottom:1px solid #1a1e26;">
            <div style="display:flex; justify-content:space-between;"><span style="color:#00ffad; font-size:9px; font-weight:bold;">NEWS</span><span style="color:#444; font-size:9px;">{time}</span></div>
            <div style="color:white; font-size:11px; margin-top:4px; line-height:1.3;">{text}</div>
            </div>''' for time, text in news])
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Últimas noticias financieras en tiempo real.">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Live News Terminal</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; overflow-y:auto;">{news_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 4 (NUEVA) =================
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
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Índice de volatilidad CBOE (VIX) que mide el miedo esperado en el mercado.">?</div>'
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
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Estado actual de la política monetaria de la FED (QE = expansión de balance, QT = contracción). Datos vía FRED.">?</div>'
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
        info_icon = '<div style="float:right; width:26px; height:26px; border-radius:50%; background:#1a1e26; border:2px solid #555; display:flex; align-items:center; justify-content:center; color:#888; font-size:16px; font-weight:bold; cursor:help;" title="Rendimiento del bono del Tesoro de EE.UU. a 10 años (benchmark de tasas de interés).">?</div>'
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">10Y Treasury Yield</p>{info_icon}</div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{tnx_html}</div></div>', unsafe_allow_html=True)
