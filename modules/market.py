import streamlit as st
import streamlit.components.v1 as components
from config import get_market_index
import requests
from bs4 import BeautifulSoup

def get_buzztickr_image():
    """Busca la imagen diaria de BuzzTickr."""
    try:
        url = "https://buzztickr.com"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Buscamos la imagen principal (ajusta el selector si cambia en la web)
        img = soup.find("img", {"src": True}) 
        if img:
            src = img['src']
            return src if src.startswith("http") else f"{url}{src}"
    except:
        return None
    return None

def render():
    st.markdown('<h1 style="margin-top:-50px; text-align:center;">Market Dashboard</h1>', unsafe_allow_html=True)
    
    # --- FILA 1: ÍNDICES, SPREADS Y BUZZTICKR ---
    col1, col2, col3 = st.columns(3)
    
    # COLUMNA 1: MARKET INDICES (Compactos)
    with col1:
        st.markdown("""
            <div class="group-container">
                <div class="group-header"><p class="group-title" style="text-align:center;">Market Indices</p></div>
                <div class="group-content">
        """, unsafe_allow_html=True)
        
        indices = [
            {"label": "S&P 500", "full": "US 500", "t": "^GSPC"},
            {"label": "NASDAQ 100", "full": "Tech Cap", "t": "^IXIC"},
            {"label": "DOW JONES", "full": "Industrials", "t": "^DJI"},
            {"label": "RUSSELL 2000", "full": "Small Cap", "t": "^RUT"}
        ]
        
        for idx in indices:
            p, c = get_market_index(idx['t'])
            color_class = "pos" if c >= 0 else "neg"
            st.markdown(f"""
                <div class="index-card" style="margin-bottom: 5px; padding: 8px 12px;">
                    <div>
                        <p class="index-ticker" style="font-size:12px;">{idx['label']}</p>
                    </div>
                    <div style="text-align:right;">
                        <span class="index-delta {color_class}" style="font-size:10px;">{c:+.2f}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # COLUMNA 2: CREDIT SPREADS (Título centrado, sin caja extra)
    with col2:
        st.markdown('<p style="text-align:center; color:#888; font-size:12px; font-weight:bold; text-transform:uppercase;">US High Yield Credit Spreads</p>', unsafe_allow_html=True)
        spread_widget = """
        <div style="height:220px; width:100%; border: 1px solid #2d3439; border-radius:12px; overflow:hidden;">
          <div id="tv_spread" style="height:100%;"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.MediumWidget({
            "symbols": [["FRED:BAMLH0A0HYM2|1M"]],
            "chartOnly": true, "width": "100%", "height": "100%",
            "locale": "en", "colorTheme": "dark", "gridLineColor": "transparent",
            "trendLineColor": "#2962ff", "underLineColor": "rgba(41, 98, 255, 0.15)",
            "container_id": "tv_spread"
          });
          </script>
        </div>
        """
        components.html(spread_widget, height=230)

    # COLUMNA 3: BUZZTICKR IMAGE
    with col3:
        st.markdown("""
            <div class="group-container">
                <div class="group-header"><p class="group-title" style="text-align:center;">BuzzTickr Sentiment</p></div>
                <div class="group-content" style="padding:10px; text-align:center;">
        """, unsafe_allow_html=True)
        
        img_url = get_buzztickr_image()
        if img_url:
            st.image(img_url, use_container_width=True)
        else:
            st.info("Cargando imagen de BuzzTickr...")
        
        st.markdown('</div></div>', unsafe_allow_html=True)

    # --- FILA 2, 3 y 4: ESPACIO PARA MÁS MÓDULOS ---
    # Aquí puedes repetir la estructura de columnas para las siguientes 3 hileras
    for i in range(2, 5):
        st.write("---")
        c1, c2, c3 = st.columns(3)
        with c1: st.caption(f"Sección hilera {i} - Col 1")
        with c2: st.caption(f"Sección hilera {i} - Col 2")
        with c3: st.caption(f"Sección hilera {i} - Col 3")
