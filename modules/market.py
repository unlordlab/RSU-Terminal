import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup

def get_buzztickr_top10():
    """Extrae el Overall Top 10 Tickers desde BuzzTickr Reddit Buzz."""
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        tickers = []
        # Buscamos la tabla o lista que contiene el Top 10
        # Se asume estructura de tabla estándar; ajustar selectores si el sitio cambia
        rows = soup.find_all('tr')[1:11]  # Saltamos cabecera y tomamos 10
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                symbol = cols[1].text.strip()
                menciones = cols[2].text.strip() if len(cols) > 2 else "-"
                tickers.append({"symbol": symbol, "mentions": menciones})
        return tickers
    except Exception:
        return []

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    # --- COLUMNA 1: MARKET INDICES ---
    with col1:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">Market Indices</p></div><div class="group-content">', unsafe_allow_html=True)
        indices = [
            {"label": "S&P 500", "full": "US 500 Index", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "Nasdaq Comp", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "Industrial Avg", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "Small Cap", "t": "^RUT"}
        ]
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            st.markdown(f"""
                <div class="index-card">
                    <div><p class="index-ticker">{idx['label']}</p><p class="index-fullname">{idx['full']}</p></div>
                    <div style="text-align:right;"><p class="index-price">{p:,.2f}</p><span class="index-delta {color_class}">{c:+.2f}%</span></div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- COLUMNA 2: CREDIT SPREADS ---
    with col2:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">Credit Spreads (OAS)</p></div><div class="group-content">', unsafe_allow_html=True)
        spread_widget = """
        <div style="height:270px; width:100%; border-radius:8px; overflow:hidden;">
          <div id="tv_spread" style="height:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.MediumWidget({
            "symbols": [["FRED:BAMLH0A0HYM2|1M"]],
            "chartOnly": true, "width": "100%", "height": "100%",
            "locale": "en", "colorTheme": "dark", "gridLineColor": "transparent",
            "trendLineColor": "#2962ff", "underLineColor": "rgba(41, 98, 255, 0.1)",
            "container_id": "tv_spread"
          });
          </script>
        </div>
        """
        components.html(spread_widget, height=275)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- COLUMNA 3: BUZZTICKR OVERALL TOP 10 ---
    with col3:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">BuzzTickr Reddit Top 10</p></div><div class="group-content">', unsafe_allow_html=True)
        top_tickers = get_buzztickr_top10()
        
        if top_tickers:
            for i, item in enumerate(top_tickers, 1):
                st.markdown(f"""
                    <div class="index-card" style="padding: 8px 15px; margin-bottom: 6px;">
                        <div style="display:flex; align-items:center;">
                            <span style="color:#555; font-size:10px; margin-right:10px;">#{i}</span>
                            <p class="index-ticker" style="color:#00ffad;">{item['symbol']}</p>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:11px; color:#888;">{item['mentions']} Mentions</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No se pudieron cargar los datos de BuzzTickr.")
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- FILAS ADICIONALES (Placeholder para mantener armonía) ---
    st.write("---")
    # Aquí puedes añadir más filas con la misma estructura de columnas
