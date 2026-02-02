import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import get_market_index

def get_economic_calendar():
    """Obtiene eventos económicos con fallback para evitar errores de carga."""
    try:
        # Aquí iría tu lógica de scraping. Si falla, devolvemos datos clave.
        return [
            {"time": "14:15", "event": "ADP Employment", "imp": "High", "val": "143K"},
            {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9"},
            {"time": "20:00", "event": "FOMC Minutes", "imp": "High", "val": "-"}
        ]
    except:
        return [{"time": "--:--", "event": "Loading Error", "imp": "Low", "val": "-"}]

def get_earnings_calendar():
    """Datos para el nuevo módulo 3.1."""
    return [
        ("AAPL", "After Market", "High"),
        ("AMZN", "After Market", "High"),
        ("GOOGL", "Before Bell", "High"),
        ("TSLA", "After Market", "High"),
    ]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- ALTURAS UNIFICADAS (Reducidas para mayor compactación) ---
    H_FIXED = "320px" # Altura para Fila 1 y Fila 2
    H_ROW3 = "250px"  # Altura para Fila 3

    # --- FILA 1 (ALTURA AJUSTADA A FILA 2) ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:10px 15px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_FIXED}; padding:15px; overflow:hidden;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events = get_economic_calendar()
        events_html = "".join([f'''
            <div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center; justify-content:space-between;">
                <div style="color:#888; font-size:10px; width:40px; font-family:monospace;">{ev['time']}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:11px; font-weight:500;">{ev['event']}</div>
                    <div style="color:{"#f23645" if ev['imp']=="High" else "#ffa500"}; font-size:8px; font-weight:bold; text-transform:uppercase;">{ev['imp']}</div>
                </div>
                <div style="color:white; font-size:11px; font-weight:bold;">{ev['val']}</div>
            </div>''' for ev in events])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_FIXED}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_FIXED}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # --- FILA 2 ---
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        val = 65
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p></div><div class="group-content" style="background:#11141a; height:{H_FIXED}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:3.5rem; font-weight:bold; color:#00ffad;">{val}</div><div style="color:white; font-size:0.8rem; letter-spacing:2px; font-weight:bold;">GREED</div>
            <div style="width:80%; background:#0c0e12; height:10px; border-radius:5px; margin-top:20px; border:1px solid #1a1e26;"><div style="width:{val}%; background:#00ffad; height:100%; border-radius:5px;"></div></div>
            </div></div>''', unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.2), ("FIN", -0.4), ("HLTH", +0.1), ("ENER", +2.1), ("CONS", -0.8), ("UTIL", -0.2)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:8px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:10px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H_FIXED}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:8px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        cryptos = [("BTC", "104,231.50", "+2.4%"), ("ETH", "3,120.12", "-1.1%"), ("SOL", "245.88", "+5.7%")]
        crypto_html = "".join([f'''<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:white; font-weight:bold; font-size:12px;">{s}</div></div>
            <div style="text-align:right;"><div style="color:white; font-size:12px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:10px;">{c}</div></div>
            </div>''' for s, p, c in cryptos])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_FIXED}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # --- FILA 3 (CON EARNINGS CALENDAR) ---
    st.write("")
    f3_c1, f3_c2, f3_c3 = st.columns(3)
    
    with f3_c1:
        earnings = get_earnings_calendar()
        earn_html = "".join([f'''<div style="background:#0c0e12; padding:8px 12px; border-radius:6px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</span>
            <span style="color:#555; font-size:9px;">{time}</span>
            <span style="background:{"#f2364522" if imp=="High" else "#444"}; color:{"#f23645" if imp=="High" else "#888"}; font-size:8px; padding:2px 5px; border-radius:3px; font-weight:bold;">{imp}</span>
            </div>''' for t, time, imp in earnings])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_ROW3}; padding:12px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    for i, col in enumerate([f3_c2, f3_c3]):
        with col:
            st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Module 3.{i+2}</p></div><div class="group-content" style="background:#11141a; height:{H_ROW3}; display:flex; align-items:center; justify-content:center; color:#222; font-weight:bold;">VOID</div></div>', unsafe_allow_html=True)
