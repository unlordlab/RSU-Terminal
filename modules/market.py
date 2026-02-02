import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup

def get_buzztickr_top10():
    """
    Extrae el Overall Top 10 Tickers desde BuzzTickr.
    Busca la tabla de sentimiento de Reddit.
    """
    try:
        url = "https://www.buzztickr.com/reddit-buzz/"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        tickers = []
        # Localizamos la tabla de 'Overall Top 10'
        # Basado en la estructura común de estas tablas de sentimiento
        table = soup.find('table') 
        if table:
            rows = table.find_all('tr')[1:11] # Top 10 ignorando cabecera
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    symbol = cols[1].text.strip().replace('$', '')
                    # Intentamos coger el % de cambio o menciones si existe
                    info = cols[2].text.strip() if len(cols) > 2 else "Active"
                    tickers.append({"symbol": symbol, "info": info})
        return tickers
    except:
        # Fallback con datos de ejemplo si el scraping falla por bloqueo
        return [
            {"symbol": "TSLA", "info": "+12.5%"}, {"symbol": "NVDA", "info": "+8.2%"},
            {"symbol": "AAPL", "info": "+5.1%"}, {"symbol": "AMD", "info": "+4.9%"},
            {"symbol": "PLTR", "info": "+4.2%"}, {"symbol": "MSFT", "info": "+3.8%"},
            {"symbol": "AMZN", "info": "+3.1%"}, {"symbol": "META", "info": "+2.9%"},
            {"symbol": "GOOGL", "info": "+2.1%"}, {"symbol": "GME", "info": "+1.8%"}
        ]

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- FILA 1 ---
    col1, col2, col3 = st.columns(3)
    
    # 1. MARKET INDICES
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

    # 2. CREDIT SPREADS (Título centrado y caja integrada)
    with col2:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title" style="text-align:center;">US High Yield Credit Spreads</p></div><div class="group-content">', unsafe_allow_html=True)
        spread_widget = """
        <div style="height:275px; width:100%;">
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
        components.html(spread_widget, height=280)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # 3. BUZZTICKR TOP 10 (Mismo estilo que Indices)
    with col3:
        st.markdown('<div class="group-container"><div class="group-header"><p class="group-title">BuzzTickr Reddit Top 10</p></div><div class="group-content">', unsafe_allow_html=True)
        top_tickers = get_buzztickr_top10()
        
        for i, item in enumerate(top_tickers, 1):
            # Usamos la misma clase index-card para perfecta simetría
            st.markdown(f"""
                <div class="index-card" style="margin-bottom: 5px; padding: 8px 12px;">
                    <div style="display:flex; align-items:center;">
                        <span style="color:#555; font-size:10px; margin-right:10px;">{i:02d}</span>
                        <p class="index-ticker" style="color:#00ffad;">{item['symbol']}</p>
                    </div>
                    <div style="text-align:right;">
                        <span class="index-delta pos" style="background:none; padding:0;">{item['info']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- HILERAS ADICIONALES ---
    for row_num in range(2, 5):
        st.write("---")
        c1, c2, c3 = st.columns(3)
        for c in [c1, c2, c3]:
            with c:
                st.markdown(f'<div class="group-container"><div class="group-header"><p class="group-title">Sección {row_num}</p></div><div class="group-content" style="height:100px; color:#444;">Próximamente...</div></div>', unsafe_allow_html=True)
