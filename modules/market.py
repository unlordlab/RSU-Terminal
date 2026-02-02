import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup
import re

def get_overall_top_10():
    """Extrae específicamente los nombres de los tickers del Top 10."""
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        tickers = []
        # Buscamos en la tabla, pero si falla, buscamos cualquier texto con formato de Ticker ($TKR o TKR en celdas)
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:11]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 1:
                    tkr = cols[1].text.strip().replace('$', '')
                    if tkr: tickers.append(tkr)
        
        # Si no encontramos nada por tabla, intentamos búsqueda por patrones
        if not tickers:
            raw_text = soup.get_text()
            # Busca palabras de 2 a 5 letras en mayúsculas que suelen ser tickers
            found = re.findall(r'\b[A-Z]{2,5}\b', raw_text)
            tickers = list(dict.fromkeys(found))[:10] # Eliminar duplicados y tomar 10

        return tickers if tickers else None
    except:
        return None

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col_idx, col_spread, col_buzz = st.columns([1, 1, 1])
    
    # --- COLUMNA 1: INDICES (config.py) ---
    with col_idx:
        indices_list = [
            {"label": "S&P 500", "full": "US 500 INDEX", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "NASDAQ COMP", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "INDUSTRIAL AVG", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "SMALL CAP", "t": "^RUT"}
        ]
        
        indices_html = ""
        for idx in indices_list:
            p, c = get_market_index(idx['t']) #
            color = "#00ffad" if c >= 0 else "#f23645"
            indices_html += f'''
            <div style="background-color: #0c0e12; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; border: 1px solid #1a1e26;">
                <div>
                    <div style="font-weight: bold; color: white; font-size: 13px;">{idx['label']}</div>
                    <div style="color: #555; font-size: 10px;">{idx['full']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; color: white;">{p:,.2f}</div>
                    <div style="color: {color}; font-size: 11px; font-weight: bold;">{c:+.2f}%</div>
                </div>
            </div>'''
            
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 15px;">
                    {indices_html}
                </div>
            </div>
        ''', unsafe_allow_html=True)

    # --- COLUMNA 2: CREDIT SPREADS ---
    with col_spread:
        st.markdown('''
            <div class="group-container">
                <div class="group-header"><p class="group-title">US High Yield Spreads</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 10px;">
        ''', unsafe_allow_html=True)
        components.html('''<div style="height:280px; width:100%; border-radius:8px; overflow:hidden;"><div id="tv_spread" style="height:100%;"></div><script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script><script type="text/javascript">new TradingView.MediumWidget({"symbols": [["FRED:BAMLH0A0HYM2|1M"]], "chartOnly": true, "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "gridLineColor": "transparent", "trendLineColor": "#2962ff", "container_id": "tv_spread"});</script></div>''', height=285)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- COLUMNA 3: BUZZTICKR OVERALL TOP 10 ---
    with col_buzz:
        top_10 = get_overall_top_10()
        
        # Si no hay datos, usamos una lista de respaldo para que no se vea vacío mientras carga
        if not top_10:
            top_10 = ["TSLA", "NVDA", "SPY", "AAPL", "AMD", "MSFT", "QQQ", "GME", "PLTR", "AMZN"]
            
        buzz_items_html = ""
        for i, tkr in enumerate(top_10, 1):
            buzz_items_html += f'''
            <div style="background-color: #0c0e12; padding: 10px 15px; border-radius: 8px; margin-bottom: 6px; border: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #444; font-weight: bold; font-size: 12px;">{i:02d}</span>
                <span style="color: #00ffad; font-weight: bold; font-size: 14px; letter-spacing: 1px;">{tkr}</span>
                <span style="color: #2962ff; font-size: 10px;">HOT 🔥</span>
            </div>'''

        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">Overall Top 10 Reddit</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 15px; height: 350px; overflow-y: auto;">
                    {buzz_items_html}
                </div>
            </div>
        ''', unsafe_allow_html=True)
