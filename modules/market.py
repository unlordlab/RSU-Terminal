import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import get_market_index

def get_real_economic_calendar():
    """Extrae eventos económicos reales de Yahoo Finance."""
    try:
        url = "https://finance.yahoo.com/calendar/economic"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        events = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:6] # Tomamos los 5 próximos eventos
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    events.append({
                        "time": cols[0].text.strip(),
                        "event": cols[2].text.strip(),
                        "imp": "High" if "High" in row.text else "Medium", # Lógica de impacto simple
                        "val": cols[3].text.strip() if cols[3].text.strip() else "-",
                        "prev": cols[4].text.strip() if cols[4].text.strip() else "-"
                    })
        return events if events else None
    except:
        return None

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- ALTURA MAESTRA ---
    MASTER_HEIGHT = "420px" # Un pelín más alta para que luzca el calendario

    col1, col2, col3 = st.columns(3)
    
    # 1. MARKET INDICES
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = ""
        for ticker, name in indices:
            price, change = get_market_index(ticker)
            color = "#00ffad" if change >= 0 else "#f23645"
            indices_html += f'''
            <div style="background:#0c0e12; padding:15px; border-radius:10px; margin-bottom:12px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
                <div><div style="font-weight:bold; color:white; font-size:14px;">{name}</div><div style="color:#555; font-size:11px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:14px;">{price:,.2f}</div><div style="color:{color}; font-size:12px; font-weight:bold;">{change:+.2f}%</div></div>
            </div>'''
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    # 2. CALENDARIO ECONÓMICO (Conexión Real)
    with col2:
        events = get_real_economic_calendar()
        if not events: # Fallback por si el scraping falla o no hay mercado
            events = [
                {"time": "08:30", "event": "CPI Data Release", "imp": "High", "val": "3.1%", "prev": "3.2%"},
                {"time": "10:00", "event": "Consumer Sentiment", "imp": "Medium", "val": "79.4", "prev": "77.0"}
            ]
        
        events_html = "".join([f'''
            <div style="padding:12px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:12px; width:55px; font-family:monospace;">{ev['time']}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:12px; font-weight:500;">{ev['event']}</div>
                    <div style="color:{"#f23645" if ev['imp']=="High" else "#ffa500"}; font-size:9px; font-weight:bold; text-transform:uppercase;">{ev['imp']} Impact</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:white; font-size:12px; font-weight:bold;">{ev['val']}</div>
                    <div style="color:#444; font-size:10px;">P: {ev['prev']}</div>
                </div>
            </div>''' for ev in events])

        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    # 3. REDDIT TOP 10 (Diseño Unificado)
    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "SNDK", "NVDA", "DVLT", "PLTR"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:11px;">{i+1:02d}</span>
                <span style="color:#00ffad; font-weight:bold; font-size:13px;">{tkr}</span>
                <span style="color:#f23645; font-size:9px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 6px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # --- FILA 2 ---
    st.write("")
    cols2 = st.columns(3)
    for i, c in enumerate(cols2):
        with c:
            st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Module 2.{i+1}</p></div><div class="group-content" style="background:#11141a; height:250px; display:flex; align-items:center; justify-content:center; border:1px solid #1a1e26; border-top:none; color:#222; font-weight:bold; letter-spacing:3px;">VOID</div></div>', unsafe_allow_html=True)
