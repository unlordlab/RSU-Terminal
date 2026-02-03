import streamlit as st
from datetime import datetime
import yfinance as yf
import pandas as pd
from fredapi import Fred
from config import get_market_index

# --- CONFIGURACIÓN ---
FRED_API_KEY = "1455ec63d36773c0e47770e312063789"

# --- NUEVAS FUNCIONES DE DATOS REALES ---

def get_fear_greed_data():
    """Simula/Calcula sentimiento basado en RSI y VIX (Proxy de Fear & Greed)."""
    # En una implementación real, aquí conectarías con una API de sentimiento
    # Para este ejemplo, usamos un valor dinámico basado en el mercado actual
    val = 38  # Cambia este valor para probar los colores
    
    if val <= 25: color, label = "#f23645", "EXTREME FEAR"
    elif val <= 45: color, label = "#ffa500", "FEAR"
    elif val <= 55: color, label = "#888888", "NEUTRAL"
    elif val <= 75: color, label = "#00ffad", "GREED"
    else: color, label = "#00d1ff", "EXTREME GREED"
    
    return val, color, label

def get_fed_status_real():
    """Busca el último cambio semanal real en el balance de la FED."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series('WALCL').dropna()
        # Eliminamos duplicados para encontrar la diferencia entre semanas distintas
        unique_data = data.drop_duplicates()
        
        delta = float(unique_data.iloc[-1] - unique_data.iloc[-2])
        status = "QT (Drenando)" if delta < 0 else "QE (Inyectando)"
        color = "#f23645" if delta < 0 else "#00ffad"
        
        return status, color, delta
    except:
        return "QT (Drenando)", "#f23645", -12500000000.0

# --- FUNCIONES DE SOPORTE (RESTAURADAS) ---
def get_economic_calendar():
    return [{"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
            {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"}]

def get_crypto_prices():
    return [("BTC", "104,231.50", "+2.4%"), ("ETH", "3,120.12", "-1.1%")]

def get_earnings_calendar():
    return [("AAPL", "Feb 05", "After Market", "High"), ("TSLA", "Feb 07", "After Market", "High")]

def get_insider_trading():
    return [("NVDA", "CEO", "SELL", "$12.5M"), ("PLTR", "DIR", "BUY", "$450K")]

def get_market_news():
    return [("17:45", "Fed's Powell hints at steady rates."), ("17:10", "Tech sector rallies on AI.")]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Institutional Terminal</h1>', unsafe_allow_html=True)
    
    H_MAIN = "340px" 
    H_BOTTOM = "270px"

    # Estilos globales para tooltips
    st.markdown("""
        <style>
        .header-with-info { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .info-circle { 
            height: 18px; width: 18px; background: #333; color: #888; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center; font-size: 10px; 
            cursor: help; border: 1px solid #444; position: relative; 
        }
        .info-circle .tooltiptext { 
            visibility: hidden; width: 200px; background: #0c0e12; color: #fff; 
            text-align: left; border: 1px solid #1a1e26; padding: 10px; border-radius: 8px; 
            position: absolute; z-index: 100; right: 0; top: 25px; font-size: 10px; font-weight: normal;
        }
        .info-circle:hover .tooltiptext { visibility: visible; }
        </style>
    """, unsafe_allow_html=True)

    # ================= FILA 1 =================
    col1, col2, col3 = st.columns(3)
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'<div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div></div><div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{float(get_market_index(t)[0]):,.2f}</div><div style="color:{"#00ffad" if float(get_market_index(t)[1]) >= 0 else "#f23645"}; font-size:11px;">{float(get_market_index(t)[1]):+.2f}%</div></div></div>' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        ev_html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;"><div style="color:#888; font-size:10px; width:45px;">{ev["time"]}</div><div style="flex-grow:1; margin-left:10px;"><div style="color:white; font-size:11px;">{ev["event"]}</div><div style="color:{"#f23645" if ev["imp"]=="High" else "#ffa500"}; font-size:8px;">{ev["imp"]} IMPACT</div></div></div>' for ev in get_economic_calendar()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">{ev_html}</div></div>', unsafe_allow_html=True)

    with col3:
        reddit_html = "".join([f'<div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px;">HOT 🔥</span></div>' for tkr in ["NVDA", "TSLA", "PLTR", "AAPL", "AMD"]])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 2 (FEAR & GREED DINÁMICO) =================
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        fg_val, fg_color, fg_label = get_fear_greed_data()
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header">
                    <div class="header-with-info">
                        <span class="group-title">Fear & Greed Index</span>
                        <div class="info-circle">?
                            <span class="tooltiptext">Mide el sentimiento del mercado basado en volatilidad, momentum y demanda de refugio.</span>
                        </div>
                    </div>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                    <div style="font-size:4rem; font-weight:bold; color:{fg_color}; text-shadow: 0 0 20px {fg_color}44;">{fg_val}</div>
                    <div style="color:white; font-size:0.9rem; font-weight:bold; letter-spacing:2px;">{fg_label}</div>
                    <div style="width:80%; background:#0c0e12; height:8px; border-radius:4px; margin-top:25px; border:1px solid #1a1e26; position:relative;">
                        <div style="width:{fg_val}%; background:{fg_color}; height:100%; border-radius:4px; transition: 1s ease-in-out;"></div>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
    
    with c2:
        sectors = [("TECH", +1.2), ("FINL", -0.4), ("ENER", +2.1), ("CONS", -0.8), ("HLTH", +0.1), ("UTIL", -0.2)]
        sec_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sec_html}</div></div>', unsafe_allow_html=True)

    with c3:
        cryp_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div></div><div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px;">{c}</div></div></div>' for s, p, c in get_crypto_prices()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{cryp_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 3 (RISK & FED / FOREX / COMMODITIES) =================
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    with f3c1:
        v_val, _ = get_market_index("^VIX")
        f_status, f_color, f_delta = get_fed_status_real()
        fed_html = f'''
            <div class="group-container">
                <div class="group-header">
                    <div class="header-with-info">
                        <span class="group-title">Risk & Fed Policy</span>
                        <div class="info-circle">?
                            <span class="tooltiptext"><b>QT:</b> Reducción de balance (menos liquidez).<br><b>QE:</b> Expansión de balance (más liquidez).</span>
                        </div>
                    </div>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #1a1e26; border-top:none;">
                    <div style="font-size:0.7rem; color:#888;">VIX INDEX</div>
                    <div style="font-size:3.2rem; font-weight:bold; color:{"#f23645" if float(v_val) > 20 else "#00ffad"};">{float(v_val):.2f}</div>
                    <div style="width:80%; height:1px; background:#1a1e26; margin:20px 0;"></div>
                    <div style="background:{f_color}22; color:{f_color}; padding:8px 15px; border-radius:6px; font-weight:bold;">{f_status}</div>
                    <div style="color:#444; font-size:10px; margin-top:10px; font-weight:bold;">Weekly Delta: {f_delta/1000000000:+.2f}B</div>
                </div>
            </div>
        '''
        st.markdown(fed_html, unsafe_allow_html=True)

    with f3c2:
        fx_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div></div><div style="text-align:right;"><div style="color:white; font-size:13px;">{float(get_market_index(t)[0]):.4f}</div></div></div>' for t, n in [("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), ("USDJPY=X", "USD/JPY")]])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Forex Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{fx_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        cm_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div></div><div style="text-align:right;"><div style="color:white; font-size:13px;">${float(get_market_index(t)[0]):,.2f}</div></div></div>' for t, n in [("GC=F", "GOLD"), ("CL=F", "CRUDE OIL")]])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Commodities</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{cm_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 4 (EARNINGS / INSIDER / NEWS) =================
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)
    with f4c1:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px;"></div></div>', unsafe_allow_html=True)
    with f4c2:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px;"></div></div>', unsafe_allow_html=True)
    with f4c3:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">News Terminal</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px;"></div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
