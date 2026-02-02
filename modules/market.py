import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup

def get_buzztickr_data():
    """Extrae el Top 10 con todas las métricas solicitadas de BuzzTickr."""
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        data = []
        table = soup.find('table') 
        if table:
            rows = table.find_all('tr')[1:11] 
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 8:
                    data.append({
                        "rk": cols[0].text.strip(),
                        "tkr": cols[1].text.strip().replace('$', ''),
                        "it": cols[2].text.strip(),
                        "ct": cols[3].text.strip(),
                        "p": cols[4].text.strip(),
                        "c": cols[5].text.strip(),
                        "s": cols[7].text.strip()
                    })
        return data
    except:
        return []

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # --- COLUMNA 1: MARKET INDICES ---
    with col1:
        indices_list = [
            {"label": "S&P 500", "full": "US 500 INDEX", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "NASDAQ COMP", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "INDUSTRIAL AVG", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "SMALL CAP", "t": "^RUT"}
        ]
        
        inner_html = ""
        for idx in indices_list:
            p, c = get_market_index(idx['t'])
            color = "#00ffad" if c >= 0 else "#f23645"
            inner_html += f"""
            <div style="background-color: #0c0e12; padding: 12px; border-radius: 8px; margin-bottom: 8px; display: flex; justify-content: space-between; border: 1px solid #1a1e26;">
                <div>
                    <div style="font-weight: bold; color: white; font-size: 13px;">{idx['label']}</div>
                    <div style="color: #555; font-size: 10px;">{idx['full']}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; color: white;">{p:,.2f}</div>
                    <div style="color: {color}; font-size: 11px; font-weight: bold;">{c:+.2f}%</div>
                </div>
            </div>"""

        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">Market Indices</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 15px;">
                    {inner_html}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --- COLUMNA 2: CREDIT SPREADS ---
    with col2:
        st.markdown("""
            <div class="group-container">
                <div class="group-header"><p class="group-title">US High Yield Credit Spreads</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 10px;">
        """, unsafe_allow_html=True)
        
        components.html("""
            <div style="height:280px; width:100%; border-radius:8px; overflow:hidden;">
              <div id="tv_spread" style="height:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.MediumWidget({"symbols": [["FRED:BAMLH0A0HYM2|1M"]], "chartOnly": true, "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "gridLineColor": "transparent", "trendLineColor": "#2962ff", "container_id": "tv_spread"});
              </script>
            </div>
        """, height=285)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

    # --- COLUMNA 3: BUZZTICKR ---
    with col3:
        tickers = get_buzztickr_data()
        
        # Generamos el HTML de los items primero
        buzz_items_html = ""
        for t in tickers:
            buzz_items_html += f"""
            <div style="background-color: #0c0e12; padding: 6px 4px; border-radius: 4px; margin-bottom: 4px; border: 1px solid #1a1e26; display: grid; grid-template-columns: 20px 45px 1fr 1fr 1fr 1fr 1fr; gap: 2px; text-align: center; align-items: center; font-size: 10px;">
                <span style="color: #444;">{t['rk']}</span>
                <span style="color: #00ffad; font-weight: bold; text-align: left; padding-left: 5px;">{t['tkr']}</span>
                <span style="color: #ccc;">{t['it']}</span>
                <span style="color: #ccc;">{t['ct']}</span>
                <span style="color: #ccc;">{t['p']}</span>
                <span style="color: #ccc;">{t['c']}</span>
                <span style="color: #f23645;">{t['s']}</span>
            </div>"""

        # Metemos todo el bloque (cabecera + items) dentro del group-content
        st.markdown(f"""
            <div class="group-container">
                <div class="group-header"><p class="group-title">BuzzTickr Reddit Top 10</p></div>
                <div class="group-content" style="background-color: #11141a; padding: 15px;">
                    <div style="display: grid; grid-template-columns: 20px 45px 1fr 1fr 1fr 1fr 1fr; gap: 2px; font-size: 9px; color: #555; font-weight: bold; margin-bottom: 10px; text-align: center;">
                        <span>RK</span><span>TKR</span><span>IT</span><span>CT</span><span>P</span><span>C</span><span>S</span>
                    </div>
                    {buzz_items_html}
                </div>
            </div>
        """, unsafe_allow_html=True)
