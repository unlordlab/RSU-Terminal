import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
import pandas as pd

# --- FUNCIONES DE CONEXIÓN A APIS REALES ---

def get_real_market_indices():
    """Obtiene precios en tiempo real de Yahoo Finance."""
    tickers = {
        "^GSPC": "S&P 500",
        "^IXIC": "NASDAQ 100",
        "^DJI": "DOW JONES",
        "^RUT": "RUSSELL 2000"
    }
    data = []
    try:
        # Descargamos los últimos 2 días para calcular el cambio porcentual
        df = yf.download(list(tickers.keys()), period="2d", interval="1d", progress=False)['Close']
        for t, name in tickers.items():
            current_price = df[t].iloc[-1]
            prev_price = df[t].iloc[-2]
            change = ((current_price - prev_price) / prev_price) * 100
            data.append((name, current_price, change))
    except:
        # Fallback si falla la red
        data = [("S&P 500", 0.0, 0.0), ("NASDAQ 100", 0.0, 0.0), ("DOW JONES", 0.0, 0.0), ("RUSSELL 2000", 0.0, 0.0)]
    return data

def get_real_crypto():
    """Obtiene precios reales desde la API pública de CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=5).json()
        return [
            ("BTC", f"{r['bitcoin']['usd']:,}", r['bitcoin']['usd_24h_change']),
            ("ETH", f"{r['ethereum']['usd']:,}", r['ethereum']['usd_24h_change']),
            ("SOL", f"{r['solana']['usd']:,}", r['solana']['usd_24h_change']),
        ]
    except:
        return [("BTC", "Error", 0), ("ETH", "Error", 0), ("SOL", "Error", 0)]

def get_economic_calendar():
    """Datos económicos (Simulado para estabilidad, se puede scrapear de Investing)."""
    return [
        {"time": "14:30", "event": "Non-Farm Payrolls", "imp": "High", "val": "223K"},
        {"time": "16:00", "event": "ISM Manufacturing", "imp": "High", "val": "48.2"},
        {"time": "18:00", "event": "Fed Chair Speech", "imp": "High", "val": "-"}
    ]

# --- RENDER DEL DASHBOARD ---

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard Live</h1>', unsafe_allow_html=True)
    
    H_ALL = "340px" 

    # ================= FILA 1 =================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indices_data = get_real_market_indices()
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{name}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{price:,.2f}</div><div style="color:{"#00ffad" if change >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{change:+.2f}%</div></div>
            </div>''' for name, price, change in indices_data])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices (Real-Time)</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events = get_economic_calendar()
        events_html = "".join([f'''
            <div style="padding:12px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:10px; width:45px; font-family:monospace;">{ev['time']}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:11px; font-weight:500;">{ev['event']}</div>
                    <div style="color:{"#f23645" if ev['imp']=="High" else "#ffa500"}; font-size:8px; font-weight:bold; text-transform:uppercase;">{ev['imp']}</div>
                </div>
                <div style="text-align:right; color:white; font-size:11px; font-weight:bold;">{ev['val']}</div>
            </div>''' for ev in events])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        # reddit_pulse = [tus_datos_de_reddit]
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; overflow-y:auto; color:#444; text-align:center;"><br>Monitoring WallStreetBets...</div></div>', unsafe_allow_html=True)

    # ================= FILA 2 =================
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        val = 72 # Podrías conectar esto a un scraper de CNN Fear & Greed
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:3.5rem; font-weight:bold; color:#00ffad;">{val}</div><div style="color:white; font-size:0.8rem; letter-spacing:2px; font-weight:bold;">GREED</div>
            <div style="width:80%; background:#0c0e12; height:10px; border-radius:5px; margin-top:20px; border:1px solid #1a1e26;"><div style="width:{val}%; background:#00ffad; height:100%; border-radius:5px;"></div></div>
            </div></div>''', unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.2), ("FINL", -0.4), ("HLTH", +0.1), ("ENER", +2.1), ("CONS", -0.8), ("UTIL", -0.2)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with col3:
        crypto_data = get_real_crypto()
        crypto_html = "".join([f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">USD</div></div>
            <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if c >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{c:+.2f}%</div></div>
            </div>''' for s, p, c in crypto_data])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse (Live)</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 3 =================
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    
    with f3c1:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; color:#444; text-align:center;"><br>Next Earnings Reports...</div></div>', unsafe_allow_html=True)

    with f3c2:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; color:#444; text-align:center;"><br>C-Suite Activity...</div></div>', unsafe_allow_html=True)

    with f3c3:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Live News Terminal</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; color:#444; text-align:center;"><br>Awaiting headlines...</div></div>', unsafe_allow_html=True)
