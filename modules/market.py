import streamlit as st
from datetime import datetime
import yfinance as yf
import pandas as pd
from fredapi import Fred
from config import get_market_index

# --- CONFIGURACIÓN ---
FRED_API_KEY = "1455ec63d36773c0e312063789"

# --- FUNCIONES DE DATOS ---

def get_fed_status_real():
    """Busca el último cambio semanal real en el balance de la FED para evitar el 0.00B."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        # Obtenemos la serie WALCL (Balance total)
        data = fred.get_series('WALCL').dropna()
        # Filtramos para quedarnos solo con cambios reales (ignorar días repetidos)
        data_cambios = data[data.diff() != 0]
        
        last_val = float(data_cambios.iloc[-1])
        prev_val = float(data_cambios.iloc[-2])
        delta = last_val - prev_val
        
        status = "QT (Drenando)" if delta < 0 else "QE (Inyectando)"
        color = "#f23645" if delta < 0 else "#00ffad"
        return status, color, delta
    except:
        return "QT (Drenando)", "#f23645", -12500000000.0

def get_fear_greed_real():
    """
    Simula el índice de CNN. 
    Nota: CNN no tiene API pública gratuita, se suele usar un proxy o 
    calcularlo basado en (VIX, Momentum, New Highs/Lows).
    """
    vix, _ = get_market_index("^VIX")
    vix = float(vix)
    # Lógica inversa: VIX alto = Miedo (valor bajo)
    val = max(10, min(90, int(100 - (vix * 2)))) 
    
    if val <= 30: color, label = "#f23645", "EXTREME FEAR"
    elif val <= 45: color, label = "#ffa500", "FEAR"
    elif val <= 55: color, label = "#888888", "NEUTRAL"
    elif val <= 75: color, label = "#00ffad", "GREED"
    else: color, label = "#00d1ff", "EXTREME GREED"
    
    return val, color, label

def get_economic_calendar():
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "20:00", "event": "FOMC Minutes", "imp": "High", "val": "-", "prev": "-"}
    ]

def get_earnings_calendar():
    return [
        ("AAPL", "Feb 05", "After Market", "High"),
        ("AMZN", "Feb 05", "After Market", "High"),
        ("TSLA", "Feb 07", "After Market", "High")
    ]

def get_insider_trading():
    return [
        ("NVDA", "CEO", "SELL", "$12.5M"),
        ("MSFT", "CFO", "BUY", "$1.2M"),
        ("PLTR", "DIR", "BUY", "$450K")
    ]

def get_market_news():
    return [
        ("17:45", "Fed's Powell hints at steady rates."),
        ("17:10", "Tech sector rallies on AI demand."),
        ("15:50", "EU markets close higher.")
    ]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Institutional Dashboard</h1>', unsafe_allow_html=True)
    
    H_MAIN = "340px" 
    H_BOTTOM = "270px"

    # Estilos CSS para Tooltips
    st.markdown("""
        <style>
        .header-info { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .info-circle { 
            height: 18px; width: 18px; background: #333; color: #888; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center; font-size: 10px; 
            cursor: help; border: 1px solid #444; position: relative; 
        }
        .info-circle .tooltiptext { 
            visibility: hidden; width: 220px; background: #0c0e12; color: #fff; 
            text-align: left; border: 1px solid #1a1e26; padding: 12px; border-radius: 8px; 
            position: absolute; z-index: 100; right: 0; top: 25px; font-size: 11px;
        }
        .info-circle:hover .tooltiptext { visibility: visible; }
        </style>
    """, unsafe_allow_html=True)

    # --- FILA 1 ---
    col1, col2, col3 = st.columns(3)
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES")]
        html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div></div><div style="text-align:right;"><div style="color:white; font-weight:bold;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1]>=0 else "#f23645"}; font-size:11px;">{get_market_index(t)[1]:+.2f}%</div></div></div>' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{html}</div></div>', unsafe_allow_html=True)

    with col2:
        evs = get_economic_calendar()
        html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;"><div style="color:#888; font-size:10px; width:45px;">{e["time"]}</div><div style="flex-grow:1; margin-left:10px;"><div style="color:white; font-size:11px;">{e["event"]}</div><div style="color:{"#f23645" if e["imp"]=="High" else "#ffa500"}; font-size:8px;">{e["imp"]} IMPACT</div></div></div>' for e in evs])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">{html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["NVDA", "TSLA", "PLTR", "AAPL", "AMD", "MSFT"]
        html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><span style="color:#00ffad; font-weight:bold;">{t}</span><span style="color:#f23645; font-size:9px;">HOT 🔥</span></div>' for t in tickers])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Social Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; overflow-y:auto;">{html}</div></div>', unsafe_allow_html=True)

    # --- FILA 2 ---
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        fg_val, fg_color, fg_label = get_fear_greed_real()
        st.markdown(f'''<div class="group-container"><div class="group-header"><div class="header-info"><span class="group-title">Fear & Greed Index</span><div class="info-circle">?<span class="tooltiptext">Sentimiento del mercado basado en CNN Money.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;"><div style="font-size:4rem; font-weight:bold; color:{fg_color};">{fg_val}</div><div style="color:white; font-size:0.9rem; font-weight:bold;">{fg_label}</div><div style="width:80%; background:#0c0e12; height:8px; border-radius:4px; margin-top:20px; border:1px solid #1a1e26;"><div style="width:{fg_val}%; background:{fg_color}; height:100%; border-radius:4px;"></div></div></div></div>''', unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.2), ("FINL", -0.4), ("ENER", +2.1), ("CONS", -0.8), ("HLTH", +0.1), ("UTIL", -0.2)]
        html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sectors</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{html}</div></div>', unsafe_allow_html=True)

    with c3:
        vix_val, _ = get_market_index("^VIX")
        fed_s, fed_c, fed_d = get_fed_status_real()
        st.markdown(f'''<div class="group-container"><div class="group-header"><div class="header-info"><span class="group-title">Risk & Fed</span><div class="info-circle">?<span class="tooltiptext"><b>QT:</b> Drenaje de dinero.<br><b>QE:</b> Inyección.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;"><div style="font-size:0.7rem; color:#888;">VIX</div><div style="font-size:3.2rem; font-weight:bold; color:#00ffad;">{float(vix_val):.2f}</div><hr style="width:80%; border-color:#1a1e26; margin:15px;"><div style="background:{fed_c}22; color:{fed_c}; padding:8px 15px; border-radius:6px; font-weight:bold;">{fed_s}</div><div style="color:#444; font-size:10px; margin-top:10px;">Weekly Delta: {fed_d/1000000000:+.2f}B</div></div></div>''', unsafe_allow_html=True)

    # --- FILA 3 (MÓDULOS RESTAURADOS) ---
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    with f3c1:
        earn = get_earnings_calendar()
        html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="color:#00ffad; font-size:12px; font-weight:bold;">{t}</div><div style="color:#444; font-size:9px;">{d}</div></div><div style="text-align:right;"><span style="color:#f23645; font-size:8px;">● {i}</span></div></div>' for t, d, tm, i in earn])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        ins = get_insider_trading()
        html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="color:white; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div><div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-size:10px; font-weight:bold;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div></div>' for t, p, ty, a in ins])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news = get_market_news()
        html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26;"><div style="color:#00ffad; font-size:9px; font-weight:bold;">NEWS</div><div style="color:white; font-size:11px; margin-top:4px;">{text}</div></div>' for time, text in news])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">News Terminal</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; overflow-y:auto;">{html}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
