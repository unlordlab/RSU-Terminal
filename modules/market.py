import streamlit as st
from datetime import datetime
import yfinance as yf
import pandas as pd
from fredapi import Fred
from config import get_market_index

# --- CONFIGURACIÓN DE APIS ---
FRED_API_KEY = "1455ec63d36773c0e47770e312063789" 

# --- FUNCIONES DE OBTENCIÓN DE DATOS (RESTAURADAS) ---

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

def get_fed_status_real():
    """Obtiene datos reales de liquidez de la FED (WALCL)."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series('WALCL')
        delta = float(data.iloc[-1] - data.iloc[-2])
        status = "QE (Inyectando)" if delta > 0 else "QT (Drenando)"
        color = "#00ffad" if delta > 0 else "#f23645"
        return status, color, delta
    except:
        return "Cargando...", "#888", 0.0

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Alturas originales de tu archivo
    H_MAIN = "340px" 
    H_BOTTOM = "270px"

    # ================= FILA 1 (RESTAURADA) =================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:12px 15px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <div><div style="font-weight:bold; color:white; font-size:13px;">{n}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:13px;">{float(get_market_index(t)[0]):,.2f}</div><div style="color:{"#00ffad" if float(get_market_index(t)[1]) >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{float(get_market_index(t)[1]):+.2f}%</div></div>
            </div>''' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events = get_economic_calendar()
        events_html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;"><div style="color:#888; font-size:10px; width:45px; font-family:monospace;">{ev["time"]}</div><div style="flex-grow:1; margin-left:10px;"><div style="color:white; font-size:11px; font-weight:500;">{ev["event"]}</div><div style="color:{"#f23645" if ev["imp"]=="High" else "#ffa500"}; font-size:8px; font-weight:bold; text-transform:uppercase;">{ev["imp"]} IMPACT</div></div><div style="text-align:right;"><div style="color:white; font-size:11px; font-weight:bold;">{ev["val"]}</div><div style="color:#444; font-size:9px;">P: {ev["prev"]}</div></div></div>' for ev in events])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "NVDA", "PLTR", "TSLA"]
        reddit_html = "".join([f'<div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:6px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><span style="color:#333; font-weight:bold; font-size:10px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:12px;">{tkr}</span><span style="color:#f23645; font-size:8px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 5px; border-radius:4px;">HOT 🔥</span></div>' for i, tkr in enumerate(tickers)])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Social Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 2 (RESTAURADA) =================
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        val = 65
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;"><div style="font-size:3.5rem; font-weight:bold; color:#00ffad;">{val}</div><div style="color:white; font-size:0.8rem; letter-spacing:2px; font-weight:bold;">GREED</div><div style="width:80%; background:#0c0e12; height:10px; border-radius:5px; margin-top:20px; border:1px solid #1a1e26; position:relative;"><div style="width:{val}%; background:#00ffad; height:100%; border-radius:5px; box-shadow:0 0 15px #00ffad66;"></div></div></div></div>''', unsafe_allow_html=True)

    with c2:
        sectors = [("TECH", +1.24), ("FINL", -0.45), ("HLTH", +0.12), ("ENER", +2.10), ("CONS", -0.80), ("UTIL", -0.25)]
        sectors_html = "".join([f'<div style="background:{"#00ffad11" if p>=0 else "#f2364511"}; border:1px solid {"#00ffad44" if p>=0 else "#f2364544"}; padding:10px; border-radius:6px; text-align:center;"><div style="color:white; font-size:9px; font-weight:bold;">{n}</div><div style="color:{"#00ffad" if p>=0 else "#f23645"}; font-size:11px; font-weight:bold;">{p:+.2f}%</div></div>' for n, p in sectors])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Sectors Heatmap</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px; display:grid; grid-template-columns:repeat(3,1fr); gap:10px;">{sectors_html}</div></div>', unsafe_allow_html=True)

    with c3:
        cryptos = get_crypto_prices()
        crypto_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{s}</div><div style="color:#555; font-size:9px;">TOKEN</div></div><div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${p}</div><div style="color:{"#00ffad" if "+" in c else "#f23645"}; font-size:11px; font-weight:bold;">{c}</div></div></div>' for s, p, c in cryptos])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Crypto Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{crypto_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 4 (VIX + FED CON TOOLTIP MEJORADO) =================
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)
    
    with f4c1:
        v_val, v_change = get_market_index("^VIX")
        fed_status, fed_color, fed_delta = get_fed_status_real()
        
        # Tooltip integrado en el HEADER del módulo
        tooltip_css = """
        <style>
            .header-with-info { display: flex; justify-content: space-between; align-items: center; width: 100%; }
            .info-circle { height: 16px; width: 16px; background: #333; color: #888; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; cursor: help; border: 1px solid #444; position: relative; }
            .info-circle .tooltiptext { visibility: hidden; width: 200px; background: #0c0e12; color: #fff; text-align: left; border: 1px solid #1a1e26; padding: 10px; border-radius: 8px; position: absolute; z-index: 100; right: 0; top: 20px; font-size: 10px; font-weight: normal; }
            .info-circle:hover .tooltiptext { visibility: visible; }
        </style>
        """
        
        fed_content = f'''
            <div style="background:#11141a; height:{H_MAIN}; border-radius: 0 0 10px 10px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid #1a1e26; border-top:none;">
                <div style="font-size:0.7rem; color:#888; letter-spacing:2px; margin-bottom:5px;">VIX INDEX</div>
                <div style="font-size:3.2rem; font-weight:bold; color:{"#f23645" if float(v_val) > 20 else "#00ffad"};">{float(v_val):.2f}</div>
                <div style="width:80%; height:1px; background:#1a1e26; margin:20px 0;"></div>
                <div style="font-size:0.7rem; color:#888; margin-bottom:10px;">LIQUIDEZ DE LA FED</div>
                <div style="background:{fed_color}22; color:{fed_color}; padding:8px 15px; border-radius:6px; font-weight:bold; font-size:0.9rem; border:1px solid {fed_color}44;">{fed_status}</div>
                <div style="color:#444; font-size:10px; margin-top:10px; font-weight:bold;">Weekly Delta: {fed_delta/1000000000:+.2f}B</div>
            </div>
        '''
        
        st.markdown(tooltip_css + f'''
            <div class="group-container">
                <div class="group-header">
                    <div class="header-with-info">
                        <span class="group-title">Risk & Fed Policy</span>
                        <div class="info-circle">?
                            <span class="tooltiptext"><b>POLÍTICA DE LIQUIDEZ:</b><br>• <b>QE:</b> Inyecta dinero (alcista).<br>• <b>QT:</b> Retira dinero (bajista).<br>Delta medido en Billones (B).</span>
                        </div>
                    </div>
                </div>
                {fed_content}
            </div>
        ''', unsafe_allow_html=True)

    with f4c2:
        forex_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div><div style="color:#555; font-size:9px;">FOREX</div></div><div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">{float(get_market_index(t)[0]):.4f}</div><div style="color:{"#00ffad" if float(get_market_index(t)[1]) >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{float(get_market_index(t)[1]):+.2f}%</div></div></div>' for t, n in [("EURUSD=X", "EUR/USD"), ("GBPUSD=X", "GBP/USD"), ("USDJPY=X", "USD/JPY")]])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Forex Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{forex_html}</div></div>', unsafe_allow_html=True)

    with f4c3:
        comm_html = "".join([f'<div style="background:#0c0e12; padding:12px; border-radius:10px; margin-bottom:10px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:white; font-weight:bold; font-size:13px;">{n}</div><div style="color:#555; font-size:9px;">COMMODITY</div></div><div style="text-align:right;"><div style="color:white; font-size:13px; font-weight:bold;">${float(get_market_index(t)[0]):,.2f}</div><div style="color:{"#00ffad" if float(get_market_index(t)[1]) >= 0 else "#f23645"}; font-size:11px; font-weight:bold;">{float(get_market_index(t)[1]):+.2f}%</div></div></div>' for t, n in [("GC=F", "GOLD"), ("CL=F", "OIL"), ("SI=F", "SILVER")]])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Commodities Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">{comm_html}</div></div>', unsafe_allow_html=True)

    # ================= FILA 3 (ORIGINAL ABAJO) =================
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    
    with f3c1:
        earn_html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</div><div style="color:#444; font-size:9px; font-weight:bold;">{d}</div></div><div style="text-align:right;"><div style="color:#888; font-size:9px;">{tm}</div><span style="color:{"#f23645" if i=="High" else "#888"}; font-size:8px; font-weight:bold;">● {i}</span></div></div>' for t, d, tm, i in get_earnings_calendar()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{earn_html}</div></div>', unsafe_allow_html=True)

    with f3c2:
        insider_html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="color:white; font-weight:bold; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div><div style="text-align:right;"><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-weight:bold; font-size:10px;">{ty}</div><div style="color:#888; font-size:9px;">{a}</div></div></div>' for t, p, ty, a in get_insider_trading()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px; overflow-y:auto;">{insider_html}</div></div>', unsafe_allow_html=True)

    with f3c3:
        news_html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26;"><div style="display:flex; justify-content:space-between;"><span style="color:#00ffad; font-size:9px; font-weight:bold;">NEWS</span><span style="color:#444; font-size:9px;">{time}</span></div><div style="color:white; font-size:11px; margin-top:4px; line-height:1.3;">{text}</div></div>' for time, text in get_market_news()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Live News Terminal</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; overflow-y:auto;">{news_html}</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
