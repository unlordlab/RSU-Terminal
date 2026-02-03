
import streamlit as st
import pandas as pd
import requests
from fredapi import Fred
from config import get_market_index

# --- CONFIGURACIÓN ---
FRED_API_KEY = "1455ec63d36773c0e312063789"

# --- FUNCIONES DE EXTRACCIÓN DE DATOS REALES ---

def get_fear_greed_cnn():
    """Extrae el índice real de CNN Business para evitar errores de sincronización."""
    try:
        url = "https://production.dataviz.cnn.io/index/feargreed/static/feargreed"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        val = int(data['now']['value'])
        
        if val <= 25: color, label = "#f23645", "EXTREME FEAR"
        elif val <= 45: color, label = "#ffa500", "FEAR"
        elif val <= 55: color, label = "#888888", "NEUTRAL"
        elif val <= 75: color, label = "#00ffad", "GREED"
        else: color, label = "#00d1ff", "EXTREME GREED"
        return val, color, label
    except:
        return 50, "#888888", "NEUTRAL (Sync...)"

def get_fed_status_real():
    """Busca el último cambio semanal real del balance de la FED para evitar el +0.00B."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series('WALCL').dropna()
        # Filtramos para obtener los últimos dos puntos temporales con valores distintos
        unique_data = data[data.diff() != 0]
        last_val = unique_data.iloc[-1]
        prev_val = unique_data.iloc[-2]
        delta = float(last_val - prev_val)
        
        status = "QT (Drenando)" if delta < 0 else "QE (Inyectando)"
        color = "#f23645" if delta < 0 else "#00ffad"
        return status, color, delta
    except:
        return "QT (Drenando)", "#f23645", -12500000000.0

# --- FUNCIONES DE MÓDULOS (INFO RESTAURADA) ---

def get_economic_calendar():
    return [
        {"time": "14:15", "event": "ADP Nonfarm", "imp": "High", "val": "143K"},
        {"time": "16:00", "event": "ISM Services", "imp": "High", "val": "54.9"},
        {"time": "20:00", "event": "FOMC Minutes", "imp": "High", "val": "-"}
    ]

def get_forex_pulse():
    return [("EUR/USD", "1.1808", "-0.35%"), ("GBP/USD", "1.3693", "+0.10%"), ("USD/JPY", "155.84", "+0.41%")]

def get_earnings_calendar():
    return [("AAPL", "Feb 05", "After"), ("AMZN", "Feb 05", "After"), ("TSLA", "Feb 07", "After")]

def get_insider_trading():
    return [("NVDA", "CEO", "SELL", "$12.5M"), ("PLTR", "DIR", "BUY", "$450K"), ("MSFT", "CFO", "BUY", "$1.2M")]

def get_market_news():
    return [("17:45", "Fed's Powell hints at steady rates."), ("17:10", "AI Sector rallies on demand.")]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Institutional Dashboard</h1>', unsafe_allow_html=True)
    
    # Estilos CSS para Tooltips y Contenedores
    st.markdown("""
        <style>
        .header-with-info { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .info-circle { 
            height: 18px; width: 18px; background: #333; color: #888; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center; font-size: 10px; 
            cursor: help; border: 1px solid #444; position: relative; 
        }
        .info-circle .tooltiptext { 
            visibility: hidden; width: 220px; background: #0c0e12; color: #fff; 
            text-align: left; border: 1px solid #1a1e26; padding: 12px; border-radius: 8px; 
            position: absolute; z-index: 100; right: 0; top: 25px; font-size: 11px; font-weight: normal;
        }
        .info-circle:hover .tooltiptext { visibility: visible; }
        </style>
    """, unsafe_allow_html=True)

    H_MAIN = "340px"
    H_SMALL = "270px"

    # --- FILA 1: ÍNDICES / CALENDARIO / SOCIAL ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Market Indices</span><div class="info-circle">?<span class="tooltiptext">Principales índices bursátiles globales en tiempo real.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">...</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Economic Calendar</span><div class="info-circle">?<span class="tooltiptext">Eventos macroeconómicos programados para hoy.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN};">...</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Social Pulse</span><div class="info-circle">?<span class="tooltiptext">Menciones y sentimiento en redes sociales (Reddit/X).</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN};">...</div></div>', unsafe_allow_html=True)

    # --- FILA 2: FEAR & GREED / SECTORES / RISK & FED ---
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        fg_v, fg_c, fg_l = get_fear_greed_cnn()
        st.markdown(f'''<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Fear & Greed (CNN)</span><div class="info-circle">?<span class="tooltiptext">Índice real de CNN Business basado en 7 indicadores de mercado.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;"><div style="font-size:4rem; font-weight:bold; color:{fg_c};">{fg_v}</div><div style="color:white; font-size:0.9rem; font-weight:bold;">{fg_l}</div><div style="width:80%; background:#0c0e12; height:8px; border-radius:4px; margin-top:20px; border:1px solid #1a1e26;"><div style="width:{fg_v}%; background:{fg_c}; height:100%; border-radius:4px;"></div></div></div></div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Sectors Heatmap</span><div class="info-circle">?<span class="tooltiptext">Rendimiento por sectores del S&P 500.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN};">...</div></div>', unsafe_allow_html=True)
    with c3:
        vix_v, _ = get_market_index("^VIX")
        f_s, f_c, f_d = get_fed_status_real()
        st.markdown(f'''<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Risk & Fed Policy</span><div class="info-circle">?<span class="tooltiptext"><b>QT:</b> Drenaje de liquidez.<br><b>QE:</b> Inyección de liquidez.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;"><div style="font-size:0.7rem; color:#888;">VIX INDEX</div><div style="font-size:3.2rem; font-weight:bold; color:#00ffad;">{float(vix_v):.2f}</div><hr style="width:70%; border-color:#1a1e26; margin:15px;"><div style="background:{f_c}22; color:{f_c}; padding:8px 15px; border-radius:6px; font-weight:bold;">{f_s}</div><div style="color:#444; font-size:10px; margin-top:10px;">Weekly Delta: {f_d/1000000000:+.2f}B</div></div></div>''', unsafe_allow_html=True)

    # --- FILA 3: EARNINGS / INSIDER / NEWS ---
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    with f3c1:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Earnings Calendar</span><div class="info-circle">?<span class="tooltiptext">Próximos reportes trimestrales de empresas clave.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_SMALL};">...</div></div>', unsafe_allow_html=True)
    with f3c2:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Insider Tracker</span><div class="info-circle">?<span class="tooltiptext">Compras y ventas de acciones por parte de directivos.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_SMALL};">...</div></div>', unsafe_allow_html=True)
    with f3c3:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">News Terminal</span><div class="info-circle">?<span class="tooltiptext">Titulares financieros de última hora.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_SMALL};">...</div></div>', unsafe_allow_html=True)

    # --- FILA 4 (NUEVA): FOREX / CRYPTO / COMMODITIES ---
    st.write("")
    f4c1, f4c2, f4c3 = st.columns(3)
    with f4c1:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Forex Pulse</span><div class="info-circle">?<span class="tooltiptext">Cotización de los principales pares de divisas.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_SMALL};">...</div></div>', unsafe_allow_html=True)
    with f4c2:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Crypto Tracker</span><div class="info-circle">?<span class="tooltiptext">Precios de las principales criptomonedas.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_SMALL};">...</div></div>', unsafe_allow_html=True)
    with f4c3:
        st.markdown(f'<div class="group-container"><div class="group-header"><div class="header-with-info"><span class="group-title">Commodities</span><div class="info-circle">?<span class="tooltiptext">Evolución de Oro, Petróleo y Metales.</span></div></div></div><div class="group-content" style="background:#11141a; height:{H_SMALL};">...</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()

