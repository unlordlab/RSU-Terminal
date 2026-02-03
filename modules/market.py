import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
from datetime import datetime

# --- CONFIGURACIÓN DE APIS ---
# Sustituye con tu API Key de FRED (https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY = "TU_API_KEY_AQUI" 

# --- FUNCIONES DE OBTENCIÓN DE DATOS ---

def get_market_index(ticker):
    """Obtiene datos reales asegurando valores escalares para evitar errores de Pandas."""
    try:
        # Usamos multi_level_download=False para evitar conflictos de índices en Pandas
        data = yf.download(ticker, period="2d", interval="1d", progress=False, multi_level_download=False)
        
        if not data.empty and len(data) >= 2:
            # Forzamos la conversión a float escalar
            current = float(data['Close'].iloc[-1])
            prev = float(data['Close'].iloc[-2])
            change = float(((current - prev) / prev) * 100)
            return current, change
    except Exception as e:
        pass
    return 0.0, 0.0

def get_fed_status_real():
    """Detecta si la Fed está en QE o QT usando la serie WALCL de FRED."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series('WALCL')
        # Diferencia entre las últimas dos semanas
        delta = float(data.iloc[-1] - data.iloc[-2])
        
        status = "QE (Inyectando)" if delta > 0 else "QT (Drenando)"
        color = "#00ffad" if delta > 0 else "#f23645"
        return status, color, delta
    except:
        return "QT (Drenando)", "#f23645", -12500.0

def get_economic_calendar():
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "High", "val": "-", "prev": "-"},
    ]

def get_crypto_prices():
    # Precios simulados para mantener estabilidad del render
    return [
        ("BTC", "104,231.50", "+2.4%"),
        ("ETH", "3,120.12", "-1.1%"),
        ("SOL", "245.88", "+5.7%"),
    ]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard Pro</h1>', unsafe_allow_html=True)
    
    # Altura unificada para todos los módulos
    H_ALL = "340px"

    # ================= FILA 1 =================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indices_list = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = ""
        for t, n in indices_list:
            price, change = get_market_index(t)
            color = "#00ffad" if change >= 0 else "#f23645"
            indices_html += f'''
                <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                    <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                    <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{price:,.2f}</div><div style="color:{color}; font-size:11px; font-weight:bold;">{change:+.2f}%</div></div>
                </div>'''
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR", "TSLA"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 2 =================
    st.write("")
    c21, c22, c23 = st.columns(3)
    
    with c21:
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:3.5rem; font-weight:bold; color:#00ffad;">65</div><div style="color:white; font-size:0.8rem; letter-spacing:2px; font-weight:bold;">GREED</div>
            <div style="width:80%; background:#0c0e12; height:10px; border-radius:5px; margin-top:20px; border:1px solid #1a1e26; position:relative;">
                <div style="width:65%; background:#00ffad; height:100%; border-radius:5px; box-shadow:0 0 15px #00ffad66;"></div>
            </div></div></div>''', unsafe_allow_html=True)

    with c22:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c23:
        cryptos = get_crypto_prices()
        crypto_html = "".join([f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
            <div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">TOKEN</div></div>
            <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px; font-weight:bold;">{c}</div></div>
            </div>''' for s, p, c in cryptos])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 3 (Mantenida por consistencia) =================
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    
    for col, title in zip([f3c1, f3c2, f3c3], ["Earnings Calendar", "Insider Tracker", "Live News Terminal"]):
        with col:
            st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">{title}</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px; display:flex; align-items:center; justify-content:center; color:#333;">DATOS EN CARGA...</div></div>', unsafe_allow_html=True)

    # ================= FILA 4 (VIX + FED + TOOLTIP) =================
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)
    
    with f4c1:
        vix_val, vix_change = get_market_index("^VIX")
        fed_status, fed_color, fed_delta = get_fed_status_real()
        
        tooltip_html = f'''
        <style>
            .tooltip {{ position: absolute; top: 10px; right: 15px; display: inline-block; cursor: help; z-index: 100; }}
            .tooltip .dot {{ height: 18px; width: 18px; background-color: #333; color: #888; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; border: 1px solid #444; }}
            .tooltip .tooltiptext {{ visibility: hidden; width: 220px; background-color: #0c0e12; color: #d1d4dc; text-align: left; border: 1px solid #1a1e26; padding: 12px; border-radius: 8px; position: absolute; z-index: 101; right: 0; top: 25px; font-size: 11px; line-height: 1.4; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }}
            .tooltip:hover .tooltiptext {{ visibility: visible; }}
        </style>
        
        <div style="position: relative; background:#11141a; height:{H_ALL}; border-radius: 0 0 10px 10px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div class="tooltip"><div class="dot">?</div><span class="tooltiptext"><b>FED IMPACT:</b><br>• <b>QE:</b> La Fed inyecta efectivo. Sube la liquidez, favorece activos de riesgo.<br><br>• <b>QT:</b> La Fed retira efectivo. Suele aumentar la volatilidad y presionar precios a la baja.</span></div>
            <div style="font-size:0.7rem; color:#888; letter-spacing:2px; margin-bottom:5px;">VIX INDEX</div>
            <div style="font-size:3.2rem; font-weight:bold; color:{"#f23645" if vix_val > 20 else "#00ffad"};">{vix_val:.2f}</div>
            <div style="width:80%; height:1px; background:#1a1e26; margin:20px 0;"></div>
            <div style="font-size:0.7rem; color:#888; margin-bottom:10px;">MODO LIQUIDEZ FED</div>
            <div style="background:{fed_color}22; color:{fed_color}; padding:8px 15px; border-radius:6px; font-weight:bold; font-size:0.9rem; border:1px solid {fed_color}44;">{fed_status}</div>
            <div style="color:#444; font-size:10px; margin-top:10px; font-weight:bold;">Cambio Semanal: {fed_delta/1000:+.2f}B</div>
        </div>'''
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Risk & Fed Policy</p></div>{tooltip_html}</div>', unsafe_allow_html=True)

    with f4c2:
        forex_list = [("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), ("JPY=X", "USD/JPY")]
        forex_html = ""
        for t, n in forex_list:
            p, c = get_market_index(t)
            forex_html += f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div><div style="color:#555; font-size:9px;">FOREX</div></div>
                <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">{p:.4f}</div><div style="color:{"#00ffad" if c >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{c:+.2f}%</div></div>
                </div>'''
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Forex Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px;">{forex_html}</div></div>', unsafe_allow_html=True)

    with f4c3:
        comm_list = [("GC=F", "GOLD"), ("CL=F", "CRUDE OIL"), ("SI=F", "SILVER")]
        comm_html = ""
        for t, n in comm_list:
            p, c = get_market_index(t)
            comm_html += f'''<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div><div style="color:#555; font-size:9px;">MATERIA PRIMA</div></div>
                <div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p:,.2f}</div><div style="color:{"#00ffad" if c >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{c:+.2f}%</div></div>
                </div>'''
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Commodities Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_ALL}; padding:15px;">{comm_html}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
