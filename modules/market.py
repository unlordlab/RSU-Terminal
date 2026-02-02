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
            # Fallback: Búsqueda por patrón si la tabla falla
            raw_text = soup.get_text()
            found = re.findall(r'\b[A-Z]{2,5}\b', raw_text)
            tickers = list(dict.fromkeys(found))[:10]

        return tickers if tickers else ["SLV", "MSFT", "SPY", "GLD", "VOO", "SNDK", "NVDA", "DVLT", "PLTR", "SLS"]
    except:
        return ["SLV", "MSFT", "SPY", "GLD", "VOO", "SNDK", "NVDA", "DVLT", "PLTR", "SLS"]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # Definimos columnas de igual ancho para simetría
    col1, col2, col3 = st.columns(3)
    
    # Altura fija para las cajas oscuras (ajustada para que coincidan)
    BOX_HEIGHT = "380px"

    # --- COLUMNA 1: MARKET INDICES ---
    with col1:
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
                <div class="group-content" style="background-color: #11141a; padding: 15px; height: {BOX_HEIGHT};">
                    {indices_html}
                </div>
            </div>
        ''', unsafe_allow_html=True)

    # --- COLUMNA 2: US HIGH YIELD SPREADS (Widget TradingView) ---
    with col2:
        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">US High Yield Spreads (OAS)</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 10px; height: {BOX_HEIGHT}; overflow: hidden;">
        ''', unsafe_allow_html=True)
        
        # Widget configurado con velas diarias (D) y ticker FRED
        components.html('''
            <div style="height:100%; width:100%; border-radius:8px; overflow:hidden;">
              <div id="tv_spread_chart" style="height:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({
                "autosize": true,
                "symbol": "FRED:BAMLH0A0HYM2",
                "interval": "D",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_top_toolbar": true,
                "hide_legend": true,
                "save_image": false,
                "container_id": "tv_spread_chart",
                "backgroundColor": "#11141a",
                "gridColor": "rgba(42, 46, 57, 0.06)"
              });
              </script>
            </div>
        ''', height=360)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- COLUMNA 3: BUZZTICKR OVERALL TOP 10 ---
    with col3:
        top_10 = get_overall_top_10()
        buzz_items_html = ""
        for i, tkr in enumerate(top_10, 1):
            buzz_items_html += f'''
            <div style="background-color: #0c0e12; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #1a1e26; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #444; font-weight: bold; font-size: 11px;">{i:02d}</span>
                <span style="color: #00ffad; font-weight: bold; font-size: 13px;">{tkr}</span>
                <span style="color: #f23645; font-size: 9px; font-weight: bold;">HOT 🔥</span>
            </div>'''

        st.markdown(f'''
            <div class="group-container">
                <div class="group-header"><p class="group-title">Reddit Top 10 Pulse</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 15px; height: {BOX_HEIGHT}; overflow-y: auto;">
                    {buzz_items_html}
                </div>
            </div>
        ''', unsafe_allow_html=True)
