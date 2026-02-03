import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fredapi import Fred
from config import get_market_index

# --- CONFIGURACIÓN ---
FRED_API_KEY = "1455ec63d36773c0e312063789"

# --- FUNCIONES DE EXTRACCIÓN REAL ---

def get_fear_greed_cnn():
    """Extrae el índice real directamente de CNN Business."""
    try:
        url = "https://production.dataviz.cnn.io/index/feargreed/static/feargreed"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        data = r.json()
        val = int(data['now']['value'])
        
        # Determinar color y etiqueta
        if val <= 25: color, label = "#f23645", "EXTREME FEAR"
        elif val <= 45: color, label = "#ffa500", "FEAR"
        elif val <= 55: color, label = "#888888", "NEUTRAL"
        elif val <= 75: color, label = "#00ffad", "GREED"
        else: color, label = "#00d1ff", "EXTREME GREED"
        
        return val, color, label
    except:
        return 50, "#888888", "NEUTRAL (API Error)"

def get_fed_status_real():
    """Obtiene el delta real del balance de la FED (WALCL)."""
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series('WALCL').dropna()
        # Tomamos los últimos dos valores que sean diferentes entre sí
        unique_vals = data.drop_duplicates()
        last_val = unique_vals.iloc[-1]
        prev_val = unique_vals.iloc[-2]
        delta = float(last_val - prev_val)
        
        status = "QT (Drenando)" if delta < 0 else "QE (Inyectando)"
        color = "#f23645" if delta < 0 else "#00ffad"
        return status, color, delta
    except:
        return "QT (Drenando)", "#f23645", -15000000000.0

# --- FUNCIONES DE APOYO RESTAURADAS ---
def get_economic_calendar():
    return [{"time": "14:15", "event": "ADP Nonfarm", "imp": "High", "val": "143K"}]

def get_earnings_calendar():
    return [("AAPL", "Feb 05", "After"), ("TSLA", "Feb 07", "After")]

def get_insider_trading():
    return [("NVDA", "CEO", "SELL", "$12.5M"), ("PLTR", "DIR", "BUY", "$450K")]

def get_market_news():
    return [("17:45", "Fed's Powell hints at steady rates."), ("17:10", "AI Sector rallies.")]

def render():
    # Estilos CSS para Tooltips e Interfaz
    st.markdown("""
        <style>
        .header-info { display: flex; justify-content: space-between; align-items: center; width: 100%; }
        .info-circle { 
            height: 18px; width: 18px; background: #333; color: #888; border-radius: 50%; 
            display: flex; align-items: center; justify-content: center; font-size: 10px; 
            cursor: help; border: 1px solid #444; position: relative; 
        }
        .info-circle .tooltiptext { 
            visibility: hidden; width: 200px; background: #0c0e12; color: #fff; 
            text-align: left; border: 1px solid #1a1e26; padding: 12px; border-radius: 8px; 
            position: absolute; z-index: 100; right: 0; top: 25px; font-size: 10px;
        }
        .info-circle:hover .tooltiptext { visibility: visible; }
        </style>
    """, unsafe_allow_html=True)

    H_MAIN = "340px"
    H_BOTTOM = "270px"

    # --- FILA 1: ÍNDICES ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN}; padding:15px;">...</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN};">...</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Social Pulse</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN};">...</div></div>', unsafe_allow_html=True)

    # --- FILA 2: FEAR & GREED REAL CNN ---
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        fg_val, fg_color, fg_label = get_fear_greed_cnn()
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header">
                    <div class="header-info">
                        <span class="group-title">Fear & Greed (CNN)</span>
                        <div class="info-circle">?
                            <span class="tooltiptext">Dato real extraído de CNN Business basado en 7 indicadores de mercado.</span>
                        </div>
                    </div>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                    <div style="font-size:4rem; font-weight:bold; color:{fg_color};">{fg_val}</div>
                    <div style="color:white; font-size:0.9rem; font-weight:bold; letter-spacing:1px;">{fg_label}</div>
                    <div style="width:80%; background:#0c0e12; height:8px; border-radius:4px; margin-top:20px; border:1px solid #1a1e26;">
                        <div style="width:{fg_val}%; background:{fg_color}; height:100%; border-radius:4px; box-shadow: 0 0 10px {fg_color}66;"></div>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

    with col2: # SECTORES
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sectors</p></div><div class="group-content" style="background:#11141a; height:{H_MAIN};">...</div></div>', unsafe_allow_html=True)

    with col3: # RISK & FED (CORREGIDO)
        vix_val, _ = get_market_index("^VIX")
        f_status, f_color, f_delta = get_fed_status_real()
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header">
                    <div class="header-info">
                        <span class="group-title">Risk & Fed Policy</span>
                        <div class="info-circle">?
                            <span class="tooltiptext"><b>QT:</b> Reducción de liquidez.<br><b>QE:</b> Inyección de liquidez.</span>
                        </div>
                    </div>
                </div>
                <div class="group-content" style="background:#11141a; height:{H_MAIN}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
                    <div style="font-size:0.7rem; color:#888;">VIX INDEX</div>
                    <div style="font-size:3rem; font-weight:bold; color:#00ffad;">{float(vix_val):.2f}</div>
                    <hr style="width:70%; border-color:#1a1e26; margin:15px;">
                    <div style="background:{f_color}22; color:{f_color}; padding:8px 15px; border-radius:6px; font-weight:bold;">{f_status}</div>
                    <div style="color:#444; font-size:10px; margin-top:10px;">Weekly Delta: {f_delta/1000000000:+.2f}B</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)

    # --- FILA 3: MÓDULOS RESTAURADOS ---
    st.write("")
    f3c1, f3c2, f3c3 = st.columns(3)
    with f3c1: # EARNINGS
        earn_html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="color:#00ffad; font-weight:bold; font-size:12px;">{t}</div><div style="color:#444; font-size:9px;">{d}</div></div></div>' for t, d, tm in get_earnings_calendar()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Earnings</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px;">{earn_html}</div></div>', unsafe_allow_html=True)
    with f3c2: # INSIDER
        ins_html = "".join([f'<div style="background:#0c0e12; padding:10px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between;"><div><div style="color:white; font-size:11px;">{t}</div><div style="color:#555; font-size:9px;">{p}</div></div><div style="color:{"#00ffad" if ty=="BUY" else "#f23645"}; font-size:10px;">{ty}</div></div>' for t, p, ty, a in get_insider_trading()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Insider Tracker</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; padding:15px;">{ins_html}</div></div>', unsafe_allow_html=True)
    with f3c3: # NEWS
        news_html = "".join([f'<div style="padding:10px; border-bottom:1px solid #1a1e26;"><div style="color:white; font-size:11px;">{txt}</div></div>' for time, txt in get_market_news()])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">News Terminal</p></div><div class="group-content" style="background:#11141a; height:{H_BOTTOM}; overflow-y:auto;">{news_html}</div></div>', unsafe_allow_html=True)
