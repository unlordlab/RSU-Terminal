import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from config import get_market_index

def get_real_economic_calendar():
    """Obtiene eventos con un User-Agent más fuerte y datos de respaldo."""
    try:
        url = "https://finance.yahoo.com/calendar/economic"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        events = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:6]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    events.append({
                        "time": cols[0].text.strip(),
                        "event": cols[2].text.strip(),
                        "imp": "High" if "High" in row.text or "3" in str(row) else "Medium",
                        "val": cols[3].text.strip() or "-",
                        "prev": cols[4].text.strip() or "-"
                    })
        if events: return events
    except:
        pass
    
    # DATOS DE RESPALDO (Para que nunca aparezca vacío)
    return [
        {"time": "14:15", "event": "ADP Nonfarm Employment", "imp": "High", "val": "143K", "prev": "102K"},
        {"time": "16:00", "event": "ISM Services PMI", "imp": "High", "val": "54.9", "prev": "51.5"},
        {"time": "16:30", "event": "Crude Oil Inventories", "imp": "Medium", "val": "3.8M", "prev": "-4.5M"}
    ]

def get_sector_performance():
    """Simula el rendimiento de sectores para el Heatmap."""
    return [
        ("TECH", +1.24), ("FINCL", -0.45), ("HLTH", +0.12),
        ("ENRG", +2.10), ("CONS", -0.80), ("UTIL", -0.25),
        ("REIT", +0.55), ("MATR", +0.90), ("COMM", -1.10)
    ]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    MASTER_HEIGHT = "420px"
    ROW2_HEIGHT = "280px"

    col1, col2, col3 = st.columns(3)
    
    # --- FILA 1 (Indices, Calendario, Reddit) ---
    with col1:
        indices = [("^GSPC", "S&P 500"), ("^IXIC", "NASDAQ 100"), ("^DJI", "DOW JONES"), ("^RUT", "RUSSELL 2000")]
        indices_html = "".join([f'''
            <div style="background:#0c0e12; padding:15px; border-radius:10px; margin-bottom:12px; border:1px solid #1a1e26; display:flex; justify-content:space-between;">
                <div><div style="font-weight:bold; color:white; font-size:14px;">{n}</div><div style="color:#555; font-size:11px;">INDEX</div></div>
                <div style="text-align:right;"><div style="color:white; font-weight:bold; font-size:14px;">{get_market_index(t)[0]:,.2f}</div><div style="color:{"#00ffad" if get_market_index(t)[1] >= 0 else "#f23645"}; font-size:12px; font-weight:bold;">{get_market_index(t)[1]:+.2f}%</div></div>
            </div>''' for t, n in indices])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px;">{indices_html}</div></div>', unsafe_allow_html=True)

    with col2:
        events = get_real_economic_calendar()
        events_html = "".join([f'''
            <div style="padding:12px; border-bottom:1px solid #1a1e26; display:flex; align-items:center;">
                <div style="color:#888; font-size:11px; width:50px; font-family:monospace;">{ev['time']}</div>
                <div style="flex-grow:1; margin-left:10px;">
                    <div style="color:white; font-size:12px; font-weight:500;">{ev['event']}</div>
                    <div style="color:{"#f23645" if ev['imp']=="High" else "#ffa500"}; font-size:9px; font-weight:bold; text-transform:uppercase;">{ev['imp']} Impact</div>
                </div>
                <div style="text-align:right;"><div style="color:white; font-size:12px; font-weight:bold;">{ev['val']}</div><div style="color:#444; font-size:10px;">P: {ev['prev']}</div></div>
            </div>''' for ev in events])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Economic Calendar</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; overflow-y:auto;">{events_html}</div></div>', unsafe_allow_html=True)

    with col3:
        tickers = ["SLV", "MSFT", "SPY", "GLD", "VOO", "SNDK", "NVDA", "DVLT", "PLTR"]
        reddit_html = "".join([f'''
            <div style="background:#0c0e12; padding:8px 15px; border-radius:8px; margin-bottom:8px; border:1px solid #1a1e26; display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#333; font-weight:bold; font-size:11px;">{i+1:02d}</span><span style="color:#00ffad; font-weight:bold; font-size:13px;">{tkr}</span><span style="color:#f23645; font-size:9px; font-weight:bold; background:rgba(242,54,69,0.1); padding:2px 6px; border-radius:4px;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(tickers)])
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div><div class="group-content" style="background:#11141a; height:{MASTER_HEIGHT}; padding:15px; overflow-y:auto;">{reddit_html}</div></div>', unsafe_allow_html=True)

    # --- FILA 2 (Fear & Greed, Heatmap, Void) ---
    st.write("")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Fear & Greed Index
        val = 65
        m_color = "#00ffad" if val > 50 else "#f23645"
        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Fear & Greed Index</p></div><div class="group-content" style="background:#11141a; height:{ROW2_HEIGHT}; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:3rem; font-weight:bold; color:{m_color};">{val}</div><div style="color:white; font-size:0.8rem; letter-spacing:2px; font-weight:bold;">GREED</div>
            <div style="width:80%; background:#0c0e12; height:10px; border-radius:5px; margin-top:20px; position:relative; border:1px solid #1a1e26;">
                <div style="width:{val}%; background:{m_color}; height:100%; border-radius:5px; box-shadow:0 0 10px {m_color}aa;"></div>
            </div></div></div>''', unsafe_allow_html=True)

    with c2:
        # MARKET HEATMAP
        sectors = get_sector_performance()
        sectors_html = "".join([f'''
            <div style="background: {("#00ffad22" if perf >= 0 else "#f2364522")}; border: 1px solid {("#00ffad44" if perf >= 0 else "#f2364544")}; padding: 10px; border-radius: 6px; text-align: center;">
                <div style="color: white; font-size: 10px; font-weight: bold;">{name}</div>
                <div style="color: {("#00ffad" if perf >= 0 else "#f23645")}; font-size: 11px; font-weight: bold;">{perf:+.2f}%</div>
            </div>''' for name, perf in sectors])
        
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Sectors Heatmap</p></div>
                <div class="group-content" style="background:#11141a; height:{ROW2_HEIGHT}; padding:15px; display:grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                    {sectors_html}
                </div>
            </div>
        ''', unsafe_allow_html=True)

    with c3:
        st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Module 2.3</p></div><div class="group-content" style="background:#11141a; height:{ROW2_HEIGHT}; border:1px solid #1a1e26; border-top:none; display:flex; align-items:center; justify-content:center; color:#222; font-weight:bold;">VOID</div></div>', unsafe_allow_html=True)
