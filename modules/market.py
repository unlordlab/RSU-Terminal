import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup

def get_buzztickr_data():
    """Extrae el Top 10 con todas las métricas solicitadas."""
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
                if len(cols) >= 8: # Verificamos que existan las columnas
                    data.append({
                        "rank": cols[0].text.strip(),
                        "ticker": cols[1].text.strip().replace('$', ''),
                        "it": cols[2].text.strip(),
                        "ct": cols[3].text.strip(),
                        "posts": cols[4].text.strip(),
                        "comments": cols[5].text.strip(),
                        "spam": cols[7].text.strip()
                    })
        return data
    except:
        return []

def render():
    # Estilo CSS extra para forzar el contenido al fondo oscuro y ajustar la mini-tabla
    st.markdown("""
        <style>
        .inner-dark-box { background-color: #0c0e12; border-radius: 4px; padding: 10px; margin-bottom: 5px; }
        .ticker-grid { 
            display: grid; 
            grid-template-columns: 30px 1fr 1fr 1fr 1fr 1fr 1fr; 
            gap: 5px; 
            font-size: 10px; 
            text-align: center;
            align-items: center;
        }
        .grid-header { color: #555; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # --- COLUMNA 1: MARKET INDICES ---
    with col1:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content">', unsafe_allow_html=True)
        indices = [
            {"label": "S&P 500", "full": "US 500 INDEX", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "NASDAQ COMP", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "INDUSTRIAL AVG", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "SMALL CAP", "t": "^RUT"}
        ]
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            st.markdown(f"""
                <div class="inner-dark-box">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><p class="index-ticker" style="margin:0;">{idx['label']}</p><p class="index-fullname" style="margin:0;">{idx['full']}</p></div>
                        <div style="text-align:right;"><p class="index-price" style="margin:0; font-size:14px;">{p:,.2f}</p><span class="index-delta {color_class}">{c:+.2f}%</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- COLUMNA 2: CREDIT SPREADS ---
    with col2:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">US High Yield Credit Spreads</p></div><div class="group-content">', unsafe_allow_html=True)
        components.html("""
            <div style="height:270px; width:100%; border-radius:4px; overflow:hidden;">
              <div id="tv_spread" style="height:100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.MediumWidget({"symbols": [["FRED:BAMLH0A0HYM2|1M"]], "chartOnly": true, "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "gridLineColor": "transparent", "trendLineColor": "#2962ff", "container_id": "tv_spread"});
              </script>
            </div>
        """, height=275)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- COLUMNA 3: BUZZTICKR (CON TODAS LAS MÉTRICAS) ---
    with col3:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">BuzzTickr Reddit Top 10</p></div><div class="group-content">', unsafe_allow_html=True)
        
        # Cabecera de la mini-tabla
        st.markdown("""
            <div class="ticker-grid grid-header">
                <span>RK</span><span>TKR</span><span>IT</span><span>CT</span><span>P</span><span>C</span><span>S</span>
            </div>
        """, unsafe_allow_html=True)
        
        tickers = get_buzztickr_data()
        for t in tickers:
            st.markdown(f"""
                <div class="inner-dark-box" style="padding: 5px 8px;">
                    <div class="ticker-grid">
                        <span style="color:#555;">{t['rank']}</span>
                        <span style="color:#00ffad; font-weight:bold;">{t['ticker']}</span>
                        <span>{t['it']}</span>
                        <span>{t['ct']}</span>
                        <span>{t['posts']}</span>
                        <span>{t['comments']}</span>
                        <span style="color:#f23645;">{t['spam']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # Filas vacías para estructura
    for row in range(2, 5):
        st.write("---")
        st.columns(3)
