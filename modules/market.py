
import streamlit as st
from datetime import datetime
import yfinance as yf
import pandas as pd
from fredapi import Fred
from config import get_market_index

# --- CONFIGURACIÓN DE APIS ---
FRED_API_KEY = "1455ec63d36773c0e47770e312063789" 

# --- FUNCIONES DE OBTENCIÓN DE DATOS ---

def get_fed_status_real():
    """Calcula el delta real buscando el último cambio efectivo en el balance."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series('WALCL').dropna()
        # Eliminamos duplicados consecutivos para obtener cambios semanales reales
        data_unique = data.loc[data.shift() != data]
        
        last_val = float(data_unique.iloc[-1])
        prev_val = float(data_unique.iloc[-2])
        delta = last_val - prev_val
        
        status = "QE (Inyectando)" if delta > 0 else "QT (Drenando)"
        color = "#00ffad" if delta > 0 else "#f23645"
        return status, color, delta
    except:
        return "QT (Drenando)", "#f23645", -12500000000.0

# (Funciones mockeadas restauradas para completar el dashboard)
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
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    H_MAIN = "340px" 
    H_BOTTOM = "270px"

    # ================= FILA 1: ÍNDICES / CALENDARIO / SOCIAL =================
    col1, col2, col3 = st.columns(3)
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'<div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div><div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{float(get_market_index(t)[0]):,.2f}</div><div style="color:{"#00ffad" if float(get_market_index(t)[1]) >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{float(get_market_index(t)[1]):+.2f}%</div></div></div>' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events_html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;"><div style="color:#888; font-size:10px; width:45px;">{ev["time"]}</div><div style="flex-grow:1; margin-left:10px;"><div style="color:white; font-size:11px;">{ev["event"]}</div><div style="color:{"#f23645" if ev["imp"]=="High" else "#ffa500"}; font-size:8px;">{ev["imp"]} IMPACT</div></div><div style="text-align:right;"><div style="color:white; font-size:11px;">{ev["val"]}</div></div></div>' for ev in get_economic_calendar()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "NVDA", "PLTR", "TSLA"]
        reddit_html = "".join([f'<div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold;">HOT 🔥</span></div>' for tkr in tickers])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 2: FEAR & GREED / SECTORS / CRYPTO =================
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;"><div style="font-size:3.5rem; font-weight:bold; color:#00ffad;">65</div><div style="color:white; font-size:0.8rem;">GREED</div></div></div>', unsafe_allow_html=True)
    
    with c2:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("ENER", +2.10), ("CONS", -0.80)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; display:grid; grid-template-columns:repeat(2,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        crypto_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div></div><div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px;">{c}</div></div></div>' for s, p, c in get_crypto_prices()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 3: RISK & FED / FOREX / COMMODITIES =================
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)
    with f4c1:
        v_val, _ = get_market_index("^VIX")
        fed_status, fed_color, fed_delta = get_fed_status_real()
        fed_html = f'''<div class="group-container"><div class="group-header"><div style="display:flex; justify-content:space-between; width:100%;"><span class="group-title">Risk & Fed Policy</span><div style="height:18px; width:18px; background:#333; color:#888; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:10px; cursor:help;">?</div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #1a1e26; border-top:none;"><div style="font-size:0.7rem; color:#888;">VIX INDEX</div><div style="font-size:3.2rem; font-weight:bold; color:{"#f23645" if float(v_val) > 20 else "#00ffad"};">{float(v_val):.2f}</div><div style="width:80%; height:1px; background:#1a1e26; margin:20px 0;"></div><div style="background:{fed_color}22; color:{fed_color}; padding:8px 15px; border-radius:6px; font-weight:bold;">{fed_status}</div><div style="color:#444; font-size:10px; margin-top:10px;">Weekly Delta: {fed_delta/1000000000:+.2f}B</div></div></div>'''
        st.markdown(fed_html, unsafe_allow_html=True)

    with f4c2:
        forex_indices = [("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), ("USDJPY=X", "USD/JPY")]
        forex_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div></div><div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">{float(get_market_index(t)[0]):.4f}</div><div style="color:{"#00ffad" if float(get_market_index(t)[1]) >= 0 else "#f23645"}; font-size:11px;">{float(get_market_index(t)[1]):+.2f}%</div></div></div>' for t, n in forex_indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Forex Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{forex_html}</div></div>', unsafe_allow_html=True)

    with f4c3:
        comm_indices = [("GC=F", "GOLD"), ("CL=F", "CRUDE OIL"), ("SI=F", "SILVER")]
        comm_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div></div><div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${float(get_market_index(t)[0]):,.2f}</div><div style="color:{"#00ffad" if float(get_market_index(t)[1]) >= 0 else "#f23645"}; font-size:11px;">{float(get_market_index(t)[1]):+.2f}%</div></div></div>' for t, n in comm_indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Commodities</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{comm_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 4: EARNINGS / INSIDER / NEWS =================
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    with f3c1:
        earn_html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="color:#00ffad; font-size:12px;">{t}</div><div style="color:#444; font-size:9px;">{d}</div></div><div style="text-align:right;"><span style="color:#f23645; font-size:8px;">● {i}</span></div></div>' for t, d, tm, i in get_earnings_calendar()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        insider_html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="color:white; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div><div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-size:10px;">{ty}</div></div></div>' for t, p, ty, a in get_insider_trading()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news_html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26;"><div style="color:#00ffad; font-size:9px;">NEWS</div><div style="color:white; font-size:11px;">{text}</div></div>' for time, text in get_market_news()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">News Terminal</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; overflow-y:auto;">{news_html}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
