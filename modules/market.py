import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup
import re

def get_overall_top_10():
    """Extrae los tickers del Top 10 de Reddit Buzz."""
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        tickers = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:11]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 1:
                    tkr = cols[1].text.strip().replace('$', '')
                    if tkr: tickers.append(tkr)
        
        if not tickers:
            raw_text = soup.get_text()
            found = re.findall(r'\b[A-Z]{2,5}\b', raw_text)
            tickers = list(dict.fromkeys(found))[:10]

        return tickers if tickers else ["SPY", "TSLA", "NVDA", "AAPL", "AMD", "MSFT", "QQQ", "GME", "PLTR", "AMZN"]
    except:
        return ["SPY", "TSLA", "NVDA", "AAPL", "AMD", "MSFT", "QQQ", "GME", "PLTR", "AMZN"]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Altura común para la primera fila
    BOX_HEIGHT = "380px"

    # --- FILA 1 ---
    col1, col2, col3 = st.columns(3)
    
    # 1. MARKET INDICES
    with col1:
        indices_list = [
            {"label": "S&P 500", "full": "US 500 INDEX", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "NASDAQ COMP", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "INDUSTRIAL AVG", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "SMALL CAP", "t": "^RUT"}
        ]
        indices_html = "".join([f'''
            <div style="background-color: #0c0e12; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; border: 1px solid #1a1e26;">
                <div>
                    <div style="font-weight: bold; color: white; font-size: 13px;">{idx['label']}</div>
                    <div style="color: #555; font-size: 10px;">{idx['full']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; color: white;">{get_market_index(idx['t'])[0]:,.2f}</div>
                    <div style="color: {"#00ffad" if get_market_index(idx['t'])[1] >= 0 else "#f23645"}; font-size: 11px; font-weight: bold;">{get_market_index(idx['t'])[1]:+.2f}%</div>
                </div>
            </div>''' for idx in indices_list])

        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content" style="background-color: #11141a; padding: 15px; height: {BOX_HEIGHT};">{indices_html}</div></div>''', unsafe_allow_html=True)

    # 2. CALENDARIO ECONÓMICO (Investing.com)
    with col2:
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">Economic Calendar</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 5px; height: {BOX_HEIGHT}; overflow: hidden;">
        ''', unsafe_allow_html=True)
        
        # Widget de calendario económico de Investing.com filtrado a modo oscuro
        components.html('''
            <iframe src="https://sslecal2.investing.com?columns=exc_flags,exc_currency,exc_importance,exc_actual,exc_forecast,exc_previous&category=_unemployment,central_banks,inflation,economic_activity&importance=2,3&features=datepicker,timezone&countries=5&calType=day&timeZone=58&lang=1" 
            width="100%" height="360" frameborder="0" allowtransparency="true" marginwidth="0" marginheight="0" style="filter: invert(0.9) hue-rotate(180deg) brightness(0.9);"></iframe>
        ''', height=365)
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    # 3. BUZZTICKR TOP 10
    with col3:
        top_10 = get_overall_top_10()
        buzz_items = "".join([f'''
            <div style="background-color: #0c0e12; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #444; font-weight: bold; font-size: 11px;">{i+1:02d}</span>
                <span style="color: #00ffad; font-weight: bold; font-size: 13px;">{tkr}</span>
                <span style="color: #f23645; font-size: 9px; font-weight: bold;">HOT 🔥</span>
            </div>''' for i, tkr in enumerate(top_10)])

        st.markdown(f'''<div class="group-container"><div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div><div class="group-content" style="background-color: #11141a; padding: 15px; height: {BOX_HEIGHT}; overflow-y: auto;">{buzz_items}</div></div>''', unsafe_allow_html=True)

    # --- HILERAS ADICIONALES (2, 3, 4) ---
    # Usamos una altura un poco menor para las cajas de expansión futura
    for row_idx in range(2, 5):
        st.write("") 
        cols = st.columns(3)
        for i, c in enumerate(cols):
            with c:
                st.markdown(f'''
                    <div class="group-container">
                        <div class="group-header"><p class="group-title">Modulo {row_idx}.{i+1}</p></div>
                        <div class="group-content" style="background-color: #11141a; height: 250px; display: flex; align-items: center; justify-content: center;">
                            <p style="color: #333; font-size: 0.8rem; font-weight: bold; letter-spacing: 2px;">DISPONIBLE</p>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
