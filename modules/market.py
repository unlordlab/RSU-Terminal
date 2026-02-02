import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_economic_calendar():
    """Obtiene datos económicos reales mediante scraping (Simulado para estabilidad)."""
    # En un entorno real, usaríamos una API o scraping de Investing
    # Aquí generamos los datos del día para asegurar que el diseño sea perfecto
    today = datetime.now().strftime("%b %d")
    events = [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "high", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "high", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "med", "val": "3.8M", "prev": "-4.5M"},
        {"time": "20:00", "event": "FOMC Meeting Minutes", "imp": "high", "val": "-", "prev": "-"},
    ]
    return events

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # ALTURA MAESTRA UNIFICADA (Píxeles exactos para todas las cajas)
    MASTER_HEIGHT = "400px"

    col1, col2, col3 = st.columns(3)
    
    # --- 1. MARKET INDICES ---
    with col1:
        # (Asumiendo que get_market_index viene de tu config)
        from config import get_market_index 
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        
        indices_html = ""
        for ticker, name in indices:
            price, change = get_market_index(ticker)
            color = "#00ffad" if change >= 0 else "#f23645"
            indices_html += f'''
            <div style="background: #0c0e12; padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #1a1e26; display: flex; justify-content: space-between;">
                <div><div style="font-weight:bold; color:white;">{name}</div><div style="color:#555; font-size:10px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold;">{price:,.2f}</div><div style="color:{color}; font-size:11px;">{change:+.2f}%</div></div>
            </div>'''
            
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px; border-radius:0 0 8px 8px;">{indices_html}</div></div>''', unsafe_allow_html=True)

    # --- 2. ECONOMIC CALENDAR (NATIVO) ---
    with col2:
        events = get_economic_calendar()
        events_html = ""
        for ev in events:
            imp_color = "#f23645" if ev['imp'] == "high" else "#ffa500"
            events_html += f'''
            <div style="padding: 10px; border-bottom: 1px solid #1a1e26; display: flex; align-items: center;">
                <div style="color: #888; font-size: 12px; width: 50px;">{ev['time']}</div>
                <div style="flex-grow: 1; margin-left: 10px;">
                    <div style="color: white; font-size: 12px; font-weight: 500;">{ev['event']}</div>
                    <div style="color: {imp_color}; font-size: 9px; font-weight: bold; text-transform: uppercase;">{ev['imp']} Impact</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: white; font-size: 11px;">{ev['val']}</div>
                    <div style="color: #555; font-size: 9px;">Prev: {ev['prev']}</div>
                </div>
            </div>'''

        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; border-radius:0 0 8px 8px; overflow-y: auto;">{events_html}</div></div>''', unsafe_allow_html=True)

    # --- 3. REDDIT TOP 10 ---
    with col3:
        # Simulación de tickers para mantener el diseño
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "SNDK", "NVDA", "DVLT", "PLTR", "SLS"]
        reddit_html = "".join([f'''
            <div style="background: #0c0e12; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; border: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #444; font-weight: bold; font-size: 11px;">{i+1:02d}</span>
                <span style="color: #00ffad; font-weight: bold; font-size: 13px;">{tkr}</span>
                <span style="color: #f23645; font-size: 9px; font-weight: bold;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
            
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px; border-radius:0 0 8px 8px; overflow-y: auto;">{reddit_html}</div></div>''', unsafe_allow_html=True)

    # --- FILA 2 (Módulos vacíos con altura fija) ---
    st.write("")
    c1, c2, c3 = st.columns(3)
    for i, col in enumerate([c1, c2, c3]):
        with col:
            st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Module 2.{i+1}</p></div><div class="group-content" style="background:#11141a; height:200px; display:flex; align-items:center; justify-content:center; border-radius:0 0 8px 8px; border:1px solid #1a1e26; border-top:none; color:#222; font-weight:bold; letter-spacing:2px;">VOID</div></div>''', unsafe_allow_html=True)
